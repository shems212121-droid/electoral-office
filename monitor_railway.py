
import psycopg2
import time

url = "postgresql://postgres:MPEXyQDQSBwqjNqhZgpEsBYjtZRkyiNj@switchback.proxy.rlwy.net:41238/railway"

print("مراقبة التقدم على Railway...")
try:
    conn = psycopg2.connect(url)
    cursor = conn.cursor()
    
    for i in range(5):
        cursor.execute("SELECT COUNT(*) FROM elections_voter")
        count = cursor.fetchone()[0]
        print(f"العدد الحالي: {count:,}")
        time.sleep(2)
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
