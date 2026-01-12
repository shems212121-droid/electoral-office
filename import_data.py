#!/usr/bin/env python
"""
استيراد البيانات إلى قاعدة البيانات الإنتاجية على Railway
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings_production')
django.setup()

from django.contrib.auth.models import User, Group
from django.core.management import call_command
import glob

def import_users_and_groups():
    """استيراد المستخدمين والمجموعات"""
    print("🔄 جاري استيراد المستخدمين والمجموعات...")
    
    # استيراد المجموعات
    if os.path.exists('groups_data.json'):
        try:
            call_command('loaddata', 'groups_data.json', verbosity=1)
            print("✅ تم استيراد المجموعات")
        except Exception as e:
            print(f"⚠️ خطأ في استيراد المجموعات: {e}")
    
    # استيراد المستخدمين
    if os.path.exists('users_data.json'):
        try:
            with open('users_data.json', 'r', encoding='utf-8') as f:
                users_list = json.load(f)
            
            for user_data in users_list:
                username = user_data['username']
                
                # تخطي admin إذا موجود مسبقاً
                if User.objects.filter(username=username).exists():
                    print(f"   ⏭️ تخطي {username} (موجود مسبقاً)")
                    continue
                
                # إنشاء المستخدم
                user = User.objects.create_user(
                    username=username,
                    email=user_data.get('email', ''),
                    password='changeme123',  # كلمة مرور مؤقتة
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    is_staff=user_data.get('is_staff', False),
                    is_superuser=user_data.get('is_superuser', False),
                    is_active=user_data.get('is_active', True),
                )
                
                # إضافة للمجموعات
                for group_name in user_data.get('groups', []):
                    try:
                        group = Group.objects.get(name=group_name)
                        user.groups.add(group)
                    except Group.DoesNotExist:
                        print(f"   ⚠️ المجموعة '{group_name}' غير موجودة")
                
                user.save()
                print(f"   ✅ تم إنشاء المستخدم: {username}")
            
            print(f"✅ تم استيراد المستخدمين (كلمة المرور المؤقتة: changeme123)")
            
        except Exception as e:
            print(f"❌ خطأ في استيراد المستخدمين: {e}")

def import_app_data():
    """استيراد بيانات التطبيقات"""
    print("\n" + "=" * 60)
    print("استيراد بيانات التطبيقات")
    print("=" * 60)
    
    # البحث عن كل ملفات البيانات
    data_files = glob.glob('*_data.json')
    data_files = [f for f in data_files if f not in ['users_data.json', 'groups_data.json']]
    
    if not data_files:
        print("⚠️ لم يتم العثور على ملفات بيانات")
        return
    
    imported_count = 0
    for filename in data_files:
        app_name = filename.replace('_data.json', '')
        print(f"\n📥 استيراد: {app_name}")
        
        try:
            call_command('loaddata', filename, verbosity=1)
            print(f"   ✅ تم استيراد {filename}")
            imported_count += 1
        except Exception as e:
            print(f"   ❌ خطأ في استيراد {filename}: {e}")
    
    print(f"\n✅ تم استيراد {imported_count} من {len(data_files)} ملف")

if __name__ == '__main__':
    print("=" * 60)
    print("استيراد البيانات إلى قاعدة البيانات الإنتاجية")
    print("=" * 60)
    
    # 1. التأكد من تشغيل migrations أولاً
    print("\n[1/3] التأكد من تشغيل migrations...")
    try:
        call_command('migrate', '--noinput', verbosity=1)
        print("✅ تم تشغيل migrations")
    except Exception as e:
        print(f"❌ خطأ في migrations: {e}")
        exit(1)
    
    # 2. استيراد المستخدمين والمجموعات
    print("\n[2/3] استيراد المستخدمين والمجموعات...")
    import_users_and_groups()
    
    # 3. استيراد بيانات التطبيقات
    print("\n[3/3] استيراد بيانات التطبيقات...")
    import_app_data()
    
    print("\n" + "=" * 60)
    print("✅ اكتمل الاستيراد!")
    print("=" * 60)
    print("\nملاحظات مهمة:")
    print("1. كلمة المرور المؤقتة للمستخدمين: changeme123")
    print("2. يجب على كل مستخدم تغيير كلمة مروره عند أول تسجيل دخول")
    print("3. راجع البيانات المستوردة قبل البدء بالإنتاج")
    print("\nرابط الموقع: https://web-production-42c39.up.railway.app")
