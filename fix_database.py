"""
تطبيق إصلاح حقل phone على قاعدة بيانات Railway PostgreSQL
يتصل مباشرة بقاعدة البيانات وينفذ التعديلات المطلوبة
"""
import os
import psycopg2
from urllib.parse import urlparse


def get_database_url():
    """
    احصل على DATABASE_URL من متغيرات البيئة
    أو اطلب من المستخدم إدخاله
    """
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("\n" + "="*60)
        print("🔑 يرجى إدخال DATABASE_URL من Railway")
        print("="*60)
        print("\nللحصول على DATABASE_URL:")
        print("1. افتح https://railway.app")
        print("2. اذهب إلى مشروعك (valiant-presence)")
        print("3. اضغط على postgres")
        print("4. اذهب إلى Variables")
        print("5. انسخ قيمة DATABASE_URL")
        print("\n" + "="*60)
        db_url = input("\nالصق DATABASE_URL هنا: ").strip()
    
    return db_url


def parse_database_url(url):
    """تحليل DATABASE_URL لاستخراج معلومات الاتصال"""
    result = urlparse(url)
    return {
        'host': result.hostname,
        'port': result.port or 5432,
        'database': result.path[1:],
        'user': result.username,
        'password': result.password
    }


def fix_phone_field(db_params):
    """تطبيق التعديلات على حقل phone"""
    print("\n" + "="*60)
    print("🔧 بدء عملية إصلاح حقل phone")
    print("="*60)
    
    try:
        # الاتصال بقاعدة البيانات
        print("\n📡 جاري الاتصال بقاعدة البيانات...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        print("✅ تم الاتصال بنجاح!")
        
        # الأمر 1: تغيير نوع الحقل إلى VARCHAR(30)
        print("\n📝 الخطوة 1/3: تغيير طول حقل phone إلى 30 حرف...")
        cursor.execute("""
            ALTER TABLE elections_voter 
            ALTER COLUMN phone TYPE VARCHAR(30);
        """)
        print("✅ تم تغيير طول الحقل بنجاح!")
        
        # الأمر 2: إزالة قيد unique
        print("\n📝 الخطوة 2/3: إزالة قيد unique من حقل phone...")
        cursor.execute("""
            ALTER TABLE elections_voter 
            DROP CONSTRAINT IF EXISTS elections_voter_phone_key;
        """)
        print("✅ تم إزالة قيد unique بنجاح!")
        
        # الأمر 3: السماح بقيم NULL
        print("\n📝 الخطوة 3/3: السماح بقيم null في حقل phone...")
        cursor.execute("""
            ALTER TABLE elections_voter 
            ALTER COLUMN phone DROP NOT NULL;
        """)
        print("✅ تم السماح بقيم null بنجاح!")
        
        # حفظ التغييرات
        conn.commit()
        print("\n💾 تم حفظ جميع التغييرات في قاعدة البيانات!")
        
        # التحقق من التغييرات
        print("\n🔍 التحقق من التغييرات...")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'elections_voter' AND column_name = 'phone';
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"✅ حقل phone:")
            print(f"   - النوع: {result[1]}")
            print(f"   - الطول الأقصى: {result[2]}")
            print(f"   - يقبل null: {result[3]}")
        
        # إغلاق الاتصال
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("🎉 تم إصلاح قاعدة البيانات بنجاح!")
        print("="*60)
        
        print("\n📋 الخطوات التالية:")
        print("1. افتح:")
        print("   https://web-production-42c39.up.railway.app/tool/import-final-data/?secret=shems_voter_import_2024_secure")
        print("\n2. انتظر 15-20 دقيقة حتى ينتهي الاستيراد")
        print("\n3. ابحث عن رقم 33037821 في:")
        print("   https://web-production-42c39.up.railway.app/voter-search/")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ خطأ في قاعدة البيانات: {e}")
        return False
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        return False


def main():
    """الدالة الرئيسية"""
    print("\n" + "="*60)
    print("🚀 أداة إصلاح حقل phone في قاعدة بيانات Railway")
    print("="*60)
    
    # الحصول على DATABASE_URL
    db_url = get_database_url()
    
    if not db_url:
        print("\n❌ لم يتم توفير DATABASE_URL")
        return
    
    # تحليل URL
    try:
        db_params = parse_database_url(db_url)
        print(f"\n✅ تم تحليل معلومات الاتصال:")
        print(f"   Host: {db_params['host']}")
        print(f"   Database: {db_params['database']}")
    except Exception as e:
        print(f"\n❌ خطأ في تحليل DATABASE_URL: {e}")
        return
    
    # تنفيذ الإصلاح
    success = fix_phone_field(db_params)
    
    if success:
        print("\n✅ العملية اكتملت بنجاح!")
    else:
        print("\n❌ فشلت العملية. يرجى مراجعة الأخطاء أعلاه.")


if __name__ == "__main__":
    main()
