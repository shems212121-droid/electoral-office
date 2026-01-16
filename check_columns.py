
import psycopg2

url = "postgresql://postgres:MPEXyQDQSBwqjNqhZgpEsBYjtZRkyiNj@switchback.proxy.rlwy.net:41238/railway"

try:
    conn = psycopg2.connect(url)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'elections_voter';
    """)
    
    columns = [row[0] for row in cursor.fetchall()]
    print("أعمدة جدول elections_voter:")
    for col in sorted(columns):
        print(f" - {col}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
