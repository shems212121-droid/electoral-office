# ===========================================
# سكريبت استيراد بيانات الناخبين إلى PostgreSQL
# Import Voters to PostgreSQL on Railway
# ===========================================
#
# هذا السكريبت يستورد بيانات الناخبين من قاعدة البيانات المحلية
# إلى PostgreSQL على Railway
#
# الخطوات:
# 1. احصل على DATABASE_URL من Railway
#    - اذهب إلى Railway Dashboard
#    - اختر مشروعك ثم قاعدة البيانات PostgreSQL
#    - انسخ DATABASE_URL من Variables
#
# 2. شغل هذا السكريبت
#
# ملاحظة: العملية قد تستغرق عدة ساعات لاستيراد 1.8 مليون ناخب
# ===========================================

# تعيين متغير البيئة لقاعدة البيانات
# DATABASE_URL from Railway (Public URL for external access)

$env:DATABASE_URL = "postgresql://postgres:JClBkfJwzsyLCrXBegCQaCOHygpXLpjo@centerbeam.proxy.rlwy.net:17251/railway"

# أولاً: تأكد من وجود الإعدادات المحلية التي تحتوي على legacy_voters_db
$env:DJANGO_SETTINGS_MODULE = "electoral_office.settings"

# الانتقال إلى مجلد المشروع
Set-Location "C:\Users\2025\.gemini\antigravity\scratch\electoral_office"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "     استيراد بيانات الناخبين إلى PostgreSQL    " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# التحقق من وجود قاعدة البيانات المحلية
$legacyDbPath = "C:\Users\2025\.gemini\antigravity\scratch\voters_decrypted_fast.sqlite"
if (-Not (Test-Path $legacyDbPath)) {
    Write-Host "خطأ: قاعدة البيانات المحلية غير موجودة!" -ForegroundColor Red
    Write-Host "المسار المتوقع: $legacyDbPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "قاعدة البيانات المحلية موجودة ✓" -ForegroundColor Green

# عرض خيارات الاستيراد
Write-Host ""
Write-Host "خيارات الاستيراد المتاحة:" -ForegroundColor Yellow
Write-Host "1. استيراد عينة صغيرة (1,000 ناخب) - للاختبار"
Write-Host "2. استيراد عينة متوسطة (10,000 ناخب)"
Write-Host "3. استيراد عينة كبيرة (100,000 ناخب)"
Write-Host "4. استيراد محافظة البصرة فقط (~1.8 مليون)"
Write-Host "5. استيراد جميع الناخبين"
Write-Host ""

$choice = Read-Host "اختر رقم الخيار"

switch ($choice) {
    "1" {
        Write-Host "جاري استيراد 1,000 ناخب للاختبار..." -ForegroundColor Cyan
        python manage.py import_voters_to_postgres --batch-size=500 --limit=1000
    }
    "2" {
        Write-Host "جاري استيراد 10,000 ناخب..." -ForegroundColor Cyan
        python manage.py import_voters_to_postgres --batch-size=2000 --limit=10000
    }
    "3" {
        Write-Host "جاري استيراد 100,000 ناخب..." -ForegroundColor Cyan
        python manage.py import_voters_to_postgres --batch-size=5000 --limit=100000
    }
    "4" {
        Write-Host "جاري استيراد ناخبي محافظة البصرة..." -ForegroundColor Cyan
        Write-Host "هذه العملية قد تستغرق عدة ساعات!" -ForegroundColor Yellow
        python manage.py import_voters_to_postgres --batch-size=5000 --governorate=8
    }
    "5" {
        Write-Host "جاري استيراد جميع الناخبين..." -ForegroundColor Cyan
        Write-Host "هذه العملية قد تستغرق وقتاً طويلاً جداً!" -ForegroundColor Yellow
        python manage.py import_voters_to_postgres --batch-size=5000
    }
    default {
        Write-Host "خيار غير صحيح" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "                 انتهى                      " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
