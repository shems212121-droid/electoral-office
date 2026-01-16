
import os
import django
import sys

# Add project root to path
sys.path.append(r'c:\Users\2025\.gemini\antigravity\scratch\electoral_office')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "electoral_office.settings")
django.setup()

from elections.models import Voter

voter = Voter.objects.first()
if voter:
    print(f"VOTER_FOUND: {voter.voter_number}")
else:
    print("NO_VOTERS_FOUND")
