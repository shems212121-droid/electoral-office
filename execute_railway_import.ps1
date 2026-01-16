# سكريبت تنفيذ استيراد الناخبين المتبقين - Railway
# يجب تشغيله على Railway Terminal أو عبر Railway CLI

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "🚀 استيراد الناخبين المتبقين إلى Railway" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# معلومات المشروع
$PROJECT_NAME = "valiant-presence"
$RAILWAY_URL = "https://web-production-42c39.up.railway.app"

Write-Host "📋 معلومات المشروع:" -ForegroundColor Yellow
Write-Host "   - المشروع: $PROJECT_NAME" -ForegroundColor White
Write-Host "   - الموقع: $RAILWAY_URL" -ForegroundColor White
Write-Host ""

# الجولات
$rounds = @(
    @{
        Name        = "الجولة 1"
        Color       = "Blue"
        Icon        = "🔵"
        Start       = 18
        End         = 28
        Description = "الدفعات 18-27 (~500,000 ناخب)"
        Duration    = "30-40 دقيقة"
    },
    @{
        Name        = "الجولة 2"
        Color       = "Green"
        Icon        = "🟢"
        Start       = 28
        End         = 34
        Description = "الدفعات 28-33 (~300,000 ناخب)"
        Duration    = "20-30 دقيقة"
    },
    @{
        Name        = "الجولة 3"
        Color       = "Yellow"
        Icon        = "🟡"
        Start       = 34
        End         = 39
        Description = "الدفعات 34-38 (~200,000 ناخب)"
        Duration    = "15-25 دقيقة"
    }
)

Write-Host "📊 خطة الاستيراد:" -ForegroundColor Yellow
Write-Host ""
foreach ($round in $rounds) {
    Write-Host "   $($round.Icon) $($round.Name): $($round.Description)" -ForegroundColor $round.Color
    Write-Host "      المدة المتوقعة: $($round.Duration)" -ForegroundColor Gray
}
Write-Host ""

# السؤال عن بدء العملية
Write-Host "⚠️  تحذير:" -ForegroundColor Yellow
Write-Host "   - هذه العملية ستستغرق ~90-120 دقيقة" -ForegroundColor White
Write-Host "   - يجب عدم إيقاف العملية أثناء التنفيذ" -ForegroundColor White
Write-Host "   - تأكد من وجود اتصال إنترنت مستقر" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "هل تريد المتابعة؟ (y/n)"
if ($confirm -ne 'y') {
    Write-Host "❌ تم الإلغاء" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "🚀 بدء عملية الاستيراد" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# التحقق من Railway CLI
try {
    $railwayVersion = railway --version 2>&1
    Write-Host "✅ Railway CLI موجود: $railwayVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ خطأ: Railway CLI غير مثبت" -ForegroundColor Red
    Write-Host ""
    Write-Host "لتثبيته، استخدم:" -ForegroundColor Yellow
    Write-Host "   iwr https://railway.app/install.ps1 -useb | iex" -ForegroundColor White
    exit 1
}

Write-Host ""

# تنفيذ الجولات
$totalStartTime = Get-Date

foreach ($round in $rounds) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor $round.Color
    Write-Host "$($round.Icon) $($round.Name): $($round.Description)" -ForegroundColor $round.Color
    Write-Host ("=" * 70) -ForegroundColor $round.Color
    Write-Host ""
    
    $roundStartTime = Get-Date
    
    # الأمر
    $command = "IMPORT_START_BATCH=$($round.Start) IMPORT_END_BATCH=$($round.End) python import_voters_batches.py"
    
    Write-Host "🔧 الأمر:" -ForegroundColor Yellow
    Write-Host "   $command" -ForegroundColor White
    Write-Host ""
    
    Write-Host "⏳ جارٍ التنفيذ..." -ForegroundColor Yellow
    Write-Host "   المدة المتوقعة: $($round.Duration)" -ForegroundColor Gray
    Write-Host ""
    
    # تنفيذ الأمر
    try {
        railway run bash -c $command
        
        $roundEndTime = Get-Date
        $roundDuration = $roundEndTime - $roundStartTime
        
        Write-Host ""
        Write-Host "✅ $($round.Name) اكتملت!" -ForegroundColor Green
        Write-Host "   المدة الفعلية: $($roundDuration.ToString('mm\:ss'))" -ForegroundColor Gray
        Write-Host ""
        
        # التحقق من العدد
        Write-Host "🔍 التحقق من العدد..." -ForegroundColor Yellow
        $countCommand = "python manage.py shell -c ""from elections.models import Voter; print(f'الإجمالي: {Voter.objects.count():,}')"""
        railway run bash -c $countCommand
        
        Write-Host ""
        
        # استراحة بين الجولات (ماعدا الأخيرة)
        if ($round -ne $rounds[-1]) {
            Write-Host "⏸️  استراحة 30 ثانية قبل الجولة التالية..." -ForegroundColor Cyan
            Start-Sleep -Seconds 30
        }
        
    }
    catch {
        Write-Host ""
        Write-Host "❌ خطأ في $($round.Name):" -ForegroundColor Red
        Write-Host "   $_" -ForegroundColor Red
        Write-Host ""
        
        $retry = Read-Host "هل تريد المحاولة مرة أخرى؟ (y/n)"
        if ($retry -eq 'y') {
            # إعادة المحاولة
            railway run bash -c $command
        }
        else {
            $continue = Read-Host "هل تريد المتابعة إلى الجولة التالية؟ (y/n)"
            if ($continue -ne 'y') {
                Write-Host "❌ تم إيقاف العملية" -ForegroundColor Red
                exit 1
            }
        }
    }
}

