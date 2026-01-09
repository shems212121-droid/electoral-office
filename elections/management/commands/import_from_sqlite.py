import sqlite3
import sys
from django.core.management.base import BaseCommand
from elections.models import Voter
from django.db import transaction

class Command(BaseCommand):
    help = 'Import voters from external SQLite database (سجل الناخبين)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--db-path',
            type=str,
            default=r'C:\Users\2025\.gemini\antigravity\scratch\سجل الناخبين\prs21_decrypted.db',
            help='Path to SQLite database'
        )
        parser.add_argument('--batch-size', type=int, default=1000, help='Batch size')
        parser.add_argument('--limit', type=int, default=None, help='Limit number of records')

    def handle(self, *args, **options):
        db_path = options['db_path']
        batch_size = options['batch_size']
        limit = options['limit']

        self.stdout.write(self.style.SUCCESS(f'🔍 محاولة الاتصال بقاعدة البيانات: {db_path}'))

        try:
            # Try to connect to SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try different possible table names
            possible_tables = ['Voters', 'voters', 'VotersList', 'VOTERS', 'Voter', 'tblVoters']
            table_name = None
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            
            self.stdout.write(f'📋 الجداول الموجودة: {", ".join(tables)}')
            
            if not tables:
                self.stdout.write(self.style.ERROR('❌ لا توجد جداول في قاعدة البيانات'))
                return
            
            # Use first table or find voter table
            table_name = tables[0]
            for t in tables:
                if 'voter' in t.lower() or 'ناخب' in t.lower():
                    table_name = t
                    break
            
            self.stdout.write(self.style.SUCCESS(f'✅ سيتم استخدام الجدول: {table_name}'))
            
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            self.stdout.write(f'📊 الأعمدة الموجودة ({len(columns)}):')
            for col in columns[:10]:  # Show first 10
                self.stdout.write(f'  - {col}')
            if len(columns) > 10:
                self.stdout.write(f'  ... و {len(columns) - 10} عمود آخر')
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_count = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f'📈 إجمالي السجلات: {total_count:,}'))
            
            # Build column mapping - try to match columns
            column_mapping = self.build_column_mapping(columns)
            
            # Get data
            limit_clause = f"LIMIT {limit}" if limit else ""
            query = f"SELECT * FROM {table_name} {limit_clause}"
            cursor.execute(query)
            
            voters_batch = []
            created_count = 0
            updated_count = 0
            error_count = 0
            processed = 0
            
            self.stdout.write(self.style.SUCCESS('🚀 بدء الاستيراد...'))
            
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                for row in rows:
                    processed += 1
                    
                    try:
                        # Create dict from row
                        row_dict = dict(zip(columns, row))
                        
                        # Extract voter data using mapping
                        voter_data = self.extract_voter_data(row_dict, column_mapping)
                        
                        if not voter_data.get('voter_number'):
                            error_count += 1
                            continue
                        
                        # Check if exists
                        existing = Voter.objects.filter(
                            voter_number=voter_data['voter_number']
                        ).first()
                        
                        if existing:
                            # Update
                            for key, value in voter_data.items():
                                setattr(existing, key, value)
                            voters_batch.append(existing)
                            updated_count += 1
                        else:
                            # Create new
                            voter = Voter(**voter_data)
                            voters_batch.append(voter)
                            created_count += 1
                        
                        # Bulk save
                        if len(voters_batch) >= batch_size:
                            with transaction.atomic():
                                Voter.objects.bulk_create(
                                    [v for v in voters_batch if not v.pk],
                                    ignore_conflicts=True
                                )
                                for v in voters_batch:
                                    if v.pk:
                                        v.save()
                            
                            self.stdout.write(f'✅ {processed:,} / {total_count:,}')
                            voters_batch = []
                    
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠️  خطأ في السجل {processed}: {str(e)}'))
                        error_count += 1
            
            # Save remaining
            if voters_batch:
                with transaction.atomic():
                    Voter.objects.bulk_create(
                        [v for v in voters_batch if not v.pk],
                        ignore_conflicts=True
                    )
                    for v in voters_batch:
                        if v.pk:
                            v.save()
            
            conn.close()
            
            self.stdout.write(self.style.SUCCESS('\n' + '='*50))
            self.stdout.write(self.style.SUCCESS('✅ اكتمل الاستيراد!'))
            self.stdout.write(self.style.SUCCESS(f'📊 إجمالي: {processed:,}'))
            self.stdout.write(self.style.SUCCESS(f'➕ تم إنشاء: {created_count:,}'))
            self.stdout.write(self.style.SUCCESS(f'🔄 تم تحديث: {updated_count:,}'))
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f'⚠️  أخطاء: {error_count:,}'))
            
            total_db = Voter.objects.count()
            self.stdout.write(self.style.SUCCESS(f'📈 إجمالي الناخبين في القاعدة: {total_db:,}'))
        
        except sqlite3.DatabaseError as e:
            self.stdout.write(self.style.ERROR(f'❌ خطأ في قاعدة البيانات: {str(e)}'))
            self.stdout.write(self.style.WARNING('💡 تلميح: جرب الملف الآخر (prs21.db بدلاً من prs21_decrypted.db)'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطأ: {str(e)}'))
            import traceback
            traceback.print_exc()
    
    def build_column_mapping(self, columns):
        """Build mapping between SQLite columns and Django model fields"""
        mapping = {}
        
        # Common patterns
        patterns = {
            'voter_number': ['VoterNumber', 'voter_number', 'رقم_الناخب', 'ID', 'VoterID'],
            'full_name': ['Name', 'FullName', 'full_name', 'الاسم', 'الاسم_الكامل'],
            'mother_name': ['MotherName', 'mother_name', 'اسم_الأم', 'MotherFullName'],
            'date_of_birth': ['BirthDate', 'DateOfBirth', 'date_of_birth', 'تاريخ_الميلاد', 'DOB'],
            'phone': ['Phone', 'phone', 'Mobile', 'PhoneNumber', 'الهاتف'],
            'voting_center_number': ['PollingCenterNumber', 'VotingCenterNumber', 'رقم_المركز'],
            'voting_center_name': ['PollingCenterName', 'VotingCenterName', 'اسم_المركز'],
            'voting_center_address': ['PollingCenterAddress', 'VotingCenterAddress', 'عنوان_المركز', 'Address'],
            'family_number': ['FamilyNumber', 'family_number', 'رقم_العائلة', 'FamilyID'],
            'registration_center_name': ['RegistrationCenterName', 'RegCenterName', 'مركز_التسجيل'],
            'registration_center_number': ['RegistrationCenterNumber', 'RegCenterNumber', 'رقم_مركز_التسجيل'],
            'governorate': ['Governorate', 'governorate', 'المحافظة', 'Province'],
            'station_number': ['StationNumber', 'station_number', 'رقم_المحطة', 'StationNo'],
            'status': ['Status', 'status', 'الحالة', 'VoterStatus'],
        }
        
        for field, possible_names in patterns.items():
            for col in columns:
                if col in possible_names:
                    mapping[field] = col
                    break
        
        return mapping
    
    def extract_voter_data(self, row_dict, mapping):
        """Extract voter data from row using mapping"""
        data = {}
        
        for field, column in mapping.items():
            value = row_dict.get(column)
            if value is not None and value != '':
                data[field] = value
        
        return data
