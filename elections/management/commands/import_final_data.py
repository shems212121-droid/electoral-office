
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
        self.stdout.write(self.style.SUCCESS('🚀 Starting Final Data Import...'))
        
        # Check output directory
        data_dir = Path('voters_data_parts')
        if not data_dir.exists():
            self.stdout.write(self.style.ERROR('❌ Data directory "voters_data_parts" not found!'))
            return

        # Get all zip files
        zip_files = sorted(data_dir.glob('voters_part_*.zip'))
        
        if not zip_files:
            self.stdout.write(self.style.ERROR('❌ No zip files found!'))
            return
            
        total_files = len(zip_files)
        self.stdout.write(f'📦 Found {total_files} parts to import.')
        
        # Create temp dir for extraction
        temp_dir = Path('temp_import_data')
        temp_dir.mkdir(exist_ok=True)
        
        for i, zip_file in enumerate(zip_files, 1):
            self.stdout.write(f'🔄 Processing part {i}/{total_files}: {zip_file.name}...')
            
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
                self.stdout.write(self.style.SUCCESS(f'   ✅ Imported part {i}. Total voters: {current_count:,}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Failed to import part {i}: {str(e)}'))
        
        # Cleanup temp dir
        try:
            temp_dir.rmdir()
        except:
            pass

        final_count = Voter.objects.count()
        self.stdout.write(self.style.SUCCESS(f'🎉 Import Complete! Final Total: {final_count:,} voters.'))
