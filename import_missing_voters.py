"""
استيراد البيانات المفقودة مباشرة إلى Railway PostgreSQL
يقرأ ملفات JSON ويستوردها batch by batch
"""
import os
import json
import psycopg2
from urllib.parse import urlparse
import glob


# معلومات الاتصال بقاعدة البيانات
DATABASE_URL = "postgresql://postgres:MPEXyQDQSBwqjNqhZgpEsBYjtZRkyiNj@switchback.proxy.rlwy.net:41238/railway"


def parse_database_url(url):
    """تحليل DATABASE_URL"""
    result = urlparse(url)
    return {
        'host': result.hostname,
        'port': result.port or 5432,
        'database': result.path[1:],
        'user': result.username,
        'password': result.password
    }


def import_voters_batch(cursor, batch_data, batch_num):
    """استيراد batch واحد من الناخبين"""
    imported = 0
    skipped = 0
    errors = 0
    
    for voter in batch_data:
        try:
            # التحقق إذا كان الناخب موجوداً
            cursor.execute(
                "SELECT id FROM elections_voter WHERE voter_number = %s",
                (voter['fields']['voter_number'],)
            )
            if cursor.fetchone():
                skipped += 1
                continue
            
            # إدراج الناخب
            cursor.execute("""
                INSERT INTO elections_voter (
                    voter_number, full_name, date_of_birth, mother_name,
                    family_number, phone, voting_center_number, voting_center_name,
                    registration_center_name, registration_center_number, 
                    station_number, status, governorate, classification,
                    notes, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    NOW(), NOW()
                )
            """, (
                voter['fields']['voter_number'],
                voter['fields']['full_name'],
                voter['fields'].get('date_of_birth'),
                voter['fields'].get('mother_name', ''),
                voter['fields'].get('family_number', ''),
                voter['fields'].get('phone'),
                voter['fields'].get('voting_center_number', ''),
                voter['fields'].get('voting_center_name', ''),
                voter['fields'].get('registration_center_name', ''),
                voter['fields'].get('registration_center_number', ''),
                voter['fields'].get('station_number', ''),
                voter['fields'].get('status', ''),
                voter['fields'].get('governorate', 'البصرة'),
                voter['fields'].get('classification', 'unknown'),
                voter['fields'].get('notes', '')
            ))
            imported += 1
            
        except Exception as e:
            errors += 1
            if errors <= 3:  # اطبع أول 3 أخطاء فقط
                print(f"      ⚠️ خطأ في السجل: {str(e)[:100]}")
    
    return imported, skipped, errors


def main():
    """الدالة الرئيسية"""
    print("\n" + "="*70)
    print("🚀 استيراد البيانات المفقودة إلى Railway PostgreSQL")
    print("="*70)
    
    # الاتصال بقاعدة البيانات
    print("\n📡 جاري الاتصال بقاعدة البيانات...")
    try:
        db_params = parse_database_url(DATABASE_URL)
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        print("✅ تم الاتصال بنجاح!")
    except Exception as e:
        print(f"❌ فشل الاتصال: {e}")
        return
    
    # الحصول على قائمة الملفات
    batch_files = sorted(glob.glob("voter_batches/voters_batch_*.json"))
    total_batches = len(batch_files)
    
    if total_batches == 0:
        print("❌ لم يتم العثور على ملفات البيانات!")
        return
    
    print(f"\n📊 تم العثور على {total_batches} batch")
    
    # إحصائيات
    total_imported = 0
    total_skipped = 0
    total_errors = 0
    
    # استيراد كل batch
    for i, batch_file in enumerate(batch_files, 1):
        batch_num = int(batch_file.split('_')[-1].replace('.json', ''))
        
        try:
            print(f"\n📝 Batch {batch_num}/{total_batches} ({i}/{total_batches})...")
            
            # قراءة الملف
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
            
            print(f"   📄 عدد السجلات: {len(batch_data):,}")
            
            # الاستيراد
            imported, skipped, errors = import_voters_batch(cursor, batch_data, batch_num)
            
            # حفظ التغييرات
            conn.commit()
            
            # تحديث الإحصائيات
            total_imported += imported
            total_skipped += skipped
            total_errors += errors
            
            print(f"   ✅ تم استيراد: {imported:,}")
            if skipped > 0:
                print(f"   ⏭️ تم تخطي: {skipped:,} (موجود مسبقاً)")
            if errors > 0:
                print(f"   ⚠️ أخطاء: {errors}")
            
            # طباعة التقدم كل 5 batches
            if i % 5 == 0:
                print(f"\n   📊 الإجمالي حتى الآن:")
                print(f"      ✅ مستورد: {total_imported:,}")
                print(f"      ⏭️ مُخطى: {total_skipped:,}")
                print(f"      ⚠️ أخطاء: {total_errors}")
            
        except Exception as e:
            print(f"   ❌ خطأ في معالجة الـ batch: {e}")
            conn.rollback()
    
    # النتائج النهائية
    print("\n" + "="*70)
    print("🎉 اكتملت عملية الاستيراد!")
    print("="*70)
    print(f"\n📊 النتائج النهائية:")
    print(f"   ✅ تم استيراد: {total_imported:,} ناخب")
    print(f"   ⏭️ تم تخطي: {total_skipped:,} (موجود مسبقاً)")
    print(f"   ⚠️ أخطاء: {total_errors}")
    
    # التحقق من العدد الإجمالي
    cursor.execute("SELECT COUNT(*) FROM elections_voter")
    final_count = cursor.fetchone()[0]
    print(f"\n💾 العدد الإجمالي في قاعدة البيانات: {final_count:,} ناخب")
    
    # التحقق من رقم 33037821
    print("\n🔍 التحقق من رقم 33037821...")
    cursor.execute(
        "SELECT id, full_name, voting_center_name FROM elections_voter WHERE voter_number = %s",
        ('33037821',)
    )
    result = cursor.fetchone()
    if result:
        print(f"   ✅ تم العثور على الناخب!")
        print(f"      الاسم: {result[1]}")
        print(f"      المركز: {result[2]}")
    else:
        print(f"   ❌ لم يتم العثور على الناخب (قد يكون في batch لم يُستورد)")
    
    # إغلاق الاتصال
    cursor.close()
    conn.close()
    
    print("\n✅ تم إغلاق الاتصال بقاعدة البيانات")
    print("\n🔗 روابط التحقق:")
    print("   Dashboard: https://web-production-42c39.up.railway.app/dashboard/")
    print("   بحث: https://web-production-42c39.up.railway.app/voter-search/")


if __name__ == "__main__":
    main()
