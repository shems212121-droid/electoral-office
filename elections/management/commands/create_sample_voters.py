from django.core.management.base import BaseCommand
from elections.models import Voter
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker('ar_EG')  # Arabic Egypt locale

class Command(BaseCommand):
    help = 'Create sample voters with complete data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100, help='Number of voters to create')

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(self.style.SUCCESS(f'🚀 إنشاء {count} ناخب تجريبي...'))
        
        governorates = ['البصرة', 'بغداد', 'نينوى', 'الأنبار', 'النجف', 'كربلاء', 'ميسان']
        statuses = ['active', 'inactive', 'transferred']
        
        voters_batch = []
        
        for i in range(count):
            voter_number = f'{10000000 + random.randint(0, 9999999)}'
            
            # Generate random birth date
            start_date = datetime(1950, 1, 1)
            end_date = datetime(2003, 12, 31)
            birth_date = fake.date_between(start_date=start_date, end_date=end_date)
            
            # Random voting centers
            center_num = random.randint(230001, 239999)
            station_num = random.randint(1, 20)
            family_num = random.randint(1000, 9999)
            
            voter = Voter(
                voter_number=voter_number,
                full_name=fake.name(),
                mother_name=f"{fake.first_name_female()} {fake.last_name()} {fake.last_name()}",
                date_of_birth=birth_date,
                phone=fake.phone_number(),
                voting_center_number=str(center_num),
                voting_center_name=f"مدرسة {fake.last_name()} الابتدائية",
                voting_center_address=fake.address(),
                family_number=str(family_num),
                registration_center_name=f"مركز {fake.city()} للتسجيل",
                registration_center_number=str(random.randint(100000, 199999)),
                governorate=random.choice(governorates),
                station_number=str(station_num),
                status=random.choice(statuses)
            )
            
            voters_batch.append(voter)
            
            if len(voters_batch) >= 1000:
                Voter.objects.bulk_create(voters_batch, ignore_conflicts=True)
                self.stdout.write(f'✅ تم إنشاء {len(voters_batch)} ناخب...')
                voters_batch = []
        
        # Create remaining
        if voters_batch:
            Voter.objects.bulk_create(voters_batch, ignore_conflicts=True)
        
        total = Voter.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\n✅ تم الإنشاء بنجاح!'))
        self.stdout.write(self.style.SUCCESS(f'📊 إجمالي الناخبين في القاعدة: {total:,}'))
