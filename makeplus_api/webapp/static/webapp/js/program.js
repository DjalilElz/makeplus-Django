/* Shared between participant and controller program pages -- same
   GET /api/sessions/?event_id=<id> call, PDF fallback, day/type/room
   filters and clickable session cards (-> session detail page), just a
   different tab-bar shell around it. */
(function () {
    if (!requireAuth()) return;
    var event = Auth.getEvent() || {};
    var rolePrefix = Auth.getRole() === 'controlleur_des_badges' ? 'controller' : 'participant';

    var pdfBtn = document.getElementById('pdf-toggle');
    var pdfBtnIcon = document.getElementById('pdf-toggle-icon');
    var pdfFrame = document.getElementById('pdf-frame');
    var listEl = document.getElementById('session-list');
    var filterBar = document.getElementById('filter-bar');
    var dayTabsEl = document.getElementById('day-tabs');
    var typeFilterEl = document.getElementById('type-filter');
    var roomFilterEl = document.getElementById('room-filter');
    var showingPdf = false;

    var allSessions = [];
    var activeDay = '';
    var activeType = '';
    var activeRoom = '';

    if (event.programme_file) {
        pdfBtn.style.display = 'block';
        pdfBtn.addEventListener('click', function () {
            showingPdf = !showingPdf;
            pdfFrame.style.display = showingPdf ? 'block' : 'none';
            listEl.style.display = showingPdf ? 'none' : 'block';
            filterBar.style.display = showingPdf ? 'none' : (allSessions.length ? 'block' : 'none');
            pdfBtnIcon.className = showingPdf ? 'bi bi-grid' : 'bi bi-file-earmark-pdf';
            if (showingPdf && !pdfFrame.src) pdfFrame.src = event.programme_file;
        });
    }

    function dayKey(iso) { return iso ? iso.slice(0, 10) : ''; }
    function fmtTime(iso) {
        if (!iso) return '';
        return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    }
    function fmtDay(iso) {
        if (!iso) return '';
        return new Date(iso).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
    }
    function fmtDayShort(iso) {
        if (!iso) return '';
        return new Date(iso).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' });
    }

    function buildFilters() {
        var days = [], types = [], rooms = [];
        allSessions.forEach(function (s) {
            var d = dayKey(s.start_time);
            if (d && days.indexOf(d) === -1) days.push(d);
            if (s.session_type && types.indexOf(s.session_type) === -1) types.push(s.session_type);
            if (s.room_name && rooms.indexOf(s.room_name) === -1) rooms.push(s.room_name);
        });
        days.sort();
        types.sort();
        rooms.sort();

        dayTabsEl.innerHTML = '';
        var allChip = document.createElement('button');
        allChip.className = 'day-chip active';
        allChip.textContent = 'Tous';
        allChip.addEventListener('click', function () { setActiveDay(''); });
        dayTabsEl.appendChild(allChip);

        days.forEach(function (d) {
            var sample = allSessions.filter(function (s) { return dayKey(s.start_time) === d; })[0];
            var chip = document.createElement('button');
            chip.className = 'day-chip';
            chip.textContent = fmtDayShort(sample.start_time);
            chip.addEventListener('click', function () { setActiveDay(d); });
            chip.setAttribute('data-day', d);
            dayTabsEl.appendChild(chip);
        });

        types.forEach(function (t) {
            var opt = document.createElement('option');
            opt.value = t; opt.textContent = t;
            typeFilterEl.appendChild(opt);
        });
        rooms.forEach(function (r) {
            var opt = document.createElement('option');
            opt.value = r; opt.textContent = r;
            roomFilterEl.appendChild(opt);
        });

        filterBar.style.display = allSessions.length ? 'block' : 'none';
    }

    function setActiveDay(day) {
        activeDay = day;
        Array.prototype.forEach.call(dayTabsEl.children, function (chip) {
            chip.classList.toggle('active', (chip.getAttribute('data-day') || '') === day);
        });
        renderList();
    }

    typeFilterEl.addEventListener('change', function () { activeType = typeFilterEl.value; renderList(); });
    roomFilterEl.addEventListener('change', function () { activeRoom = roomFilterEl.value; renderList(); });

    function renderList() {
        var sessions = allSessions.filter(function (s) {
            if (activeDay && dayKey(s.start_time) !== activeDay) return false;
            if (activeType && s.session_type !== activeType) return false;
            if (activeRoom && s.room_name !== activeRoom) return false;
            return true;
        });

        listEl.innerHTML = '';
        document.getElementById('empty').style.display = sessions.length ? 'none' : 'block';
        if (!sessions.length) { listEl.style.display = 'none'; return; }

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
            card.className = 'card session-card';
            var liveBadge = s.is_live ? ' <span style="color:var(--error); font-weight:700;">● EN DIRECT</span>' : '';
            var paidBadge = s.is_paid ? ' <span style="color:var(--warning); font-weight:600;">· Payant</span>' : '';
            card.innerHTML =
                '<div style="font-size:0.8rem; color:var(--navy-light); font-weight:700;">' +
                    fmtTime(s.start_time) + ' – ' + fmtTime(s.end_time) + liveBadge + paidBadge +
                '</div>' +
                '<div style="font-weight:700; margin:4px 0 2px;">' + escapeHtml(s.title) + '</div>' +
                (s.speaker_name ? '<div style="font-size:0.85rem; color:var(--text-secondary);">' + escapeHtml(s.speaker_name) + '</div>' : '') +
                (s.room_name ? '<div style="font-size:0.8rem; color:var(--text-secondary); margin-top:4px;"><i class="bi bi-geo-alt"></i> ' + escapeHtml(s.room_name) + '</div>' : '');
            card.addEventListener('click', function () {
                window.location.href = '/app/' + rolePrefix + '/session/' + s.id + '/';
            });
            listEl.appendChild(card);
        });
        listEl.style.display = 'block';
    }

    Api.get('/sessions/?event_id=' + encodeURIComponent(event.id || '')).then(function (r) { return r.json(); })
        .then(function (data) {
            document.getElementById('loading').style.display = 'none';
            allSessions = Array.isArray(data) ? data : (data.results || []);
            allSessions.sort(function (a, b) { return new Date(a.start_time) - new Date(b.start_time); });
            buildFilters();
            renderList();
        }).catch(function () {
            document.getElementById('loading').innerHTML = '<div class="empty-state">Impossible de charger le programme.</div>';
        });
})();
