"""
Supabase Storage Backend
Uploads files to a Supabase Storage bucket via its REST API (not the
S3-compatible layer -- this avoids adding boto3 as a dependency and
keeps the same shape as the existing CPanelHTTPStorage backend it
replaces).

The bucket is expected to be PUBLIC (created once via
`manage.py setup_supabase_bucket`), so .url() returns a plain,
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

    def _save(self, name, content):
        content.seek(0)
        file_content = content.read()
        content_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'

        response = requests.post(
            self._upload_url(name),
            data=file_content,
            headers={**self._auth_headers(content_type), 'x-upsert': 'true'},
            timeout=60,
        )
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
