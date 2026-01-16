# 🎯 دليل تطبيق SQL على Railway - الطريقة الأسهل

## 📊 الوضع الحالي
✅ الموقع يعمل  
✅ العدد الحالي: 1,818,933 ناخب  
🎯 المطلوب: تطبيق SQL لإصلاح حقل phone

---

## 🚀 الطريقة 1: Railway CLI (الأسهل والأسرع)

### الخطوة 1: فتح PowerShell

اضغط `Win + X` واختر **"Windows Terminal"** أو **"PowerShell"**

---

### الخطوة 2: تثبيت Railway CLI

انسخ والصق هذا الأمر:

```powershell
npm i -g @railway/cli
```

⏳ انتظر حتى ينتهي التثبيت (30-60 ثانية)

---

### الخطوة 3: تسجيل الدخول

```powershell
railway login
```

سيفتح متصفح لتسجيل الدخول. سجل دخولك ثم ارجع للـ PowerShell.

---

### الخطوة 4: ربط المشروع

```powershell
cd C:\Users\2025\.gemini\antigravity\scratch\electoral_office
railway link
```

اختر المشروع: **valiant-presence** (أو electoral-office)

---

### الخطوة 5: الاتصال بقاعدة البيانات

```powershell
railway connect postgres
```

ستظهر واجهة PostgreSQL (`postgres=#`)

---

### الخطوة 6: تنفيذ الأوامر SQL

انسخ والصق **سطر سطر** ثم اضغط Enter بعد كل سطر:

```sql
ALTER TABLE elections_voter ALTER COLUMN phone TYPE VARCHAR(30);
```

ثم:

```sql
ALTER TABLE elections_voter DROP CONSTRAINT IF EXISTS elections_voter_phone_key;
```

ثم:

```sql
ALTER TABLE elections_voter ALTER COLUMN phone DROP NOT NULL;
```

---

### الخطوة 7: الخروج

```sql
\q
```

✅ تم! الآن حقل phone أصبح جاهزاً لاستقبال أرقام أطول.

---

## 🔄 الطريقة 2: عبر pgAdmin أو DBeaver (للمطورين)

إذا كان لديك pgAdmin أو DBeaver:

### 1. احصل على Connection String من Railway

في Railway Dashboard → postgres → Variables → ابحث عن `DATABASE_URL`

### 2. اتصل باستخدام الـ URL

### 3. نفّذ الـ SQL:

```sql
ALTER TABLE elections_voter ALTER COLUMN phone TYPE VARCHAR(30);
ALTER TABLE elections_voter DROP CONSTRAINT IF EXISTS elections_voter_phone_key;
ALTER TABLE elections_voter ALTER COLUMN phone DROP NOT NULL;
```

---

## 📝 بعد تنفيذ SQL بنجاح

### الخطوة التالية: إعادة استيراد البيانات

افتح هذا الرابط في المتصفح:

```
https://web-production-42c39.up.railway.app/tool/import-final-data/?secret=shems_voter_import_2024_secure
```

⏱️ **انتظر 15-20 دقيقة** حتى ينتهي الاستيراد

---

### التحقق النهائي

**1. تحقق من العدد:**
```
https://web-production-42c39.up.railway.app/dashboard/
```
يجب أن يصبح ~**1,868,933**

**2. ابحث عن رقمك:**
```
https://web-production-42c39.up.railway.app/voter-search/
```
أدخل: **33037821** ✅

---

## 🆘 إذا واجهت مشاكل

### خطأ "npm not found"

ثبت Node.js من: https://nodejs.org

### خطأ في railway link

تأكد من أنك في مجلد المشروع:
```powershell
cd C:\Users\2025\.gemini\antigravity\scratch\electoral_office
```

### خطأ في railway connect

تأكد من اسم قاعدة البيانات:
```powershell
railway services
```
ثم:
```powershell
railway connect [اسم الخدمة]
```

---

## ✅ ملخص الأوامر (نسخة سريعة)

```powershell
# 1. تثبيت
npm i -g @railway/cli

# 2. تسجيل دخول
railway login

# 3. ربط المشروع
cd C:\Users\2025\.gemini\antigravity\scratch\electoral_office
railway link

# 4. الاتصال
railway connect postgres

# 5. تنفيذ SQL (واحد تلو الآخر)
ALTER TABLE elections_voter ALTER COLUMN phone TYPE VARCHAR(30);
ALTER TABLE elections_voter DROP CONSTRAINT IF EXISTS elections_voter_phone_key;
ALTER TABLE elections_voter ALTER COLUMN phone DROP NOT NULL;

# 6. خروج
\q
```

---

**آخر تحديث:** 00:17 - 16 يناير 2026  
**الحالة:** ✅ الموقع يعمل وجاهز للتطبيق
