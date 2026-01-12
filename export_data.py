#!/usr/bin/env python
"""
تصدير البيانات المهمة من قاعدة البيانات المحلية لرفعها إلى الإنتاج
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.core import serializers

def export_users_and_groups():
    """تصدير المستخدمين والمجموعات"""
    print("🔄 جاري تصدير المستخدمين والمجموعات...")
    
    # تصدير المجموعات
    groups = Group.objects.all()
    groups_data = serializers.serialize('json', groups, indent=2, use_natural_foreign_keys=True)
    
    with open('groups_data.json', 'w', encoding='utf-8') as f:
        f.write(groups_data)
    print(f"✅ تم تصدير {groups.count()} مجموعة")
    
    # تصدير المستخدمين (بدون كلمات المرور للأمان)
    users = User.objects.all()
    users_list = []
    for user in users:
        users_list.append({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'groups': [g.name for g in user.groups.all()],
        })
    
    with open('users_data.json', 'w', encoding='utf-8') as f:
        json.dump(users_list, f, ensure_ascii=False, indent=2)
    print(f"✅ تم تصدير {len(users_list)} مستخدم")

def export_app_data(app_name):
    """تصدير بيانات تطبيق معين"""
    from django.apps import apps
    
    try:
        app_config = apps.get_app_config(app_name)
        models = app_config.get_models()
        
        all_data = []
        total_count = 0
        
        for model in models:
            objects = model.objects.all()
            count = objects.count()
            if count > 0:
                model_data = serializers.serialize('json', objects, indent=2, use_natural_foreign_keys=True)
                all_data.append(model_data)
                total_count += count
                print(f"   - {model.__name__}: {count} سجل")
        
        if all_data:
            filename = f'{app_name}_data.json'
            # دمج كل البيانات
            combined_data = '[\n' + ',\n'.join([d.strip()[1:-1] for d in all_data if d.strip() != '[]']) + '\n]'
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(combined_data)
            print(f"✅ تم تصدير {total_count} سجل من تطبيق {app_name}")
            return True
        else:
            print(f"⚠️ لا توجد بيانات في تطبيق {app_name}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في تصدير {app_name}: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("تصدير البيانات من قاعدة البيانات المحلية")
    print("=" * 60)
    
    # تصدير المستخدمين والمجموعات
    export_users_and_groups()
    
    print("\n" + "=" * 60)
    print("تصدير بيانات التطبيقات")
    print("=" * 60)
    
    # قائمة التطبيقات التي تريد تصديرها
    apps_to_export = [
        'candidates',      # المرشحون
        'anchors',         # المراسي
        'introducers',     # المعرفون  
        'voters',          # الناخبون
        'monitors',        # المراقبون
        'vote_counting',   # فرز الأصوات
        'operations_room', # غرفة العمليات
        # أضف المزيد حسب الحاجة
    ]
    
    exported_count = 0
    for app_name in apps_to_export:
        print(f"\n📦 تصدير تطبيق: {app_name}")
        if export_app_data(app_name):
            exported_count += 1
    
    print("\n" + "=" * 60)
    print("✅ اكتمل التصدير!")
    print("=" * 60)
    print(f"\nتم تصدير {exported_count} تطبيق بنجاح")
    print("\nالخطوات التالية:")
    print("1. راجع الملفات المصدرة (users_data.json, candidates_data.json, ...)")
    print("2. ارفع الملفات للمستودع:")
    print("   git add *_data.json")
    print("   git commit -m 'إضافة البيانات الأولية'")
    print("   git push origin main")
    print("3. على Railway، شغل:")
    print("   python manage.py loaddata candidates_data.json")
    print("   python manage.py loaddata voters_data.json")
    print("   ... إلخ")
