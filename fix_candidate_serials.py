import os
import django
from django.db.models import Count, Max

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from elections.models import PoliticalParty, PartyCandidate

def check_and_fix_serials():
    print("Checking candidate serial numbers...")
    
    parties = PoliticalParty.objects.all()
    
    for party in parties:
        candidates = party.candidates.all().order_by('serial_number', 'created_at', 'id')
        count = candidates.count()
        
        if count == 0:
            continue
            
        print(f"Party: {party.name} ({count} candidates)")
        
        # Check if re-sequencing is needed
        needs_fix = False
        seen_serials = set()
        
        for i, candidate in enumerate(candidates, 1):
            if candidate.serial_number != i:
                needs_fix = True
                break
            if candidate.serial_number in seen_serials:
                needs_fix = True
                break
            seen_serials.add(candidate.serial_number)
            
        if needs_fix:
            print(f"  -> Found inconsistencies. Re-sequencing 1 to {count}...")
            for i, candidate in enumerate(candidates, 1):
                if candidate.serial_number != i:
                   candidate.serial_number = i
                   candidate.save(update_fields=['serial_number'])
            print("  -> Done.")
        else:
            print("  -> Sequence OK.")

if __name__ == "__main__":
    check_and_fix_serials()
