from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db import transaction
import json
from datetime import datetime, timedelta

from .models import (
    BarcodeScanSession, BarcodeScanRecord,
    PollingCenter, PollingStation, PartyCandidate, VoteCount
)
from .decorators import role_required


# ==================== Barcode Scanner Main View ====================

@login_required
@role_required(['admin', 'supervisor', 'data_entry_votes'])
def barcode_scanner(request):
    """صفحة الماسح الضوئي الرئيسية"""
    
    # Get or create active session for this user
    active_session = BarcodeScanSession.objects.filter(
        operator=request.user,
        status='active'
    ).first()
    
    # Get recent scans from active session
    recent_scans = []
    if active_session:
        recent_scans = BarcodeScanRecord.objects.filter(
            session=active_session
        ).order_by('-scanned_at')[:10]
    
    # Get overall statistics for user
    total_sessions = BarcodeScanSession.objects.filter(operator=request.user).count()
    total_scans = BarcodeScanRecord.objects.filter(operator=request.user).count()
    successful_scans = BarcodeScanRecord.objects.filter(
        operator=request.user, 
        status='processed'
    ).count()
    
    context = {
        'active_session': active_session,
        'recent_scans': recent_scans,
        'total_sessions': total_sessions,
        'total_scans': total_scans,
        'successful_scans': successful_scans,
        'page_title': 'ماسح الباركود - جرد الأصوات',
    }
    
    return render(request, 'elections/barcode_scanner.html', context)


# ==================== Session Management APIs ====================

@login_required
@require_http_methods(["POST"])
def start_scan_session(request):
    """بدء جلسة مسح جديدة"""
    try:
        data = json.loads(request.body)
        vote_type = data.get('vote_type', 'general')
        
        # Check if user has an active session
        active_session = BarcodeScanSession.objects.filter(
            operator=request.user,
            status='active'
        ).first()
        
        if active_session:
            return JsonResponse({
                'success': False,
                'error': 'لديك جلسة نشطة بالفعل. يرجى إنهائها أولاً.',
                'session_code': active_session.session_code
            })
        
        # Create new session
        session = BarcodeScanSession.objects.create(
            operator=request.user,
            vote_type=vote_type
        )
        
        return JsonResponse({
            'success': True,
            'session_code': session.session_code,
            'session_id': session.id,
            'message': 'تم بدء جلسة المسح بنجاح'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ: {str(e)}'
        }, status=400)


