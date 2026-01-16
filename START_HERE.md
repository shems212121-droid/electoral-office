# 🚀 دليل سريع: استيراد الناخبين عبر Railway Dashboard
# (بدون الحاجة إلى CLI)

## 📝 الملخص
نظراً لعدم توفر Railway CLI، سنستخدم Railway Dashboard Terminal مباشرة.

---

## ✅ الخطة البسيطة (3 خطوات رئيسية)

### **الخطوة 1: رفع ملفات الدفعات إلى Git**

```powershell
cd C:\Users\2025\.gemini\antigravity\scratch\electoral_office

# إضافة الملفات (إذا لم تكن مرفوعة)
git add voter_batches/*.json
git commit -m "Add remaining voter batches"
git push origin main
```

**ملاحظة:** إذا كانت الملفات كبيرة جداً لـ Git، استخدم الخطوة البديلة أدناه.

---

### **الخطوة 2: فتح Railway Dashboard Terminal**

1. افتح متصفحك
2. اذهب إلى: https://railway.app/
3. سجل دخول إلى حسابك
4. اختر المشروع: **valiant-presence**
5. انقر على الـ **Deployment** الحالي
6. اضغط على زر **"Terminal"** أو **"Console"**

---

### **الخطوة 3: تنفيذ الاستيراد**

في Terminal الخاص بـ Railway، شغّل الأوامر التالية:

#### **أ. التحقق من وجود الملفات**
```bash
# تحقق من المجلد
ls voter_batches/ | wc -l
# يجب أن يظهر: 39 (38 ملف بيانات + manifest.json)

# تحقق من العدد الحالي
python manage.py shell -c "from elections.models import Voter; print(f'الحالي: {Voter.objects.count():,}')"
```

#### **ب. الجولة 1: الدفعات 18-27 (30-40 دقيقة)**
```bash
IMPORT_START_BATCH=18 IMPORT_END_BATCH=28 python import_voters_batches.py
```

**انتظر حتى تظهر:** `✅ اكتمل الاستيراد!`

**ثم تحقق:**
```bash
python manage.py shell -c "from elections.models import Voter; print(f'الإجمالي: {Voter.objects.count():,}')"
```
**المتوقع:** ~1,368,933

---

#### **ج. الجولة 2: الدفعات 28-33 (20-30 دقيقة)**
```bash
IMPORT_START_BATCH=28 IMPORT_END_BATCH=34 python import_voters_batches.py
```

**تحقق:**
```bash
python manage.py shell -c "from elections.models import Voter; print(f'الإجمالي: {Voter.objects.count():,}')"
```
**المتوقع:** ~1,668,933

---

#### **د. الجولة 3: الدفعات 34-38 (15-25 دقيقة)**
```bash
IMPORT_START_BATCH=34 IMPORT_END_BATCH=39 python import_voters_batches.py
```

**التحقق النهائي:**
```bash
python manage.py shell -c "from elections.models import Voter; print(f'🎉 الإجمالي النهائي: {Voter.objects.count():,}')"
```
**المتوقع:** **1,868,933** ✅

---

## 🔄 إذا لم تكن الملفات موجودة على Railway

إذا لم يكن مجلد `voter_batches` موجوداً، استخدم إحدى هذه الطرق:

### **الطريقة 1: رفع ملف مضغوط عبر Git**

```powershell
# على جهازك المحلي
Compress-Archive -Path voter_batches -DestinationPath voter_batches.zip -Force

# رفع الملف المضغوط
git add voter_batches.zip
git commit -m "Add voter batches archive"
git push origin main
```

**ثم على Railway Terminal:**
```bash
# فك الضغط
unzip -q voter_batches.zip

# تأكيد
ls voter_batches/ | wc -l
```

---

### **الطريقة 2: رفع للتخزين السحابي**

1. ارفع `voter_batches.zip` إلى Google Drive / Dropbox / OneDrive
2. احصل على رابط التحميل المباشر
3. على Railway Terminal:

```bash
# تحميل الملف
wget "DIRECT_DOWNLOAD_LINK" -O voter_batches.zip

# فك الضغط
unzip -q voter_batches.zip

# تحقق
ls voter_batches/ | wc -l
```

---

## 📊 جدول التنفيذ

| الجولة | الأمر | المدة | المتوقع بعدها |
|--------|-------|-------|---------------|
| **1** | `IMPORT_START_BATCH=18 IMPORT_END_BATCH=28 python import_voters_batches.py` | 30-40 دقيقة | ~1,368,933 |
| **استراحة** | `python manage.py shell -c "from elections.models import Voter; print(Voter.objects.count())"` | 1 دقيقة | - |
| **2** | `IMPORT_START_BATCH=28 IMPORT_END_BATCH=34 python import_voters_batches.py` | 20-30 دقيقة | ~1,668,933 |
| **استراحة** | `python manage.py shell -c "from elections.models import Voter; print(Voter.objects.count())"` | 1 دقيقة | - |
| **3** | `IMPORT_START_BATCH=34 IMPORT_END_BATCH=39 python import_voters_batches.py` | 15-25 دقيقة | **1,868,933** ✅ |

**الإجمالي:** ~90-120 دقيقة

---

## ✅ قائمة التحقق السريعة

### قبل البدء:
- [ ] الملفات موجودة محلياً (39 ملف) ✅
- [ ] تم رفعها إلى Git أو التخزين السحابي
- [ ] فتح Railway Dashboard → المشروع → Terminal

### أثناء التنفيذ:
- [ ] لا تغلق Terminal
- [ ] لا تقطع الاتصال
- [ ] راقب السجلات للتأكد من التقدم

### بعد كل جولة:
- [ ] تحقق من العدد
- [ ] انتظر 1-2 دقيقة قبل الجولة التالية

### بعد الانتهاء:
- [ ] العدد النهائي = 1,868,933
- [ ] افتح الموقع وتحقق من لوحة التحكم
- [ ] جرب البحث عن ناخب

---

## 🚀 ابدأ الآن!

**الخطوات البسيطة:**

1. **افتح:** https://railway.app/ → المشروع → Terminal
2. **تحقق:** `ls voter_batches/`
3. **شغّل الجولة 1:** `IMPORT_START_BATCH=18 IMPORT_END_BATCH=28 python import_voters_batches.py`
4. **تابع** الجولات الأخرى

---

**هل تحتاج مساعدة في أي خطوة؟** 
- فتح Railway Terminal؟
- رفع الملفات؟
- تشغيل الأوامر؟

**الوقت الإجمالي المتوقع:** 90-120 دقيقة ⏱️
**النتيجة:** 1,868,933 ناخب كامل في Railway! 🎉
