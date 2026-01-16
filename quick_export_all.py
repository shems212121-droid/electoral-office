#!/usr/bin/env python
"""
التحقق السريع من حالة قاعدة البيانات وتصدير البيانات
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from elections.models import Voter
from django.core import serializers
import json

print("=" * 70)
print("📊 التحقق من قاعدة البيانات واستخراج البيانات")
print("=" * 70)
print()

# 1. عد الناخبين
count = Voter.objects.count()
print(f"✅ عدد الناخبين المحليين: {count:,}")

if count == 0:
    print("❌ لا يوجد ناخبون! يجب استرجاع من نسخة احتياطية")
    exit(1)

# 2. عينة من البيانات
print(f"\n🔍 عينة من 5 ناخبين:")
for voter in Voter.objects.all()[:5]:
    print(f"   - {voter.voter_number}: {voter.full_name}")

# 3. تصدير الكل إلى JSON
print(f"\n📦 جارٍ تصدير {count:,} ناخب...")
print(f"   (هذا قد يستغرق 2-3 دقائق...)")

# تصدير بطريقة فعالة
BATCH_SIZE = 50000
total_exported = []

for offset in range(0, count, BATCH_SIZE):
    batch = Voter.objects.all()[offset:offset + BATCH_SIZE]
    batch_data = json.loads(serializers.serialize('json', batch))
    total_exported.extend(batch_data)
    
    progress = ((offset + len(batch)) / count) * 100
    print(f"   التقدم: {progress:.1f}% ({offset + len(batch):,}/{count:,})")

# حفظ الملف
output_file = 'voters_complete_export.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(total_exported, f, ensure_ascii=False)

file_size = os.path.getsize(output_file) / 1024 / 1024
print(f"\n✅ تم التصدير بنجاح!")
print(f"   - الملف: {output_file}")
print(f"   - الحجم: {file_size:.1f} MB")
print(f"   - السجلات: {len(total_exported):,}")

print(f"\n📋 الخطوات التالية:")
print(f"   1. ضغط الملف:")
print(f"      Compress-Archive -Path {output_file} -DestinationPath voters_backup.zip")
print(f"   2. رفع إلى Git:")
print(f"      git add {output_file}")
print(f"      git commit -m \"Add complete voters backup\"")
print(f"      git push origin main")
print(f"   3. على Railway، استخدم:")
print(f"      python manage.py loaddata {output_file}")

print("\n" + "=" * 70)
print("✅ انتهى التصدير")
print("=" * 70)
