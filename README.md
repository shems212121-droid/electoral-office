# نظام المكتب الانتخابي - Electoral Office System

نظام شامل لإدارة العمليات الانتخابية

## النشر على Railway.app

### المتغيرات المطلوبة (Environment Variables):

```
DJANGO_SETTINGS_MODULE=electoral_office.settings_production
SECRET_KEY=your-super-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=*
DATABASE_URL=(سيتم إضافتها تلقائياً من PostgreSQL)
```

### خطوات النشر:

1. ارفع المشروع على GitHub
2. أنشئ حساب على railway.app
3. اربط GitHub مع Railway
4. أضف PostgreSQL من قائمة الخدمات
5. انشر التطبيق

### بعد النشر:

```bash
# إنشاء superuser
railway run python manage.py createsuperuser
```

## الميزات الرئيسية:

- إدارة المرشحين والناخبين
- فرز الأصوات (عام وخاص)
- نظام الصلاحيات المتقدم
- تقارير وإحصائيات
- دعم كامل للغة العربية

## المتطلبات:

- Python 3.12+
- PostgreSQL (للإنتاج)
- SQLite (للتطوير)

## الترخيص:

حقوق النشر محفوظة © 2025
