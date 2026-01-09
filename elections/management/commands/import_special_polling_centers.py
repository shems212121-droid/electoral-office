"""
Django Management Command لاستيراد مراكز الاقتراع الخاص من ملف Excel
"""
import os
import openpyxl
from django.core.management.base import BaseCommand
from elections.models import PollingCenter, PollingStation, Area


class Command(BaseCommand):
    help = 'استيراد مراكز الاقتراع الخاص من ملف Excel'

    def handle(self, *args, **options):
        excel_file = 'مراكز الاقتراع الخاص.xlsx'
        
        if not os.path.exists(excel_file):
            self.stdout.write(self.style.ERROR(f'الملف {excel_file} غير موجود!'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'بدء استيراد مراكز الاقتراع الخاص من {excel_file}'))
        
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        ws = wb.active
        
        created_centers = 0
        updated_centers = 0
        created_stations = 0
        errors = []
        
        # تخطي الصف الأول (العناوين)
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            try:
                # استخراج البيانات من الصف
                # ت, رقم مركز التسجيل, اسم مركز التسجيل, رقم مركز الاقتراع الخاص, 
                # اسم مركز الاقتراع, عنوان مركز الاقتراع, الموقع, المحطات
                seq_num = row[0]
                registration_center_number = str(row[1]) if row[1] else ""
                registration_center_name = row[2] if row[2] else ""
                center_number = str(row[3]) if row[3] else ""
                center_name = row[4] if row[4] else ""
                address = row[5] if row[5] else ""
                location = row[6] if row[6] else ""
                station_count = row[7] if row[7] else 1
                
                # تخطي الصفوف الفارغة
                if not center_number:
                    continue
                
                # تنظيف البيانات
                try:
                    station_count = int(station_count)
                except (ValueError, TypeError):
                    station_count = 1
                
                # إنشاء أو تحديث مركز الاقتراع الخاص
                center, created = PollingCenter.objects.update_or_create(
                    center_number=center_number,
                    defaults={
                        'name': center_name.strip() if center_name else "غير محدد",
                        'voting_type': 'special',
                        'governorate': "البصرة",
                        'location': location.strip() if location else "",
                        'address': address.strip() if address else "",
                        'registration_center_number': registration_center_number.strip() if registration_center_number else "",
                        'registration_center_name': registration_center_name.strip() if registration_center_name else "",
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
                
                if row_num % 10 == 0:
                    self.stdout.write(f'تمت معالجة {row_num - 1} صف...')
                    
            except Exception as e:
                error_msg = f'خطأ في الصف {row_num}: {str(e)}'
                errors.append(error_msg)
                self.stdout.write(self.style.WARNING(error_msg))
                continue
        
        # عرض الإحصائيات النهائية
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('اكتمل الاستيراد!'))
        self.stdout.write(self.style.SUCCESS(f'مراكز اقتراع خاصة جديدة: {created_centers}'))
        self.stdout.write(self.style.SUCCESS(f'مراكز اقتراع خاصة محدثة: {updated_centers}'))
        self.stdout.write(self.style.SUCCESS(f'محطات اقتراع جديدة: {created_stations}'))
        
        if errors:
            self.stdout.write(self.style.WARNING(f'\nعدد الأخطاء: {len(errors)}'))
            self.stdout.write(self.style.WARNING('للاطلاع على تفاصيل الأخطاء راجع الرسائل أعلاه'))
        
        self.stdout.write(self.style.SUCCESS('='*60))
