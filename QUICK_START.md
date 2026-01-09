# دليل البدء السريع - المكتب الانتخابي

## 🚀 كيفية التشغيل

### 1. تشغيل السيرفر
```bash
cd C:\Users\2025\.gemini\antigravity\scratch\electoral_office
python manage.py runserver
```

**الوصول إلى التطبيق:**
- 🌐 المتصفح: `http://localhost:8000/`
- 📱 من الهاتف على نفس الشبكة: `http://[IP]:8000/`

### 2. إنشاء المستخدمين

#### إنشاء مدير نظام (Super Admin):
```bash
python manage.py createsuperuser
# أدخل: اسم المستخدم، البريد، كلمة المرور
```

#### تعديل دور المستخدم:
1. سجل دخول إلى `/admin/`
2. اذهب إلى **Users** → اختر المستخدم
3. في قسم **"الملف الشخصي والصلاحيات"**:
   - اختر **الدور الوظيفي** (مدير النظام، مشرف، إلخ)
   - فعّل **يمكنه تصدير التقارير** (اختياري)
   - اختر **المنطقة المخصصة** (اختياري)
4. احفظ

### 3. إنشاء مستخدمين بالكود

```python
python manage.py shell

from django.contrib.auth.models import User
from elections.models import UserProfile, UserRole

# مدير نظام
admin = User.objects.create_user('admin', 'admin@example.com', 'admin123')
admin.profile.role = UserRole.ADMIN
admin.profile.can_export_reports = True
admin.profile.can_delete_records = True
admin.profile.save()

# مشرف
supervisor = User.objects.create_user('supervisor', password='super123')
supervisor.profile.role = UserRole.SUPERVISOR
supervisor.profile.can_export_reports = True
supervisor.profile.save()

# مدخل بيانات الناخبين
data_entry = User.objects.create_user('voter_entry', password='entry123')
data_entry.profile.role = UserRole.DATA_ENTRY_VOTERS
data_entry.profile.save()

# مستعرض
viewer = User.objects.create_user('viewer', password='view123')
viewer.profile.role = UserRole.VIEWER
viewer.profile.save()
```

---

## 📱 تجربة PWA على الهاتف

### Android (Chrome):
1. افتح `http://[IP]:8000` على Chrome
2. سيظهر بانر "ثبّت التطبيق"
3. اضغط "تثبيت"
4. التطبيق سيظهر على الشاشة الرئيسية

### iOS (Safari):
1. افتح الموقع في Safari
2. اضغط زر المشاركة 📤
3. اختر "إضافة إلى الشاشة الرئيسية"
4. مسمى التطبيق: "المكتب الانتخابي"

---

## 🎯 الأدوار والصلاحيات

| الدور | إضافة | تعديل | حذف | تصدير | عرض |
|------|-------|-------|------|-------|-----|
| **مدير النظام** | ✅ كل شيء | ✅ كل شيء | ✅ كل شيء | ✅ | ✅ |
| **مشرف** | ✅ (عدا المستخدمين) | ✅ | ❌ | ✅ | ✅ |
| **مدخل ناخبين** | ✅ ناخبين فقط | ✅ ناخبين فقط | ❌ | ❌ | ✅ ناخبين |
| **مدخل مرشحين** | ✅ مرشحين فقط | ✅ مرشحين فقط | ❌ | ❌ | ✅ مرشحين |
| **مدخل مراقبين** | ✅ مراقبين فقط | ✅ مراقبين فقط | ❌ | ❌ | ✅ مراقبين |
| **مستعرض** | ❌ | ❌ | ❌ | ❌ | ✅ كل شيء |

---

## 🔧 المميزات المُنفذة

### ✅ نظام الأدوار (Role-Based Access Control)
- [x] 8 أدوار وظيفية
- [x] Permission decorators جاهزة
- [x] Context processor للقوالب
- [x] Django Admin integration
- [x] Auto signals لإنشاء profiles

### ✅ Progressive Web App
- [x] Manifest.json (RTL)
- [x] Service Worker (offline support)
- [x] Install prompts
- [x] 8 أيقونات (72px-512px)
- [x] Update notifications
- [x] Online/Offline status

### ✅ Responsive Design
- [x] Mobile-first CSS
- [x] Bottom navigation للهواتف
- [x] Table-to-cards transformation
- [x] Touch optimizations
- [x] Safe area support (iPhone notch)

---

## 📖 الصفحات المتاحة

- `/` → تسجيل الدخول
- `/dashboard/` → لوحة التحكم الرئيسية
- `/admin/` → لوحة Django Admin
- `/vote/candidates/` → قائمة المرشحين
- `/voters/` → قائمة الناخبين
- `/monitors/` → قائمة المراقبين
- `/reports/comprehensive/` → التقارير الشاملة

---

## 🎨 التخصيص

### ألوان كتلة الصادقون:
```css
--sadiqoon-green: #1B5E20;
--sadiqoon-green-dark: #0D3310;
--sadiqoon-gold: #FFD700;
```

### تغيير الألوان:
عدّل في `templates/elections/base.html` في قسم `:root`

---

## 🐛 استكشاف الأخطاء

### المستخدم ليس لديه profile:
```python
python manage.py shell
from django.contrib.auth.models import User
from elections.models import UserProfile

user = User.objects.get(username='USERNAME')
if not hasattr(user, 'profile'):
    UserProfile.objects.create(user=user)
```

### Service Worker لا يعمل:
1. تأكد من فتح الموقع عبر `http://` (localhost) أو `https://`
2. افتح DevTools → Application → Service Workers
3. اضغط "Unregister" ثم حدّث الصفحة

### CSS التجاوب لا يظهر:
تأكد من أن `responsive.css` في المكان الصحيح:
```
static/css/responsive.css
```

---

## 📚 للمطورين

### إضافة decorator لـ View:
```python
from elections.decorators import permission_required

@permission_required('add_voters')
def add_voter_view(request):
    # Your code
    pass
```

### في القوالب:
```django
{% if is_admin %}
    <!-- يظهر للـ Admin فقط -->
{% endif %}

{% if user_profile.has_permission 'export_reports' %}
    <a href="export">تصدير</a>
{% endif %}
```

---

## 🎯 الخطوات التالية الموصى بها

1. **اختبار الأدوار**: جرّب كل دور والتأكد من الصلاحيات
2. **تطبيق Decorators**: أضف decorators لبقية الـ Views
3. **إنشاء Dashboards مخصصة**: dashboard لكل دور
4. **اختبار PWA**: جرّب التثبيت على Android و iOS
5. **اختبار التجاوب**: جرّب على أحجام شاشات مختلفة

---

## 📞 المساعدة

للحصول على المساعدة، راجع:
- 📄 [walkthrough.md](file:///C:/Users/2025/.gemini/antigravity/brain/252684f5-0864-4317-be96-80284ed1fd66/walkthrough.md) - شرح مفصل
- 📋 [task.md](file:///C:/Users/2025/.gemini/antigravity/brain/252684f5-0864-4317-be96-80284ed1fd66/task.md) - حالة المهام
- 📝 [implementation_plan.md](file:///C:/Users/2025/.gemini/antigravity/brain/252684f5-0864-4317-be96-80284ed1fd66/implementation_plan.md) - خطة التنفيذ

---

**🎉 تطبيقك جاهز الآن!**
