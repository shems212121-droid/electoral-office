# Script to push code to GitHub
# سكريبت لرفع الكود إلى GitHub

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   رفع الكود إلى GitHub   " -ForegroundColor Yellow
Write-Host "   Pushing Code to GitHub   " -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Get GitHub username
$username = Read-Host "أدخل اسم المستخدم في GitHub (shems212121-droid)"
if ([string]::IsNullOrEmpty($username)) {
    $username = "shems212121-droid"
}

# Get GitHub token or password
Write-Host ""
Write-Host "ملاحظة: استخدم Personal Access Token وليس كلمة المرور العادية" -ForegroundColor Yellow
Write-Host "Note: Use Personal Access Token, not your regular password" -ForegroundColor Yellow
Write-Host ""
$token = Read-Host "أدخل Personal Access Token" -AsSecureString

# Convert secure string to plain text
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
$PlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Create URL with credentials
$repoUrl = "https://${username}:${PlainPassword}@github.com/shems212121-droid/electoral-office.git"

Write-Host ""
Write-Host "جاري رفع الكود..." -ForegroundColor Green
Write-Host "Pushing code..." -ForegroundColor Green
Write-Host ""

# Push to GitHub
git push $repoUrl main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "   ✓ نجح رفع الكود!   " -ForegroundColor Green
    Write-Host "   ✓ Code pushed successfully!   " -ForegroundColor Green  
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "الآن سيبدأ Railway النشر تلقائياً خلال 30 ثانية" -ForegroundColor Yellow
    Write-Host "Railway will start deploying automatically within 30 seconds" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Red
    Write-Host "   ✗ فشل رفع الكود   " -ForegroundColor Red
    Write-Host "   ✗ Failed to push code   " -ForegroundColor Red
    Write-Host "==================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "تحقق من اسم المستخدم والـ Token" -ForegroundColor Yellow
    Write-Host "Check your username and token" -ForegroundColor Yellow
}

# Clear sensitive data from memory
$PlainPassword = $null
[System.GC]::Collect()

Write-Host ""
Write-Host "اضغط أي مفتاح للخروج..." -ForegroundColor Cyan
Write-Host "Press any key to exit..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
