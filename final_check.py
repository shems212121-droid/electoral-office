from django.contrib.auth.models import User
from elections.models import UserProfile, UserRole

print('=== الإحصائيات النهائية بعد الحذف ===\n')

# عد دقيق حسب الدور
print('المستخدمون حسب الدور:')
role_counts = {}
for role_value, role_label in UserRole.choices:
    count = UserProfile.objects.filter(role=role_value).count()
    if count > 0:
        role_counts[role_label] = count
        print(f'  {role_label}: {count}')

# إحصائيات عامة
total = User.objects.count()
active = UserProfile.objects.filter(is_active=True).count()
inactive = UserProfile.objects.filter(is_active=False).count()

print(f'\nالإحصائيات العامة:')
print(f'  إجمالي المستخدمين: {total}')
print(f'  نشط: {active}')
print(f'  معطل: {inactive}')

# فحص المستخدمين الباقين بدور مدخل نتائج ولكن ليس باسم result_entry
other_result_entry = UserProfile.objects.filter(
    role=UserRole.DATA_ENTRY_RESULTS
).exclude(user__username__startswith='result_entry_')

if other_result_entry.exists():
    print(f'\n⚠️ توجد {other_result_entry.count()} حسابات أخرى بدور "مدخل نتائج" بأسماء مختلفة:')
    for profile in other_result_entry[:10]:
        print(f'  - {profile.user.username}')
    if other_result_entry.count() > 10:
        print(f'  ... و {other_result_entry.count() - 10} آخرين')
