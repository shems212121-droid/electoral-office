import os
import django
import random

# إعداد بيئة جانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from elections.models import PoliticalParty, PartyCandidate

# قائمة الأحزاب والكيانات (بيانات حقيقية لانتخابات البصرة)
PARTIES_DATA = [
    {
        "name": "تحالف تصميم",
        "serial_number": 215,
        "color": "#1abc9c",
        "description": "تحالف بقيادة محافظ البصرة أسعد العيداني",
        "real_candidates": ["أسعد عبد الأمير عبد الغفار العيداني", "زينب خزعل مكي جري المصيلح", "عقيل إبراهيم عيسى علي الخالدي", "سوزان عكلاوي صالح حمود السعد", "ياسين حسن طاهر حسن", "عامر حسين جاسم علي الفائز"]
    },
    {
        "name": "حركة الصادقون",
        "serial_number": 190,
        "color": "#16a085",
        "description": "الجناح السياسي لعصائب أهل الحق",
        "real_candidates": ["عدي عواد كاظم محمود الحسين", "رفيق هاشم شناوة سالم الصالحي", "محمد حسين محمد بريج الموسوي", "قيصر صبحي عفات علي الجوراني", "رجاء فاضل عزيز حسوني الحمدي"]
    },
    {
        "name": "ائتلاف الإعمار والتنمية",
        "serial_number": 150,
        "color": "#3498db",
        "description": "تحالف سياسي في البصرة",
        "real_candidates": ["أحمد داغر جاسم كاظم الشبيبي", "عباس حيال لكن حسين المالكي", "عبد الأمير نجم عبد الله مدلول المياحي", "حوراء عزيز حميد حسن العلي"]
    },
    {
        "name": "ائتلاف دولة القانون",
        "serial_number": 120,
        "color": "#f1c40f",
        "description": "ائتلاف بقيادة نوري المالكي",
        "real_candidates": ["زياد علي فاضل هواش الرزيج", "فالح حسن جاسم مطلق الحريشاوي"]
    },
    {
        "name": "تحالف قوى الدولة الوطنية",
        "serial_number": 130,
        "color": "#8e44ad",
        "description": "تحالف الحكمة والنصر",
        "real_candidates": ["علي شداد فارس شهيل الجوراني", "سمية فيصل عودة ظاهر الحلفي"]
    },
    {
        "name": "حركة حقوق",
        "serial_number": 180,
        "color": "#e74c3c",
        "description": "حركة سياسية مقربة من الفصائل",
        "real_candidates": ["حسين علي جبار خلف العبد الله", "منى سوادي عبد الله مجيري الكرعاني"]
    },
    {
        "name": "تحالف الأساس العراقي",
        "serial_number": 160,
        "color": "#95a5a6",
        "description": "تحالف بقيادة محسن المندلاوي",
        "real_candidates": ["علاء الحيدري", "سعود الساعدي"]
    },
    {
        "name": "تجمع الفاو زاخو",
        "serial_number": 170,
        "color": "#d35400",
        "description": "تجمع بقيادة عامر عبد الجبار",
        "real_candidates": ["عامر عبد الجبار"]
    },
    {
        "name": "تحالف ابشر يا عراق",
        "serial_number": 140,
        "color": "#2c3e50",
        "description": "تحالف بقيادة المجلس الأعلى الإسلامي",
        "real_candidates": ["مصطفى جبار سند"]
    },
     {
        "name": "منظمة بدر",
        "serial_number": 110,
        "color": "#27ae60",
        "description": "الجناح السياسي لمنظمة بدر",
        "real_candidates": ["شاكر أبو تراب"]
    }
]

# بيانات لتوليد أسماء افتراضية واقعية
FIRST_NAMES = ["محمد", "أحمد", "علي", "حسين", "حسن", "عباس", "قاسم", "رضا", "حيدر", "كرار", "مهدي", "صادق", "باقر", "جعفر", "موسى", "علاء", "سعد", "جاسم", "عبد الله", "مصطفى", "عمار", "ياسر", "زياد", "فالح", "حميد", "عادل", "مازن", "سيف", "ضرغام", "وسام", "خالد", "عمر", "عثمان", "أيمن", "إبراهيم", "يوسف", "يعقوب", "نوح", "آدم", "عيسى"]
FEMALE_NAMES = ["فاطمة", "زينب", "زهراء", "مريم", "نور", "هدى", "سارة", "آلاء", "بنين", "رقية", "سمية", "حوراء", "ليلى", "أمل", "إيمان", "نجلاء", "سعاد", "رجاء", "بتول", "خديجة", "عائشة", "منال", "ابتسام", "وداد"]
FATHER_NAMES = ["جاسم", "كاظم", "محمود", "إبراهيم", "علي", "حسين", "محمد", "عبد الله", "هاشم", "سعد", "صالح", "خلف", "فارس", "فيصل", "سعيد", "جبار", "نجم", "داغر", "حيال", "فاضل", "عزيز", "حميد", "رزاق", "كريم", "رحيم", "جواد", "هادي", "ناصر", "منصور", "سامي", "رعد"]
GRAND_NAMES = ["موسى", "عيسى", "طه", "ياسين", "مهدي", "سليمان", "يونس", "داود", "هارون", "مكي", "شناوة", "بريج", "عفات", "مطلق", "شهيل", "ظاهر", "مجيري", "سلمان", "حمد", "عودة", "مطر", "سبتي", "جمعة", "خميس", "عيدان", "مهاوي"]
TRIBES = ["المالكي", "التميمي", "الخالدي", "الأسدي", "اللامي", "الكناني", "الزبيدي", "الخفاجي", "العبيدي", "الجبوري", "الدليمي", "السعدي", "المياحي", "البزوني", "الحلفي", "العيداني", "المطوري", "الغانمي", "المنصوري", "البصري", "القرني", "الفريجي", "الشمري", "الكعبي", "الساعدي", "الموسوي", "الحسيني", "العلوي", "الجوراني", "الصالحي", "الكرعاني", "الرزيج", "الحريشاوي", "الشبيبي", "الحمدي", "المصيلح"]

