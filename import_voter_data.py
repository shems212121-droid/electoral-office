"""
Import voter data from JSON chunks on Railway
Run this script after uploading the voter_data_export folder
"""

import os
import sys
import django
import json
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings_production')
django.setup()

from django.core import serializers
from elections.models import Voter

def main():
    print("=" * 60)
    print("📥 Importing Voter Data from JSON")
    print("=" * 60)
    
    base_dir = Path(__file__).resolve().parent
    export_dir = base_dir / 'voter_data_export'
    
    if not export_dir.exists():
        print(f"\n❌ Error: Directory '{export_dir}' not found!")
        print("\nPlease upload the voter_data_export folder first.")
        print("You can:") 
        print("1. Extract voter_data.zip")
        print("2. Place the voter_data_export folder in the project root")
        sys.exit(1)
    
    # Get all JSON chunk files
    json_files = sorted(export_dir.glob('voters_chunk_*.json'))
    
    if not json_files:
        print("\n❌ Error: No chunk files found in voter_data_export/")
        sys.exit(1)
    
    total_files = len(json_files)
    print(f"\n📦 Found {total_files} chunk files to import\n")
    
    total_imported = 0
    total_skipped = 0
    
    for file_num, json_file in enumerate(json_files, 1):
        print(f"Processing {json_file.name} ({file_num}/{total_files})...", end=' ', flush=True)
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = f.read()
            
            # Deserialize and save
            objects = serializers.deserialize('json', json_data)
            imported_count = 0
            skipped_count = 0
            
            for obj in objects:
                try:
                    # Check if voter already exists (by voter_number)
                    if not Voter.objects.filter(voter_number=obj.object.voter_number).exists():
                        obj.save()
                        imported_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    print(f"\n⚠️  Skipping voter {obj.object.voter_number}: {str(e)}")
                    skipped_count += 1
            
            total_imported += imported_count
            total_skipped += skipped_count
            
            print(f"✅ ({imported_count:,} imported, {skipped_count:,} skipped)")
            
        except Exception as e:
            print(f"\n❌ Error processing {json_file.name}: {str(e)}")
            continue
    
    print("\n" + "=" * 60)
    print("✅ Import Complete!")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   Total imported: {total_imported:,}")
    print(f"   Total skipped:  {total_skipped:,}")
    print(f"   Total in database: {Voter.objects.count():,}")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
