"""
One-time setup: create (or fix) the Supabase Storage bucket used by
SupabaseStorage, and make sure it's public -- a plain, directly-fetchable
URL is what every template in this project expects from
`{{ some_field.url }}` in an <img>/<a> tag, no signed URLs.

Safe to run more than once: does nothing if the bucket already exists
and is already public.
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the Supabase Storage bucket for file uploads (idempotent)"

    def handle(self, *args, **options):
        if not getattr(settings, 'USE_SUPABASE_STORAGE', False):
            raise CommandError(
                "USE_SUPABASE_STORAGE is not enabled -- set it (and SUPABASE_URL/"
                "SUPABASE_SERVICE_KEY) before running this command."
            )

        base_url = settings.SUPABASE_URL.rstrip('/')
        bucket = settings.SUPABASE_STORAGE_BUCKET
        headers = {
            'Authorization': f'Bearer {settings.SUPABASE_SERVICE_KEY}',
            'apikey': settings.SUPABASE_SERVICE_KEY,
        }

        # Does it already exist?
        response = requests.get(f'{base_url}/storage/v1/bucket/{bucket}', headers=headers, timeout=15)

        if response.status_code == 200:
            bucket_info = response.json()
            if bucket_info.get('public'):
                self.stdout.write(self.style.SUCCESS(f"Bucket '{bucket}' already exists and is public. Nothing to do."))
                return
            self.stdout.write(f"Bucket '{bucket}' exists but is not public -- making it public...")
            update_response = requests.put(
                f'{base_url}/storage/v1/bucket/{bucket}',
                headers={**headers, 'Content-Type': 'application/json'},
                json={'public': True},
                timeout=15,
            )
            if update_response.status_code not in (200, 204):
                raise CommandError(f"Failed to make bucket public ({update_response.status_code}): {update_response.text}")
            self.stdout.write(self.style.SUCCESS(f"Bucket '{bucket}' is now public."))
            return

        if response.status_code != 404:
            raise CommandError(f"Unexpected response checking bucket ({response.status_code}): {response.text}")

        # Doesn't exist -- create it, public, no file-size/type restrictions.
        self.stdout.write(f"Creating bucket '{bucket}'...")
        create_response = requests.post(
            f'{base_url}/storage/v1/bucket',
            headers={**headers, 'Content-Type': 'application/json'},
            json={'name': bucket, 'public': True},
            timeout=15,
        )
        if create_response.status_code not in (200, 201):
            raise CommandError(f"Failed to create bucket ({create_response.status_code}): {create_response.text}")

        self.stdout.write(self.style.SUCCESS(f"Bucket '{bucket}' created and set to public."))
