from django.core.management.base import BaseCommand
import subprocess
import os
from django.conf import settings
import sys

class Command(BaseCommand):
    help = 'Imports voters from the batches zip file'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting voter import process...'))
        
        script_path = os.path.join(settings.BASE_DIR, 'import_voters_batches.py')
        
        try:
            # Execute the import script in the same python environment
            result = subprocess.run(
                [sys.executable, script_path], 
                check=True,
                capture_output=False  # Let the output stream to the console
            )
            self.stdout.write(self.style.SUCCESS('Successfully imported voters'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Error importing voters: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))
