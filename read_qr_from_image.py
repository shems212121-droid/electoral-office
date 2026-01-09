"""
قراءة QR من صورة وإدخال البيانات في نظام الجرد
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')

import django
django.setup()

from PIL import Image
from pyzbar.pyzbar import decode
from elections.barcode_views import parse_barcode_data
from elections.models import PollingCenter, PollingStation, BarcodeScanSession, BarcodeScanRecord
from django.contrib.auth.models import User

def read_qr_from_image(image_path):
    """قراءة QR من صورة"""
    try:
        img = Image.open(image_path)
        decoded_objects = decode(img)
        
        if not decoded_objects:
            print("❌ لم يتم العثور على QR في الصورة")
            return None
        
        # أخذ أول QR وجد
        qr_data = decoded_objects[0].data.decode('utf-8')
        print(f"✅ تم قراءة QR: {qr_data}")
        return qr_data
        
    except Exception as e:
        print(f"❌ خطأ في قراءة الصورة: {e}")
        return None

def process_qr_data(qr_data):
    """معالجة بيانات QR"""
    print("\n" + "="*60)
    print("📊 معالجة بيانات QR")
    print("="*60)
    
    print(f"\n🔍 البيانات الخام:")
    print(f"   {qr_data[:100]}...")
    
    # صيغة المفوضية: TYPE-CENTER-STATION-...
    # مثال: 2-19520102-5-4-...
    parts = qr_data.split('-')
    
    if len(parts) >= 3:
        qr_type = parts[0]  # نوع QR
        center_code_full = parts[1]  # الكود الكامل
        station_number = parts[2]  # رقم المحطة
        
        # استخراج رقم المركز (أول 6 أرقام من الكود)
        center_number = center_code_full[:6] if len(center_code_full) >= 6 else center_code_full
        
        print(f"\n📝 البيانات المستخرجة (صيغة المفوضية):")
        print(f"   • نوع QR: {qr_type} ({'تصويت عام' if qr_type == '2' else 'تصويت خاص'})")
        print(f"   • الكود الكامل: {center_code_full}")
        print(f"   • رقم المركز: {center_number}")
        print(f"   • رقم المحطة: {station_number}")
        
        # البحث عن المركز باستخدام رقم المحطة الكامل
        # في نظام المفوضية قد يكون رقم المحطة هو الرقم الكامل
        center = PollingCenter.objects.filter(
            center_number=center_number
        ).first()
        
        if not center:
            # محاولة أخرى: البحث باستخدام جزء من رقم المحطة
            # أول 5 أرقام قد تكون رقم المركز
            alt_center_num = station_number[:5] if len(station_number) >= 5 else center_number
            center = PollingCenter.objects.filter(
                center_number__startswith=alt_center_num
            ).first()
        
        if center:
            print(f"\n✅ المركز موجود في قاعدة البيانات:")
            print(f"   • رقم المركز: {center.center_number}")
            print(f"   • الاسم: {center.name}")
            print(f"   • الموقع: {center.location}")
            print(f"   • النوع: {center.get_voting_type_display()}")
            
            # التحقق من نوع التصويت
            if qr_type == '2':  # 2 = تصويت عام
                expected_type = 'general'
            elif qr_type == '1':  # 1 = تصويت خاص  
                expected_type = 'special'
            else:
                expected_type = 'general'
            
            if center.voting_type != expected_type:
                print(f"\n⚠️  تحذير: نوع المركز '{center.get_voting_type_display()}' لا يطابق نوع QR")
            
            # البحث عن المحطة
            # في نظام المفوضية، رقم المحطة الكامل هو center_number + station_number
            station = None
            
            # محاولة 1: البحث برقم المحطة الكامل
            station = PollingStation.objects.filter(
                full_number=station_number
            ).first()
            
            # محاولة 2: البحث برقم المحطة فقط
            if not station and len(parts) >= 3:
                try:
                    station_num = int(parts[2])
                    station = PollingStation.objects.filter(
                        center=center,
                        station_number=station_num
                    ).first()
                except:
                    pass
            
            if station:
                print(f"\n✅ المحطة موجودة:")
                print(f"   • رقم المحطة: {station.station_number}")
                print(f"   • الرقم الكامل: {station.full_number}")
                return center, station, {'center': center_number, 'station': station_number, 'qr_type': qr_type}
            else:
                print(f"\n⚠️  المحطة غير موجودة في قاعدة البيانات")
                print(f"   سيتم استخدام معلومات QR كما هي")
                return center, None, {'center': center_number, 'station': station_number, 'qr_type': qr_type}
        else:
            print(f"\n❌ المركز رقم {center_number} (أو {station_number[:5]}) غير موجود في قاعدة البيانات")
            return None, None, {'center': center_number, 'station': station_number, 'qr_type': qr_type}
    
    else:
        # استخدام المحلل القديم
        parsed = parse_barcode_data(qr_data)
        
        print(f"\n📝 البيانات المستخرجة:")
        print(f"   • رقم المركز: {parsed['center_number']}")
        print(f"   • رقم المحطة: {parsed['station_number']}")
        print(f"   • نوع التصويت: {parsed['vote_type']}")
        
        center = PollingCenter.objects.filter(
            center_number=parsed['center_number']
        ).first()
        
        return center, None, parsed

def create_scan_record(qr_data, center, station):
    """إنشاء سجل مسح"""
    print("\n" + "="*60)
    print("💾 إنشاء سجل المسح")
    print("="*60)
    
    # الحصول على أو إنشاء مستخدم
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.first()
    
    # الحصول على أو إنشاء جلسة نشطة
    session = BarcodeScanSession.objects.filter(
        operator=user,
        status='active',
        vote_type='general'
    ).first()
    
    if not session:
        session = BarcodeScanSession.objects.create(
            operator=user,
            vote_type='general'
        )
        print(f"\n✅ تم إنشاء جلسة جديدة: {session.session_code}")
    else:
        print(f"\n✅ استخدام الجلسة النشطة: {session.session_code}")
    
    # تحليل البيانات
    parsed = parse_barcode_data(qr_data)
    
    # التحقق من التكرار
    existing = BarcodeScanRecord.objects.filter(
        center_number=parsed['center_number'],
        station_number=parsed['station_number'],
        status__in=['validated', 'processed']
    ).first()
    
    if existing:
        print(f"\n⚠️  تحذير: هذه المحطة تم مسحها مسبقاً!")
        print(f"   • الجلسة: {existing.session.session_code}")
        print(f"   • التاريخ: {existing.scanned_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"   • المشغل: {existing.operator.username if existing.operator else 'غير معروف'}")
        return None
    
    # إنشاء السجل
    scan_record = BarcodeScanRecord.objects.create(
        session=session,
        operator=user,
        barcode_data=qr_data,
        barcode_type='QR_CODE',
        center_number=parsed['center_number'],
        station_number=parsed['station_number'],
        vote_type='general',
        polling_center=center,
        polling_station=station,
        status='validated' if station else 'pending'
    )
    
    # تحديث إحصائيات الجلسة
    session.total_scans += 1
    if station:
        session.successful_scans += 1
    else:
        session.failed_scans += 1
    session.save()
    
    print(f"\n✅ تم إنشاء السجل بنجاح!")
    print(f"   • رقم السجل: {scan_record.id}")
    print(f"   • الحالة: {scan_record.get_status_display()}")
    print(f"   • الرمز الكامل: {scan_record.get_full_station_code()}")
    
    return scan_record

def main():
    print("="*60)
    print("🔍 قراءة QR من الصورة")
    print("="*60)
    
    image_path = 'qr1.jpg'
    
    if not os.path.exists(image_path):
        print(f"❌ الصورة غير موجودة: {image_path}")
        return
    
    # قراءة QR
    qr_data = read_qr_from_image(image_path)
    if not qr_data:
        return
    
    # معالجة البيانات
    center, station, qr_info = process_qr_data(qr_data)
    
    if not center:
        print("\n❌ فشلت العملية: المركز غير موجود")
        print(f"\n💡 نصيحة: تأكد من استيراد بيانات المراكز من ملفات Excel:")
        print(f"   • مراكز الاقتراع العام.xlsx")
        print(f"   • مراكز الاقتراع الخاص.xlsx")
        return
    
    # إنشاء السجل
    scan_record = create_scan_record(qr_data, center, station)
    
    if scan_record:
        print("\n" + "="*60)
        print("✅ تمت العملية بنجاح!")
        print("="*60)
        print(f"\nمعلومات السجل:")
        print(f"   • رقم السجل: {scan_record.id}")
        print(f"   • المركز: {center.name}")
        if station:
            print(f"   • المحطة: {station.full_number}")
        print(f"   • الجلسة: {scan_record.session.session_code}")
        print(f"\nيمكنك الآن:")
        print(f"1. عرض السجل في واجهة الجرد العام")
        print(f"2. إكمال إدخال أصوات المرشحين")
        print(f"3. مراجعة الإحصائيات")
    else:
        print("\n⚠️  تنبيه: السجل موجود مسبقاً")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
