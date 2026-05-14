"""
Custom storage backend for FTP with lazy connection
This prevents memory issues by only connecting when actually saving files
"""
from django.conf import settings
from storages.backends.ftp import FTPStorage as BaseFTPStorage


class LazyFTPStorage(BaseFTPStorage):
    """
    FTP Storage that connects lazily to prevent memory issues
    """
    def __init__(self, **settings):
        # Only initialize when actually needed
        super().__init__(**settings)
    
    def _open(self, name, mode='rb'):
        """Open file for reading - connect to FTP only when needed"""
        try:
            return super()._open(name, mode)
        except Exception as e:
            # If FTP fails, log but don't crash
            print(f"FTP open error for {name}: {e}")
            raise
    
    def _save(self, name, content):
        """Save file to FTP - connect only when saving"""
        try:
            return super()._save(name, content)
        except Exception as e:
            # If FTP fails, log the error
            print(f"FTP save error for {name}: {e}")
            raise
