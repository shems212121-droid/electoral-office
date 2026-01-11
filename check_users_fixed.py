from django.contrib.auth.models import User
from elections.models import UserProfile, UserRole

print('=== احصائيات المستخدمين ===')
total_users = User.objects.count()
users_with_profile = User.objects.filter(profile__isnull=False).count()
users_without_profile = total_users - users_with_profile

print(f'اجمالي المستخدمين: {total_users}')
print(f'لديهم ملف تعريف: {users_with_profile}')
print(f'بدون ملف تعريف: {users_without_profile}')

# اصلاح المستخدمين بدون ملف تعريف
if users_without_profile > 0:
    print('\n=== اصلاح المستخدمين بدون ملف تعريف ===')
    for user in User.objects.filter(profile__isnull=True):
        UserProfile.objects.create(user=user)
        print(f'تم انشاء ملف تعريف لـ: {user.username}')

print('\n=== المستخدمون حسب الدور ===')
for role_value, role_label in UserRole.choices:
    count = UserProfile.objects.filter(role=role_value).count()
    if count > 0:
        print(f'{role_label}: {count}')

print('\n=== المستخدمون المرتبطون ===')
candidates_users = UserProfile.objects.filter(linked_candidate__isnull=False).count()
rooms_users = UserProfile.objects.filter(linked_operations_room__isnull=False).count()
print(f'مرتبطون بمرشحين: {candidates_users}')
print(f'مرتبطون بغرف عمليات: {rooms_users}')

print('\n=== امثلة على الحسابات المولدة ===')
users = User.objects.select_related('profile').all()[:10]
for u in users:
    try:
        role = u.profile.get_role_display() if hasattr(u, 'profile') else 'بدون دور'
        linked = ''
        if hasattr(u, 'profile'):
            if u.profile.linked_candidate:
                linked = f' -> {u.profile.linked_candidate}'
            elif u.profile.linked_operations_room:
                linked = f' -> {u.profile.linked_operations_room}'
        print(f'{u.username} | {role}{linked}')
    except Exception as e:
        print(f'{u.username} | خطأ: {e}')
