
import os
import django
import json
import zipfile
from pathlib import Path

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from elections.models import Voter
from django.core.serializers import serialize

def export_and_split():
    print("🚀 بدء تصدير البيانات وتقسيمها للرفع الآمن...")
    
    # المجلد الوجهة
    output_dir = Path('voters_data_parts')
    output_dir.mkdir(exist_ok=True)
    
    # تنظيف المجلد القديم
    for f in output_dir.glob('*'):
        f.unlink()
        
    BATCH_SIZE = 50000  # 50,000 ناخب في كل ملف (حوالي 10-15 ميجا JSON)
    total_count = Voter.objects.count()
    
    print(f"📊 الإجمالي: {total_count:,} ناخب")
    
    for i, offset in enumerate(range(0, total_count, BATCH_SIZE)):
        batch_num = i + 1
        print(f"📦 معالجة الجزء {batch_num} (من {offset} إلى {offset+BATCH_SIZE})...")
        
        # جلب البيانات
        voters = Voter.objects.all()[offset:offset+BATCH_SIZE]
        
        # تحويل لـ JSON
        json_data = serialize('json', voters)
        
        # حفظ كملف مضغوط مباشرة
        zip_filename = output_dir / f'voters_part_{batch_num:03d}.zip'
        json_filename = f'voters_part_{batch_num:03d}.json'
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(json_filename, json_data)
            
        print(f"   ✅ تم الحفظ: {zip_filename} ({os.path.getsize(zip_filename)/1024/1024:.2f} MB)")
        
    print("\n✅ تم الانتهاء! الملفات جاهزة في مجلد voters_data_parts")

if __name__ == '__main__':
    export_and_split()
