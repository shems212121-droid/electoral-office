import requests
from bs4 import BeautifulSoup
import json

# Railway app URL
BASE_URL = "https://web-production-42c39.up.railway.app"
LOGIN_URL = f"{BASE_URL}/accounts/login/"
ADMIN_URL = f"{BASE_URL}/admin/elections/voter/"

# Login credentials
USERNAME = "admin"
PASSWORD = "admin123"

print("🔍 التحقق من عدد الناخبين على Railway...")
print("=" * 60)

# Create session
session = requests.Session()

try:
    # Get login page to get CSRF token
    print("1️⃣ جارٍ تسجيل الدخول...")
    response = session.get(LOGIN_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    if csrf_token:
        csrf_token = csrf_token.get('value')
    else:
        print("⚠️  لم يتم العثور على CSRF token")
        # Try to get from cookies
        csrf_token = session.cookies.get('csrftoken', '')
    
    # Login
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrfmiddlewaretoken': csrf_token,
        'next': '/dashboard/'
    }
    
    response = session.post(LOGIN_URL, data=login_data, headers={'Referer': LOGIN_URL})
    
    if response.status_code == 200:
        print("✅ تم تسجيل الدخول بنجاح")
    else:
        print(f"❌ فشل تسجيل الدخول: {response.status_code}")
        exit(1)
    
    # Get voter admin page
    print("\n2️⃣ جارٍ جلب بيانات الناخبين...")
    response = session.get(ADMIN_URL)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find paginator element
        paginator = soup.find('p', class_='paginator')
        
        if paginator:
            text = paginator.get_text().strip()
            print(f"✅ معلومات الصفحات: {text}")
            
            # Try to extract number
            import re
            numbers = re.findall(r'[\d,]+', text)
            if numbers:
                # The last number is usually the total
                total = numbers[-1].replace(',', '')
                print(f"\n📊 إجمالي عدد الناخبين: {int(total):,}")
                
                # Compare with expected
                expected = 1868933
                imported = int(total)
                percentage = (imported / expected) * 100
                
                print(f"📈 المتوقع: {expected:,}")
                print(f"📥 تم استيراده: {imported:,}")
                print(f"📊 النسبة المئوية: {percentage:.2f}%")
                
                if imported == expected:
                    print("\n✅ تم استيراد جميع الناخبين بنجاح!")
                elif imported > 0:
                    print(f"\n⚠️  تم استيراد {imported:,} ناخب من أصل {expected:,}")
                    print(f"   الناقص: {expected - imported:,} ناخب")
                else:
                    print("\n❌ لا يوجد ناخبون في قاعدة البيانات")
            else:
                print("⚠️  لم يتم العثور على أرقام في معلومات الصفحات")
        else:
            print("⚠️  لم يتم العثور على عنصر paginator")
            # Try alternative method - count from response
            print("🔍 محاولة طريقة بديلة...")
            
    else:
        print(f"❌ فشل جلب صفحة الناخبين: {response.status_code}")
        
except Exception as e:
    print(f"❌ حدث خطأ: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ انتهى الفحص")
