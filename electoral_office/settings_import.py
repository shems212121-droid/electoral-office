"""
Settings for importing data to Railway PostgreSQL from local machine.
This imports the local settings but overrides the default database 
to use the Railway PostgreSQL while keeping the legacy_voters_db.
"""
import os
import dj_database_url

# Import everything from the main settings
from electoral_office.settings import *

# Override the default database to use Railway PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
    print(f"Using Railway PostgreSQL database")
else:
    print("Warning: DATABASE_URL not set, using local SQLite")

# Keep the legacy database for reading voters
# This is already defined in the settings.py, but let's make sure
if 'legacy_voters_db' not in DATABASES:
    from pathlib import Path
    DATABASES['legacy_voters_db'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(r'C:\Users\2025\.gemini\antigravity\scratch\voters_decrypted_fast.sqlite'),
        'OPTIONS': {
            'timeout': 30,
        },
    }
    print(f"Legacy voters database configured")
