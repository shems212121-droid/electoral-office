#!/usr/bin/env python3
"""
PostgreSQL Setup Checker for Railway
يتحقق من إعداد PostgreSQL بشكل صحيح
"""

import os
import sys
from urllib.parse import urlparse

def check_database_url():
    """التحقق من متغير DATABASE_URL"""
    print("🔍 فحص DATABASE_URL...")
    
    db_url = os.environ.get('DATABASE_URL', '')
    
    if not db_url:
        print("❌ DATABASE_URL غير موجود!")
        print("   الرجاء إضافة PostgreSQL من Railway Dashboard")
        return False
    
    # تحليل الـ URL
    try:
        parsed = urlparse(db_url)
        
        if parsed.scheme == 'postgresql' or parsed.scheme == 'postgres':
            print(f"✅ DATABASE_URL موجود ونوعه: {parsed.scheme}")
            print(f"   المضيف: {parsed.hostname}")
            print(f"   المنفذ: {parsed.port or 5432}")
            print(f"   قاعدة البيانات: {parsed.path[1:] if parsed.path else 'N/A'}")
            return True
        elif parsed.scheme == 'sqlite':
            print("⚠️  DATABASE_URL موجود لكنه SQLite!")
            print("   الرجاء إضافة PostgreSQL من Railway Dashboard")
            return False
        else:
            print(f"⚠️  نوع غير معروف: {parsed.scheme}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في تحليل DATABASE_URL: {e}")
        return False


def check_django_settings():
    """التحقق من إعدادات Django"""
    print("\n🔍 فحص إعدادات Django...")
    
    try:
        # استيراد الإعدادات
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings_production')
        
        import django
        django.setup()
        
        from django.conf import settings
        
        # فحص محرك قاعدة البيانات
        engine = settings.DATABASES['default']['ENGINE']
        
        if 'postgresql' in engine:
            print(f"✅ Django يستخدم: {engine}")
            
            # فحص اسم قاعدة البيانات
            db_name = settings.DATABASES['default'].get('NAME', 'N/A')
            print(f"   اسم قاعدة البيانات: {db_name}")
            
            return True
        elif 'sqlite' in engine:
            print(f"⚠️  Django يستخدم SQLite: {engine}")
            print("   تأكد من وجود DATABASE_URL في متغيرات البيئة")
            return False
        else:
            print(f"❓ محرك غير معروف: {engine}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في فحص Django: {e}")
        return False


def check_migrations():
    """التحقق من حالة Migrations"""
    print("\n🔍 فحص Migrations...")
    
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # التحقق من migrations غير المطبقة
        out = StringIO()
        call_command('showmigrations', '--plan', stdout=out)
        output = out.getvalue()
        
        unapplied = [line for line in output.split('\n') if '[ ]' in line]
        
        if unapplied:
            print(f"⚠️  يوجد {len(unapplied)} migration غير مطبق:")
            for migration in unapplied[:5]:  # عرض أول 5 فقط
                print(f"   {migration.strip()}")
            if len(unapplied) > 5:
                print(f"   ... و {len(unapplied) - 5} آخرين")
            print("\n   قم بتشغيل: python manage.py migrate")
            return False
        else:
            print("✅ جميع migrations مطبقة!")
            return True
            
    except Exception as e:
        print(f"⚠️  لم يمكن فحص migrations: {e}")
        return None


def check_voter_count():
    """التحقق من عدد الناخبين"""
    print("\n🔍 فحص بيانات الناخبين...")
    
    try:
        from elections.models import Voter
        
        count = Voter.objects.count()
        
        if count == 0:
            print("⚠️  لا يوجد ناخبون في قاعدة البيانات!")
            print("   قم باستيراد البيانات من:")
            print("   /tool/import-voters-secret/")
            return False
        elif count < 1000000:
            print(f"⚠️  عدد الناخبين منخفض: {count:,}")
            print("   هل اكتمل الاستيراد؟")
            return None
        else:
            print(f"✅ عدد الناخبين: {count:,}")
            return True
            
    except Exception as e:
        print(f"❌ خطأ في فحص الناخبين: {e}")
        return False


def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("🔧 فحص إعداد PostgreSQL على Railway")
    print("=" * 60)
    
    results = {
        'database_url': check_database_url(),
        'django_settings': check_django_settings(),
        'migrations': check_migrations(),
        'voter_count': check_voter_count(),
    }
    
    print("\n" + "=" * 60)
    print("📊 ملخص النتائج:")
    print("=" * 60)
    
    for key, value in results.items():
        status = "✅" if value is True else ("⚠️" if value is None else "❌")
        print(f"{status} {key.replace('_', ' ').title()}")
    
    # الحكم النهائي
    print("\n" + "=" * 60)
    
    if all(v is True for v in results.values()):
        print("🎉 التهانينا! الإعداد كامل وصحيح!")
        print("=" * 60)
        return 0
    elif results['database_url'] is False:
        print("⚠️  يجب إضافة PostgreSQL أولاً من Railway Dashboard")
        print("=" * 60)
        return 1
    elif results['django_settings'] is False:
        print("⚠️  يجب إعادة نشر التطبيق بعد إضافة DATABASE_URL")
        print("=" * 60)
        return 1
    elif results['migrations'] is False:
        print("⚠️  يجب تطبيق migrations:")
        print("   railway run python manage.py migrate")
        print("=" * 60)
        return 1
    elif results['voter_count'] is False:
        print("⚠️  يجب استيراد بيانات الناخبين:")
        print("   افتح: /tool/import-voters-secret/")
        print("=" * 60)
        return 1
    else:
        print("⚠️  بعض الخطوات غير مكتملة - راجع النتائج أعلاه")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
