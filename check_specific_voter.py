
import os
import django
import sys

# Setup Django
sys.path.append(r'c:\Users\2025\.gemini\antigravity\scratch\electoral_office')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "electoral_office.settings")
django.setup()

from elections.models import Voter

voter_number = '33037821'
try:
    voter = Voter.objects.get(voter_number=voter_number)
    print(f"FOUND: {voter.full_name} - {voter.voter_number} - {voter.voting_center_name}")
except Voter.DoesNotExist:
    print(f"NOT_FOUND: Voter {voter_number} does not exist in local DB.")
except Exception as e:
    print(f"ERROR: {e}")
