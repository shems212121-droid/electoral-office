#!/usr/bin/env python
"""
تصدير بيانات الناخبين على دفعات صغيرة لتسهيل النقل
"""
import os
import django
import json
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from elections.models import Voter
from django.core import serializers

# حجم كل دفعة (batch)
BATCH_SIZE = 50000  # 50 ألف ناخب لكل ملف

def export_voters_in_batches():
    """تصدير الناخبين على دفعات"""
    
    print("=" * 70)
    print("تصدير بيانات الناخبين على دفعات")
    print("=" * 70)
    
    # إنشاء مجلد للدفعات
    batch_dir = Path('voter_batches')
    batch_dir.mkdir(exist_ok=True)
    
    # حساب العدد الإجمالي
    total_voters = Voter.objects.count()
    total_batches = (total_voters // BATCH_SIZE) + 1
    
    print(f"\n📊 إحصائيات:")
    print(f"   - إجمالي الناخبين: {total_voters:,}")
    print(f"   - حجم الدفعة: {BATCH_SIZE:,}")
    print(f"   - عدد الدفعات: {total_batches}")
    print(f"   - الحجم المتوقع: ~{total_voters * 0.5 / 1024:.1f} MB")
    
    print(f"\n🔄 بدء التصدير...")
    
    batch_num = 0
    for offset in range(0, total_voters, BATCH_SIZE):
        batch_num += 1
        
        # جلب الدفعة الحالية
        voters = Voter.objects.all()[offset:offset + BATCH_SIZE]
        
        # تصدير كـ JSON
        filename = batch_dir / f'voters_batch_{batch_num:03d}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            serializers.serialize('json', voters, stream=f,use_natural_foreign_keys=True, use_natural_primary_keys=True)
        
        # حساب حجم الملف
        file_size = os.path.getsize(filename) / 1024 / 1024
        
        # عرض التقدم
        progress = (offset + len(voters)) / total_voters * 100
        print(f"   [{batch_num:3d}/{total_batches}] "
              f"{offset + len(voters):,} / {total_voters:,} "
              f"({progress:.1f}%) - {file_size:.1f} MB")
    
    print(f"\n✅ اكتمل التصدير!")
    print(f"   - تم إنشاء {batch_num} ملف في: {batch_dir}")
    
    # إنشاء ملف manifest
    manifest = {
        'total_voters': total_voters,
        'batch_size': BATCH_SIZE,
        'total_batches': batch_num,
        'files': [f'voters_batch_{i:03d}.json' for i in range(1, batch_num + 1)]
    }
    
    with open(batch_dir / 'manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 الخطوات التالية:")
    print(f"   1. ضغط المجلد:")
    print(f"      Compress-Archive -Path voter_batches -DestinationPath voter_batches.zip")
    print(f"   2. رفع للمستودع أو استخدام خدمة تخزين سحابي")
    print(f"   3. على Railway، شغل سكريبت الاستيراد")

if __name__ == '__main__':
    try:
        export_voters_in_batches()
    except KeyboardInterrupt:
        print("\n\n⚠️ تم الإيقاف بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
