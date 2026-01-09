from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from elections.models import VoteCount


class Command(BaseCommand):
    help = 'Create 30 data entry users for vote counting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='Vote2024@',
            help='Default password for all users (default: Vote2024@)'
        )
        parser.add_argument(
            '--prefix',
            type=str,
            default='data_entry_',
            help='Username prefix (default: data_entry_)'
        )

    def handle(self, *args, **options):
        password = options['password']
        prefix = options['prefix']
        
        # Create or get Data Entry group
        data_entry_group, created = Group.objects.get_or_create(name='Data Entry')
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created "Data Entry" group'))
            
            # Set permissions for the group
            content_type = ContentType.objects.get_for_model(VoteCount)
            permissions = Permission.objects.filter(
                content_type=content_type,
                codename__in=['add_votecount', 'view_votecount']
            )
            data_entry_group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS('Set permissions for Data Entry group'))
        
        created_users = []
        existing_users = []
        
        # Create 30 users
        for i in range(1, 31):
            username = f'{prefix}{i:02d}'
            
            # Check if user exists
            if User.objects.filter(username=username).exists():
                existing_users.append(username)
                continue
            
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=f'مُدخِل بيانات {i:02d}',
                is_staff=True,  # Allow access to admin
                is_active=True
            )
            
            # Add to Data Entry group
            user.groups.add(data_entry_group)
            
            created_users.append(username)
            
        # Display results
        if created_users:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Successfully created {len(created_users)} users:'
                )
            )
            for username in created_users:
                self.stdout.write(f'   - {username}')
            
            self.stdout.write(
                self.style.WARNING(
                    f'\n🔑 Default password: {password}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Users can change their passwords after first login'
                )
            )
        
        if existing_users:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  {len(existing_users)} users already exist (skipped):'
                )
            )
            for username in existing_users:
                self.stdout.write(f'   - {username}')
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Summary:'
                f'\n   Created: {len(created_users)}'
                f'\n   Existing: {len(existing_users)}'
                f'\n   Total: 30'
            )
        )
        
        # Instructions
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📝 Next steps:'
                f'\n   1. Users can login at: http://127.0.0.1:8000/'
                f'\n   2. Navigate to vote counting pages'
                f'\n   3. Users can change passwords in admin panel'
            )
        )
