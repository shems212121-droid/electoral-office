"""
View to trigger the fix_phone_field management command via URL
"""
from django.http import HttpResponse
from django.core.management import call_command
from io import StringIO


def run_fix_phone_field(request):
    """Execute fix_phone_field command via web interface"""
    # Security check
    secret = request.GET.get('secret')
    if secret != 'shems_voter_import_2024_secure' and not request.user.is_superuser:
        return HttpResponse('❌ Unauthorized - Admin Access Only', status=403)
    
    # Capture command output
    output = StringIO()
    
    try:
        call_command('fix_phone_field', stdout=output)
        result = output.getvalue()
        
        return HttpResponse(f'''
            <html>
            <head>
                <title>Phone Field Fix</title>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                        background: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #2ecc71;
                        text-align: center;
                    }}
                    pre {{
                        background: #2c3e50;
                        color: #ecf0f1;
                        padding: 20px;
                        border-radius: 5px;
                        overflow-x: auto;
                        direction: ltr;
                        text-align: left;
                    }}
                    .success {{
                        color: #2ecc71;
                        font-size: 18px;
                        font-weight: bold;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 10px 20px;
                        background: #3498db;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 10px 5px;
                    }}
                    .button:hover {{
                        background: #2980b9;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ إصلاح حقل الهاتف تم بنجاح!</h1>
                    
                    <p class="success">تم تطبيق التغييرات على قاعدة البيانات:</p>
                    <ul>
                        <li>✓ زيادة طول حقل phone إلى 30 حرف</li>
                        <li>✓ إزالة قيد unique من الحقل</li>
                        <li>✓ السماح بالقيم null</li>
                    </ul>
                    
                    <h3>سجل العملية:</h3>
                    <pre>{result}</pre>
                    
                    <h3>الخطوات القادمة:</h3>
                    <p>يمكنك الآن إعادة استيراد البيانات المفقودة:</p>
                    
                    <a href="/tool/import-final-data/?secret=shems_voter_import_2024_secure" class="button">
                        🔄 إعادة استيراد كل البيانات
                    </a>
                    
                    <a href="/voter-search/" class="button">
                        🔍 البحث عن ناخب
                    </a>
                    
                    <a href="/dashboard/" class="button">
                        📊 لوحة التحكم
                    </a>
                </div>
            </body>
            </html>
        ''', content_type='text/html; charset=utf-8')
        
    except Exception as e:
        return HttpResponse(f'''
            <html>
            <head>
                <title>Error</title>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                        background: #f5f5f5;
                    }}
                    .error {{
                        background: #e74c3c;
                        color: white;
                        padding: 20px;
                        border-radius: 10px;
                    }}
                    pre {{
                        background: white;
                        color: #e74c3c;
                        padding: 15px;
                        border-radius: 5px;
                        margin-top: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>❌ حدث خطأ</h1>
                    <pre>{str(e)}</pre>
                    <p>يرجى التحقق من logs على Railway</p>
                </div>
            </body>
            </html>
        ''', content_type='text/html; charset=utf-8', status=500)
