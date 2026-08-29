/*
 * Thin client for the same DRF API the Flutter app talks to. Tokens live
 * in localStorage (this app has no Django session of its own -- it's a
 * pure API client, same trust model as the mobile app). Api.request()
 * auto-attaches the access token and retries once via the refresh token
 * on a 401, mirroring what a mobile HTTP interceptor would do.
 */
var Auth = {
    KEYS: {
        access: 'dq_access', refresh: 'dq_refresh', role: 'dq_role',
        event: 'dq_event', user: 'dq_user',
    },

    setSession: function (data) {
        localStorage.setItem(this.KEYS.access, data.access);
        localStorage.setItem(this.KEYS.refresh, data.refresh);
        localStorage.setItem(this.KEYS.role, data.role || '');
        localStorage.setItem(this.KEYS.event, JSON.stringify(data.event || null));
        localStorage.setItem(this.KEYS.user, JSON.stringify(data.user || null));
    },

    getAccess: function () { return localStorage.getItem(this.KEYS.access); },
    getRefresh: function () { return localStorage.getItem(this.KEYS.refresh); },
    getRole: function () { return localStorage.getItem(this.KEYS.role) || ''; },
    getEvent: function () {
        try { return JSON.parse(localStorage.getItem(this.KEYS.event)); } catch (e) { return null; }
    },
    getUser: function () {
        try { return JSON.parse(localStorage.getItem(this.KEYS.user)); } catch (e) { return null; }
    },
    setAccess: function (token) { localStorage.setItem(this.KEYS.access, token); },

    isLoggedIn: function () { return !!this.getAccess(); },

    clear: function () {
        Object.keys(this.KEYS).forEach(function (k) { localStorage.removeItem(Auth.KEYS[k]); });
    },

    // Where to land after login/select-event, based on role.
    homeUrl: function () {
        var role = this.getRole();
        return (role === 'controlleur_des_badges') ? '/app/controller/home/' : '/app/participant/home/';
    },

    logout: function () {
        this.clear();
        window.location.href = '/app/login/';
    },
};

var Api = {
    BASE: '/api',

    request: function (path, options) {
        options = options || {};
        var self = this;
        var url = this.BASE + path;

        function doFetch(token) {
            var headers = Object.assign({}, options.headers || {});
            if (token) headers['Authorization'] = 'Bearer ' + token;
            if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
                headers['Content-Type'] = 'application/json';
            }
            return fetch(url, {
                method: options.method || 'GET',
                headers: headers,
                body: options.body && !(options.body instanceof FormData)
                    ? JSON.stringify(options.body) : options.body,
            });
        }

        // Login/signup themselves can legitimately return 401 (SimpleJWT
        // returns 401, not 400, for bad credentials) -- the retry-via-
        // refresh logic below must never fire for those calls, or a wrong
        // password on the login page itself would force a redirect back
        // to /app/login/ that wipes the error message before it's shown.
        var isAuthEndpoint = path.indexOf('/auth/token/') === 0
            || path.indexOf('/auth/signup/') === 0
            || path.indexOf('/auth/select-event/') === 0;

        return doFetch(Auth.getAccess()).then(function (response) {
            if (response.status !== 401 || options._retried || isAuthEndpoint) return response;
            // Access token expired on an already-authenticated page --
            // refresh once and retry, same as the app's own interceptor.
            // If there's no refresh token to try, the session is simply
            // not logged in -- let the caller's own requireAuth() guard
            // handle that instead of forcing a redirect from in here.
            var refresh = Auth.getRefresh();
            if (!refresh) return response;

            return fetch(self.BASE + '/auth/token/refresh/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: refresh }),
            }).then(function (refreshResp) {
                if (!refreshResp.ok) { Auth.logout(); return response; }
                return refreshResp.json().then(function (data) {
                    Auth.setAccess(data.access);
                    var retryOptions = Object.assign({}, options, { _retried: true });
                    return self.request(path, retryOptions);
                });
            });
        });
    },

    get: function (path) { return this.request(path, { method: 'GET' }); },
    post: function (path, body) { return this.request(path, { method: 'POST', body: body }); },
    patch: function (path, body) { return this.request(path, { method: 'PATCH', body: body }); },
};

// Guard for pages that require an authenticated session -- call at the
// top of a page's script. Redirects to login if there's no session.
function requireAuth() {
    if (!Auth.isLoggedIn()) {
        window.location.href = '/app/login/';
        return false;
    }
    applyEventTheme();
    return true;
}

// Themes the app to the current event's own color, same as the mobile
// app does (AppTheme.light/dark(seedColor: event.primaryColor) in
// app_theme.dart) -- --navy/--navy-dark/--navy-light are the only brand
// variables that become event-specific; --sage stays fixed, matching
// the app's own AppColors.accent, which never changes per event.
function applyEventTheme() {
    var event = Auth.getEvent();
    if (!event || !event.primary_color || !/^#[0-9a-fA-F]{6}$/.test(event.primary_color)) return;

    function hexToHsl(hex) {
        var r = parseInt(hex.substr(1, 2), 16) / 255;
        var g = parseInt(hex.substr(3, 2), 16) / 255;
        var b = parseInt(hex.substr(5, 2), 16) / 255;
        var max = Math.max(r, g, b), min = Math.min(r, g, b);
        var h = 0, s = 0, l = (max + min) / 2;
        if (max !== min) {
            var d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            if (max === r) h = (g - b) / d + (g < b ? 6 : 0);
            else if (max === g) h = (b - r) / d + 2;
            else h = (r - g) / d + 4;
            h /= 6;
        }
        return [h, s, l];
    }

    function hslToHex(h, s, l) {
        function hue2rgb(p, q, t) {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1 / 6) return p + (q - p) * 6 * t;
            if (t < 1 / 2) return q;
            if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
            return p;
        }
        var r, g, b;
        if (s === 0) { r = g = b = l; }
        else {
            var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            var p = 2 * l - q;
            r = hue2rgb(p, q, h + 1 / 3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1 / 3);
        }
        function toHex(x) { var v = Math.round(x * 255).toString(16); return v.length === 1 ? '0' + v : v; }
        return '#' + toHex(r) + toHex(g) + toHex(b);
    }

    var hsl = hexToHsl(event.primary_color);
    var dark = hslToHex(hsl[0], hsl[1], Math.max(0, hsl[2] - 0.18));
    var light = hslToHex(hsl[0], hsl[1], Math.min(1, hsl[2] + 0.18));

    var root = document.documentElement.style;
    root.setProperty('--navy', event.primary_color);
    root.setProperty('--navy-dark', dark);
    root.setProperty('--navy-light', light);
}

// Every page builds its cards via innerHTML from API text fields (titles,
// names, descriptions) -- escape before interpolating so that content
// can never be parsed as markup.
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
