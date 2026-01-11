from django.contrib.auth.models import User
from elections.models import UserProfile, UserRole

print('=== تحديث الاحصائيات الدقيقة ===\n')

# عد دقيق حسب الدور
print('المستخدمون حسب الدور:')
for role_value, role_label in UserRole.choices:
    count = UserProfile.objects.filter(role=role_value).count()
    if count > 0:
        print(f'  {role_label}: {count}')

# إحصائيات عامة
total = User.objects.count()
active = UserProfile.objects.filter(is_active=True).count()
inactive = UserProfile.objects.filter(is_active=False).count()

print(f'\nالإحصائيات العامة:')
print(f'  إجمالي المستخدمين: {total}')
print(f'  نشط: {active}')
print(f'  معطل: {inactive}')

# التحقق من مدخلي النتائج
result_entry_users = User.objects.filter(username__startswith='result_entry_')
print(f'\nمدخلو النتائج (بحسب اسم المستخدم):')
print(f'  العدد: {result_entry_users.count()}')
print(f'  الأسماء: {", ".join([u.username for u in result_entry_users[:10]])}')
if result_entry_users.count() > 10:
    print(f'  ... و {result_entry_users.count() - 10} آخرين')
