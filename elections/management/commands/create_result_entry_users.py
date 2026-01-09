from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from elections.models import UserProfile, UserRole
import random
import string

class Command(BaseCommand):
    help = 'Creates 50 data entry users for election results'

    def handle(self, *args, **options):
        # Create or update "Data Entry Results" Group
        group, created = Group.objects.get_or_create(name='Data Entry Results')
        if created:
            self.stdout.write(self.style.SUCCESS('Created "Data Entry Results" group'))

        # Add permissions to group (if needed, though we restrict via view logic mostly)
        # We might want them to be able to "add vote count" but not "view vote count lists" outside their scope
        # For now, we rely on custom role checks, but basic model permissions are good practice
        content_type = ContentType.objects.get(app_label='elections', model='votecount')
        add_perm = Permission.objects.get(content_type=content_type, codename='add_votecount')
        group.permissions.add(add_perm)

        print("="*60)
        print("👤 بيانات المستخدمين (Data Entry Results Users)")
        print("="*60)
        print(f"{'Username':<25} | {'Password':<15}")
        print("-" * 43)

        for i in range(1, 51):
            username = f'admin{i:02d}'
            password = f'alaa{i:02d}'

            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                action = "Updated"
            else:
                user = User.objects.create_user(username=username, password=password)
                action = "Created"

            # Assign to Group
            user.groups.add(group)

            # Assign Role in UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = UserRole.DATA_ENTRY_RESULTS
            profile.save()

            print(f"{username:<25} | {password:<15}")

        print("="*60)
        self.stdout.write(self.style.SUCCESS('Successfully processed 50 result entry users'))
