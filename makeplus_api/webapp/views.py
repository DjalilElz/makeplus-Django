"""
DendrIQ web app -- a pinnable PWA for iOS participants/badge controllers,
replicating a subset of the Flutter app's functionality. Every page here
is a thin Django template shell; all real data comes from client-side JS
calling the SAME DRF API the mobile app uses (see webapp/static/webapp/js/api.js).
This app deliberately has no Django session/auth of its own -- it's a
pure API client, same trust model as the mobile app.
"""
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def index_view(request):
    """
    '/app/' itself -- a splash that just routes client-side to the right
    place (login state lives in localStorage, not a cookie, so this can't
    be decided server-side). Mirrors the app's own '/' splash screen.
    """
    return render(request, 'webapp/index.html', {'show_tab_bar': False})


@never_cache
def login_view(request):
    return render(request, 'webapp/login.html')


@never_cache
def signup_view(request):
    return render(request, 'webapp/signup.html')


@never_cache
def select_event_view(request):
    return render(request, 'webapp/select_event.html')


@never_cache
def install_view(request):
    return render(request, 'webapp/install.html', {'show_tab_bar': False})


@never_cache
def participant_home_view(request):
    return render(request, 'webapp/participant/home.html', {
        'show_tab_bar': True, 'active_tab': 'home', 'role': 'participant',
    })


@never_cache
def controller_home_view(request):
    return render(request, 'webapp/controller/home.html', {
        'show_tab_bar': True, 'active_tab': 'home', 'role': 'controlleur_des_badges',
    })


@never_cache
def participant_program_view(request):
    return render(request, 'webapp/participant/program.html', {
        'show_tab_bar': True, 'active_tab': 'program', 'role': 'participant',
    })


@never_cache
def participant_guide_view(request):
    return render(request, 'webapp/participant/guide.html', {
        'show_tab_bar': True, 'active_tab': 'guide', 'role': 'participant',
    })


@never_cache
def participant_announcements_view(request):
    return render(request, 'webapp/participant/announcements.html', {
        'show_tab_bar': True, 'active_tab': 'announcements', 'role': 'participant',
    })


@never_cache
def controller_program_view(request):
    return render(request, 'webapp/controller/program.html', {
        'show_tab_bar': True, 'active_tab': 'program', 'role': 'controlleur_des_badges',
    })


@never_cache
def controller_announcements_view(request):
    return render(request, 'webapp/controller/announcements.html', {
        'show_tab_bar': True, 'active_tab': 'announcements', 'role': 'controlleur_des_badges',
    })


@never_cache
def participant_profile_view(request):
    # Same template for both roles (the app itself has one shared
    # 'profile' route) -- but the tab-bar variant is picked server-side
    # from `role` in the template context, which can't be resolved from
    # a single shared URL (role lives in localStorage, not a cookie), so
    # each role gets its own thin route to the same template instead.
    return render(request, 'webapp/profile.html', {
        'show_tab_bar': True, 'active_tab': 'profile', 'role': 'participant',
    })


@never_cache
def controller_profile_view(request):
    return render(request, 'webapp/profile.html', {
        'show_tab_bar': True, 'active_tab': 'profile', 'role': 'controlleur_des_badges',
    })


@never_cache
def controller_statistics_view(request):
    return render(request, 'webapp/controller/statistics.html', {
        'show_tab_bar': True, 'active_tab': 'statistics', 'role': 'controlleur_des_badges',
    })


@never_cache
def controller_scanner_view(request):
    return render(request, 'webapp/controller/scanner.html', {
        'show_tab_bar': True, 'active_tab': 'scanner', 'role': 'controlleur_des_badges',
    })


@never_cache
def manifest_json(request):
    """
    Served at a fixed, unhashed /app/manifest.json -- deliberately NOT
    routed through the (Manifest/hashed) static files pipeline, since a
    PWA manifest needs a stable, predictable URL.
    """
    icon = lambda name: request.build_absolute_uri(staticfiles_storage.url(f'webapp/icons/{name}'))
    data = {
        'name': 'DendrIQ',
        'short_name': 'DendrIQ',
        'description': "Votre badge, programme et accès aux salles pour l'événement.",
        'start_url': '/app/',
        'scope': '/app/',
        'display': 'standalone',
        'background_color': '#F2F2F7',
        'theme_color': '#163751',
        'orientation': 'portrait',
        'icons': [
            {'src': icon('icon-192.png'), 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any maskable'},
            {'src': icon('icon-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'},
        ],
    }
    return JsonResponse(data, content_type='application/manifest+json')


@never_cache
def service_worker(request):
    """
    Served at /app/sw.js (not under /static/) so its registration scope
    defaults to /app/*. Minimal app-shell cache -- just enough that the
    shell repaints instantly on repeat opens; it does not attempt to make
    API data itself available offline.
    """
    shell_paths = [
        staticfiles_storage.url('webapp/css/app.css'),
        staticfiles_storage.url('webapp/js/api.js'),
    ]
    js = """
const CACHE = 'dendriq-shell-v1';
const SHELL = %s;

self.addEventListener('install', (event) => {
    event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)));
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    // Never cache API calls or non-GET requests -- only the static shell.
    if (event.request.method !== 'GET' || url.pathname.startsWith('/api/')) return;
    if (SHELL.indexOf(url.pathname) === -1) return;

    event.respondWith(
        caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
});
""" % (
        str(shell_paths).replace("'", '"'),
    )
    return HttpResponse(js, content_type='application/javascript')
