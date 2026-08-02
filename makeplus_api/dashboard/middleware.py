"""
Dashboard-wide cache prevention.

settings.py runs UpdateCacheMiddleware/FetchFromCacheMiddleware as a
site-wide response cache (CACHE_MIDDLEWARE_SECONDS = 300) -- any view
that doesn't explicitly opt out with @never_cache can have its rendered
HTML cached for up to 5 minutes and served back to a *different* user
hitting the same URL, since that cache is not inherently keyed per
session. Only a handful of dashboard views (mostly the event-owner and
committee ones) were ever decorated with @never_cache; the rest of the
admin dashboard was not, which is what let a superuser's page get served
to a different account shortly after (reported as "pressed browser back
after logging in as someone else and landed on a superuser page").

Decorating every dashboard view individually is easy to forget on new
views, so this closes it at the middleware level instead: every
response under /dashboard/ is marked uncacheable, the same way
@never_cache would mark it.
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
