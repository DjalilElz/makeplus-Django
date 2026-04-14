"""
Django management command to create a test user
Usage: python manage.py create_test_user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a test user for mobile app testing'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='User email', default='controller1@wemakeplus.com')
        parser.add_argument('--password', type=str, help='User password', default='test123')
        parser.add_argument('--first-name', type=str, help='First name', default='Controller')
        parser.add_argument('--last-name', type=str, help='Last name', default='One')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Check if user exists
        try:
            user = User.objects.get(email=email)
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists'))
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Active: {user.is_active}')
            
            # Update password
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Password updated for {email}'))
            
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'✓ User created successfully!'))
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Active: {user.is_active}')

        self.stdout.write(self.style.SUCCESS(f'\n✓ You can now login with:'))
        self.stdout.write(f'  Email: {email}')
        self.stdout.write(f'  Password: {password}')
