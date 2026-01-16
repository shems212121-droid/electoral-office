# 🚀 دليل سريع: تثبيت Railway CLI وبدء الاستيراد

## الخطوة 1: تثبيت Railway CLI

### الطريقة الأولى (موصى بها):
```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

### الطريقة الثانية (باستخدام npm):
```powershell
npm install -g @railway/cli
```

### الطريقة الثالثة (تحميل مباشر):
1. اذهب إلى: https://github.com/railwayapp/cli/releases
2. حمّل النسخة المناسبة لـ Windows
3. أضف المسار إلى PATH

---

## الخطوة 2: تسجيل الدخول

بعد التثبيت:
```powershell
# سجل دخول
railway login

# سيفتح متصفح للمصادقة
# سجل دخول بحسابك على Railway
```

---

## الخطوة 3: ربط المشروع

```powershell
cd C:\Users\2025\.gemini\antigravity\scratch\electoral_office

# ربط المشروع
railway link

# اختر: valiant-presence
```

---

## الخطوة 4: رفع ملفات الدفعات

```powershell
# تحقق من المجلد الحالي
railway status

# رفع مجلد الدفعات
railway up voter_batches:/app/voter_batches
```

**ملاحظة:** إذا كان المجلد كبيراً جداً (~1.3 GB)، قد يفشل `railway up`.  
في هذه الحالة، استخدم Git:

```powershell
# إضافة الملفات إلى Git LFS أو رفعها عادي
git add voter_batches/*.json
git commit -m "Add voter batches"
git push origin main

# ثم انتظر حتى يكتمل الـ deployment على Railway
```

---

## الخطوة 5: تشغيل السكريبت الآلي

الآن يمكنك تشغيل السكريبت:

```powershell
.\execute_railway_import.ps1
```

**أو يدوياً:**

```powershell
# الجولة 1
railway run bash -c "IMPORT_START_BATCH=18 IMPORT_END_BATCH=28 python import_voters_batches.py"

# الجولة 2
railway run bash -c "IMPORT_START_BATCH=28 IMPORT_END_BATCH=34 python import_voters_batches.py"

# الجولة 3
railway run bash -c "IMPORT_START_BATCH=34 IMPORT_END_BATCH=39 python import_voters_batches.py"
```

---

## ⚡ بديل: العمل مباشرة على Railway Dashboard

إذا واجهت مشاكل مع CLI، يمكنك:

### 1. رفع الملفات عبر Git
```powershell
# ضغط الملفات أولاً
Compress-Archive -Path voter_batches -DestinationPath voter_batches.zip -Force

# رفع الملف المضغوط
git add voter_batches.zip
git commit -m "Add voter batches zip"
git push origin main
```

### 2. استخدام Railway Dashboard Terminal
1. افتح: https://railway.app/
2. اذهب لمشروعك: `valiant-presence`
3. انقر على **Deploy** → **Deployments**
4. افتح **Terminal** من الـ Deployment الحالي
5. شغّل:

```bash
# فك الضغط (إذا رفعت zip)
unzip voter_batches.zip

# أو تحقق من وجود المجلد
ls voter_batches/

# ثم شغل الاستيراد
IMPORT_START_BATCH=18 IMPORT_END_BATCH=28 python import_voters_batches.py
```

---

## 📊 ملخص الخطوات

### ✅ **الطريقة السريعة (مع CLI):**
1. تثبيت Railway CLI
2. تسجيل الدخول وربط المشروع
3. رفع الملفات
4. تشغيل السكريبت الآلي

### ✅ **الطريقة البديلة (بدون CLI):**
1. رفع `voter_batches.zip` عبر Git
2. استخدام Railway Dashboard Terminal
3. فك الضغط على الخادم
4. تشغيل الأوامر يدوياً

---

## 🎯 **الموصى به الآن:**

نظراً لأن Railway CLI غير مثبت، أنصحك بـ:

### **الخيار أ: تثبيت CLI (الأفضل)**
```powershell
# تشغيل هذا الأمر في PowerShell (كمسؤول)
iwr https://railway.app/install.ps1 -useb | iex
```

### **الخيار ب: استخدام Dashboard مباشرة (أسرع)**
1. الملفات موجودة محلياً بالفعل ✅
2. افتح Railway Dashboard
3. استخدم Terminal للتنفيذ

---

**ما الذي تفضله؟**
- تثبيت Railway CLI الآن؟
- أو استخدام Railway Dashboard Terminal مباشرة؟
