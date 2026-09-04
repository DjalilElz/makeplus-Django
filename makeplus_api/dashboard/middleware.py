"""
Dashboard-wide cache prevention.

This used to be needed to counter Django's own site-wide response
cache (UpdateCacheMiddleware/FetchFromCacheMiddleware), which cached a
GET response keyed by URL only and served it back to a *different*
user hitting the same URL -- that middleware has since been removed
from settings.py entirely (see the comment there) after it caused this
same class of bug a third time, in /api/.

Kept here anyway as defense-in-depth against browser/proxy caching of
personalized dashboard HTML (some of it renders per-account data like
a superuser's own admin tools), and against anyone reintroducing
per-view caching later: every response under /dashboard/ is marked
uncacheable, the same way @never_cache would mark it, without relying
on each view remembering to opt in individually.
"""
from django.utils.cache import add_never_cache_headers


class NoCacheDashboardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/dashboard/'):
            add_never_cache_headers(response)
        return response
