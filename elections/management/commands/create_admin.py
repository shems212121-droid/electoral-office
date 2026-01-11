"""
Management command to create a default admin superuser
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Creates a default admin superuser if not exists'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            default='admin',
            help='Username for the superuser (default: admin)',
        )
        parser.add_argument(
            '--password',
            default='admin123',
            help='Password for the superuser (default: admin123)',
        )
        parser.add_argument(
            '--email',
            default='admin@example.com',
            help='Email for the superuser (default: admin@example.com)',
        )

    def handle(self, *args, **options):
        from elections.models import UserProfile, UserRole

        username = options['username']
        password = options['password']
        email = options['email']

        user = None
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists.')
            )
        else:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser "{username}"')
            )
        
        # Ensure profile exists
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(
                user=user,
                role=UserRole.ADMIN,
                full_name='مدير النظام'
            )
            self.stdout.write(self.style.SUCCESS(f'Created UserProfile for "{username}"'))
        else:
            self.stdout.write(self.style.WARNING(f'UserProfile for "{username}" already exists.'))
