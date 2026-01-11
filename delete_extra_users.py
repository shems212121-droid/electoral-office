from django.contrib.auth.models import User
from elections.models import UserProfile

print('=== حذف مدخلي النتائج الزائدين ===\n')

# البحث عن جميع مدخلي النتائج
all_result_entry = User.objects.filter(username__startswith='result_entry_').order_by('username')
print(f'إجمالي مدخلي النتائج الحاليين: {all_result_entry.count()}')

# تحديد المستخدمين الذين سنحذفهم (من 31 فما فوق)
users_to_delete = []
for user in all_result_entry:
    try:
        # استخراج الرقم من اسم المستخدم
        num = int(user.username.replace('result_entry_', ''))
        if num > 30:
            users_to_delete.append(user)
    except ValueError:
        # إذا كان اسم المستخدم لا يحتوي على رقم
        pass

print(f'عدد المستخدمين المراد حذفهم: {len(users_to_delete)}')
print(f'سيتم الإبقاء على: result_entry_01 إلى result_entry_30\n')

# عرض أول 10 مستخدمين سيتم حذفهم
print('أمثلة على المستخدمين الذين سيتم حذفهم:')
for user in users_to_delete[:10]:
    print(f'  - {user.username}')
if len(users_to_delete) > 10:
    print(f'  ... و {len(users_to_delete) - 10} آخرين')

# تأكيد العملية
print(f'\nجاري حذف {len(users_to_delete)} مستخدم...')

deleted_count = 0
for user in users_to_delete:
    username = user.username
    user.delete()
    deleted_count += 1
    if deleted_count % 10 == 0:
        print(f'  تم حذف {deleted_count} مستخدم...')

print(f'\n✅ تم حذف {deleted_count} مستخدم بنجاح!')

# التحقق من النتيجة
remaining = User.objects.filter(username__startswith='result_entry_').count()
print(f'عدد مدخلي النتائج المتبقي: {remaining}')

# عرض الإحصائيات النهائية
total_users = User.objects.count()
print(f'\nالإحصائيات النهائية:')
print(f'  إجمالي المستخدمين: {total_users}')
print(f'  مدخلو النتائج: {remaining}')
