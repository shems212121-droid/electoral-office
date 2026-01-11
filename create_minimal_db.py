"""
Script to create a minimal database for Railway deployment
This will create a small database with schema only, then we'll use data dumps
"""

import os
import sys
import django
import shutil
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from django.core.management import call_command
from elections.models import Voter

def main():
    print("=" * 60)
    print("🗄️  Creating Minimal Database for Railway")
    print("=" * 60)
    
    base_dir = Path(__file__).resolve().parent
    
    # Create a new minimal database
    minimal_db = base_dir / 'db_minimal.sqlite3'
    
    print("\n📦 Step 1: Creating minimal database with schema only...")
    
    # Remove if exists
    if minimal_db.exists():
        minimal_db.unlink()
        print(f"✅ Removed existing {minimal_db.name}")
    
    # Temporarily use minimal database
    from django.conf import settings
    original_db = settings.DATABASES['default']['NAME']
    settings.DATABASES['default']['NAME'] = str(minimal_db)
    
    # Create tables
    print("\n📋 Step 2: Creating database tables...")
    call_command('migrate', '--run-syncdb', verbosity=0)
    print("✅ Tables created")
    
    # Create admin user
    print("\n👤 Step 3: Creating admin user...")
    call_command('create_admin', verbosity=1)
    print("✅ Admin user created")
    
    # Restore original database setting
    settings.DATABASES['default']['NAME'] = original_db
    
    # Check size
    db_size = minimal_db.stat().st_size
    db_size_kb = db_size / 1024
    print(f"\n📊 Minimal database size: {db_size_kb:.2f} KB")
    
    # Rename to main database name for deployment
    deployment_db = base_dir / 'db_railway.sqlite3'
    if deployment_db.exists():
        deployment_db.unlink()
    shutil.copy(minimal_db, deployment_db)
    
    print(f"✅ Created deployment database: {deployment_db.name}")
    
    print("\n" + "=" * 60)
    print("✅ Minimal Database Created Successfully!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("\n1. The minimal database 'db_railway.sqlite3' can be committed to Git")
    print(f"   Size: {db_size_kb:.2f} KB (small enough for Git)")
    print("\n2. On Railway, you'll need to import the voter data separately")
    print("\n3. Options for data import:")
    print("   a) Use Railway console to run import script")
    print("   b) Create a data dump file and import via Django management command")
    print("   c) Use Railway's file upload feature (if available)")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
