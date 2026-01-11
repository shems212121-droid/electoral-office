from django.contrib.auth.models import User
from elections.models import UserProfile, UserRole

# إجمالي المستخدمين
users = User.objects.select_related('profile').all()
print(f'إجمالي المستخدمين: {users.count()}')

# المستخدمون حسب الدور
print('\n=== المستخدمون حسب الدور ===')
for role_value, role_label in UserRole.choices:
    count = UserProfile.objects.filter(role=role_value).count()
    if count > 0:
        print(f'{role_label}: {count}')

# أمثلة على المستخدمين
print('\n=== أمثلة على المستخدمين المولدين ===')
for u in users[:15]:
    linked = u.profile.linked_candidate or u.profile.linked_operations_room or "لا يوجد"
    print(f'{u.username} - {u.profile.get_role_display()} - مرتبط بـ: {linked}')

# البحث عن المستخدمين المولدين تلقائياً
print('\n=== المستخدمون المولدين (حسب نمط الاسم) ===')
generated_users = User.objects.filter(username__startswith='cand_') | User.objects.filter(username__startswith='admin_') | User.objects.filter(username__startswith='support_') | User.objects.filter(username__startswith='room_')
print(f'عدد المستخدمين المولدين: {generated_users.count()}')
for u in generated_users:
    print(f'{u.username} - {u.profile.get_role_display()}')