def generate_random_name(gender='male'):
    if gender == 'female':
        first = random.choice(FEMALE_NAMES)
    else:
        first = random.choice(FIRST_NAMES)
    
    father = random.choice(FATHER_NAMES)
    grand = random.choice(GRAND_NAMES)
    tribe = random.choice(TRIBES)
    
    # أحياناً يكون الاسم رباعي بدون لقب
    if random.random() > 0.7:
        great_grand = random.choice(GRAND_NAMES)
        return f"{first} {father} {grand} {great_grand}"
    return f"{first} {father} {grand} {tribe}"

def generate_phone_number():
    prefixes = ["077", "078", "075"]
    prefix = random.choice(prefixes)
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix

def run():
    print("Starting data import for Basra 2025 Elections...")
    
    # الحصول على جميع الأكواد وتحليلها للعثور على أقصى رقم مستخدم
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
            
    print(f"Starting with candidate code suffix: {current_code_num} (Max existing was {max_num})")

    for party_data in PARTIES_DATA:
        # إنشاء أو تحديث الحزب
        party, created = PoliticalParty.objects.get_or_create(
            name=party_data["name"],
            defaults={
                "serial_number": party_data["serial_number"],
                "color": party_data["color"],
                "description": party_data["description"]
            }
        )
        
        if not created:
            party.serial_number = party_data["serial_number"]
            party.color = party_data["color"]
            party.description = party_data["description"]
            party.save()
            # print(f"Updated party: {party.name}")
        else:
            print(f"Created party: {party.name}")
            
        # إضافة المرشحين
        current_candidates_count = party.candidates.count()
        if current_candidates_count >= 50:
             print(f"Party {party.name} already has {current_candidates_count} candidates. Skipping.")
             continue

        # 1. إضافة الأسماء الحقيقية أولاً
        real_names = party_data.get("real_candidates", [])
        
        # قائمة لتتبع الأرقام التسلسلية المستخدمة
        used_serials = set(party.candidates.values_list('serial_number', flat=True))
        
        for i, real_name in enumerate(real_names):
            # التسلسل يبدأ من 1
            serial = i + 1
            
            if serial in used_serials:
                continue
                
            # التحقق إذا كان الاسم موجوداً بالفعل لهذا الحزب
            if party.candidates.filter(full_name=real_name).exists():
                continue
            
            # توليد كود فريد
            code = f"03{current_code_num:02d}"
            current_code_num += 1
            
            PartyCandidate.objects.create(
                candidate_code=code,
                party=party,
                full_name=real_name,
                serial_number=serial,
                council_type='parliament',
                governorate='البصرة',
                status='active',
                phone=generate_phone_number()
            )
            # print(f"  - Added real candidate: {real_name} (#{serial})")
            used_serials.add(serial)
            
        # 2. إكمال القائمة حتى 50 مرشح بأسماء مولدة
        candidates_needed = 50 - len(used_serials)
        if candidates_needed > 0:
            print(f"  - Filling {party.name} with {candidates_needed} generated candidates...")
        
        for i in range(candidates_needed):
            # البحث عن رقم تسلسلي فارغ
            serial = 1
            while serial in used_serials:
                serial += 1
            
            # تحديد جنس عشوائي (كوتا النساء 25% تقريباً)
            gender = 'female' if random.random() < 0.25 else 'male'
            name = generate_random_name(gender)
            
            # توليد كود فريد
            code = f"03{current_code_num:02d}"
            current_code_num += 1
            
            try:
                PartyCandidate.objects.create(
                    candidate_code=code,
                    party=party,
                    full_name=name,
                    serial_number=serial,
                    council_type='parliament',
                    governorate='البصرة',
                    status='active',
                    phone=generate_phone_number()
                )
                used_serials.add(serial)
            except Exception as e:
                print(f"Error creating candidate {name}: {e}")
                # محاولة مرة أخرى بكود جديد في الدورة القادمة
                current_code_num += 1
                continue
        
    print("Import completed successfully!")

if __name__ == "__main__":
    run()
