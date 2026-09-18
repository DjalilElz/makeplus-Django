"""
Optional one-time/manual check: create (or fix) the Supabase Storage
bucket used by SupabaseStorage, and make sure it's public.

Not required for normal operation any more -- SupabaseStorage._save()
now creates the bucket automatically the first time an upload hits a
"bucket not found" error, using the exact same ensure_bucket_exists()
logic this command calls. This command is still useful to run manually
to verify/fix the bucket ahead of time without waiting for an upload.

Safe to run more than once: does nothing if the bucket already exists
and is already public.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from makeplus_api.supabase_storage import ensure_bucket_exists


class Command(BaseCommand):
    help = "Create the Supabase Storage bucket for file uploads (idempotent)"

    def handle(self, *args, **options):
        if not getattr(settings, 'USE_SUPABASE_STORAGE', False):
            raise CommandError(
                "USE_SUPABASE_STORAGE is not enabled -- set it (and SUPABASE_URL/"
                "SUPABASE_SERVICE_KEY) before running this command."
            )

        try:
            ensure_bucket_exists(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY, settings.SUPABASE_STORAGE_BUCKET)
        except Exception as e:
            raise CommandError(str(e))

        self.stdout.write(self.style.SUCCESS(f"Bucket '{settings.SUPABASE_STORAGE_BUCKET}' exists and is public."))
