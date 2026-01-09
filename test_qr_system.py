"""
سكريبت اختبار نظام QR المحسّن
يختبر:
1. قراءة QR بصيغ مختلفة
2. منع التكرار
3. دقة البيانات
"""

from elections.models import BarcodeScanSession, BarcodeScanRecord, PollingCenter, PollingStation
from django.contrib.auth.models import User
from elections.barcode_views import (
    parse_barcode_data,
    check_duplicate_scan_detailed,
    link_to_polling_station
)

def test_qr_system():
    print("=" * 60)
    print("🧪 اختبار نظام QR المحسّن")
    print("=" * 60)
    
    # إنشاء مستخدم للاختبار
    user, _ = User.objects.get_or_create(username='test_qr_user')
    
    # إنشاء جلسة اختبارية
    session = BarcodeScanSession.objects.create(
        operator=user,
        vote_type='general'
    )
    print(f"\n✅ تم إنشاء جلسة اختبارية: {session.session_code}\n")
    
    # ===== اختبار 1: تحليل QR بصيغة JSON =====
    print("📝 اختبار 1: تحليل QR بصيغة JSON")
    json_qr = '{"center": "12345", "station": "3", "vote_type": "general"}'
    parsed_json = parse_barcode_data(json_qr)
    print(f"   المدخل: {json_qr}")
    print(f"   المركز: {parsed_json['center_number']}")
    print(f"   المحطة: {parsed_json['station_number']}")
    print(f"   النوع: {parsed_json['vote_type']}")
    assert parsed_json['center_number'] == '12345', "خطأ في قراءة رقم المركز"
    assert parsed_json['station_number'] == '3', "خطأ في قراءة رقم المحطة"
    print("   ✅ نجح الاختبار\n")
    
    # ===== اختبار 2: تحليل QR بصيغة CENTER-STATION =====
    print("📝 اختبار 2: تحليل QR بصيغة CENTER-STATION")
    simple_qr = "12345-3"
    parsed_simple = parse_barcode_data(simple_qr)
    print(f"   المدخل: {simple_qr}")
    print(f"   المركز: {parsed_simple['center_number']}")
    print(f"   المحطة: {parsed_simple['station_number']}")
    assert parsed_simple['center_number'] == '12345', "خطأ في قراءة رقم المركز"
    assert parsed_simple['station_number'] == '3', "خطأ في قراءة رقم المحطة"
    print("   ✅ نجح الاختبار\n")
    
    # ===== اختبار 3: تنظيف البيانات من الفراغات =====
    print("📝 اختبار 3: تنظيف البيانات من الفراغات")
    messy_qr = "  12345  -  3  "
    parsed_messy = parse_barcode_data(messy_qr)
    print(f"   المدخل: '{messy_qr}'")
    print(f"   المركز: '{parsed_messy['center_number']}'")
    print(f"   المحطة: '{parsed_messy['station_number']}'")
    assert parsed_messy['center_number'] == '12345', "فشل تنظيف رقم المركز"
    assert parsed_messy['station_number'] == '3', "فشل تنظيف رقم المحطة"
    print("   ✅ نجح الاختبار\n")
    
    # ===== اختبار 4: منع التكرار =====
    print("📝 اختبار 4: منع التكرار")
    
    # إنشاء سجل أول
    scan1 = BarcodeScanRecord.objects.create(
        session=session,
        operator=user,
        barcode_data="12345-3",
        center_number="12345",
        station_number="3",
        status='validated'
    )
    print(f"   ✅ تم إنشاء السجل الأول: {scan1.id}")
    
    # محاولة تكرار في نفس الجلسة
    duplicate_check = check_duplicate_scan_detailed("12345", "3", session)
    print(f"   🔍 فحص التكرار في نفس الجلسة:")
    print(f"      - هل مكرر؟ {duplicate_check['is_duplicate']}")
    print(f"      - الرسالة: {duplicate_check['message']}")
    assert duplicate_check['is_duplicate'] == True, "فشل في اكتشاف التكرار"
    print("   ✅ نجح الاختبار\n")
    
    # ===== اختبار 5: التكرار عبر جلسات مختلفة =====
    print("📝 اختبار 5: التكرار عبر جلسات مختلفة")
    
    # إنشاء جلسة جديدة
    session2 = BarcodeScanSession.objects.create(
        operator=user,
        vote_type='general'
    )
    print(f"   ✅ تم إنشاء جلسة جديدة: {session2.session_code}")
    
    # محاولة تكرار في الجلسة الجديدة
    duplicate_check2 = check_duplicate_scan_detailed("12345", "3", session2)
    print(f"   🔍 فحص التكرار في جلسة مختلفة:")
    print(f"      - هل مكرر؟ {duplicate_check2['is_duplicate']}")
    print(f"      - الرسالة: {duplicate_check2['message']}")
    print(f"      - الجلسة السابقة: {duplicate_check2.get('session_code')}")
    assert duplicate_check2['is_duplicate'] == True, "فشل في اكتشاف التكرار عبر الجلسات"
    assert duplicate_check2['session_code'] == session.session_code, "خطأ في رمز الجلسة"
    print("   ✅ نجح الاختبار\n")
    
    # ===== اختبار 6: السماح بمسح محطة جديدة =====
    print("📝 اختبار 6: السماح بمسح محطة جديدة")
    duplicate_check3 = check_duplicate_scan_detailed("12346", "1", session)
    print(f"   🔍 فحص محطة جديدة:")
    print(f"      - هل مكرر؟ {duplicate_check3['is_duplicate']}")
    assert duplicate_check3['is_duplicate'] == False, "خطأ: تم اكتشاف تكرار لمحطة جديدة"
    print("   ✅ نجح الاختبار\n")
    
    # ===== اختبار 7: ربط بمركز حقيقي (إذا وجد) =====
    print("📝 اختبار 7: ربط بمركز حقيقي")
    real_center = PollingCenter.objects.first()
    if real_center:
        real_station = real_center.stations.first()
        if real_station:
            scan_real = BarcodeScanRecord.objects.create(
                session=session2,
                operator=user,
                barcode_data=f"{real_center.center_number}-{real_station.station_number}",
                center_number=str(real_center.center_number),
                station_number=str(real_station.station_number),
                status='pending'
            )
            
            link_to_polling_station(scan_real)
            scan_real.refresh_from_db()
            
            print(f"   المركز: {real_center.name}")
            print(f"   المحطة: {real_station.full_number}")
            print(f"   ربط المركز: {'✅' if scan_real.polling_center else '❌'}")
            print(f"   ربط المحطة: {'✅' if scan_real.polling_station else '❌'}")
            
            assert scan_real.polling_center == real_center, "فشل ربط المركز"
            assert scan_real.polling_station == real_station, "فشل ربط المحطة"
            print("   ✅ نجح الاختبار\n")
        else:
            print("   ⚠️ لا توجد محطات للاختبار\n")
    else:
        print("   ⚠️ لا توجد مراكز للاختبار\n")
    
    # تنظيف بيانات الاختبار
    print("🧹 تنظيف بيانات الاختبار...")
    BarcodeScanRecord.objects.filter(session__in=[session, session2]).delete()
    session.delete()
    session2.delete()
    print("   ✅ تم التنظيف\n")
    
    print("=" * 60)
    print("✅ جميع الاختبارات نجحت!")
    print("=" * 60)

if __name__ == '__main__':
    test_qr_system()
