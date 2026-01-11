from django.contrib.auth.models import User
from elections.models import UserProfile, UserRole

print('=== حذف حسابات admin01-50 ===\n')

# البحث عن المستخدمين admin01 إلى admin50
admin_users = User.objects.filter(username__startswith='admin').exclude(username='admin').exclude(username='admin_scan')
print(f'عدد حسابات admin المراد فحصها: {admin_users.count()}')

# تصفية الحسابات التي تبدأ بـ admin متبوعة برقم
users_to_delete = []
for user in admin_users:
    try:
        # التحقق من أن الاسم يحتوي على رقم بعد admin
        num_part = user.username.replace('admin', '')
        if num_part.isdigit():
            users_to_delete.append(user)
    except:
        pass

print(f'عدد المستخدمين المراد حذفهم: {len(users_to_delete)}')
print('\nأمثلة:')
for user in users_to_delete[:10]:
    print(f'  - {user.username} (دور: {user.profile.get_role_display()})')
if len(users_to_delete) > 10:
    print(f'  ... و {len(users_to_delete) - 10} آخرين')

# الحذف
print(f'\nجاري حذف {len(users_to_delete)} مستخدم...')
deleted_count = 0
for user in users_to_delete:
    user.delete()
    deleted_count += 1
    if deleted_count % 10 == 0:
        print(f'  تم حذف {deleted_count}...')

print(f'\n✅ تم حذف {deleted_count} مستخدم بنجاح!')

# الإحصائيات النهائية
print('\n=== الإحصائيات النهائية ===')
print(f'إجمالي المستخدمين: {User.objects.count()}')
print(f'مدخلو النتائج: {UserProfile.objects.filter(role=UserRole.DATA_ENTRY_RESULTS).count()}')
print(f'  - result_entry_XX: {User.objects.filter(username__startswith="result_entry_").count()}')

# التحقق النهائي
remaining_admin_numbered = User.objects.filter(username__regex=r'^admin\d+$')
if remaining_admin_numbered.exists():
    print(f'\n⚠️ تحذير: لا يزال هناك {remaining_admin_numbered.count()} حسابات admin برقم')
else:
    print(f'\n✅ تم حذف جميع حسابات admin المرقمة بنجاح')
