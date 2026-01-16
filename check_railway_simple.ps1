# التحقق من عدد الناخبين على Railway
$BASE_URL = "https://web-production-42c39.up.railway.app"
$LOGIN_URL = "$BASE_URL/accounts/login/"
$ADMIN_URL = "$BASE_URL/admin/elections/voter/"

Write-Host "🔍 التحقق من عدد الناخبين على Railway..." -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Gray

# Create session
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

try {
    Write-Host "1️⃣ جارٍ تسجيل الدخول..." -ForegroundColor Yellow
    
    # Get login page
    $response = Invoke-WebRequest -Uri $LOGIN_URL -SessionVariable session -UseBasicParsing
    
    # Extract CSRF token
    if ($response.Content -match 'name="csrfmiddlewaretoken" value="([^"]+)"') {
        $csrfToken = $Matches[1]
    } else {
        # Try from cookies
        $csrfToken = $session.Cookies.GetCookies($LOGIN_URL) | Where-Object { $_.Name -eq "csrftoken" } | Select-Object -ExpandProperty Value
    }
    
    # Login
    $loginData = @{
        username = "admin"
        password = "admin123"
        csrfmiddlewaretoken = $csrfToken
        next = "/dashboard/"
    }
    
    $response = Invoke-WebRequest -Uri $LOGIN_URL -Method Post -Body $loginData -WebSession $session -UseBasicParsing
    
    Write-Host "✅ تم تسجيل الدخول بنجاح" -ForegroundColor Green
    
    Write-Host "`n2️⃣ جارٍ جلب بيانات الناخبين..." -ForegroundColor Yellow
    
    # Get voter page
    $response = Invoke-WebRequest -Uri $ADMIN_URL -WebSession $session -UseBasicParsing
    
    # Extract voter count from paginator
    if ($response.Content -match '(\d+)\s*(?:من|of)\s*(\d[\d,]*)\s*(?:ناخب|voter)') {
        $total = $Matches[2] -replace ',', ''
        Write-Host "✅ تم العثور على العدد في النص" -ForegroundColor Green
        Write-Host "`n📊 إجمالي عدد الناخبين: $total" -ForegroundColor Cyan
        
        $expected = 1868933
        $imported = [int]$total
        $percentage = ($imported / $expected) * 100
        
        Write-Host "📈 المتوقع: $expected" -ForegroundColor White
        Write-Host "📥 تم استيراده: $imported" -ForegroundColor White
        Write-Host "📊 النسبة المئوية: $($percentage.ToString('F2'))%" -ForegroundColor White
        
        if ($imported -eq $expected) {
            Write-Host "`n✅ تم استيراد جميع الناخبين بنجاح!" -ForegroundColor Green
        } elseif ($imported -gt 0) {
            $missing = $expected - $imported
            Write-Host "`n⚠️  تم استيراد $imported ناخب من أصل $expected" -ForegroundColor Yellow
            Write-Host "   الناقص: $missing ناخب" -ForegroundColor Yellow
        } else {
            Write-Host "`n❌ لا يوجد ناخبون في قاعدة البيانات" -ForegroundColor Red
        }
    } else {
        # Alternative pattern
        if ($response.Content -match '([\d,]+)\s*(?:ناخب|voters?)') {
            $total = $Matches[1] -replace ',', ''
            Write-Host "`n📊 إجمالي عدد الناخبين: $total" -ForegroundColor Cyan
        } else {
            Write-Host "⚠️  لم يتم العثور على عدد الناخبين في الصفحة" -ForegroundColor Yellow
            Write-Host "محاولة البحث عن نمط آخر..." -ForegroundColor Yellow
            
            # Search for any large numbers
            $numbers = [regex]::Matches($response.Content, '\d[\d,]+') | ForEach-Object { $_.Value -replace ',', '' } | Where-Object { [int]$_ -gt 100000 }
            if ($numbers) {
                Write-Host "الأرقام الكبيرة الموجودة في الصفحة:" -ForegroundColor Yellow
                $numbers | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
            }
        }
    }
    
} catch {
    Write-Host "❌ حدث خطأ: $_" -ForegroundColor Red
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Gray
Write-Host "✅ انتهى الفحص" -ForegroundColor Green
