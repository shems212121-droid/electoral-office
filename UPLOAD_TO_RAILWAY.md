# خطوات رفع البيانات إلى Railway

## استخدام Railway CLI (الطريقة الموصى بها)

### 1. تثبيت Railway CLI (إذا لم يكن مثبتاً)
```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

### 2. تسجيل الدخول وربط المشروع
```powershell
railway login
railway link
# اختر: valiant-presence
```

### 3. رفع مجلد البيانات مباشرة
```powershell
# هذا سيرفع المجلد للخادم
railway up voter_batches:/app/voter_batches
```

### 4. تشغيل الاستيراد
```powershell
railway run python import_voters_batches.py
```

سيستغرق 30-60 دقيقة حسب سرعة الاتصال.
