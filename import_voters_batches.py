#!/usr/bin/env python
"""
استيراد بيانات الناخبين من الدفعات إلى PostgreSQL على Railway
"""
import os
import django
import json
from pathlib import Path
import glob

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings_production')
django.setup()

from django.core.management import call_command
from elections.models import Voter

def import_voters_from_batches():
    """استيراد الناخبين من ملفات الدفعات"""
    
    print("=" * 70)
    print("استيراد بيانات الناخبين إلى قاعدة البيانات الإنتاجية")
    print("=" * 70)
    
    # تحديد مجلد الدفعات
    batch_dir = Path('voter_batches')
    log_file = Path('import_log.txt')
    
    def log(msg):
        print(msg)
        with open(log_file, 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"[{datetime.now()}] {msg}\n")
            
    log("=" * 70)
    log("استيراد بيانات الناخبين إلى قاعدة البيانات الإنتاجية")
    log("=" * 70)
    zip_file = Path('voter_batches.zip')
    if zip_file.exists() and not batch_dir.exists():
        log(f"\n📦 تم العثور على ملف مضغوط: {zip_file}")
        log("🔄 جاري فك الضغط...")
        import zipfile
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall('.')
        log("✅ تم فك الضغط بنجاح")

    # Fix for literal backslashes in filenames (Windows style zip extracted on Linux)
    for f in Path('.').glob('voter_batches\\*'):
        try:
            log(f"🔧 إصلاح مسار الملف: {f.name}")
            # Create the directory if it doesn't exist
            os.makedirs('voter_batches', exist_ok=True)
            # Move the file to the real directory
            new_path = Path('voter_batches') / f.name.split('\\')[-1]
            import shutil
            shutil.move(str(f), str(new_path))
        except Exception as e:
            log(f"⚠️ فشل إصلاح المسار {f.name}: {e}")

    if not batch_dir.exists():
        # Check if files were extracted to root instead
        if Path('manifest.json').exists() or list(Path('.').glob('voters_batch_*.json')):
            log("⚠️  تم استخراج الملفات في المجلد الرئيسي بدلاً من voter_batches")
            batch_dir = Path('.')
        else:
            log(f"\n❌ خطأ: المجلد {batch_dir} غير موجود، ولم يتم العثور على ملفات في المجلد الرئيسي!")
            log(f"محتويات المجلد الحالي: {[f.name for f in Path('.').glob('*') if f.is_file()]}")
            return False
    
    # قراءة ملف التوصيف (manifest)
    manifest_file = batch_dir / 'manifest.json'
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        log(f"\n📋 معلومات الدفعات:")
        log(f"   - إجمالي الناخبين: {manifest.get('total_voters', 'N/A')}")
        log(f"   - عدد الدفعات: {manifest.get('total_batches', len(manifest.get('files', [])))}")
        
        batch_files = []
        for f in manifest['files']:
             # Always try three possibilities:
             # 1. Path as is (relative to CWD)
             # 2. Path joined with batch_dir
             # 3. Path's basename only (if flattened)
             
             p1 = Path(f)
             p2 = batch_dir / f
             p3 = Path(Path(f).name)
             
             if p1.exists():
                 batch_files.append(p1)
             elif p2.exists():
                 batch_files.append(p2)
             elif p3.exists():
                 batch_files.append(p3)
             else:
                 # Default to p2 and let it fail later or keep looking
                 batch_files.append(p2)
    else:
        # البحث التلقائي عن ملفات الدفعات
        batch_files = sorted(batch_dir.glob('voters_batch_*.json'))
        log(f"\n📋 تم العثور على {len(batch_files)} ملف دفعة")
    
    if not batch_files:
        log("\n❌ لم يتم العثور على ملفات دفعات!")
        return False
    
    # عرض الحجم الإجمالي
    total_size = sum(os.path.getsize(f) for f in batch_files) / 1024 / 1024
    log(f"   - الحجم الإجمالي: {total_size:.1f} MB")
    
    # التحقق من قاعدة البيانات الحالية
    current_count = Voter.objects.count()
    if current_count > 0:
        log(f"\n⚠️  تحذير: يوجد بالفعل {current_count:,} ناخب في قاعدة البيانات")
        # response = input("هل تريد المتابعة والإضافة؟ (y/n): ")
        # if response.lower() != 'y':
        #     log("تم الإلغاء")
        #     return False
    
    log(f"\n🔄 بدء الاستيراد...")
    log("⏳ هذا قد يستغرق 30-60 دقيقة حسب سرعة الاتصال...")
    
    imported_count = 0
    errors = []
    
    # Smart Resume Mapping (Filename -> Last PK)
    # This allows us to skip batches that are already fully imported
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
        "voters_batch_037.json": 5208,    "voters_batch_038.json": 1107
    }

    for i, batch_file in enumerate(batch_files, 1):
        file_size = os.path.getsize(batch_file) / 1024 / 1024
        
        # Check if already imported
        last_pk = batch_last_pks.get(batch_file.name)
        if last_pk:
            if Voter.objects.filter(pk=last_pk).exists():
                log(f"   [{i:3d}/{len(batch_files)}] {batch_file.name}: ⏭️ تخطي (موجود مسبقاً)")
                continue

        try:
            log(f"\n   [{i:3d}/{len(batch_files)}] {batch_file.name} ({file_size:.1f} MB)...")
            
            # استيراد الدفعة
            call_command('loaddata', str(batch_file), verbosity=0, ignorenonexistent=True)
            
            # عد السجلات الحالية
            new_count = Voter.objects.count()
            batch_imported = new_count - imported_count
            imported_count = new_count
            
            log(f" ✅ ({batch_imported:,} سجل)")
            
        except Exception as e:
            log(f" ❌ فشل")
            errors.append({
                'file': batch_file.name,
                'error': str(e)
            })
            log(f"       خطأ: {e}")
    
    # ملخص النتائج
    log(f"\n" + "=" * 70)
    log(f"✅ اكتمل الاستيراد!")
    log(f"=" * 70)
    log(f"\n📊 النتائج:")
    log(f"   - تم استيراد: {imported_count:,} ناخب")
    log(f"   - ملفات ناجحة: {len(batch_files) - len(errors)}/{len(batch_files)}")
    
    if errors:
        log(f"\n⚠️  أخطاء ({len(errors)}):")
        for error in errors:
            log(f"   - {error['file']}: {error['error']}")
    
    # التحقق النهائي
    final_count = Voter.objects.count()
    log(f"\n✅ إجمالي الناخبين في القاعدة: {final_count:,}")
    
    return True

if __name__ == '__main__':
    try:
        import_voters_from_batches()
    except KeyboardInterrupt:
        log("\n\n⚠️ تم الإيقاف بواسطة المستخدم")
        log("💡 يمكنك إعادة تشغيل السكريبت وسيتابع من حيث توقف")
    except Exception as e:
        log(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        log(traceback.format_exc())
