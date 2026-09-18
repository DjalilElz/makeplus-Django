"""
Supabase Storage Backend
Uploads files to a Supabase Storage bucket via its REST API (not the
S3-compatible layer -- this avoids adding boto3 as a dependency and
keeps the same shape as the existing CPanelHTTPStorage backend it
replaces).

The bucket is PUBLIC (auto-created on first upload if missing -- see
ensure_bucket_exists below), so .url() returns a plain,
directly-fetchable link -- no signed URLs, no auth needed for reads --
matching how every template in this project already uses
`{{ some_field.url }}` directly in <img>/<a> tags.
"""
import posixpath
import mimetypes
import requests
from urllib.parse import quote
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings


def ensure_bucket_exists(base_url, service_key, bucket):
    """
    Creates `bucket` (public) if it doesn't exist, or flips it to public
    if it exists but is private. Idempotent -- safe to call before every
    upload (SupabaseStorage._save does this automatically whenever a
    bucket-not-found is hit) and from the one-time setup_supabase_bucket
    management command, which shares this same logic.
    """
    headers = {'Authorization': f'Bearer {service_key}', 'apikey': service_key}
    base_url = base_url.rstrip('/')

    check = requests.get(f'{base_url}/storage/v1/bucket/{bucket}', headers=headers, timeout=15)

    if check.status_code == 200:
        if check.json().get('public'):
            return
        response = requests.put(
            f'{base_url}/storage/v1/bucket/{bucket}',
            headers={**headers, 'Content-Type': 'application/json'},
            json={'public': True},
            timeout=15,
        )
        if response.status_code not in (200, 204):
            raise Exception(f"Failed to make Supabase bucket public ({response.status_code}): {response.text}")
        return

    if check.status_code != 404:
        raise Exception(f"Unexpected response checking Supabase bucket ({check.status_code}): {check.text}")

    response = requests.post(
        f'{base_url}/storage/v1/bucket',
        headers={**headers, 'Content-Type': 'application/json'},
        json={'name': bucket, 'public': True},
        timeout=15,
    )
    if response.status_code not in (200, 201):
        raise Exception(f"Failed to create Supabase bucket ({response.status_code}): {response.text}")


class SupabaseStorage(Storage):
    def __init__(self):
        self.base_url = settings.SUPABASE_URL.rstrip('/')
        self.service_key = settings.SUPABASE_SERVICE_KEY
        self.bucket = settings.SUPABASE_STORAGE_BUCKET

    def _auth_headers(self, content_type=None):
        headers = {
            'Authorization': f'Bearer {self.service_key}',
            'apikey': self.service_key,
        }
        if content_type:
            headers['Content-Type'] = content_type
        return headers

    def _object_path(self, name):
        # Quote each path segment separately so real "/" separators
        # (directories) survive -- quoting the whole name would encode
        # them into %2F and break the bucket's folder structure.
        return '/'.join(quote(part) for part in name.split('/'))

    def _upload_url(self, name):
        return f"{self.base_url}/storage/v1/object/{self.bucket}/{self._object_path(name)}"

    def _public_url(self, name):
        return f"{self.base_url}/storage/v1/object/public/{self.bucket}/{self._object_path(name)}"

    def _do_upload(self, name, file_content, content_type):
        return requests.post(
            self._upload_url(name),
            data=file_content,
            headers={**self._auth_headers(content_type), 'x-upsert': 'true'},
            timeout=60,
        )

    def _save(self, name, content):
        content.seek(0)
        file_content = content.read()
        content_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'

        response = self._do_upload(name, file_content, content_type)

        if response.status_code == 404:
            # Bucket doesn't exist yet -- create it once, then retry this
            # same upload, so a first-time setup never needs a separate
            # manual step (a real production failure: NoSuchBucket).
            ensure_bucket_exists(self.base_url, self.service_key, self.bucket)
            response = self._do_upload(name, file_content, content_type)

        if response.status_code not in (200, 201):
            raise Exception(f"Supabase Storage upload failed ({response.status_code}): {response.text}")
        return name

    def _open(self, name, mode='rb'):
        response = requests.get(self._public_url(name), timeout=30)
        if response.status_code != 200:
            raise FileNotFoundError(f"File not found in Supabase Storage: {name}")
        return ContentFile(response.content)

    def exists(self, name):
        try:
            response = requests.head(self._public_url(name), timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def url(self, name):
        return self._public_url(name)

    def delete(self, name):
        try:
            requests.delete(self._upload_url(name), headers=self._auth_headers(), timeout=10)
        except requests.RequestException:
            pass

    def size(self, name):
        try:
            response = requests.head(self._public_url(name), timeout=10)
            return int(response.headers.get('Content-Length', 0))
        except (requests.RequestException, ValueError, TypeError):
            return 0

    def get_available_name(self, name, max_length=None):
        # posixpath, not os.path -- storage object keys are always
        # forward-slash paths regardless of the host OS. os.path.join
        # would silently produce backslashes on Windows (caught by an
        # actual test run locally), corrupting the stored path.
        if self.exists(name):
            dir_name, file_name = posixpath.split(name)
            file_root, file_ext = posixpath.splitext(file_name)
            count = 1
            while self.exists(name):
                name = posixpath.join(dir_name, f"{file_root}_{count}{file_ext}")
                count += 1
        return name
