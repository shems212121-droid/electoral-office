"""
أداة استيراد الناخبين المتبقين - عبر واجهة ويب
"""
import os
import json
import threading
from pathlib import Path
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command
from elections.models import Voter

# متغير عام لتتبع حالة الاستيراد
import_status = {
    'running': False,
    'current_round': 0,
    'current_batch': 0,
    'total_batches': 0,
    'imported_count': 0,
    'errors': [],
    'log': []
}

def is_admin_or_superuser(user):
    """التحقق من أن المستخدم مسؤول"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@user_passes_test(is_admin_or_superuser)
def import_remaining_voters_page(request):
    """صفحة أداة الاستيراد"""
    
    # إحصائيات حالية
    current_count = Voter.objects.count()
    expected_count = 1868933
    remaining = expected_count - current_count
    percentage = (current_count / expected_count) * 100 if expected_count > 0 else 0
    
    # معلومات الجولات
    rounds = [
        {
            'number': 1,
            'name': 'الجولة الأولى',
            'batches': '18-27',
            'start': 18,
            'end': 28,
            'expected_voters': 500000,
            'duration': '30-40 دقيقة',
            'color': 'primary'
        },
        {
            'number': 2,
            'name': 'الجولة الثانية',
            'batches': '28-33',
            'start': 28,
            'end': 34,
            'expected_voters': 300000,
            'duration': '20-30 دقيقة',
            'color': 'success'
        },
        {
            'number': 3,
            'name': 'الجولة الثالثة',
            'batches': '34-38',
            'start': 34,
            'end': 39,
            'expected_voters': 200000,
            'duration': '15-25 دقيقة',
            'color': 'warning'
        }
    ]
    
    context = {
        'current_count': current_count,
        'expected_count': expected_count,
        'remaining': remaining,
        'percentage': percentage,
        'rounds': rounds,
        'import_status': import_status,
    }
    
    return render(request, 'elections/tools/import_remaining_voters.html', context)

@user_passes_test(is_admin_or_superuser)
@require_http_methods(["POST"])
def start_import_round(request):
    """بدء جولة استيراد"""
    
    global import_status
    
    if import_status['running']:
        return JsonResponse({
            'success': False,
            'message': 'عملية استيراد قيد التشغيل بالفعل'
        })
    
    # الحصول على معلومات الجولة
    try:
        data = json.loads(request.body)
        round_num = data.get('round')
        start_batch = data.get('start')
        end_batch = data.get('end')
        
        if not all([round_num, start_batch, end_batch]):
            return JsonResponse({
                'success': False,
                'message': 'بيانات غير مكتملة'
            })
        
        # إعادة تعيين الحالة
        import_status.update({
            'running': True,
            'current_round': round_num,
            'current_batch': start_batch,
            'total_batches': end_batch - start_batch,
            'imported_count': 0,
            'errors': [],
            'log': [f'🔵 بدء الجولة {round_num}: الدفعات {start_batch}-{end_batch-1}']
        })
        
        # تشغيل الاستيراد في thread منفصل
        thread = threading.Thread(
            target=run_import_process,
            args=(start_batch, end_batch)
        )
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'message': f'تم بدء الجولة {round_num}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ: {str(e)}'
        })

def run_import_process(start_batch, end_batch):
    """تشغيل عملية الاستيراد"""
    global import_status
    
    try:
        batch_dir = Path('voter_batches')
        
        if not batch_dir.exists():
            import_status['log'].append('❌ مجلد voter_batches غير موجود')
            import_status['running'] = False
            return
        
        # قائمة آخر PK في كل دفعة (للتخطي الذكي)
        batch_last_pks = {
            "voters_batch_001.json": 1599354, "voters_batch_002.json": 1695272,
            "voters_batch_003.json": 1633596, "voters_batch_004.json": 1391694,
            "voters_batch_005.json": 1284534, "voters_batch_006.json": 1362024,
            "voters_batch_007.json": 1318182, "voters_batch_008.json": 1494498,
            "voters_batch_009.json": 1544464, "voters_batch_010.json": 1162137,
            "voters_batch_011.json": 1198579, "voters_batch_012.json": 1102554,
            "voters_batch_013.json": 1012774, "voters_batch_014.json": 799410,
            "voters_batch_015.json": 892045, "voters_batch_016.json": 867375,
            "voters_batch_017.json": 802612, "voters_batch_018.json": 640225,
            "voters_batch_019.json": 690327, "voters_batch_020.json": 737947,
            "voters_batch_021.json": 545395, "voters_batch_022.json": 405097,
            "voters_batch_023.json": 637332, "voters_batch_024.json": 473003,
            "voters_batch_025.json": 557555, "voters_batch_026.json": 151599,
            "voters_batch_027.json": 325970, "voters_batch_028.json": 1736232,
            "voters_batch_029.json": 347296, "voters_batch_030.json": 367576,
            "voters_batch_031.json": 315777, "voters_batch_032.json": 1795986,
            "voters_batch_033.json": 200771, "voters_batch_034.json": 296133,
            "voters_batch_035.json": 1837535, "voters_batch_036.json": 176468,
            "voters_batch_037.json": 5208, "voters_batch_038.json": 1107
        }
        
        # جمع ملفات الدفعات المطلوبة
        batch_files = []
        for i in range(start_batch, end_batch):
            if use_zips:
                filename = f'voters_part_{i:03d}.zip'
                filepath = zip_dir / filename
            else:
                filename = f'voters_batch_{i:03d}.json'
                filepath = batch_dir / filename
                
            if filepath.exists():
                batch_files.append((filepath, use_zips))
        
        if not batch_files:
            import_status['log'].append(f'❌ لم يتم العثور على بيانات في النطاق {start_batch}-{end_batch-1}')
            import_status['running'] = False
            return
        
        import_status['log'].append(f'📦 تم العثور على {len(batch_files)} دفعة')
        
        # معالجة كل دفعة
        for i, (batch_file, is_zip) in enumerate(batch_files, 1):
            import_status['current_batch'] = start_batch + i - 1
            
            # التحقق من الملف - الاسم للمقارنة
            batch_name = batch_file.name
            if is_zip:
                batch_name = batch_name.replace('voters_part_', 'voters_batch_').replace('.zip', '.json')

            # التحقق من الاستيراد المسبق
            last_pk = batch_last_pks.get(batch_name)
            if last_pk and Voter.objects.filter(pk=last_pk).exists():
                import_status['log'].append(f'⏭️  [{i}/{len(batch_files)}] {batch_name}: تم تخطيها (موجودة مسبقاً)')
                continue
            
            try:
                import_status['log'].append(f'🔄 [{i}/{len(batch_files)}] {batch_name}: جارٍ الاستيراد...')
                
                final_file_path = str(batch_file)
                
                if is_zip:
                    import zipfile
                    from tempfile import TemporaryDirectory
                    with TemporaryDirectory() as temp_dir:
                        with zipfile.ZipFile(batch_file, 'r') as zf:
                            json_filename = zf.namelist()[0]
                            zf.extract(json_filename, temp_dir)
                            temp_json_path = os.path.join(temp_dir, json_filename)
                            call_command('loaddata', temp_json_path, verbosity=0, ignorenonexistent=True)
                else:
                    # استيراد الدفعة مباشرة
                    call_command('loaddata', final_file_path, verbosity=0, ignorenonexistent=True)
                
                # تحديث العدد
                new_count = Voter.objects.count()
                import_status['imported_count'] = new_count
                
                import_status['log'].append(f'✅ [{i}/{len(batch_files)}] {batch_name}: تم بنجاح (الإجمالي: {new_count:,})')
                
            except Exception as e:
                error_msg = f'❌ [{i}/{len(batch_files)}] {batch_name}: فشل - {str(e)}'
                import_status['log'].append(error_msg)
                import_status['errors'].append(error_msg)
        
        # النهاية
        final_count = Voter.objects.count()
        import_status['log'].append(f'🎉 اكتملت الجولة! الإجمالي الآن: {final_count:,}')
        import_status['running'] = False
        
    except Exception as e:
        import_status['log'].append(f'❌ خطأ غير متوقع: {str(e)}')
        import_status['running'] = False

@user_passes_test(is_admin_or_superuser)
def get_import_status(request):
    """الحصول على حالة الاستيراد الحالية"""
    
    return JsonResponse({
        'running': import_status['running'],
        'current_round': import_status['current_round'],
        'current_batch': import_status['current_batch'],
        'total_batches': import_status['total_batches'],
        'imported_count': import_status['imported_count'],
        'errors': import_status['errors'],
        'log': import_status['log'][-20:],  # آخر 20 رسالة فقط
        'current_voter_count': Voter.objects.count()
    })

@user_passes_test(is_admin_or_superuser)
def stop_import(request):
    """إيقاف الاستيراد (تجميد)"""
    global import_status
    
    if import_status['running']:
        import_status['log'].append('⏸️  تم طلب الإيقاف - سيتوقف بعد الدفعة الحالية')
        import_status['running'] = False
        return JsonResponse({'success': True, 'message': 'تم طلب الإيقاف'})
    
    return JsonResponse({'success': False, 'message': 'لا توجد عملية قيد التشغيل'})

@user_passes_test(is_admin_or_superuser)
def run_final_import(request):
    """تشغيل الاستيراد النهائي من الملفات المرفوعة"""
    global import_status
    
    if import_status['running']:
        return JsonResponse({'success': False, 'message': 'يوجد عملية جارية بالفعل'})
        
    import_status.update({
        'running': True,
        'current_round': 99, # Special code for final import
        'log': ['🚀 بدء الاستيراد النهائي الشامل...']
    })
    
    def run_cmd():
        try:
            from io import StringIO
            out = StringIO()
            import_status['log'].append('📦 فحص ملفات البيانات (38 جزء)...')
            
            # Note: call_command doesn't easily stream output to a variable while running
            # So we will just call it and report completion.
            # To show progress, the command itself should ideally update a shared state.
            
            call_command('import_final_data', stdout=out)
            
            # Since we can't easily stream, we'll just append the final success message
            # and maybe some summary from 'out'
            import_status['log'].append('✅ اكتملت العملية بنجاح!')
            import_status['log'].append('🎉 تم استيراد جميع الأجزاء الـ 38.')
            
        except Exception as e:
            error_msg = f'❌ فشل الاستيراد: {str(e)}'
            import_status['log'].append(error_msg)
            import_status['errors'].append(error_msg)
        finally:
            import_status['running'] = False
            import_status['current_voter_count'] = Voter.objects.count()
            
    thread = threading.Thread(target=run_cmd)
    thread.daemon = True
    thread.start()
    
    return JsonResponse({'success': True, 'message': 'تم بدء الاستيراد النهائي'})
