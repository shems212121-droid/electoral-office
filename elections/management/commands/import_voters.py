import csv
import random
from django.core.management.base import BaseCommand
from elections.models import Voter
from django.db import transaction

class Command(BaseCommand):
    help = 'Import voters from CSV and enrich with complete data'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('--batch-size', type=int, default=5000, help='Batch size')
        parser.add_argument('--skip-header', action='store_true', help='Skip first row')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        batch_size = options['batch_size']
        skip_header = options['skip_header']

        self.stdout.write(self.style.SUCCESS(f'🚀 بدء استيراد الناخبين من: {csv_file}'))

        # Sample data for enrichment
        governorates = ['البصرة', 'بغداد', 'نين وى', 'الأنبار', 'النجف', 'كربلاء', 'ذي قار', 'ميسان', 'واسط', 'بابل', 'ديالى', 'صلاح الدين']
        mother_names_first = ['زهراء', 'فاطمة', 'مريم', 'نور', 'سارة', 'هدى', 'ليلى', 'آمنة', 'خديجة', 'عائشة']
        mother_names_last = ['حسن', 'علي', 'محمد', 'أحمد', 'كاظم', 'جاسم', 'حسين', 'عباس', 'صالح', 'كريم']
        statuses = ['نشط', 'غير نشط', 'منقول']
        
        registration_centers = [
            'مركز التسجيل المركزي',
            'مركز الزهور',
            'مركز الشهداء',
            'مركز العدل',
            'مركز السلام',
            'مركز النور'
        ]

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                if skip_header:
                    next(reader)

                voters_batch = []
                created_count = 0
                row_count = 0

                for row in reader:
                    row_count += 1
                    
                    if len(row) < 2:
                        continue

                    try:
                        # Basic data from CSV
                        voter_number = str(row[0]).strip()
                        full_name = str(row[1]).strip() if len(row) > 1 else ''
                        date_of_birth = row[2] if len(row) > 2 and row[2] else None
                        voting_center_number = str(row[3]).strip() if len(row) > 3 else ''
                        voting_center_name = str(row[4]).strip() if len(row) > 4 else ''

                        if not voter_number:
                            continue

                        # Generate enriched data
                        mother_name = f"{random.choice(mother_names_first)} {random.choice(mother_names_last)} {random.choice(mother_names_last)}"
                        family_number = str(random.randint(1000, 99999))
                        governorate = random.choice(governorates)
                        station_number = str(random.randint(1, 25))
                        registration_center = random.choice(registration_centers)
                        reg_center_num = str(random.randint(100000, 199999))
                        status = random.choice(statuses)
                        
                        # Generate realistic phone number
                        phone_prefix = random.choice(['0770', '0780', '0790', '0750'])
                        phone = f"{phone_prefix}{random.randint(1000000, 9999999)}"
                        
                        # Generate address based on voting center
                        address = f"{voting_center_name}, {governorate}" if voting_center_name else f"منطقة {random.randint(1, 100)}, {governorate}"

                        # Check if voter exists
                        existing_voter = Voter.objects.filter(voter_number=voter_number).first()
                        
                        if existing_voter:
                            # Update with enriched data
                            existing_voter.full_name = full_name or existing_voter.full_name
                            existing_voter.mother_name = mother_name
                            existing_voter.date_of_birth = date_of_birth or existing_voter.date_of_birth
                            existing_voter.phone = phone
                            existing_voter.voting_center_number = voting_center_number or existing_voter.voting_center_number
                            existing_voter.voting_center_name = voting_center_name or existing_voter.voting_center_name
                            existing_voter.voting_center_address = address
                            existing_voter.family_number = family_number
                            existing_voter.registration_center_name = registration_center
                            existing_voter.registration_center_number = reg_center_num
                            existing_voter.governorate = governorate
                            existing_voter.station_number = station_number
                            existing_voter.status = status
                            voters_batch.append(existing_voter)
                        else:
                            # Create new voter with all data
                            voter = Voter(
                                voter_number=voter_number,
                                full_name=full_name,
                                mother_name=mother_name,
                                date_of_birth=date_of_birth,
                                phone=phone,
                                voting_center_number=voting_center_number,
                                voting_center_name=voting_center_name,
                                voting_center_address=address,
                                family_number=family_number,
                                registration_center_name=registration_center,
                                registration_center_number=reg_center_num,
                                governorate=governorate,
                                station_number=station_number,
                                status=status
                            )
                            voters_batch.append(voter)
                            created_count += 1

                        # Bulk save when batch is full
                        if len(voters_batch) >= batch_size:
                            with transaction.atomic():
                                # Separate new vs existing
                                new_voters = [v for v in voters_batch if not v.pk]
                                existing_voters = [v for v in voters_batch if v.pk]
                                
                                if new_voters:
                                    Voter.objects.bulk_create(new_voters, ignore_conflicts=True)
                                
                                for v in existing_voters:
                                    v.save()
                            
                            self.stdout.write(f'✅ تم معالجة {row_count:,} سجل...')
                            voters_batch = []

                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠️  خطأ في السطر {row_count}: {str(e)}'))

                # Process remaining batch
                if voters_batch:
                    with transaction.atomic():
                        new_voters = [v for v in voters_batch if not v.pk]
                        existing_voters = [v for v in voters_batch if v.pk]
                        
                        if new_voters:
                            Voter.objects.bulk_create(new_voters, ignore_conflicts=True)
                        
                        for v in existing_voters:
                            v.save()

                total = Voter.objects.count()
                self.stdout.write(self.style.SUCCESS(f'\n✅ اكتمل الاستيراد!'))
                self.stdout.write(self.style.SUCCESS(f'📊 إجمالي السجلات: {row_count:,}'))
                self.stdout.write(self.style.SUCCESS(f'📈 إجمالي الناخبين في القاعدة: {total:,}'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ الملف غير موجود: {csv_file}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطأ: {str(e)}'))
