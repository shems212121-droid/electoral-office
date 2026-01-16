#!/usr/bin/env python
"""
نقل البيانات مباشرة من SQLite المحلي إلى PostgreSQL على Railway
"""
import os
import django
import psycopg2
from psycopg2.extras import execute_batch
import sys
from datetime import datetime

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from elections.models import Voter

def transfer_voters_to_railway():
    """نقل الناخبين إلى Railway PostgreSQL"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Transfer voters to Railway')
    parser.add_argument('--url', help='Railway DATABASE_URL')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    args = parser.parse_args()

    print("=" * 70)
    print("🚀 نقل البيانات من SQLite المحلي إلى Railway PostgreSQL")
    print("=" * 70)
    print()
    
    if args.url:
        railway_url = args.url
        print("📋 تم استخدام DATABASE_URL من المعاملات.")
    else:
        # طلب DATABASE_URL من المستخدم
        print("📋 يرجى نسخ DATABASE_URL من Railway:")
        print("   1. افتح Railway Dashboard")
        print("   2. اذهب إلى Variables")
        print("   3. انسخ قيمة DATABASE_URL")
        print()
        railway_url = input("الصق DATABASE_URL هنا: ").strip()
    
    if not railway_url:
        print("❌ لم تدخل DATABASE_URL!")
        return
    
    # التحقق من العدد المحلي
    local_count = Voter.objects.count()
    print(f"\n📊 عدد الناخبين المحليين: {local_count:,}")
    
    if local_count == 0:
        print("❌ لا يوجد ناخبون في قاعدة البيانات المحلية!")
        return
    
    # الاتصال بـ Railway
    print(f"\n🔌 جارٍ الاتصال بـ Railway...")
    try:
        conn = psycopg2.connect(railway_url)
        cursor = conn.cursor()
        print("✅ تم الاتصال بنجاح!")
    except Exception as e:
        print(f"❌ فشل الاتصال: {e}")
        return
    
    # التحقق من العدد على Railway
    try:
        cursor.execute("SELECT COUNT(*) FROM elections_voter")
        remote_count = cursor.fetchone()[0]
        print(f"📊 عدد الناخبين على Railway حالياً: {remote_count:,}")
    except Exception as e:
        print(f"⚠️  لا يمكن التحقق من العدد: {e}")
        remote_count = 0
    
    # سؤال التأكيد
    print(f"\n⚠️  سيتم نقل {local_count:,} ناخب إلى Railway")
    if remote_count > 0:
        print(f"   ملاحظة: يوجد بالفعل {remote_count:,} ناخب على Railway")
        print(f"   سيتم تجاهل السجلات المكررة")
    
    if not args.yes:
        confirm = input("\nهل تريد المتابعة؟ (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ تم الإلغاء")
            cursor.close()
            conn.close()
            return
    
    # إعداد للنقل
    BATCH_SIZE = 500  # تقليل حجم الدفعة لتفادي انقطاع الاتصال
    total_inserted = 0
    start_time = datetime.now()
    
    # محاولة إعادة الاتصال التلقائي
    def get_connection():
        return psycopg2.connect(railway_url)
        
    print(f"\n🔄 بدء النقل (دفعات من {BATCH_SIZE:,} سجل) مع وضع الاستقرار...")
    print()
    
    offset = 0
    batch_num = 0
    
    conn = get_connection()
    cursor = conn.cursor()
    
    import time
    
    while offset < local_count:
        batch_num += 1
        batch_start = datetime.now()
        
        # جلب الدفعة محلياً
        voters = Voter.objects.all()[offset:offset + BATCH_SIZE]
        
        if not voters:
            break
        
        # تحضير البيانات للإدراج
        insert_query = """
            INSERT INTO elections_voter (
                voter_number, full_name, mother_name, family_number,
                date_of_birth,
                registration_center_fk_id, polling_center_id, polling_station_id,
                governorate, voting_center_number, voting_center_name,
                registration_center_name, registration_center_number,
                station_number, status, classification, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (voter_number) DO NOTHING
        """
        
        values = []
        for voter in voters:
            values.append((
                voter.voter_number,
                voter.full_name,
                voter.mother_name,
                voter.family_number,
                voter.date_of_birth,
                voter.registration_center_fk_id,
                voter.polling_center_id,
                voter.polling_station_id,
                voter.governorate,
                voter.voting_center_number,
                voter.voting_center_name,
                voter.registration_center_name,
                voter.registration_center_number,
                voter.station_number,
                voter.status,
                voter.classification or 'unknown'
            ))
            
        # محاولة الإدخال مع إعادة المحاولة
        for attempt in range(3):
            try:
                execute_batch(cursor, insert_query, values, page_size=100)
                conn.commit()
                break # نجح
            except Exception as e:
                print(f"   ⚠️ فشل (محاولة {attempt+1}): {e}")
                try:
                    conn.close()
                except:
                    pass
                time.sleep(2)
                conn = get_connection()
                cursor = conn.cursor()
                if attempt == 2:
                    print(f"❌ تخطي الدفعة {batch_num} بعد 3 محاولات")
        
        inserted = len(voters)
        total_inserted += inserted
        
        # عرض التقدم
        elapsed = (datetime.now() - start_time).total_seconds()
        rate = total_inserted / elapsed if elapsed > 0 else 0
        remaining = local_count - (offset + inserted)
        eta = remaining / rate if rate > 0 else 0
        progress = ((offset + inserted) / local_count) * 100

        print(f"[{batch_num:4d}] {offset + inserted:,}/{local_count:,} ({progress:.1f}%) | {rate:.0f}/s | ETA: {eta/60:.1f}m", flush=True)
        
        offset += BATCH_SIZE
        # استراحة قصيرة جداً للمساعدة في الاستقرار
        # time.sleep(0.05)
    
    # النهاية
    cursor.close()
    conn.close()
    
    total_duration = (datetime.now() - start_time).total_seconds()
    
    print()
    print("=" * 70)
    print("✅ اكتمل النقل!")
    print("=" * 70)
    print(f"\n📊 الإحصائيات:")
    print(f"   - تم إدراج: {total_inserted:,} ناخب")
    print(f"   - المدة: {total_duration/60:.1f} دقيقة")
    print(f"   - المعدل: {total_inserted/total_duration:,.0f} ناخب/ثانية")
    
    # التحقق النهائي
    print(f"\n🔍 التحقق النهائي...")
    try:
        conn2 = psycopg2.connect(railway_url)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT COUNT(*) FROM elections_voter")
        final_count = cursor2.fetchone()[0]
        cursor2.close()
        conn2.close()
        
        print(f"✅ إجمالي الناخبين على Railway: {final_count:,}")
        
        if final_count == local_count:
            print(f"🎉 تطابق كامل! جميع الناخبين تم نقلهم بنجاح!")
        elif final_count < local_count:
            print(f"⚠️  ناقص {local_count - final_count:,} ناخب")
        else:
            print(f"⚠️  عدد أكبر من المتوقع!")
            
    except Exception as e:
        print(f"⚠️  لا يمكن التحقق: {e}")
    
    print()
    print("=" * 70)
    print("🎉 تمت العملية بنجاح!")
    print("=" * 70)

if __name__ == '__main__':
    try:
        transfer_voters_to_railway()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()
