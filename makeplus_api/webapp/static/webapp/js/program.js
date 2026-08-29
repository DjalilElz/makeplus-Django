/* Shared between participant and controller program pages -- same
   GET /api/sessions/?event_id=<id> call and PDF fallback, just a
   different tab-bar shell around it. */
(function () {
    if (!requireAuth()) return;
    var event = Auth.getEvent() || {};

    var pdfBtn = document.getElementById('pdf-toggle');
    var pdfFrame = document.getElementById('pdf-frame');
    var listEl = document.getElementById('session-list');
    var showingPdf = false;

    if (event.programme_file) {
        pdfBtn.style.display = 'block';
        pdfBtn.addEventListener('click', function () {
            showingPdf = !showingPdf;
            pdfFrame.style.display = showingPdf ? 'block' : 'none';
            listEl.style.display = showingPdf ? 'none' : 'block';
            pdfBtn.textContent = showingPdf ? '▦ Sessions' : '📄 PDF';
            if (showingPdf && !pdfFrame.src) pdfFrame.src = event.programme_file;
        });
    }

    function fmtTime(iso) {
        if (!iso) return '';
        return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    }
    function fmtDay(iso) {
        if (!iso) return '';
        return new Date(iso).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
    }

    Api.get('/sessions/?event_id=' + encodeURIComponent(event.id || '')).then(function (r) { return r.json(); })
        .then(function (data) {
            document.getElementById('loading').style.display = 'none';
            var sessions = Array.isArray(data) ? data : (data.results || []);
            sessions.sort(function (a, b) { return new Date(a.start_time) - new Date(b.start_time); });

            if (!sessions.length) {
                document.getElementById('empty').style.display = 'block';
                return;
            }

            var lastDay = null;
            sessions.forEach(function (s) {
                var day = fmtDay(s.start_time);
                if (day !== lastDay) {
                    lastDay = day;
                    var dayHeader = document.createElement('div');
                    dayHeader.style.cssText = 'font-weight:700; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.04em; color:var(--text-secondary); margin:18px 0 8px;';
                    dayHeader.textContent = day;
                    listEl.appendChild(dayHeader);
                }

                var card = document.createElement('div');
                card.className = 'card';
                var liveBadge = s.is_live ? ' <span style="color:var(--error); font-weight:700;">● EN DIRECT</span>' : '';
                var paidBadge = s.is_paid ? ' <span style="color:var(--warning); font-weight:600;">· Payant</span>' : '';
                card.innerHTML =
                    '<div style="font-size:0.8rem; color:var(--navy-light); font-weight:700;">' +
                        fmtTime(s.start_time) + ' – ' + fmtTime(s.end_time) + liveBadge + paidBadge +
                    '</div>' +
                    '<div style="font-weight:700; margin:4px 0 2px;">' + escapeHtml(s.title) + '</div>' +
                    (s.speaker_name ? '<div style="font-size:0.85rem; color:var(--text-secondary);">' + escapeHtml(s.speaker_name) + '</div>' : '') +
                    (s.room_name ? '<div style="font-size:0.8rem; color:var(--text-secondary); margin-top:4px;">📍 ' + escapeHtml(s.room_name) + '</div>' : '');
                listEl.appendChild(card);
            });
            listEl.style.display = 'block';
        }).catch(function () {
            document.getElementById('loading').innerHTML = '<div class="empty-state">Impossible de charger le programme.</div>';
        });
})();