$totalEndTime = Get-Date
$totalDuration = $totalEndTime - $totalStartTime

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host "🎉 اكتملت جميع الجولات!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host ""

Write-Host "⏱️  المدة الإجمالية: $($totalDuration.ToString('hh\:mm\:ss'))" -ForegroundColor Cyan
Write-Host ""

# التحقق النهائي
Write-Host ("=" * 70) -ForegroundColor Yellow
Write-Host "✅ التحقق النهائي" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Yellow
Write-Host ""

Write-Host "🔍 فحص العدد الإجمالي..." -ForegroundColor Yellow
$finalCountCommand = @"
from elections.models import Voter
total = Voter.objects.count()
expected = 1868933
percentage = (total / expected) * 100

print(f"""
📊 النتيجة النهائية:
   - الموجود: {total:,}
   - المتوقع: {expected:,}
   - النسبة: {percentage:.2f}%
""")

if total == expected:
    print("✅ جميع الناخبين مستوردون بنجاح!")
elif total > expected * 0.99:
    print("⚠️  مستورد تقريباً - قد يكون هناك بعض السجلات الناقصة")
else:
    missing = expected - total
    print(f"❌ ناقص {missing:,} ناخب")
"@

railway run python manage.py shell -c $finalCountCommand

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host "✅ انتهت عملية الاستيراد" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host ""

Write-Host "📍 الخطوات التالية:" -ForegroundColor Yellow
Write-Host "   1. افتح الموقع: $RAILWAY_URL" -ForegroundColor White
Write-Host "   2. سجل دخول بـ: admin / admin123" -ForegroundColor White
Write-Host "   3. تحقق من لوحة التحكم" -ForegroundColor White
Write-Host "   4. جرب البحث عن ناخب" -ForegroundColor White
Write-Host ""

# فتح الموقع (اختياري)
$openBrowser = Read-Host "هل تريد فتح الموقع في المتصفح؟ (y/n)"
if ($openBrowser -eq 'y') {
    Start-Process $RAILWAY_URL
}

Write-Host ""
Write-Host "🎉 تمت العملية بنجاح!" -ForegroundColor Green
