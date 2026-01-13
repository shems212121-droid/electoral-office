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
        log(f"   - إجمالي الناخبين: {manifest['total_voters']:,}")
        log(f"   - عدد الدفعات: {manifest['total_batches']}")
        
        # If paths in manifest are relative, we need to join them with batch_dir
        # but if batch_dir is '.', and files in manifest have 'voter_batches/' prefix, we need to handle that.
        
        batch_files = []
        for f in manifest['files']:
            # If we are in root (batch_dir is '.'), but manifest says 'voter_batches/file.json', 
            # we need to check if 'voter_batches/file.json' exists OR if 'file.json' exists directly.
            
            p = batch_dir / f
            if not p.exists() and batch_dir == Path('.'):
                 # Try stripping parent dir from manifest path
                 p_alt = Path(Path(f).name)
                 if p_alt.exists():
                     p = p_alt
            
            batch_files.append(p)
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
    
    for i, batch_file in enumerate(batch_files, 1):
        file_size = os.path.getsize(batch_file) / 1024 / 1024
        
        try:
            log(f"\n   [{i:3d}/{len(batch_files)}] {batch_file.name} ({file_size:.1f} MB)...")
            
            # استيراد الدفعة
            call_command('loaddata', str(batch_file), verbosity=0)
            
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
