/* Practice board for the instructor: who is practising now, per-scenario numbers, students' XP and corrections, the
   room's settings and the bonus. Every route checks the admin role on the server. */
(function () {
    'use strict';
    var API = ((typeof CONFIG !== 'undefined' && CONFIG.server && CONFIG.server.url) || '').replace(/\/+$/, '');
    var q = new URLSearchParams(location.search);
    if (q.get('api')) API = q.get('api').replace(/\/+$/, '');
    var PAGE = 'practice-board.html';
    var token = sessionStorage.getItem('authToken') || '';
    var ov = null, tab = 'live', timer = null, editing = false;
    var TABS = ['live', 'scen', 'road', 'stud', 'set', 'bonus'];
    var LEVEL = { easy: 'Easy', medium: 'Medium', hard: 'Hard', 'super': 'Super' };

    function $(id) { return document.getElementById(id); }
    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function mmss(sec) { sec = Math.max(0, Math.round(sec || 0)); return Math.floor(sec / 60) + ':' + ('0' + sec % 60).slice(-2); }
    function when(ts) { return ts ? new Date(ts * 1000).toLocaleString('en-GB', { timeZone: 'Asia/Phnom_Penh', hour12: false }).slice(0, 17) : '—'; }
    function qs() { return q.get('api') ? '?api=' + encodeURIComponent(API) : ''; }

    function api(path, opts) {
        opts = opts || {};
        var h = { 'Content-Type': 'application/json' };
        if (token) h.Authorization = 'Bearer ' + token;
        return fetch(API + path, { method: opts.method || 'GET', headers: h, mode: 'cors', body: opts.body ? JSON.stringify(opts.body) : undefined })
            .then(function (r) {
                if (opts.raw) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); }
                return r.json().catch(function () { return {}; }).then(function (d) {
                    if (!r.ok) { var e = new Error(d.error || ('HTTP ' + r.status)); e.status = r.status; throw e; }
                    return d;
                });
            });
    }

    // One login for the whole site: the portal's. Without a valid one, go to the portal's login page, which comes
    // back here afterwards (index.html?next=...).
    function toPortal() {
        sessionStorage.removeItem('examToken');
        location.replace('index.html?next=' + encodeURIComponent(PAGE + location.search));
    }

    // No login, or an expired one: the portal's login page. Logged in, but not as the instructor: say so here.
    function showLogin(msg) {
        if (!token || !msg || !/instructor/.test(msg)) { toPortal(); return; }
        $('app').classList.add('hidden');
        $('screen').classList.remove('hidden');
        $('screen-body').innerHTML = '<p class="prompt">instructor board</p><p class="err">' + esc(msg) + '</p>' +
            '<p>Log in on the portal with the instructor account, then open this page again.</p>' +
            '<p><a class="btn btn-tool" href="index.html?next=practice-board.html' + encodeURIComponent(location.search) + '">← menu</a></p>';
    }

    function start() {
        $('screen').classList.add('hidden');
        $('app').classList.remove('hidden');
        $('to-exam').href = 'exam-board.html' + qs();
        $('as-go').addEventListener('click', function () {   // the practice page as that student sees it, read-only
            if (!$('as-user').value) return;
            var p = new URLSearchParams(location.search); p.set('as', $('as-user').value);
            location.href = 'practice.html?' + p.toString();
        });
        load();
        clearInterval(timer);
        timer = setInterval(function () { if (!editing) load(); }, 5000);
    }

    function job(kind, text) {
        $('job').className = 'job ' + kind;
        $('job').textContent = text;
        if (kind !== 'busy') setTimeout(function () { if ($('job').textContent === text) $('job').className = 'job hidden'; }, 6000);
    }

    function load() {
        return api('/api/admin/practice/overview').then(function (o) {
            ov = o;
            draw();
        }).catch(function (err) {
            if (err.status === 401) toPortal();
            else if (err.status === 403) showLogin('Log in with the instructor account.');
            else job('error', 'error: ' + err.message);
        });
    }

    function draw() {
        var o = ov;
        var open = o.installed && !o.exam_running;
        $('c-open').textContent = !o.installed ? 'not set up' : o.exam_running ? 'closed' : 'open';
        $('c-open').className = 'num ' + (open ? 'st-ok' : 'st-bad');
        $('c-why').textContent = !o.installed ? 'examctl install adds practice' : o.exam_running ? 'an exam is running' : 'always, except during an exam';
        var live = o.live.filter(function (x) { return x.connected; }).length;
        $('c-live').textContent = live;
        $('c-cap').textContent = o.settings ? 'at most ' + o.settings.max_sessions + ' at once' : '';
        var xp = o.students.filter(function (s) { return s.xp > 0; });
        $('c-xp').innerHTML = esc(xp.length) + '<small class="muted"> / ' + esc(o.students.length) + '</small>';
        $('c-clears').textContent = o.students.reduce(function (a, s) { return a + s.clears; }, 0) + ' clears in total';
        $('c-runner').textContent = o.runner_ok ? 'running' : 'not reachable';
        $('c-runner').className = 'num ' + (o.runner_ok ? 'st-ok' : 'st-bad');
        $('c-scen').textContent = o.scenarios.length + ' scenarios (' + o.scenarios.filter(function (s) { return s.private; }).length + ' private)';
        $('errors').classList.toggle('hidden', !o.errors.length);
        $('errors').textContent = o.errors.length ? 'Scenario files that did not load: ' + o.errors.join('; ') : '';
        drawLive(); drawScen(); drawRoad(); drawStud();
        if (!editing) { drawSettings(); drawBonus(); }
    }

    function drawLive() {
        var rows = ov.live.slice().sort(function (a, b) { return (b.locked - a.locked) || (b.connected - a.connected) || (a.id < b.id ? -1 : 1); });
        $('live-rows').innerHTML = rows.map(function (r) {
            var conn = r.connected ? '<span class="st-ok">connected</span>' : '<span class="muted">left ' + esc(when(r.last_seen).slice(12)) + '</span>';
            var wait = r.locked ? (r.lock_left > 0 ? '<span class="st-partial">waiting ' + esc(mmss(r.lock_left)) + '</span>' : '<span class="st-partial">can continue</span>') +
                ' <span class="muted">(' + esc(r.lock_n_today) + ' today)</span>' : (r.lock_n_today ? '<span class="muted">' + esc(r.lock_n_today) + ' wait(s) today</span>' : '');
            return '<tr><td><span class="id">' + esc(r.id) + '</span> ' + esc(r.name) + '</td><td>' + esc(r.scenario) + (r.attempt > 1 ? ' <span class="muted">remix ' + esc(r.attempt - 1) + '</span>' : '') +
                '</td><td>' + conn + '</td><td>' + wait + '</td><td><code>' + esc(r.last_cmd) + '</code></td><td>' +
                (r.locked ? '<button class="btn btn-tool" type="button" data-unlock="' + esc(r.user) + '">end the wait</button> ' : '') +
                '<button class="btn-link" type="button" data-preview="' + esc(r.user) + '|' + esc(r.scenario) + '">their task</button></td></tr>';
        }).join('') || '<tr><td colspan="6" class="muted"># nobody has practised in the last hour.</td></tr>';
    }

    function drawScen() {
        $('scen-rows').innerHTML = ov.scenarios.map(function (s) {
            var hard = s.cleared && s.hint3 / s.cleared > 0.5;
            return '<tr><td><span class="id">' + esc(s.title) + '</span> <span class="muted">' + esc(s.id) + (s.private ? ', private' : '') + '</span></td>' +
                '<td><span class="lvl ' + esc(s.level) + '">' + esc(LEVEL[s.level]) + '</span></td><td class="num">' + esc(s.xp) + '</td><td class="num">' + esc(s.minutes) +
                '</td><td class="num">' + esc(s.started) + '</td><td class="num">' + esc(s.cleared) + '</td><td class="num">' + (s.median_min == null ? '—' : esc(s.median_min) + ' min') +
                '</td><td class="num">' + (s.hints_avg == null ? '—' : esc(s.hints_avg)) + '</td><td class="num' + (hard ? ' st-partial' : '') + '">' + esc(s.hint3) +
                '</td><td class="num">' + (s.checks_avg == null ? '—' : esc(s.checks_avg)) + '</td><td>' + (Object.keys(s.stuck || {}).map(function (k) { return 'step ' + esc(k) + ': ' + esc(s.stuck[k]); }).join(', ') || '<span class="muted">' + (s.guided ? '—' : 'not guided') + '</span>') +
                '</td><td><button class="btn-link" type="button" data-preview="|' + esc(s.id) + '">read it</button></td></tr>';
        }).join('');
    }

    function drawRoad() {
        var stages = (ov.stages || []), rows = ov.roadmap || [];
        $('road-rows').innerHTML = stages.map(function (s) {
            var mine = rows.filter(function (x) { return x.stage === s.id; });
            return '<tr class="stage-row"><td colspan="10"><b>' + esc(s.title) + '</b> <span class="muted">· ' + esc(s.badge) + ' · ' + mine.length + ' exercises</span></td></tr>' + mine.map(function (x) {
                var stuck = Object.keys(x.stuck || {}).map(function (k) { return 'step ' + esc(k) + ': ' + esc(x.stuck[k]); }).join(', ');
                var many = x.cleared && x.hints_avg != null && x.hints_avg >= 1.5;
                return '<tr><td><span class="id">' + esc(x.title) + '</span> <span class="muted">' + esc(x.id) + '</span></td><td>' + esc(x.kind) + '</td><td class="num">' + esc(x.xp) + '</td><td class="num">' + esc(x.started) +
                    '</td><td class="num">' + esc(x.cleared) + '</td><td class="num">' + (x.median_min == null ? '—' : esc(x.median_min) + ' min') + '</td><td class="num' + (many ? ' st-partial' : '') + '">' + (x.hints_avg == null ? '—' : esc(x.hints_avg)) +
                    '</td><td class="num">' + (x.checks_avg == null ? '—' : esc(x.checks_avg)) + '</td><td>' + (stuck || '<span class="muted">—</span>') + '</td><td>' +
                    (x.kind === 'quiz' ? '' : '<button class="btn-link" type="button" data-preview="|' + esc(x.id) + '">read it</button>') + '</td></tr>';
            }).join('');
        }).join('') || '<tr><td colspan="10" class="muted"># the roadmap is not on this server yet.</td></tr>';
    }

    function drawStud() {
        var f = ($('st-filter').value || '').toLowerCase();
        var rows = ov.students.filter(function (s) { return !f || (s.id + ' ' + s.name + ' ' + s.nick).toLowerCase().indexOf(f) >= 0; })
            .sort(function (a, b) { return b.xp - a.xp || (a.id < b.id ? -1 : 1); });
        $('stud-rows').innerHTML = rows.map(function (s) {
            return '<tr><td><span class="id">' + esc(s.id) + '</span> ' + esc(s.name) + '</td><td>' + (s.nick ? esc(s.nick) + ' <button class="btn-link" type="button" data-clearnick="' + esc(s.user) + '">clear</button>'
                : (s.nick_cleared ? '<span class="muted">cleared</span>' : '')) + '</td><td class="num">' + esc(s.xp) + '</td><td class="num">' + esc(s.week) + '</td><td>' + esc(s.rank) +
                '</td><td class="num">' + esc(s.clears) + '</td><td class="num">' + esc(s.supers) + '</td><td class="num">' + esc(s.skills) + ' / ' + esc(ov.skills_total || 57) + '</td><td>' + esc(when(s.last)) + '</td><td class="num">' + esc(s.bonus) +
                '</td><td><label class="muted"><input type="checkbox" data-author="' + esc(s.user) + '"' + (s.author ? ' checked' : '') + '> author</label></td></tr>';
        }).join('') || '<tr><td colspan="11" class="muted"># no student matches.</td></tr>';
        var opts = ov.students.map(function (s) { return '<option value="' + esc(s.user) + '">' + esc(s.id + ' ' + s.name) + '</option>'; }).join('');
        ['corr-user', 'man-user', 'as-user'].forEach(function (id) { var v = $(id).value; $(id).innerHTML = opts; if (v) $(id).value = v; });
        var byUser = {}; ov.students.forEach(function (s) { byUser[s.user] = s; });
        $('corr-rows').innerHTML = ov.corrections.slice().reverse().map(function (c) {
            var s = byUser[c.user] || { id: c.user, name: '' };
            return '<tr><td>' + esc(when(c.ts)) + '</td><td>' + esc(s.id + ' ' + s.name) + '</td><td class="num">' + esc(c.xp > 0 ? '+' + c.xp : c.xp) + '</td><td>' + esc(c.reason) + '</td><td>' + esc(c.by) + '</td></tr>';
        }).join('') || '<tr><td colspan="5" class="muted"># no corrections.</td></tr>';
        $('st-csv').onclick = function (e) {
            e.preventDefault();
            api('/api/admin/practice/export.csv', { raw: true }).then(function (text) {
                var a = document.createElement('a');
                a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv' }));
                a.download = 'practice-xp.csv';
                a.click();
            }).catch(function (err) { job('error', 'error: ' + err.message); });
        };
    }

    function drawSettings() {
        var s = ov.settings;
        $('set-form').querySelectorAll('input').forEach(function (i) { i.disabled = !s; });
        if (!s) { $('set-note').textContent = 'Practice is not set up on this server yet.'; return; }
        ['fs_exit', 'panel', 'leave'].forEach(function (t) { $('p-lock-' + t).checked = (s['lock.on'] || []).indexOf(t) >= 0; });
        $('p-wait').value = s['lock.wait_s']; $('p-wait-max').value = s['lock.wait_max_s'];
        $('p-cap').value = s.max_sessions; $('p-idle').value = s.idle_min;
    }

    function drawBonus() {
        var b = ov.bonus;
        $('bonus-ranks').innerHTML = ov.ranks.map(function (r, i) {
            var v = (b.per_rank || {})[r];
            return '<label class="inline" for="br-' + i + '"><span style="min-width:9em;display:inline-block">' + esc(r) + '</span><input class="input small" type="number" id="br-' + i +
                '" data-rank="' + esc(r) + '" min="0" max="10" step="0.25" value="' + (v == null ? '' : esc(v)) + '" placeholder="none"></label>';
        }).join('');
        $('b-cap').value = b.cap || 0;
        $('b-date').value = b.read_at || '';
        var byUser = {}; ov.students.forEach(function (s) { byUser[s.user] = s; });
        $('man-rows').innerHTML = (b.manual || []).map(function (m, i) {
            var s = byUser[m.user] || { id: m.user, name: '' };
            return '<tr><td>' + esc(s.id + ' ' + s.name) + '</td><td class="num">' + esc(m.amount) + '</td><td>' + esc(m.reason) + '</td><td>' + esc(m.by) +
                '</td><td><button class="btn-link" type="button" data-unman="' + i + '">remove</button></td></tr>';
        }).join('') || '<tr><td colspan="5" class="muted"># no manual bonus.</td></tr>';
        var given = ov.students.filter(function (s) { return s.bonus > 0; }).length;
        $('pub-state').textContent = (b.published ? 'Published ' + when(b.published_at) + '.' : 'Not published: students do not see it.') +
            ' ' + given + ' student(s) get a bonus with the amounts saved now.';
    }

    function ask(title, text, yes) {
        return new Promise(function (resolve) {
            $('ask-h').textContent = title; $('ask-p').textContent = text; $('ask-yes').textContent = yes;
            $('ask').classList.remove('hidden'); $('ask-yes').focus();
            function done(v) { $('ask').classList.add('hidden'); resolve(v); }
            $('ask-yes').onclick = function () { done(true); };
            $('ask-no').onclick = function () { done(false); };
        });
    }
    function post(path, body, ok) {
        return api(path, { method: 'POST', body: body }).then(function (r) { job('ok', ok); editing = false; load(); return r; })
            .catch(function (err) { job('error', 'error: ' + err.message); });
    }

    // tabs
    function showTab(name) {
        tab = name;
        TABS.forEach(function (t) {
            $('tab-' + t).setAttribute('aria-selected', t === name ? 'true' : 'false');
            $('tab-' + t).tabIndex = t === name ? 0 : -1;
            $(t + '-view').classList.toggle('hidden', t !== name);
        });
        editing = false;
        if (ov) draw();
    }
    document.querySelector('.tabs').addEventListener('click', function (e) { var t = e.target.closest('[data-tab]'); if (t) showTab(t.getAttribute('data-tab')); });
    document.querySelector('.tabs').addEventListener('keydown', function (e) {
        var i = TABS.indexOf(tab);
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
            i = (i + (e.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length;
            showTab(TABS[i]); $('tab-' + TABS[i]).focus(); e.preventDefault();
        }
    });
    ['set-form', 'bonus-form'].forEach(function (id) { $(id).addEventListener('input', function () { editing = true; }); });
    $('st-filter').addEventListener('input', drawStud);

    document.addEventListener('click', function (e) {
        var u = e.target.closest('[data-unlock]');
        if (u) post('/api/admin/practice/unlock', { user: u.getAttribute('data-unlock') }, 'The wait ends within a few seconds.');
        var p = e.target.closest('[data-preview]');
        if (p) {
            var parts = p.getAttribute('data-preview').split('|');
            var user = parts[0] || (ov.students[0] || {}).user;
            api('/api/practice/scenario?id=' + encodeURIComponent(parts[1]) + '&user=' + encodeURIComponent(user)).then(function (s) {
                var text = (s.brief || []).map(function (b) { return b.p || (b.ol ? b.ol.map(function (x, i) { return (i + 1) + '. ' + x; }).join('\n') : b.pre || ''); }).join('\n\n');
                var hints = (s.hints || []).map(function (h, i) { return 'Hint ' + (i + 1) + ': ' + h; }).join('\n');
                ask(s.meta.title + ' (' + user + ')', text + (hints ? '\n\n' + hints : ''), 'Close').then(function () {});
                $('ask-p').style.whiteSpace = 'pre-wrap';
            }).catch(function (err) { job('error', 'error: ' + err.message); });
        }
        var c = e.target.closest('[data-clearnick]');
        if (c) ask('Clear this nickname?', 'The student sees that it was cleared and can choose another.', 'Clear it')
            .then(function (y) { if (y) post('/api/admin/practice/nick-clear', { user: c.getAttribute('data-clearnick') }, 'Nickname cleared.'); });
        var m = e.target.closest('[data-unman]');
        if (m) post('/api/admin/practice/bonus/manual', { remove: +m.getAttribute('data-unman') }, 'Manual bonus removed.');
    });
    document.addEventListener('change', function (e) {
        var a = e.target.closest('[data-author]');
        if (a) post('/api/admin/practice/author', { user: a.getAttribute('data-author'), on: a.checked }, a.checked ? 'Scenario author badge given.' : 'Scenario author badge removed.');
    });

    $('corr-form').addEventListener('submit', function (e) {
        e.preventDefault();
        post('/api/admin/practice/xp', { user: $('corr-user').value, xp: parseInt($('corr-xp').value, 10), reason: $('corr-why').value.trim() }, 'Correction added.')
            .then(function (r) { if (r) { $('corr-xp').value = ''; $('corr-why').value = ''; } });
    });
    $('set-form').addEventListener('submit', function (e) {
        e.preventDefault();
        var on = ['fs_exit', 'panel', 'leave'].filter(function (t) { return $('p-lock-' + t).checked; });
        post('/api/admin/practice/settings', { changes: { 'lock.on': on, 'lock.wait_s': +$('p-wait').value, 'lock.wait_max_s': +$('p-wait-max').value,
            max_sessions: +$('p-cap').value, idle_min: +$('p-idle').value } }, 'Saved. The gateway uses it within 10 seconds.');
    });
    $('bonus-form').addEventListener('submit', function (e) {
        e.preventDefault();
        var per = {};
        document.querySelectorAll('[data-rank]').forEach(function (i) { if (i.value !== '') per[i.getAttribute('data-rank')] = +i.value; });
        post('/api/admin/practice/bonus', { per_rank: per, cap: +$('b-cap').value || 0, read_at: $('b-date').value || '' }, 'Bonus amounts saved.');
    });
    $('man-form').addEventListener('submit', function (e) {
        e.preventDefault();
        post('/api/admin/practice/bonus/manual', { user: $('man-user').value, amount: +$('man-amt').value, reason: $('man-why').value.trim() }, 'Manual bonus added.')
            .then(function (r) { if (r) { $('man-amt').value = ''; $('man-why').value = ''; } });
    });
    $('pub-on').addEventListener('click', function () {
        ask('Publish the bonus?', 'Every student sees their bonus on the practice page.', 'Publish').then(function (y) {
            if (y) post('/api/admin/practice/bonus/publish', { published: true }, 'Published.');
        });
    });
    $('pub-off').addEventListener('click', function () { post('/api/admin/practice/bonus/publish', { published: false }, 'Hidden from students.'); });

    if (!API) { showLogin('error: the site has no server address (config.js).'); return; }
    api('/api/auth/verify', { method: 'POST' }).then(function (d) {
        if (d.role !== 'admin') { showLogin('This page is for the instructor account.'); return; }
        $('me').textContent = d.user || d.username || 'instructor';
        start();
    }).catch(function () { showLogin(''); });
})();
