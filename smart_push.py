
import os
import subprocess
import time
from pathlib import Path

def progressive_push():
    print("🚀 بدء الرفع التدريجي...")
    
    # الحصول على ملفات الـ zip
    data_dir = Path('voters_data_parts')
    files = sorted([f.name for f in data_dir.glob('voters_part_*.zip')])
    
    total_files = len(files)
    batch_size = 5
    
    print(f"📦 الإجمالي: {total_files} ملف. سيتم الرفع على دفعات من {batch_size}.")
    
    # إلغاء الـ stage الحالي
    subprocess.run(['git', 'reset', 'HEAD'], check=False)
    
    # إضافة الملفات الأساسية أولاً
    subprocess.run(['git', 'add', 'elections/management/commands/import_final_data.py', 'elections/views_import_tool.py', 'elections/urls.py', 'elections/templates/elections/tools/import_remaining_voters.html'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Add import logic'], check=False)
    subprocess.run(['git', 'push', 'origin', 'main'], check=False)
    
    for i in range(0, total_files, batch_size):
        batch = files[i:i+batch_size]
        print(f"\n📤 رفع الدفعة {i//batch_size + 1} ({len(batch)} ملفات)...")
        
        for f in batch:
            subprocess.run(['git', 'add', str(data_dir / f)], check=True)
            
        subprocess.run(['git', 'commit', '-m', f'Upload data batch {i//batch_size + 1}'], check=False)
        
        # المحاولة 3 مرات للـ push
        success = False
        for attempt in range(3):
            try:
                print(f"   ⏳ محاولة Push رقم {attempt+1}...")
                result = subprocess.run(['git', 'push', 'origin', 'main'], check=True, text=True, capture_output=True)
                print("   ✅ تم الرفع!")
                success = True
                break
            except subprocess.CalledProcessError as e:
                print(f"   ❌ فشل: {e.stderr}")
                time.sleep(5)
        
        if not success:
            print("❌ فشل رفع الدفعة بعد 3 محاولات. توقف.")
            return

    print("\n🎉 تم رفع جميع الملفات بنجاح!")

if __name__ == '__main__':
    progressive_push()
