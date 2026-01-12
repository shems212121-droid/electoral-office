#!/usr/bin/env python
"""
نقل قاعدة البيانات الكبيرة من SQLite إلى PostgreSQL مباشرة
يستخدم pg_dump و pg_restore بدلاً من JSON (أسرع بكثير)
"""
import os
import sys

print("=" * 70)
print("دليل نقل 1.9 مليون ناخب إلى Railway")
print("=" * 70)

print("""
⚠️ مع 1.9 مليون ناخب، استخدام JSON سيكون بطيئاً جداً!

✅ الحل الأمثل: استخدام pg_dump و pg_restore

📋 الخطوات:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
الطريقة 1️⃣: نقل مباشر باستخدام PostgreSQL Tools (الأسرع)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

الخطوة 1: تحويل SQLite إلى PostgreSQL محلياً
─────────────────────────────────────────────

أ) ثبّت PostgreSQL محلياً:
   https://www.postgresql.org/download/windows/

ب) أنشئ قاعدة بيانات مؤقتة:
   createdb electoral_temp

ج) استخدم pgloader لنقل البيانات:
   # ثبّت pgloader:
   # https://github.com/dimitri/pgloader/releases
   
   pgloader db.sqlite3 postgresql://localhost/electoral_temp

د) صدّر من PostgreSQL المحلي:
   pg_dump -Fc electoral_temp > electoral_backup.dump


الخطوة 2: رفع إلى Railway
─────────────────────────

أ) احصل على DATABASE_URL من Railway:
   railway variables | findstr DATABASE_URL

ب) استورد مباشرة:
   pg_restore -d <DATABASE_URL> electoral_backup.dump


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
الطريقة 2️⃣: تصدير على دفعات (Batches) - أسهل لكن أبطأ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

سأنشئ سكريبت يصدر البيانات على دفعات صغيرة:

   python export_in_batches.py    # سينشئ ملفات متعددة
   
   # ثم على Railway:
   railway run python import_batches.py


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
الطريقة 3️⃣: رفع قاعدة البيانات كاملة (الأبسط)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

إذا كان حجم db.sqlite3 أقل من 2 GB:

أ) على Railway، أضف Volume:
   - اذهب لـ Service → Settings
   - أضف Volume جديد
   - Mount path: /data

ب) ارفع قاعدة البيانات:
   railway up db.sqlite3:/data/db.sqlite3

ج) على Railway، شغّل سكريبت النقل:
   railway run python migrate_sqlite_to_postgres.py


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 توصيتي:

بما أن لديك 1.9 مليون سجل:
1. استخدم الطريقة 2 (على دفعات) - أسهل وأكثر أماناً
2. سأنشئ السكريبتات لك الآن
3. سيستغرق حوالي 30-60 دقيقة لإكمال النقل

هل تريد المتابعة؟ (y/n)
""")

# انتظار موافقة المستخدم
response = input("\nاضغط Enter لإنشاء سكريبتات النقل على دفعات: ")

print("\n✅ سأنشئ السكريبتات...")
