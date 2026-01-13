"""
Django Management Command لاستيراد مراكز الاقتراع العام من ملف Excel
"""
import os
import openpyxl
from django.core.management.base import BaseCommand
from elections.models import PollingCenter, PollingStation, Area, Neighborhood, RegistrationCenter


class Command(BaseCommand):
    help = 'استيراد مراكز الاقتراع العام من ملف Excel'

    def handle(self, *args, **options):
        excel_file = 'مراكز الاقتراع العام.xlsx'
        
        if not os.path.exists(excel_file):
            self.stdout.write(self.style.ERROR(f'الملف {excel_file} غير موجود!'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'بدء استيراد مراكز الاقتراع العام من {excel_file}'))
        
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        ws = wb.active
        
        created_centers = 0
        updated_centers = 0
        created_stations = 0
        errors = []
        
        # تخطي الصف الأول (العناوين) والصف الثاني (إجمالي)
        for row_num, row in enumerate(ws.iter_rows(min_row=3, values_only=True), start=3):
            try:
                # استخراج البيانات من الصف
                governorate = row[0] if row[0] else "البصرة"
                area_name = row[1] if row[1] else ""
                location = row[2] if row[2] else ""
                registration_center_number = str(row[3]) if row[3] else ""
                registration_center_name = row[4] if row[4] else ""
                center_number = str(row[5]) if row[5] else ""
                card_name = row[6] if row[6] else ""
                address = row[7] if row[7] else ""
                station_count = row[8] if row[8] else 1
                actual_name = row[9] if row[9] else ""
                
                # تخطي الصفوف الفارغة
                if not center_number:
                    continue
                
                # تنظيف البيانات
                try:
                    station_count = int(station_count)
                except (ValueError, TypeError):
                    station_count = 1
                
                # محاولة العثور على الناحية
                area = None
                if area_name:
                    area, _ = Area.objects.get_or_create(name=area_name.strip())
                
                # إنشاء أو تحديث مركز التسجيل
                registration_center = None
                if registration_center_number:
                    registration_center, _ = RegistrationCenter.objects.get_or_create(
                        center_number=registration_center_number.strip(),
                        defaults={
                            'name': registration_center_name.strip() if registration_center_name else f"مركز تسجيل {registration_center_number}",
                            'governorate': governorate.strip() if governorate else "البصرة"
                        }
                    )
                
                # إنشاء أو تحديث مركز الاقتراع
                center, created = PollingCenter.objects.update_or_create(
                    center_number=center_number,
                    defaults={
                        'name': actual_name or card_name or "غير محدد",
                        'voting_type': 'general',
                        'governorate': governorate.strip() if governorate else "البصرة",
                        'area': area,
                        'registration_center': registration_center,
                        'location': location.strip() if location else "",
                        'address': address.strip() if address else "",
                        'registration_center_number': registration_center_number.strip() if registration_center_number else "",
                        'registration_center_name': registration_center_name.strip() if registration_center_name else "",
                        'card_name': card_name.strip() if card_name else "",
                        'actual_name': actual_name.strip() if actual_name else "",
                        'station_count': station_count,
                    }
                )
                
                if created:
                    created_centers += 1
                else:
                    updated_centers += 1
                
                # إنشاء المحطات
                existing_stations = center.stations.count()
                if existing_stations < station_count:
                    for station_num in range(existing_stations + 1, station_count + 1):
                        PollingStation.objects.get_or_create(
                            center=center,
                            station_number=station_num,
                            defaults={
                                'counting_status': 'pending'
                            }
                        )
                        created_stations += 1
                
                if row_num % 50 == 0:
                    self.stdout.write(f'تمت معالجة {row_num - 2} صف...')
                    
            except Exception as e:
                error_msg = f'خطأ في الصف {row_num}: {str(e)}'
                errors.append(error_msg)
                self.stdout.write(self.style.WARNING(error_msg))
                continue
        
        # عرض الإحصائيات النهائية
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('اكتمل الاستيراد!'))
        self.stdout.write(self.style.SUCCESS(f'مراكز اقتراع جديدة: {created_centers}'))
        self.stdout.write(self.style.SUCCESS(f'مراكز اقتراع محدثة: {updated_centers}'))
        self.stdout.write(self.style.SUCCESS(f'محطات اقتراع جديدة: {created_stations}'))
        
        if errors:
            self.stdout.write(self.style.WARNING(f'\nعدد الأخطاء: {len(errors)}'))
            self.stdout.write(self.style.WARNING('للاطلاع على تفاصيل الأخطاء راجع الرسائل أعلاه'))
        
        self.stdout.write(self.style.SUCCESS('='*60))
