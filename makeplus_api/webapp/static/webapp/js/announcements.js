/* Shared between participant and controller announcements pages -- same
   list, same GET /api/annonces/ call (server-filters by role/event from
   the JWT already), just a different tab-bar/top-bar shell around it. */
(function () {
    if (!requireAuth()) return;

    var TARGET_ICONS = {
        all: 'bi-megaphone', participants: 'bi-mortarboard', exposants: 'bi-building',
        controlleurs: 'bi-shield-check', gestionnaires: 'bi-tools',
    };

    function timeAgo(iso) {
        var diffMs = Date.now() - new Date(iso).getTime();
        var mins = Math.floor(diffMs / 60000);
        if (mins < 1) return "À l'instant";
        if (mins < 60) return 'Il y a ' + mins + ' min';
        var hours = Math.floor(mins / 60);
        if (hours < 24) return 'Il y a ' + hours + 'h';
        var days = Math.floor(hours / 24);
        return 'Il y a ' + days + 'j';
    }

    var event = Auth.getEvent() || {};

    loadWithCache('announcements_' + (event.id || ''), function () {
        return Api.get('/annonces/').then(function (r) { return r.json(); });
    }, function (data) {
        document.getElementById('loading').style.display = 'none';
        var items = Array.isArray(data) ? data : (data.results || []);
        var listEl = document.getElementById('announcement-list');
        listEl.innerHTML = '';

        if (!items.length) {
            document.getElementById('empty').style.display = 'block';
            listEl.style.display = 'none';
            return;
        }
        document.getElementById('empty').style.display = 'none';

        items.forEach(function (a) {
            var card = document.createElement('div');
            card.className = 'card';
            card.innerHTML =
                '<div style="display:flex; gap:10px; align-items:flex-start;">' +
                    '<span style="font-size:1.3rem;"><i class="bi ' + (TARGET_ICONS[a.target] || 'bi-megaphone') + '"></i></span>' +
                    '<div style="flex:1; min-width:0;">' +
                        '<div style="font-weight:700;">' + escapeHtml(a.title) + '</div>' +
                        '<div style="font-size:0.88rem; color:var(--text-secondary); margin:4px 0; white-space:pre-line;">' + escapeHtml(a.description) + '</div>' +
                        '<div style="font-size:0.75rem; color:var(--text-secondary);">' + timeAgo(a.created_at) + '</div>' +
                    '</div>' +
                '</div>';
            listEl.appendChild(card);
        });
        listEl.style.display = 'block';
    }, function () {
        document.getElementById('loading').innerHTML = '<div class="empty-state">Impossible de charger les annonces.</div>';
    });
})();
