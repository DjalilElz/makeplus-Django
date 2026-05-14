"""
cPanel HTTP Storage Backend
Uploads files to cPanel via HTTP POST (no FTP, no memory issues)
"""
import os
import requests
from io import BytesIO
from django.core.files.storage import Storage
from django.core.files.base import File, ContentFile
from django.conf import settings
from urllib.parse import urljoin


class CPanelHTTPStorage(Storage):
    """
    Custom storage backend that uploads files to cPanel via HTTP POST
    This avoids FTP memory issues and is more reliable
    """
    
    def __init__(self):
        self.upload_url = settings.CPANEL_UPLOAD_URL
        self.upload_key = settings.CPANEL_UPLOAD_KEY
        self.base_url = settings.CPANEL_BASE_URL
    
    def _save(self, name, content):
        """
        Save file by uploading via HTTP POST to cPanel
        """
        try:
            # Read file content
            content.seek(0)
            file_content = content.read()
            
            # Prepare upload
            files = {'file': (os.path.basename(name), file_content)}
            data = {
                'key': self.upload_key,
                'path': name
            }
            
            # Upload to cPanel
            response = requests.post(
                self.upload_url,
                files=files,
                data=data,
                timeout=60,
                headers={'X-Upload-Key': self.upload_key}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return name
                else:
                    raise Exception(f"Upload failed: {result.get('error')}")
            else:
                raise Exception(f"Upload failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            # Log error and re-raise
            print(f"cPanel Storage error: {e}")
            raise
    
    def _open(self, name, mode='rb'):
        """
        Open file from HTTP URL
        """
        url = self.url(name)
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return ContentFile(response.content)
        except Exception as e:
            raise FileNotFoundError(f"File not found: {name}")
    
    def exists(self, name):
        """
        Check if file exists by making HEAD request
        """
        url = self.url(name)
        try:
            response = requests.head(url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def url(self, name):
        """
        Return the URL where the file can be accessed
        """
        return urljoin(self.base_url, name)
    
    def delete(self, name):
        """
        Delete file (not implemented - files stay on cPanel)
        """
        pass
    
    def size(self, name):
        """
        Return file size
        """
        url = self.url(name)
        try:
            response = requests.head(url, timeout=10)
            return int(response.headers.get('Content-Length', 0))
        except:
            return 0
    
    def get_available_name(self, name, max_length=None):
        """
        Return a filename that's available in the storage
        """
        # If file exists, append a number
        if self.exists(name):
            dir_name, file_name = os.path.split(name)
            file_root, file_ext = os.path.splitext(file_name)
            count = 1
            while self.exists(name):
                name = os.path.join(dir_name, f"{file_root}_{count}{file_ext}")
                count += 1
        return name
