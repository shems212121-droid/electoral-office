"""
Export voter data to JSON chunks for Railway import
This will split the data into manageable chunks that can be imported
"""

import os
import sys
import django
import json
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from elections.models import Voter
from django.core.serializers import serialize

def main():
    print("=" * 60)
    print("📤 Exporting Voter Data to JSON")
    print("=" * 60)
    
    base_dir = Path(__file__).resolve().parent
    export_dir = base_dir / 'voter_data_export'
    export_dir.mkdir(exist_ok=True)
    
    # Get total count
    total_voters = Voter.objects.count()
    print(f"\n📊 Total voters to export: {total_voters:,}")
    
    # Export in chunks of 50,000 to keep files manageable
    chunk_size = 50000
    total_chunks = (total_voters // chunk_size) + 1
    
    print(f"📦 Will create {total_chunks} chunk files")
    print(f"🔢 Chunk size: {chunk_size:,} records\n")
    
    for chunk_num in range(total_chunks):
        start_idx = chunk_num * chunk_size
        end_idx = min((chunk_num + 1) * chunk_size, total_voters)
        
        print(f"Processing chunk {chunk_num + 1}/{total_chunks} (records {start_idx:,} to {end_idx:,})...", end=' ')
        
        # Get chunk of voters
        voters_chunk = Voter.objects.all()[start_idx:end_idx]
        
        # Serialize to JSON
        json_data = serialize('json', voters_chunk, use_natural_foreign_keys=True)
        
        # Save to file
        chunk_file = export_dir / f'voters_chunk_{chunk_num + 1:03d}.json'
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        file_size_mb = chunk_file.stat().st_size / (1024 * 1024)
        print(f"✅ ({file_size_mb:.2f} MB)")
    
    print("\n" + "=" * 60)
    print("✅ Export Complete!")
    print("=" * 60)
    print(f"\n📁 Exported to: {export_dir}")
    print(f"📊 Total files: {total_chunks}")
    
    # Calculate total export size
    total_size = sum(f.stat().st_size for f in export_dir.glob('*.json'))
    total_size_mb = total_size / (1024 * 1024)
    print(f"💾 Total size: {total_size_mb:.2f} MB")
    
    print("\n📋 Next Steps:")
    print("1. Compress the export folder:")
    print(f"   Compress-Archive -Path '{export_dir}' -DestinationPath 'voter_data.zip'")
    print("\n2. Upload to a cloud storage (Google Drive, Dropbox, etc.)")
    print("\n3. On Railway, use the import script to load the data")
    print("   python import_voter_data.py")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Export interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
