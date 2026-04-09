"""
Compatibility shim for legacy imports.

Some older code paths import User from dashboard.models_user.
Keep this module to avoid runtime ModuleNotFoundError on old deployments.
"""

from django.contrib.auth.models import User

__all__ = ["User"]
