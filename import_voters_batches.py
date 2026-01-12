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
    
    if not batch_dir.exists():
        print(f"\n❌ خطأ: المجلد {batch_dir} غير موجود!")
        print("تأكد من رفع ملفات الدفعات أولاً")
        return False
    
    # قراءة ملف التوصيف (manifest)
    manifest_file = batch_dir / 'manifest.json'
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        print(f"\n📋 معلومات الدفعات:")
        print(f"   - إجمالي الناخبين: {manifest['total_voters']:,}")
        print(f"   - عدد الدفعات: {manifest['total_batches']}")
        
        batch_files = [batch_dir / f for f in manifest['files']]
    else:
        # البحث التلقائي عن ملفات الدفعات
        batch_files = sorted(batch_dir.glob('voters_batch_*.json'))
        print(f"\n📋 تم العثور على {len(batch_files)} ملف دفعة")
    
    if not batch_files:
        print("\n❌ لم يتم العثور على ملفات دفعات!")
        return False
    
    # عرض الحجم الإجمالي
    total_size = sum(os.path.getsize(f) for f in batch_files) / 1024 / 1024
    print(f"   - الحجم الإجمالي: {total_size:.1f} MB")
    
    # التحقق من قاعدة البيانات الحالية
    current_count = Voter.objects.count()
    if current_count > 0:
        print(f"\n⚠️  تحذير: يوجد بالفعل {current_count:,} ناخب في قاعدة البيانات")
        response = input("هل تريد المتابعة والإضافة؟ (y/n): ")
        if response.lower() != 'y':
            print("تم الإلغاء")
            return False
    
    print(f"\n🔄 بدء الاستيراد...")
    print("⏳ هذا قد يستغرق 30-60 دقيقة حسب سرعة الاتصال...")
    
    imported_count = 0
    errors = []
    
    for i, batch_file in enumerate(batch_files, 1):
        file_size = os.path.getsize(batch_file) / 1024 / 1024
        
        try:
            print(f"\n   [{i:3d}/{len(batch_files)}] {batch_file.name} ({file_size:.1f} MB)...", end='', flush=True)
            
            # استيراد الدفعة
            call_command('loaddata', str(batch_file), verbosity=0)
            
            # عد السجلات الحالية
            new_count = Voter.objects.count()
            batch_imported = new_count - imported_count
            imported_count = new_count
            
            print(f" ✅ ({batch_imported:,} سجل)")
            
        except Exception as e:
            print(f" ❌ فشل")
            errors.append({
                'file': batch_file.name,
                'error': str(e)
            })
            print(f"       خطأ: {e}")
    
    # ملخص النتائج
    print(f"\n" + "=" * 70)
    print(f"✅ اكتمل الاستيراد!")
    print(f"=" * 70)
    print(f"\n📊 النتائج:")
    print(f"   - تم استيراد: {imported_count:,} ناخب")
    print(f"   - ملفات ناجحة: {len(batch_files) - len(errors)}/{len(batch_files)}")
    
    if errors:
        print(f"\n⚠️  أخطاء ({len(errors)}):")
        for error in errors:
            print(f"   - {error['file']}: {error['error']}")
    
    # التحقق النهائي
    final_count = Voter.objects.count()
    print(f"\n✅ إجمالي الناخبين في القاعدة: {final_count:,}")
    
    return True

if __name__ == '__main__':
    try:
        import_voters_from_batches()
    except KeyboardInterrupt:
        print("\n\n⚠️ تم الإيقاف بواسطة المستخدم")
        print("💡 يمكنك إعادة تشغيل السكريبت وسيتابع من حيث توقف")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()
