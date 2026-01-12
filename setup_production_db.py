#!/usr/bin/env python
"""
سكريبت إعداد قاعدة البيانات الإنتاجية على Railway
يمكن تشغيله محلياً أو على Railway
"""
import os
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings_production')
django.setup()

from django.contrib.auth.models import User
from django.core.management import call_command

def setup_database():
    """إعداد قاعدة البيانات الإنتاجية"""
    print("=" * 60)
    print("بدء إعداد قاعدة البيانات الإنتاجية")
    print("=" * 60)
    
    # 1. تشغيل Migrations
    print("\n[1/4] تشغيل migrations...")
    try:
        call_command('migrate', '--noinput', verbosity=2)
        print("✅ تم تشغيل migrations بنجاح")
    except Exception as e:
        print(f"❌ خطأ في migrations: {e}")
        return False
    
    # 2. جمع الملفات الثابتة
    print("\n[2/4] جمع الملفات الثابتة...")
    try:
        call_command('collectstatic', '--noinput', '--clear', verbosity=1)
        print("✅ تم جمع الملفات الثابتة بنجاح")
    except Exception as e:
        print(f"⚠️ تحذير في collectstatic: {e}")
    
    # 3. إنشاء مستخدم Admin
    print("\n[3/4] إنشاء مستخدم Admin...")
    try:
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@electoral-office.local',
                password='admin123'
            )
            print("✅ تم إنشاء مستخدم admin بنجاح")
            print("   - اسم المستخدم: admin")
            print("   - كلمة المرور: admin123")
            print("   ⚠️ يُرجى تغيير كلمة المرور بعد تسجيل الدخول!")
        else:
            print("ℹ️ مستخدم admin موجود مسبقاً")
    except Exception as e:
        print(f"❌ خطأ في إنشاء admin: {e}")
    
    # 4. إنشاء بيانات أساسية
    print("\n[4/4] إنشاء البيانات الأساسية...")
    try:
        create_initial_data()
        print("✅ تم إنشاء البيانات الأساسية بنجاح")
    except Exception as e:
        print(f"⚠️ تحذير في البيانات الأساسية: {e}")
    
    print("\n" + "=" * 60)
    print("✅ اكتمل إعداد قاعدة البيانات بنجاح!")
    print("=" * 60)
    print("\nيمكنك الآن:")
    print("1. زيارة الموقع على: https://web-production-42c39.up.railway.app")
    print("2. تسجيل الدخول بـ: admin / admin123")
    print("3. البدء في استخدام النظام")
    print("\n⚠️ تذكير: قم بتغيير كلمة مرور admin من لوحة التحكم!")
    
    return True

def create_initial_data():
    """إنشاء بيانات أولية أساسية"""
    from django.contrib.auth.models import User, Group, Permission
    
    # إنشاء المجموعات الأساسية
    groups_data = [
        'المشرفون',
        'إدخال البيانات',
        'المشاهدون',
        'المرشحون',
        'الدعم الفني',
    ]
    
    for group_name in groups_data:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"   - تم إنشاء مجموعة: {group_name}")
    
    # يمكنك إضافة بيانات أخرى هنا
    # مثل: المحافظات، المناطق، إلخ...
    
if __name__ == '__main__':
    setup_database()