@login_required
@require_http_methods(["POST"])
def end_scan_session(request, session_id):
    """إنهاء جلسة المسح"""
    try:
        session = get_object_or_404(
            BarcodeScanSession, 
            id=session_id,
            operator=request.user
        )
        
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()
        
        return JsonResponse({
            'success': True,
            'message': 'تم إنهاء الجلسة بنجاح',
            'stats': {
                'total_scans': session.total_scans,
                'successful': session.successful_scans,
                'failed': session.failed_scans,
                'duplicates': session.duplicate_scans,
                'success_rate': session.get_success_rate()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ: {str(e)}'
        }, status=400)


# ==================== Barcode Processing API ====================

@login_required
@require_http_methods(["POST"])
def process_barcode_scan(request):
    """معالجة بيانات مسح الباركود"""
    try:
        data = json.loads(request.body)
        
        barcode_data = data.get('barcode_data', '')
        barcode_type = data.get('barcode_type', '')
        session_id = data.get('session_id')
        
        if not barcode_data:
            return JsonResponse({
                'success': False,
                'error': 'بيانات الباركود مفقودة'
            }, status=400)
        
        # Get active session
        if session_id:
            session = get_object_or_404(
                BarcodeScanSession,
                id=session_id,
                operator=request.user,
                status='active'
            )
        else:
            # Get or create active session
            session, created = BarcodeScanSession.objects.get_or_create(
                operator=request.user,
                status='active',
                defaults={'vote_type': 'general'}
            )
        
        # Parse barcode data
        parsed_data = parse_barcode_data(barcode_data)
        
        # Check for duplicates - مع معلومات أكثر تفصيلاً
        duplicate_info = check_duplicate_scan_detailed(
            parsed_data['center_number'], 
            parsed_data['station_number'],
            session
        )
        
        if duplicate_info['is_duplicate']:
            session.duplicate_scans += 1
            session.total_scans += 1
            session.save()
            
            return JsonResponse({
                'success': False,
                'error': duplicate_info['message'],
                'status': 'duplicate',
                'duplicate_details': {
                    'previous_session': duplicate_info.get('session_code'),
                    'scan_date': duplicate_info.get('scan_date'),
                    'operator': duplicate_info.get('operator')
                }
            })
        
        # Create scan record
        with transaction.atomic():
            scan_record = BarcodeScanRecord.objects.create(
                session=session,
                operator=request.user,
                barcode_data=barcode_data,
                barcode_type=barcode_type,
                center_number=parsed_data.get('center_number', ''),
                station_number=parsed_data.get('station_number', ''),
                vote_type=parsed_data.get('vote_type', session.vote_type),
                scan_date=parsed_data.get('scan_date'),
                total_votes=parsed_data.get('total_votes'),
                valid_votes=parsed_data.get('valid_votes'),
                invalid_votes=parsed_data.get('invalid_votes'),
                vote_data=parsed_data.get('vote_data')
            )
            
            # Try to link to existing polling center/station
            link_to_polling_station(scan_record)
            
            # Validate extracted data
            validation_result = validate_scan_data(scan_record)
            
            if validation_result['valid']:
                scan_record.status = 'validated'
                session.successful_scans += 1
            else:
                scan_record.status = 'error'
                scan_record.validation_errors = '\n'.join(validation_result['errors'])
                session.failed_scans += 1
            
            scan_record.save()
            
            # Update session stats
            session.total_scans += 1
            session.save()
        
        return JsonResponse({
            'success': True,
            'scan_id': scan_record.id,
            'status': scan_record.status,
            'data': {
                'center_number': scan_record.center_number,
                'station_number': scan_record.station_number,
                'full_station_code': scan_record.get_full_station_code(),
                'vote_type': scan_record.vote_type,
                'total_votes': scan_record.total_votes,
                'valid_votes': scan_record.valid_votes,
                'invalid_votes': scan_record.invalid_votes,
                'polling_center': scan_record.polling_center.name if scan_record.polling_center else None,
                'polling_station': scan_record.polling_station.full_number if scan_record.polling_station else None
            },
            'validation': validation_result,
            'session_stats': {
                'total_scans': session.total_scans,
                'successful': session.successful_scans,
                'failed': session.failed_scans,
                'success_rate': session.get_success_rate()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في المعالجة: {str(e)}'
        }, status=500)


# ==================== Helper Functions ====================

def parse_barcode_data(barcode_raw):
    """
    تحليل بيانات الباركود واستخراج المعلومات
    
    Format examples for IHEC barcodes:
    - Simple: "CENTER_NUMBER-STATION_NUMBER"
    - Complex: JSON with more details
    """
    parsed = {
        'center_number': '',
        'station_number': '',
        'vote_type': 'general',
        'scan_date': None,
        'total_votes': None,
        'valid_votes': None,
        'invalid_votes': None,
        'vote_data': {}
    }
    
    try:
        # تنظيف البيانات من الفراغات والأحرف غير المرغوبة
        barcode_clean = barcode_raw.strip()
        
        # Try to parse as JSON first
        if barcode_clean.startswith('{'):
            data = json.loads(barcode_clean)
            
            # استخراج رقم المركز (دعم صيغ مختلفة)
            parsed['center_number'] = str(data.get('center', data.get('center_number', ''))).strip()
            
            # استخراج رقم المحطة (دعم صيغ مختلفة)
            parsed['station_number'] = str(data.get('station', data.get('station_number', ''))).strip()
            
            parsed['vote_type'] = data.get('vote_type', 'general')
            parsed['total_votes'] = data.get('total_votes')
            parsed['valid_votes'] = data.get('valid_votes')
            parsed['invalid_votes'] = data.get('invalid_votes')
            parsed['vote_data'] = data.get('vote_data', {})
            
            if data.get('date'):
                try:
                    parsed['scan_date'] = datetime.strptime(data['date'], '%Y-%m-%d').date()
                except:
                    pass
        
        # Try simple dash-separated format
        elif '-' in barcode_clean:
            parts = barcode_clean.split('-')
            if len(parts) >= 2:
                # تنظيف أرقام المركز والمحطة
                parsed['center_number'] = parts[0].strip()
                parsed['station_number'] = parts[1].strip()
                
                # If there are more parts, try to parse them
                if len(parts) > 2:
                    for i, part in enumerate(parts[2:]):
                        if part.strip().isdigit():
                            if not parsed['total_votes']:
                                parsed['total_votes'] = int(part.strip())
                            elif not parsed['valid_votes']:
                                parsed['valid_votes'] = int(part.strip())
        
        # Fallback: use entire string as center number
        else:
            parsed['center_number'] = barcode_clean
        
        # التحقق النهائي: التأكد من عدم وجود قيم فارغة
        if parsed['center_number']:
            parsed['center_number'] = parsed['center_number'].strip()
        if parsed['station_number']:
            parsed['station_number'] = parsed['station_number'].strip()
            
    except Exception as e:
        print(f"Error parsing barcode: {e}")
        # Return with just the raw data as center number
        parsed['center_number'] = barcode_raw.strip()
    
    return parsed


def link_to_polling_station(scan_record):
    """
    ربط سجل المسح بمركز ومحطة الاقتراع في قاعدة البيانات
    مع التحقق من دقة البيانات المدخلة
    """
    try:
        # Find polling center - التحقق من وجود رقم المركز
        if not scan_record.center_number:
            print(f"Warning: No center number provided in scan record {scan_record.id}")
            return
        
        # البحث عن المركز بدقة
        center = PollingCenter.objects.filter(
            center_number=scan_record.center_number.strip()
        ).first()
        
        if center:
            scan_record.polling_center = center
            
            # Find polling station - التحقق من وجود رقم المحطة
            if scan_record.station_number:
                try:
                    # تحويل رقم المحطة إلى عدد صحيح
                    station_num = int(scan_record.station_number)
                    
                    station = PollingStation.objects.filter(
                        center=center,
                        station_number=station_num
                    ).first()
                    
                    if station:
                        scan_record.polling_station = station
                        print(f"Successfully linked to station: {station.full_number}")
                    else:
                        print(f"Warning: Station {station_num} not found in center {center.center_number}")
                        
                except ValueError:
                    print(f"Error: Invalid station number format: {scan_record.station_number}")
        else:
            print(f"Warning: Center {scan_record.center_number} not found in database")
        
        scan_record.save()
        
    except Exception as e:
        print(f"Error linking to polling station: {e}")
        import traceback
        traceback.print_exc()


def validate_scan_data(scan_record):
    """التحقق من صحة البيانات المستخرجة"""
    errors = []
    warnings = []
    
    # Check if center number exists
    if not scan_record.center_number:
        errors.append("رقم المركز مفقود")
    
    # Check if station number exists
    if not scan_record.station_number:
        errors.append("رقم المحطة مفقود")
    
    # Check if polling center found in database
    if scan_record.center_number and not scan_record.polling_center:
        warnings.append(f"مركز الاقتراع رقم {scan_record.center_number} غير موجود في قاعدة البيانات")
    
    # Check if polling station found
    if scan_record.station_number and scan_record.polling_center and not scan_record.polling_station:
        warnings.append(f"المحطة رقم {scan_record.station_number} غير موجودة في قاعدة البيانات")
    
    # Check vote counts validity
    if scan_record.total_votes and scan_record.valid_votes and scan_record.invalid_votes:
        if scan_record.total_votes != (scan_record.valid_votes + scan_record.invalid_votes):
            errors.append("مجموع الأصوات الصحيحة والباطلة لا يساوي الإجمالي")
    
    scan_record.validation_warnings = '\n'.join(warnings)
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def check_duplicate_scan(center_number, station_number, session):
    """
    التحقق من وجود مسح مكرر عبر جميع الجلسات
    يتحقق من:
    1. نفس الجلسة الحالية
    2. أي جلسة سابقة تم معالجتها بنجاح
    """
    # التحقق من التكرار عبر جميع الجلسات (ليس فقط الجلسة الحالية)
    duplicate_in_any_session = BarcodeScanRecord.objects.filter(
        center_number=center_number,
        station_number=station_number,
        status__in=['validated', 'processed']
    ).exists()
    
    if duplicate_in_any_session:
        return True
    
    # التحقق إضافي من التكرار في الجلسة الحالية (حتى لو لم تتم المعالجة بعد)
    duplicate_in_current_session = BarcodeScanRecord.objects.filter(
        session=session,
        center_number=center_number,
        station_number=station_number
    ).exclude(status='error').exists()
    
    return duplicate_in_current_session


def check_duplicate_scan_detailed(center_number, station_number, session):
    """
    التحقق من وجود مسح مكرر مع إرجاع معلومات تفصيلية
    
    Returns:
        dict: {
            'is_duplicate': bool,
            'message': str,
            'session_code': str (optional),
            'scan_date': str (optional),
            'operator': str (optional)
        }
    """
    # أولاً: التحقق من التكرار في جلسات سابقة تمت معالجتها
    previous_scan = BarcodeScanRecord.objects.filter(
        center_number=center_number,
        station_number=station_number,
        status__in=['validated', 'processed']
    ).select_related('session', 'operator').first()
    
    if previous_scan:
        scan_date = previous_scan.scanned_at.strftime('%Y-%m-%d %H:%M')
        operator_name = previous_scan.operator.username if previous_scan.operator else 'غير معروف'
        
        return {
            'is_duplicate': True,
            'message': f'⚠️ تم مسح هذه المحطة مسبقاً في جلسة سابقة ({previous_scan.session.session_code})',
            'session_code': previous_scan.session.session_code,
            'scan_date': scan_date,
            'operator': operator_name
        }
    
    # ثانياً: التحقق من التكرار في الجلسة الحالية
    current_scan = BarcodeScanRecord.objects.filter(
        session=session,
        center_number=center_number,
        station_number=station_number
    ).exclude(status='error').first()
    
    if current_scan:
        scan_date = current_scan.scanned_at.strftime('%Y-%m-%d %H:%M')
        
        return {
            'is_duplicate': True,
            'message': '⚠️ تم مسح هذه المحطة مسبقاً في نفس الجلسة الحالية',
            'session_code': session.session_code,
            'scan_date': scan_date,
            'operator': current_scan.operator.username if current_scan.operator else 'غير معروف'
        }
    
    # لا يوجد تكرار
    return {
        'is_duplicate': False,
        'message': ''
    }



# ==================== Scan Records Management ====================

@login_required
@role_required(['admin', 'supervisor'])
def approve_and_process_scan(request, scan_id):
    """الموافقة على المسح ومعالجته (إضافته إلى جدول جرد الأصوات)"""
    try:
        scan_record = get_object_or_404(BarcodeScanRecord, id=scan_id)
        
        if scan_record.status != 'validated':
            return JsonResponse({
                'success': False,
                'error': 'لا يمكن معالجة هذا المسح. يجب أن تكون الحالة "تم التحقق"'
            })
        
        if not scan_record.polling_station:
            return JsonResponse({
                'success': False,
                'error': 'لا يمكن المعالجة. المحطة غير مربوطة في قاعدة البيانات'
            })
        
        # Process vote data and create VoteCount records
        with transaction.atomic():
            created_count = 0
            
            if scan_record.vote_data:
                for candidate_id, vote_count in scan_record.vote_data.items():
                    try:
                        candidate = PartyCandidate.objects.get(id=int(candidate_id))
                        
                        # Create or update vote count
                        vote_obj, created = VoteCount.objects.update_or_create(
                            station=scan_record.polling_station,
                            candidate=candidate,
                            vote_type=scan_record.vote_type,
                            defaults={
                                'vote_count': int(vote_count),
                                'entered_by': request.user,
                                'notes': f'تم الإدخال عبر مسح الباركود - جلسة: {scan_record.session.session_code}'
                            }
                        )
                        
                        if created:
                            created_count += 1
                            
                    except PartyCandidate.DoesNotExist:
                        continue
            
            # Mark as processed
            scan_record.status = 'processed'
            scan_record.is_processed = True
            scan_record.processed_at = timezone.now()
            scan_record.processed_by = request.user
            scan_record.save()
            
            # Update station counting status
            if scan_record.polling_station:
                scan_record.polling_station.counting_status = 'completed'
                scan_record.polling_station.valid_votes = scan_record.valid_votes or 0
                scan_record.polling_station.invalid_votes = scan_record.invalid_votes or 0
                scan_record.polling_station.save()
        
        return JsonResponse({
            'success': True,
            'message': f'تمت المعالجة بنجاح. تم إنشاء {created_count} سجل أصوات',
            'created_count': created_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في المعالجة: {str(e)}'
        }, status=500)


# ==================== Session List and Details ====================

@login_required
def scan_sessions_list(request):
    """قائمة جلسات المسح"""
    sessions = BarcodeScanSession.objects.all().order_by('-started_at')
    
    # Filter by user if not admin
    if not request.user.is_superuser:
        sessions = sessions.filter(operator=request.user)
    
    context = {
        'sessions': sessions,
        'page_title': 'جلسات مسح الباركود'
    }
    
    return render(request, 'elections/scan_sessions_list.html', context)


@login_required
def scan_session_detail(request, pk):
    """تفاصيل جلسة مسح معينة"""
    session = get_object_or_404(BarcodeScanSession, pk=pk)
    
    # Get all scans for this session
    scans = BarcodeScanRecord.objects.filter(session=session).order_by('-scanned_at')
    
    # Calculate statistics
    stats = {
        'total': scans.count(),
        'validated': scans.filter(status='validated').count(),
        'processed': scans.filter(status='processed').count(),
        'rejected': scans.filter(status='rejected').count(),
        'duplicates': scans.filter(status='duplicate').count(),
        'errors': scans.filter(status='error').count(),
    }
    
    context = {
        'session': session,
        'scans': scans,
        'stats': stats,
        'page_title': f'جلسة المسح: {session.session_code}'
    }
    
    return render(request, 'elections/scan_session_detail.html', context)


@login_required
@role_required(['admin', 'supervisor'])
def vote_count_report(request):
    """تقرير جرد الأصوات من المسح الضوئي"""
    
    # Get processed scans
    processed_scans = BarcodeScanRecord.objects.filter(
        status='processed'
    ).select_related('polling_center', 'polling_station', 'session')
    
    # Get filters from request
    center_filter = request.GET.get('center')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    vote_type = request.GET.get('vote_type')
    
    if center_filter:
        processed_scans = processed_scans.filter(center_number=center_filter)
    
    if date_from:
        processed_scans = processed_scans.filter(scanned_at__date__gte=date_from)
    
    if date_to:
        processed_scans = processed_scans.filter(scanned_at__date__lte=date_to)
    
    if vote_type:
        processed_scans = processed_scans.filter(vote_type=vote_type)
    
    # Calculate totals
    totals = processed_scans.aggregate(
        total_scans=Count('id'),
        total_votes=Sum('total_votes'),
        total_valid=Sum('valid_votes'),
        total_invalid=Sum('invalid_votes')
    )
    
    # Get unique centers
    centers = PollingCenter.objects.filter(
        barcode_scans__status='processed'
    ).distinct()
    
    context = {
        'processed_scans': processed_scans[:100],  # Limit for performance
        'totals': totals,
        'centers': centers,
        'page_title': 'تقرير جرد الأصوات'
    }
    
    return render(request, 'elections/vote_count_report.html', context)
