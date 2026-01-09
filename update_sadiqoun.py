import os
import django

# إعداد بيئة جانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from elections.models import PoliticalParty, PartyCandidate

# قائمة الأسماء من الصورة
SADIQOUN_CANDIDATES = [
    "عدي عواد",
    "رفيق هاشم الصالحي",
    "هادي علي هادي الشلال",
    "زهره حمزه البجاري",
    "محمد كامل ابوالهيل المنصوري",
    "عماد نعيم الاسدي",
    "جاسم جحيل هلال الحميدي",
    "ساره توفيق الصالحي",
    "ناصر سماري جعفر",
    "جبار امين جبار",
    "علاوي عباس الوافي",
    "زهراء عبدالرضا السلمي",
    "جلال عباس جولان",
    "عبدالحكيم قدوري الاجودي",
    "احمد حسن عيسى القطراني",
    "ضفاف ناظم داخل البوعلي",
    "سلام جمعة هاشم البديري",
    "جوده سلمان علي البصيري",
    "مصطفى كنعان مصطفى التميمي",
    "رجاء فاضل عزيز الحربي",
    "ماجد حامد دينار الخالدي",
    "عدي حاتم هجول راضي",
    "علي طالب عبدالله البدران",
    "امل محمد عبدالكريم العبدالله",
    "مهند حسين موحان الغزي",
    "احمد حامد داود العطبي",
    "علي عاصي نمر الشمري",
    "افراح طالب علي الهلال",
    "احسان منور عبدالنبي العبود",
    "حسين هادي مهجر الحلفي",
    "احمد راضي لازم مزبان",
    "وجدان عبداللطيف نعمه الظالمي",
    "جبر ياسين خلف المنصوري",
    "احمد عبدالحميد حسين",
    "عمار عبدالرحيم احمد الحلفي",
    "حنان فاخر محمد الزركاني",
    "منتصر محسن شنشول اللامي",
    "علاء جواد محمد شبل",
    "الاء عوده خلف الموسوي",
    "محمد حسين محمد الموسوي",
    "ناديه محمد جبر العبودي",
    "سمير قاسم سلمان قاسم",
    "حسان عبداللطيف ناصر",
    "براء قاسم جياد الصريفي",
    "علي فالح عويد الاماره",
    "سوسن حبيب حسين الموسوي",
    "علي عبدالحافظ إبراهيم الصالحي",
    "سامر ضايف مزيد ناجي",
    "نداء رسن عبدالصاحب الساعدي",
    "وجدي عبدالحسين الاماره"
]

def update_sadiqoun():
    print("Restoring/Creating Kotlat Al-Sadiqoun candidates...")
    
    # إنشاء الحزب بالاسم الصحيح "كتلة الصادقون"
    party, created = PoliticalParty.objects.get_or_create(
        name="كتلة الصادقون",
        defaults={
            "serial_number": 190, # نفس الرقم السابق أو يمكن تعديله
            "color": "#16a085",
            "description": "كتلة الصادقون النيابية"
        }
    )
    
    if created:
        print(f"Created party: {party.name}")
    else:
        print(f"Found party: {party.name}")

    # حذف المرشحين الحاليين للحزب (لإعادة بنائهم بالترتيب الصحيح وضمان عدم التكرار)
    current_count = party.candidates.count()
    if current_count > 0:
        print(f"Cleaning up {current_count} existing candidates for re-import...")
        party.candidates.all().delete()
    
    # الحصول على آخر رقم كود
    existing_codes = PartyCandidate.objects.filter(candidate_code__startswith='03').values_list('candidate_code', flat=True)
    max_num = 0
    for code in existing_codes:
        if code and len(code) > 2:
            try:
                num = int(code[2:])
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    
    current_code_num = max_num + 1
    print(f"Starting candidate codes from: 03{current_code_num:02d}")

    # إضافة الأسماء
    print(f"Adding {len(SADIQOUN_CANDIDATES)} candidates...")
    
    for i, name in enumerate(SADIQOUN_CANDIDATES):
        serial = i + 1
        code = f"03{current_code_num:02d}"
        current_code_num += 1
        
        PartyCandidate.objects.create(
            candidate_code=code,
            party=party,
            full_name=name,
            serial_number=serial,
            council_type='parliament',
            governorate='البصرة',
            status='active'
        )
        
    print("Restoration completed successfully!")

if __name__ == "__main__":
    update_sadiqoun()
