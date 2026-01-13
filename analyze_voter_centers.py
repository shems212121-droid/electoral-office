import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings_production')
django.setup()

from elections.models import Voter, PollingCenter, PollingStation

def analyze_voter_centers():
    print("Analyzing Voter centers and stations...")
    
    # 1. Get unique center numbers from Voter
    voter_centers = Voter.objects.values('voting_center_number', 'voting_center_name').annotate(voter_count=Count('id')).order_by('-voter_count')
    print(f"Total unique voting centers in Voter model: {len(voter_centers)}")
    
    # 2. Get unique registration centers
    reg_centers = Voter.objects.values('registration_center_number', 'registration_center_name').annotate(voter_count=Count('id')).order_by('-voter_count')
    print(f"Total unique registration centers in Voter model: {len(reg_centers)}")
    
    # 3. Check PollingCenter model
    existing_centers = PollingCenter.objects.count()
    print(f"Total entries in PollingCenter model: {existing_centers}")
    
    # 4. Find missing centers
    voter_center_nums = set(v['voting_center_number'] for v in voter_centers if v['voting_center_number'])
    existing_center_nums = set(PollingCenter.objects.values_list('center_number', flat=True))
    
    missing_centers = voter_center_nums - existing_center_nums
    print(f"Centers found in Voter but MISSING in PollingCenter: {len(missing_centers)}")
    
    if missing_centers:
        print("\nSome missing centers:")
        for i, num in enumerate(list(missing_centers)[:10]):
            v = next(item for item in voter_centers if item['voting_center_number'] == num)
            print(f" - {num}: {v['voting_center_name']} ({v['voter_count']} voters)")

    # 5. Station analysis
    voter_stations = Voter.objects.values('voting_center_number', 'station_number').annotate(voter_count=Count('id')).order_by('voting_center_number', 'station_number')
    print(f"\nTotal unique station assignments in Voter model: {len(voter_stations)}")

if __name__ == '__main__':
    analyze_voter_centers()
