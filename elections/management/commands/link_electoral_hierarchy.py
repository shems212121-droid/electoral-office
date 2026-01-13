from django.core.management.base import BaseCommand
from elections.models import Voter, PollingCenter, PollingStation, RegistrationCenter
from django.db import transaction
from django.db.models import Q

class Command(BaseCommand):
    help = 'Links voters, stations, and centers into a proper hierarchy'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='Limit number of voters to process (0 for all)')
        parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for updates')

    def handle(self, *args, **options):
        self.stdout.write("Starting electoral hierarchy linking...")

        # 1. Create RegistrationCenters from PollingCenters
        self.stdout.write("\n[1/3] Creating RegistrationCenters and linking PollingCenters...")
        centers = PollingCenter.objects.all()
        for pc in centers:
            if pc.registration_center_number:
                rc, created = RegistrationCenter.objects.get_or_create(
                    center_number=pc.registration_center_number,
                    defaults={'name': pc.registration_center_name or f"مركز تسجيل {pc.registration_center_number}"}
                )
                if pc.registration_center != rc:
                    pc.registration_center = rc
                    pc.save()
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created RegistrationCenter: {rc.name}"))
        
        # 2. Add missing RegistrationCenters from Voters (for centers that don't have a PollingCenter yet)
        self.stdout.write("\n[2/3] Checking for RegistrationCenters in Voter records...")
        voter_regs = Voter.objects.values('registration_center_number', 'registration_center_name').distinct()
        for vr in voter_regs:
            num = vr['registration_center_number']
            if num:
                rc, created = RegistrationCenter.objects.get_or_create(
                    center_number=num,
                    defaults={'name': vr['registration_center_name'] or f"مركز تسجيل {num}"}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created RegistrationCenter from Voter: {rc.name}"))

        # 3. Link Voters to Centers and Stations
        self.stdout.write("\n[3/3] Linking Voters to PollingCenters and PollingStations...")
        limit = options['limit']
        batch_size = options['batch_size']
        
        # We only process voters who haven't been linked yet
        voters_to_link = Voter.objects.filter(
            Q(polling_center__isnull=True) | Q(polling_station__isnull=True) | Q(registration_center_fk__isnull=True)
        )
        
        if limit > 0:
            voters_to_link = voters_to_link[:limit]
            
        total = voters_to_link.count()
        self.stdout.write(f"Voters needing linking: {total}")
        
        if total == 0:
            self.stdout.write("All voters are already linked.")
            return

        processed = 0
        
        # Pre-fetch centers and stations to avoid N+1
        all_centers = {c.center_number: c for c in PollingCenter.objects.all()}
        # For stations, we use a composite key: (center_number, station_number)
        all_stations = {}
        for s in PollingStation.objects.select_related('center').all():
            all_stations[(s.center.center_number, str(s.station_number))] = s
        
        all_regs = {r.center_number: r for r in RegistrationCenter.objects.all()}

        count = 0
        batch = []
        
        # Iterate in chunks manually for performance
        voter_iter = voters_to_link.iterator(chunk_size=batch_size)
        
        for voter in voter_iter:
            # Link Center
            if voter.voting_center_number in all_centers:
                voter.polling_center = all_centers[voter.voting_center_number]
            
            # Link Station
            station_key = (voter.voting_center_number, str(voter.station_number))
            if station_key in all_stations:
                voter.polling_station = all_stations[station_key]
            
            # Link Reg Center
            if voter.registration_center_number in all_regs:
                voter.registration_center_fk = all_regs[voter.registration_center_number]
                
            batch.append(voter)
            count += 1
            
            if len(batch) >= batch_size:
                Voter.objects.bulk_update(batch, ['polling_center', 'polling_station', 'registration_center_fk'])
                processed += len(batch)
                self.stdout.write(f"Processed {processed}/{total} voters...")
                batch = []
        
        if batch:
            Voter.objects.bulk_update(batch, ['polling_center', 'polling_station', 'registration_center_fk'])
            processed += len(batch)
            self.stdout.write(f"Processed {processed}/{total} voters...")

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully linked {processed} records."))
