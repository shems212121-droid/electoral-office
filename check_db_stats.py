
import os
import django
import sys

# Setup Django
sys.path.append(r'c:\Users\2025\.gemini\antigravity\scratch\electoral_office')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "electoral_office.settings")
django.setup()

from elections.models import Voter, PollingCenter, RegistrationCenter, Candidate

print(f"Voters: {Voter.objects.count()}")
print(f"Polling Centers: {PollingCenter.objects.count()}")
print(f"Registration Centers: {RegistrationCenter.objects.count()}")
print(f"Candidates: {Candidate.objects.count()}")
