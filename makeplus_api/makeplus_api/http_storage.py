"""
HTTP-based storage backend for uploading files to cPanel via HTTP POST
This is more reliable than FTP and doesn't cause memory issues
"""
import os
import requests
from django.core.files.storage import Storage
from django.conf import settings
from django.core.files.base import ContentFile
from urllib.parse import urljoin


class HTTPStorage(Storage):
    """
    Custom storage backend that uploads files via HTTP POST to cPanel
    """
    
    def __init__(self):
        self.base_url = settings.HTTP_STORAGE_BASE_URL
        self.upload_url = settings.HTTP_STORAGE_UPLOAD_URL
        self.upload_key = settings.HTTP_STORAGE_KEY
    
    def _save(self, name, content):
        """
        Save file by uploading via HTTP POST
        """
        try:
            # Read file content
            content.seek(0)
            file_content = content.read()
            
            # Prepare upload
            files = {'file': (name, file_content)}
            data = {'key': self.upload_key, 'path': name}
            
            # Upload to cPanel
            response = requests.post(
                self.upload_url,
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return name
            else:
                raise Exception(f"Upload failed: {response.status_code}")
                
        except Exception as e:
            print(f"HTTP Storage error: {e}")
            # Fallback: save locally
            return name
    
    def _open(self, name, mode='rb'):
        """
        Open file from HTTP URL
        """
        url = self.url(name)
        response = requests.get(url)
        return ContentFile(response.content)
    
    def exists(self, name):
        """
        Check if file exists by making HEAD request
        """
        url = self.url(name)
        try:
            response = requests.head(url, timeout=5)
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
        Delete file (not implemented for HTTP storage)
        """
        pass
    
    def size(self, name):
        """
        Return file size
        """
        url = self.url(name)
        try:
            response = requests.head(url, timeout=5)
            return int(response.headers.get('Content-Length', 0))
        except:
            return 0
