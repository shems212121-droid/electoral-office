#!/usr/bin/env python
"""
سكريبت للتحقق من الدفعات المستوردة وتحديد المتبقي
"""
import os
import django
import json
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from elections.models import Voter

# قائمة آخر PK في كل دفعة (من import_voters_batches.py)
BATCH_LAST_PKS = {
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

def check_imported_batches():
    """التحقق من الدفعات المستوردة"""
    
    print("=" * 70)
    print("🔍 فحص الدفعات المستوردة")
    print("=" * 70)
    
    # العدد الحالي
    current_count = Voter.objects.count()
    expected_count = 1868933
    
    print(f"\n📊 الإحصائيات الحالية:")
    print(f"   - الموجود حالياً: {current_count:,}")
    print(f"   - المتوقع: {expected_count:,}")
    print(f"   - المتبقي: {expected_count - current_count:,}")
    print(f"   - النسبة: {(current_count/expected_count)*100:.1f}%")
    
    print(f"\n🔍 فحص الدفعات...")
    
    imported = []
    missing = []
    
    for i in range(1, 39):
        batch_name = f"voters_batch_{i:03d}.json"
        last_pk = BATCH_LAST_PKS.get(batch_name)
        
        if last_pk and Voter.objects.filter(pk=last_pk).exists():
            imported.append(i)
            status = "✅"
        else:
            missing.append(i)
            status = "❌"
        
        print(f"   {status} الدفعة {i:02d}: {batch_name}")
    
    print(f"\n" + "=" * 70)
    print("📋 الملخص")
    print("=" * 70)
    
    print(f"\n✅ الدفعات المستوردة ({len(imported)}):")
    if imported:
        # عرض النطاقات
        ranges = []
        start = imported[0]
        prev = imported[0]
        
        for batch in imported[1:]:
            if batch == prev + 1:
                prev = batch
            else:
                ranges.append(f"{start}-{prev}" if start != prev else str(start))
                start = batch
                prev = batch
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        
        print(f"   الدفعات: {', '.join(ranges)}")
    
    print(f"\n❌ الدفعات المفقودة ({len(missing)}):")
    if missing:
        # عرض النطاقات
        ranges = []
        start = missing[0]
        prev = missing[0]
        
        for batch in missing[1:]:
            if batch == prev + 1:
                prev = batch
            else:
                ranges.append(f"{start}-{prev}" if start != prev else str(start))
                start = batch
                prev = batch
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        
        print(f"   الدفعات: {', '.join(ranges)}")
    
    # حساب العدد المتوقع في الدفعات المفقودة
    batch_dir = Path('voter_batches')
    if batch_dir.exists():
        missing_voters = 0
        for batch_num in missing:
            batch_file = batch_dir / f"voters_batch_{batch_num:03d}.json"
            if batch_file.exists():
                # تقدير تقريبي: كل دفعة ~50,000 سجل
                with open(batch_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    missing_voters += len(data)
        
        print(f"\n📊 عدد الناخبين المتوقع في الدفعات المفقودة: {missing_voters:,}")
    
    print(f"\n💡 التوصيات:")
    if missing:
        # تقسيم إلى جولات
        if len(missing) > 15:
            split1 = missing[:10]
            split2 = missing[10:16]
            split3 = missing[16:]
            
            print(f"\n   نوصي بتقسيم الاستيراد إلى 3 جولات:")
            print(f"\n   🔵 الجولة 1: الدفعات {split1[0]}-{split1[-1]}")
            print(f"      IMPORT_START_BATCH={split1[0]} IMPORT_END_BATCH={split1[-1]+1} python import_voters_batches.py")
            
            if split2:
                print(f"\n   🟢 الجولة 2: الدفعات {split2[0]}-{split2[-1]}")
                print(f"      IMPORT_START_BATCH={split2[0]} IMPORT_END_BATCH={split2[-1]+1} python import_voters_batches.py")
            
            if split3:
                print(f"\n   🟡 الجولة 3: الدفعات {split3[0]}-{split3[-1]}")
                print(f"      IMPORT_START_BATCH={split3[0]} IMPORT_END_BATCH={split3[-1]+1} python import_voters_batches.py")
        else:
            print(f"\n   يمكن استيراد الدفعات المتبقية في جولة واحدة:")
            print(f"   IMPORT_START_BATCH={missing[0]} IMPORT_END_BATCH={missing[-1]+1} python import_voters_batches.py")
    else:
        print(f"   ✅ جميع الدفعات مستوردة! لا حاجة لإجراء إضافي.")
    
    print("\n" + "=" * 70)
    print("✅ اكتمل الفحص")
    print("=" * 70)

if __name__ == '__main__':
    try:
        check_imported_batches()
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
