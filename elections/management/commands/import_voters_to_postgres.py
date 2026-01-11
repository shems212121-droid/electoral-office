"""
Management command to import voters from legacy SQLite database to PostgreSQL
This command reads from the local legacy database and imports to the production database.

Usage:
    # First, set the DATABASE_URL environment variable to your Railway PostgreSQL URL
    # Then run:
    python manage.py import_voters_to_postgres --batch-size=5000 --limit=100000

    # To import all voters (may take hours):
    python manage.py import_voters_to_postgres --batch-size=5000
"""
import os
import time
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from elections.models import Voter
from elections.models_legacy import PersonHD, PCHd, VrcHD, GovernorateHD


class Command(BaseCommand):
    help = 'Import voters from legacy SQLite database to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5000,
            help='Number of records to process in each batch (default: 5000)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of records to import (default: all)',
        )
        parser.add_argument(
            '--offset',
            type=int,
            default=0,
            help='Start from this offset (default: 0)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing',
        )
        parser.add_argument(
            '--governorate',
            type=str,
            default=None,
            help='Filter by governorate ID (e.g., "8" for Basra)',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing voters instead of skipping them',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        limit = options['limit']
        offset = options['offset']
        dry_run = options['dry_run']
        governorate_filter = options['governorate']
        update_existing = options['update_existing']

        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.NOTICE('استيراد بيانات الناخبين إلى PostgreSQL'))
        self.stdout.write(self.style.NOTICE('=' * 60))

        # Check if legacy database is available
        from django.conf import settings
        if 'legacy_voters_db' not in settings.DATABASES:
            raise CommandError(
                'قاعدة بيانات legacy_voters_db غير معرفة في الإعدادات.\n'
                'تأكد من وجود تعريف قاعدة البيانات في settings.py'
            )

        # Build cache for centers, VRCs, and governorates
        self.stdout.write('جاري تحميل بيانات المراكز والمحافظات...')
        
        centers_cache = {}
        for center in PCHd.objects.using('legacy_voters_db').all():
            centers_cache[center.pcno] = center.pc_name

        vrc_cache = {}
        for vrc in VrcHD.objects.using('legacy_voters_db').all():
            vrc_cache[vrc.vrc_id] = vrc.vrc_name_ar

        gov_cache = {}
        for gov in GovernorateHD.objects.using('legacy_voters_db').all():
            gov_cache[str(gov.gov_no)] = gov.gov_name

        self.stdout.write(self.style.SUCCESS(
            f'تم تحميل: {len(centers_cache)} مركز, '
            f'{len(vrc_cache)} مركز تسجيل, '
            f'{len(gov_cache)} محافظة'
        ))

        # Count total records
        queryset = PersonHD.objects.using('legacy_voters_db')
        if governorate_filter:
            queryset = queryset.filter(per_gov_id=governorate_filter)
        
        total_count = queryset.count()
        self.stdout.write(f'إجمالي السجلات المتوفرة: {total_count:,}')

        if limit:
            records_to_process = min(limit, total_count - offset)
        else:
            records_to_process = total_count - offset

        self.stdout.write(f'السجلات المطلوب استيرادها: {records_to_process:,}')
        self.stdout.write(f'حجم الدفعة: {batch_size:,}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('وضع المعاينة - لن يتم حفظ أي بيانات'))

        # Process in batches
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        start_time = time.time()

        current_offset = offset
        batch_num = 0

        while imported_count + skipped_count + error_count < records_to_process:
            batch_num += 1
            batch_start = time.time()

            # Fetch batch
            persons = queryset.order_by('per_id')[current_offset:current_offset + batch_size]
            persons_list = list(persons)

            if not persons_list:
                break

            # Get existing voter numbers in this batch
            voter_numbers = [p.per_id for p in persons_list]
            existing_voters = set(
                Voter.objects.filter(voter_number__in=voter_numbers)
                .values_list('voter_number', flat=True)
            )

            voters_to_create = []
            voters_to_update = []

            for person in persons_list:
                voter_number = str(person.per_id)

                # Build full name
                name_parts = filter(None, [person.per_first, person.per_father, person.per_grand])
                full_name = ' '.join(name_parts)

                # Get related data from cache
                center_name = centers_cache.get(person.pcno, '')
                reg_center_name = vrc_cache.get(person.per_vrc_id, '')
                gov_name = gov_cache.get(str(person.per_gov_id), '')

                voter_data = {
                    'voter_number': voter_number,
                    'full_name': full_name,
                    'date_of_birth': self._parse_date(person.per_dob),
                    'voting_center_number': str(person.pcno) if person.pcno else '',
                    'voting_center_name': center_name,
                    'station_number': str(person.psno) if person.psno else '',
                    'family_number': str(person.per_famno) if person.per_famno else '',
                    'registration_center_number': str(person.per_vrc_id) if person.per_vrc_id else '',
                    'registration_center_name': reg_center_name,
                    'governorate': gov_name,
                    'status': 'active',
                }

                if voter_number in existing_voters:
                    if update_existing:
                        voters_to_update.append((voter_number, voter_data))
                    else:
                        skipped_count += 1
                else:
                    voters_to_create.append(Voter(**voter_data))

            # Bulk create new voters
            if voters_to_create and not dry_run:
                try:
                    with transaction.atomic():
                        Voter.objects.bulk_create(
                            voters_to_create,
                            batch_size=1000,
                            ignore_conflicts=True
                        )
                    imported_count += len(voters_to_create)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'خطأ في الدفعة {batch_num}: {e}')
                    )
                    error_count += len(voters_to_create)
            elif dry_run:
                imported_count += len(voters_to_create)

            # Update existing voters
            if voters_to_update and not dry_run:
                for voter_number, data in voters_to_update:
                    try:
                        Voter.objects.filter(voter_number=voter_number).update(**data)
                        updated_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'خطأ في تحديث {voter_number}: {e}')
                        )
                        error_count += 1
            elif dry_run:
                updated_count += len(voters_to_update)

            current_offset += batch_size
            batch_time = time.time() - batch_start
            
            # Progress report
            total_processed = imported_count + updated_count + skipped_count + error_count
            progress = (total_processed / records_to_process) * 100 if records_to_process > 0 else 0
            
            elapsed = time.time() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            remaining = (records_to_process - total_processed) / rate if rate > 0 else 0

            self.stdout.write(
                f'الدفعة {batch_num}: '
                f'{total_processed:,}/{records_to_process:,} ({progress:.1f}%) - '
                f'جديد: {imported_count:,}, تحديث: {updated_count:,}, '
                f'تخطي: {skipped_count:,}, أخطاء: {error_count} - '
                f'{batch_time:.1f}ث - المتبقي: {remaining/60:.0f} دقيقة'
            )

            # Check if we've reached the limit
            if limit and total_processed >= limit:
                break

        # Final report
        total_time = time.time() - start_time
        
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.SUCCESS('اكتمل الاستيراد!'))
        self.stdout.write(f'الوقت الإجمالي: {total_time/60:.1f} دقيقة')
        self.stdout.write(f'سجلات جديدة: {imported_count:,}')
        self.stdout.write(f'سجلات محدثة: {updated_count:,}')
        self.stdout.write(f'سجلات متخطاة: {skipped_count:,}')
        self.stdout.write(f'أخطاء: {error_count}')
        self.stdout.write(self.style.NOTICE('=' * 60))

    def _parse_date(self, date_str):
        """Parse date string from legacy database"""
        if not date_str:
            return None
        
        try:
            # Try common formats
            from datetime import datetime
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(str(date_str), fmt).date()
                except ValueError:
                    continue
        except:
            pass
        
        return None
