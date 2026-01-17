
import os
import zipfile
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.management import call_command
from elections.models import Voter

class Command(BaseCommand):
    help = 'Imports final voter data from split zip files'

    def handle(self, *args, **kwargs):
        # Import status tracker from views if it exists to allow real-time UI updates
        status = None
        try:
            from elections.views_import_tool import import_status
            status = import_status
        except ImportError:
            pass

        def log(msg):
            self.stdout.write(msg)
            if status:
                status['log'].append(msg)
                status['imported_count'] = Voter.objects.count()

        log('🚀 Starting Final Data Import...')
        
        # Check output directory
        data_dir = Path('voters_data_parts')
        if not data_dir.exists():
            log('❌ Data directory "voters_data_parts" not found!')
            return

        # Get all zip files
        zip_files = sorted(data_dir.glob('voters_part_*.zip'))
        
        if not zip_files:
            log('❌ No zip files found!')
            return
            
        # Mapping of last PKs to skip existing data
        batch_last_pks = {
            "voters_batch_001.json": 1599354, "voters_batch_002.json": 1695272,
            "voters_batch_003.json": 1633596, "voters_batch_004.json": 1391694,
            "voters_batch_005.json": 1284534, "voters_batch_006.json": 1362024,
            "voters_batch_007.json": 1318182, "voters_batch_008.json": 1494498,
            "voters_batch_009.json": 1544464, "voters_batch_010.json": 1162137,
            "voters_batch_011.json": 1198579, "voters_batch_012.json": 1102554,
            "voters_batch_013.json": 1012774, "voters_batch_014.json": 799410,
            "voters_batch_015.json": 892045, "voters_batch_016.json": 867375,
            "voters_batch_017.json": 802612, "voters_batch_018.json": 640225,
            "voters_batch_019.json": 690327, "voters_batch_020.json": 737947,
            "voters_batch_021.json": 545395, "voters_batch_022.json": 405097,
            "voters_batch_023.json": 637332, "voters_batch_024.json": 473003,
            "voters_batch_025.json": 557555, "voters_batch_026.json": 151599,
            "voters_batch_027.json": 325970, "voters_batch_028.json": 1736232,
            "voters_batch_029.json": 347296, "voters_batch_030.json": 367576,
            "voters_batch_031.json": 315777, "voters_batch_032.json": 1795986,
            "voters_batch_033.json": 200771, "voters_batch_034.json": 296133,
            "voters_batch_035.json": 1837535, "voters_batch_036.json": 176468,
            "voters_batch_037.json": 5208, "voters_batch_038.json": 1107
        }

        total_files = len(zip_files)
        log(f'📦 Found {total_files} parts to process.')
        
        # Create temp dir for extraction
        temp_dir = Path('temp_import_data')
        temp_dir.mkdir(exist_ok=True)
        
        for i, zip_file in enumerate(zip_files, 1):
            batch_num = zip_file.name.replace('voters_part_', '').replace('.zip', '')
            batch_json_name = f'voters_batch_{batch_num}.json'
            
            # Check if we can skip
            last_pk = batch_last_pks.get(batch_json_name)
            if last_pk and Voter.objects.filter(pk=last_pk).exists():
                log(f'⏭️  [{i}/{total_files}] Part {batch_num}: Skipped (Already in DB)')
                continue

            log(f'🔄 [{i}/{total_files}] Part {batch_num}: Importing...')
            
            try:
                # Extract
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    json_filename = zf.namelist()[0]
                    zf.extract(json_filename, temp_dir)
                    
                json_path = temp_dir / json_filename
                
                # Import
                call_command('loaddata', str(json_path), verbosity=0)
                
                # Cleanup
                json_path.unlink()
                
                current_count = Voter.objects.count()
                log(f'✅ [{i}/{total_files}] Part {batch_num}: Success (Total: {current_count:,})')
                
            except Exception as e:
                log(f'❌ [{i}/{total_files}] Part {batch_num}: Failed - {str(e)}')
        
        # Cleanup temp dir
        try:
            if temp_dir.exists():
                for f in temp_dir.iterdir(): f.unlink()
                temp_dir.rmdir()
        except:
            pass

        final_count = Voter.objects.count()
        log(f'🎉 Import Complete! Final Total: {final_count:,} voters.')
