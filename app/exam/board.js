/* Instructor board for the exam room: one row per student, refreshed every 5 seconds, and the session replay. */
(function () {
    'use strict';

    var API = ((typeof CONFIG !== 'undefined' && CONFIG.server && CONFIG.server.url) || '').replace(/\/+$/, '');
    var q = new URLSearchParams(location.search);
    if (q.get('api')) API = q.get('api').replace(/\/+$/, '');
    var PAGE = 'exam-board.html';
    var token = sessionStorage.getItem('authToken') || '';
    var board = null, filter = 'all', timer = null, rep = null;
    var shown = {};  // user -> the unlock code revealed on this screen; a new lock has a new code, which starts hidden

    function $(id) { return document.getElementById(id); }
    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function mmss(sec) { sec = Math.round(sec || 0); var m = Math.floor(sec / 60), s = sec % 60; return m + ':' + (s < 10 ? '0' : '') + s; }
    function hms(sec) { sec = Math.max(0, Math.floor(sec)); var h = Math.floor(sec / 3600), m = Math.floor(sec % 3600 / 60), s = sec % 60; return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s; }
    function clock(ts) { return new Date(ts * 1000).toLocaleTimeString('en-GB', { timeZone: 'Asia/Phnom_Penh', hour12: false }); }

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
            '<p><a class="btn btn-tool" href="index.html?next=exam-board.html' + encodeURIComponent(location.search) + '">← menu</a></p>';
    }

    function startBoard() {
        $('screen').classList.add('hidden');
        $('app').classList.remove('hidden');
        load();
        clearInterval(timer);
        timer = setInterval(function () { if (!rep) load(); }, 5000);
    }

    function load() {
        api('/api/admin/exam/board').then(function (b) {
            board = b;
            draw();
        }).catch(function (err) {
            if (err.status === 403) showLogin('Log in with the instructor account.');
            else $('updated').textContent = 'error: ' + err.message;
        });
    }

    // "View as student": the exam page with that student's paper and checks, read-only (exam.html?as=<user>).
    function fillViewAs(rows) {
        var sel = $('as-user'), keep = sel.value;
        if (sel.options.length === rows.length) return;
        sel.innerHTML = rows.slice().sort(function (a, b) { return a.id < b.id ? -1 : 1; }).map(function (r) {
            return '<option value="' + esc(r.user) + '">' + esc(r.id + ' ' + r.name) + '</option>';
        }).join('');
        if (keep) sel.value = keep;
    }
    $('as-go').addEventListener('click', function () {
        if (!$('as-user').value) return;
        var p = new URLSearchParams(location.search); p.set('as', $('as-user').value);
        location.href = 'exam.html?' + p.toString();
    });
    $('to-practice').href = 'practice-board.html' + location.search;

    function progressCell(p, parts) {
        if (!p) return '<span class="muted">unreadable</span>';
        return parts.map(function (id) {
            var x = p[id]; if (!x) return '';
            var auto = x.of - 1, kind = x.ok === auto ? 'ok' : x.ok > 0 ? 'partial' : (x.present > 0 ? 'bad' : 'none');
            var icon = { ok: '✅', partial: '⚠️', bad: '❌', none: '' }[kind];
            return '<span class="st-' + kind + '" title="' + esc(id + ': ' + x.ok + ' of ' + auto + ' checks right, ' + x.present + ' of ' + x.of + ' files in place') + '">' +
                (icon ? '<i class="ico" aria-hidden="true">' + icon + '</i>' : '') + esc(id) + '</span>';
        }).join(' ');
    }

    // Screen column: how many screens the browser reported, and side panels opened beside the exam.
    function screenCell(r) {
        var s = r.screens === 'extended' ? '<span class="st-partial">2 screens</span>'
            : r.screens === 'single' ? '<span class="muted">1 screen</span>'
            : '<span class="muted" title="Firefox and Safari do not report screens">unknown</span>';
        if (r.panel_n) s += '<br><span class="st-partial" title="the page got narrower inside the same window: a side panel or developer tools">panel ' +
            esc(r.panel_n) + ' × ' + esc(mmss(r.panel_s)) + (r.panel_now ? ' now' : '') + '</span>';
        return s;
    }

    function draw() {
        var b = board;
        if (!b.exam) { $('rows').innerHTML = '<tr><td colspan="11" class="muted"># no exam is set up (examctl config).</td></tr>'; return; }
        fillViewAs(b.rows);
        $('win-title').textContent = 'bash — exam board ' + b.exam.id;
        $('cmd').textContent = 'exam board ' + b.exam.id;
        $('head-title').title = $('head-title').textContent;
        $('c-time').textContent = b.left_s == null ? '—' : hms(b.left_s);
        $('c-time').className = 'num ' + (b.left_s != null && b.left_s <= 600 ? 'st-partial' : 'st-ok');
        $('c-phase').textContent = b.phase + (b.end ? ', ends ' + b.end.slice(11, 16) : '');
        $('c-conn').innerHTML = esc(b.connected) + '<small class="muted"> / ' + esc(b.students) + '</small>';
        $('c-high').textContent = b.high + ' high';
        $('c-review').textContent = b.review + ' review';
        $('c-locked').textContent = b.locked ? b.locked + ' locked' : '';
        var pts = b.rows.filter(function (r) { return r.points != null; });
        var autoTotal = b.exam.total * 0.8;
        $('c-avg').innerHTML = pts.length ? esc((pts.reduce(function (s, r) { return s + r.points; }, 0) / pts.length).toFixed(1)) + '<small class="muted"> / ' + esc(autoTotal) + '</small>' : '—';
        var rows = b.rows.filter(function (r) {
            return filter === 'all' || (filter === 'flag' && r.flag) || (filter === 'off' && r.connection !== 'connected') || (filter === 'locked' && r.locked);
        });
        $('rows').innerHTML = rows.map(function (r) {
            var conn = r.connection === 'connected' ? '<span class="st-ok">● connected</span>'
                : r.connection === 'reconnecting' ? '<span class="st-partial">◌ reconnecting</span>'
                : r.connection === 'offline' ? '<span class="st-bad">○ offline ' + esc(mmss(r.connection_s)) + '</span>'
                : '<span class="muted">○ not yet</span>';
            if (r.locked && r.lock_mode === 'wait') {
                conn += '<br><span class="badge st-bad" title="' + esc(LOCK_WHY[r.lock_why] || r.lock_why) + '">waiting</span> ' +
                    (r.lock_left > 0 ? esc(mmss(r.lock_left)) + ' left' : 'can continue') +
                    ' <button class="btn-link" type="button" data-unlock="' + esc(r.user) + '" title="end the wait now">unlock</button>';
            } else if (r.locked) {
                var open = shown[r.user] === r.unlock_code;
                conn += '<br><span class="badge st-bad" title="' + esc(LOCK_WHY[r.lock_why] || r.lock_why) + '">locked</span> ' +
                    '<span class="unlock-code' + (open ? '' : ' muted') + '">' + (open ? esc(r.unlock_code) : '••••') + '</span> ' +
                    '<button class="btn-link" type="button" data-code="' + esc(r.user) + '" aria-label="' + (open ? 'hide' : 'show') + ' the unlock code of ' + esc(r.name) + '">' +
                    (open ? 'hide' : 'show') + '</button> <button class="btn-link" type="button" data-unlock="' + esc(r.user) + '" title="unlock now, without a code">unlock</button>';
                if (r.wrong_codes) conn += '<br><span class="st-bad">' + esc(r.wrong_codes) + ' wrong code' + (r.wrong_codes > 1 ? 's' : '') + '</span>';
            }
            else if (r.lock_n) conn += '<br><span class="muted">unlocked ' + esc(r.lock_n) + ' × ' + esc(mmss(r.lock_s)) + '</span>';
            var flag = r.flag ? '<span class="badge ' + (r.flag === 'high' ? 'st-bad' : 'st-partial') + '">' + esc(r.flag) + '</span>' : '<span class="muted">—</span>';
            var away = r.away_n ? esc(r.away_n) + ' × ' + esc(mmss(r.away_s)) + (r.away_now ? ' <span class="st-partial">now</span>' : '') : '0';
            return '<tr' + (r.flag === 'high' ? ' class="flag-high"' : '') + '><td><span class="id">' + esc(r.id) + '</span> ' + esc(r.name) + '</td>' +
                '<td>' + conn + '</td><td>' + flag + '</td><td class="num">' + away + '</td>' +
                '<td class="num">' + esc(r.large_pastes) + (r.pastes > r.large_pastes ? '<span class="muted"> (' + esc(r.pastes) + ')</span>' : '') + '</td>' +
                '<td class="num">' + esc(r.fs_exits) + '</td><td>' + screenCell(r) + '</td><td>' + progressCell(r.progress, b.exam.parts) + '</td>' +
                '<td class="num">' + (r.points == null ? '—' : esc(r.points)) + '</td>' +
                '<td><code class="st-ok" title="' + esc(r.last_cmd) + '">' + esc(r.last_cmd || '') + '</code>' + (r.truncated ? ' <span class="badge st-bad">output truncated</span>' : '') + '</td>' +
                '<td><button class="btn-link" type="button" data-u="' + esc(r.user) + '">▶ replay</button></td></tr>';
        }).join('') || '<tr><td colspan="11" class="muted"># nobody in this filter.</td></tr>';
        $('updated').textContent = 'updated ' + new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Phnom_Penh', hour12: false });
    }

    document.addEventListener('click', function (e) {
        var u = e.target.closest && e.target.closest('[data-u]');
        if (u) { openReplay(u.getAttribute('data-u')); return; }
        var un = e.target.closest && e.target.closest('[data-unlock]');
        if (un) {
            un.disabled = true;
            api('/api/admin/exam/unlock', { method: 'POST', body: { user: un.getAttribute('data-unlock') } })
                .then(function () { setTimeout(load, 1500); })
                .catch(function (err) { $('updated').textContent = 'error: ' + err.message; });
            return;
        }
        var c = e.target.closest && e.target.closest('[data-code]');
        if (c && board) {
            var who = c.getAttribute('data-code'), row = board.rows.filter(function (x) { return x.user === who; })[0];
            if (row) { shown[who] = shown[who] === row.unlock_code ? '' : row.unlock_code; draw(); }
            return;
        }
        var f = e.target.closest && e.target.closest('[data-f]');
        if (f) {
            filter = f.getAttribute('data-f');
            document.querySelectorAll('[data-f]').forEach(function (c) { c.setAttribute('aria-pressed', c === f ? 'true' : 'false'); });
            if (board) draw();
        }
        var s = e.target.closest && e.target.closest('[data-s]');
        if (s && rep) {
            rep.speed = +s.getAttribute('data-s');
            document.querySelectorAll('[data-s]').forEach(function (c) { c.setAttribute('aria-pressed', c === s ? 'true' : 'false'); });
        }
        var j = e.target.closest && e.target.closest('[data-jump]');
        if (j && rep) seek(+j.getAttribute('data-jump') - 2);
    });
    $('refresh').addEventListener('click', load);

    var LOCK_WHY = { fs_exit: 'left fullscreen', restart: 'started the exam again (reload or another tab)', panel: 'opened a side panel',
        leave: 'left the page', fs_refused: 'the browser refused fullscreen' };

    // ── Replay ───────────────────────────────────────────
    var EV = {
        start: 'started the exam', leave: 'left the page', back: 'came back', paste: 'paste', big_input: 'long input',
        fs_exit: 'left fullscreen', fs_enter: 'back to fullscreen', connect: 'terminal connected',
        disconnect: 'terminal disconnected', replaced: 'opened in another tab', shell_end: 'shell ended',
        open_failed: 'shell refused', reload: 'page reloaded', note: 'note',
        screens: 'screens', panel_open: 'side panel opened', panel_close: 'side panel closed', kb_lock: 'keyboard lock',
        lock: 'exam locked', unlock: 'unlocked with the code', unlock_bad: 'wrong unlock code'
    };

    function openReplay(user) {
        $('board-view').classList.add('hidden');
        $('replay-view').classList.remove('hidden');
        $('r-who').textContent = user + ', loading…';
        $('r-events').innerHTML = '';
        $('r-checks').innerHTML = '';
        $('r-flag').innerHTML = '';
        $('timeline').querySelectorAll('.mk').forEach(function (m) { m.remove(); });
        $('cmd').textContent = 'exam replay ' + user;
        api('/api/admin/exam/replay?user=' + encodeURIComponent(user)).then(function (r) {
            return Promise.all(r.casts.map(function (c) {
                return api('/api/admin/exam/cast?user=' + encodeURIComponent(user) + '&name=' + encodeURIComponent(c.name), { raw: true });
            })).then(function (texts) { buildReplay(r, texts); });
        }).catch(function (err) { $('r-who').textContent = 'error: ' + err.message; });
    }

    function parseCast(text) {
        var lines = text.split('\n'), head = null, out = [];
        for (var i = 0; i < lines.length; i++) {
            if (!lines[i]) continue;
            var v; try { v = JSON.parse(lines[i]); } catch (e) { continue; }
            if (!head) { head = v; out.push([v.timestamp, 'r', (v.width || 80) + 'x' + (v.height || 24)]); continue; }
            if (Array.isArray(v) && (v[1] === 'o' || v[1] === 'r' || v[1] === 'm')) out.push([head.timestamp + v[0], v[1], v[2]]);
        }
        return { head: head, events: out };
    }

    function buildReplay(r, texts) {
        if (rep && rep.raf) cancelAnimationFrame(rep.raf);
        var frames = [], casts = texts.map(parseCast);
        casts.forEach(function (c) { frames = frames.concat(c.events); });
        frames.sort(function (a, b) { return a[0] - b[0]; });
        var evs = r.events || [];
        var t0 = r.start ? Date.parse(r.start) / 1000 : null, t1 = r.end ? Date.parse(r.end) / 1000 : null;
        var times = frames.map(function (f) { return f[0]; }).concat(evs.map(function (e) { return e.ts; }));
        var first = Math.min.apply(null, times.concat(t0 ? [t0] : [])), last = Math.max.apply(null, times.concat(t1 ? [Math.min(t1, Date.now() / 1000)] : []));
        if (!isFinite(first)) { first = Date.now() / 1000; last = first + 60; }
        if (last <= first) last = first + 1;
        rep = { user: r.user, frames: frames, events: evs, first: first, last: last, pos: first, idx: 0, playing: false, speed: rep ? rep.speed : 1, raf: 0, lastTick: 0 };
        $('r-who').textContent = r.id + ' ' + r.name;
        var s = r.summary || {};
        $('r-flag').innerHTML = s.flag ? '<span class="badge ' + (s.flag === 'high' ? 'st-bad' : 'st-partial') + '">' + esc(s.flag) + '</span>' : '';
        // timeline marks
        var tl = $('timeline');
        tl.querySelectorAll('.mk').forEach(function (m) { m.remove(); });
        var span = last - first, leaveAt = null, panelAt = null, big = (board && board.exam && board.exam.large_paste_chars) || 200;
        function mark(cls, a, b) {
            var m = document.createElement('span');
            m.className = 'mk ' + cls;
            m.style.left = (100 * (a - first) / span) + '%';
            if (b != null) m.style.width = Math.max(0.4, 100 * (b - a) / span) + '%';
            tl.appendChild(m);
        }
        evs.forEach(function (e) {
            if (e.k === 'panel_open') panelAt = e.ts;
            else if (e.k === 'panel_close') { mark('panel', panelAt || (e.ts - (e.away_ms || 0) / 1000), e.ts); panelAt = null; }
            else if (e.k === 'leave') leaveAt = e.ts;
            else if (e.k === 'back') { mark('away', leaveAt || (e.ts - (e.away_ms || 0) / 1000), e.ts); leaveAt = null; }
            else if ((e.k === 'paste' && e.n > big) || e.k === 'big_input') mark('paste', e.ts);
            else if (e.k === 'connect' || e.k === 'disconnect') mark('conn', e.ts);
        });
        // event list
        $('r-events').innerHTML = evs.map(function (e) {
            var d = '';
            if (e.k === 'back') d = 'after ' + mmss((e.away_ms || 0) / 1000) + (e.why ? ' (' + e.why + ')' : '');
            else if (e.k === 'leave') d = e.why === 'tab' ? 'another tab' : e.why === 'window' ? 'another window' : '';
            else if (e.k === 'paste' || e.k === 'big_input') d = (e.n || 0) + ' characters';
            else if (e.k === 'disconnect' && e.why) d = e.why;
            else if (e.k === 'fs_exit' && e.why === 'refused') d = 'the browser refused fullscreen';
            else if (e.k === 'screens') d = e.detail === 'extended' ? 'a second screen is connected' : e.detail === 'single' ? 'one screen' : 'the browser does not say';
            else if (e.k === 'panel_open') d = 'the page lost ' + (e.n || 0) + '% of its width';
            else if (e.k === 'panel_close') d = 'after ' + mmss((e.away_ms || 0) / 1000);
            else if (e.k === 'lock') d = LOCK_WHY[e.why] || e.why || '';
            else if (e.k === 'kb_lock') d = e.detail === 'on' ? 'on: leaving fullscreen needs a held Esc' : 'not supported by this browser';
            var cls = (e.k === 'lock' || e.k === 'unlock_bad') ? 'st-bad' : (e.k === 'leave' || e.k === 'back' || e.k === 'fs_exit' || e.k === 'panel_open' || e.k === 'panel_close' || e.k === 'unlock' ||
                (e.k === 'screens' && e.detail === 'extended')) ? 'st-partial' : (e.k === 'big_input' || (e.k === 'paste' && e.n > big)) ? 'st-bad' : '';
            return '<tr><td class="num">' + esc(clock(e.ts)) + '</td><td class="' + cls + '">' + esc(EV[e.k] || e.k) + ' <span class="muted">' + esc(d) + '</span></td>' +
                '<td><button class="btn-link" type="button" data-jump="' + e.ts + '">jump</button></td></tr>';
        }).join('') || '<tr><td colspan="3" class="muted"># no events.</td></tr>';
        // checks
        var ch = r.checks, rows = '';
        if (ch) Object.keys(ch).forEach(function (p) {
            ch[p].forEach(function (i) {
                var k = i.ok === null ? (i.present ? '<span class="muted">to mark</span>' : '<span class="muted">empty</span>') : i.ok ? '<span class="st-ok"><i class="ico">✅</i>ok</span>' : (i.present ? '<span class="st-bad"><i class="ico">❌</i>wrong</span>' : '<span class="muted">missing</span>');
                rows += '<tr><td>' + esc(i.id) + '</td><td>' + k + '</td><td class="muted">' + esc(i.note || '') + '</td></tr>';
            });
        });
        $('r-checks').innerHTML = rows || '<tr><td colspan="3" class="muted"># the exam folder cannot be read.</td></tr>';
        // terminal
        if (!rep.term) {
            $('replay-term').innerHTML = '';
            rep.term = new window.Terminal({ fontFamily: '"Fira Code", monospace', fontSize: 14, lineHeight: 1.2, disableStdin: true, cursorBlink: false, scrollback: 2000,
                theme: { background: '#0d1117', foreground: '#c9d1d9', cursor: '#00ff41' } });
            rep.term.open($('replay-term'));
        }
        seek(first);
        draw2();
    }

    function seek(t) {
        if (!rep) return;
        rep.pos = Math.max(rep.first, Math.min(rep.last, t));
        rep.term.reset();
        var buf = '', i = 0, f = rep.frames;
        for (; i < f.length && f[i][0] <= rep.pos; i++) {
            if (f[i][1] === 'o') buf += f[i][2];
            else if (f[i][1] === 'r') { var p = f[i][2].split('x'); rep.term.resize(+p[0] || 80, +p[1] || 24); }
        }
        if (buf) rep.term.write(buf);
        rep.idx = i;
        draw2();
    }

    function draw2() {
        var pct = 100 * (rep.pos - rep.first) / (rep.last - rep.first);
        $('played').style.width = pct + '%';
        $('head').style.left = pct + '%';
        $('r-pos').textContent = clock(rep.pos) + ' (' + clock(rep.first) + ' to ' + clock(rep.last) + ')';
        $('play').textContent = rep.playing ? '❚❚ Pause' : '▶ Play';
    }

    function frame(ts) {
        if (!rep || !rep.playing) return;
        var dt = rep.lastTick ? (ts - rep.lastTick) / 1000 : 0;
        rep.lastTick = ts;
        rep.pos += dt * rep.speed;
        var f = rep.frames, buf = '';
        if ($('skip').checked && rep.idx < f.length && f[rep.idx][0] - rep.pos > 3) rep.pos = f[rep.idx][0] - 0.5;
        while (rep.idx < f.length && f[rep.idx][0] <= rep.pos) {
            var x = f[rep.idx++];
            if (x[1] === 'o') buf += x[2];
            else if (x[1] === 'r') { if (buf) { rep.term.write(buf); buf = ''; } var p = x[2].split('x'); rep.term.resize(+p[0] || 80, +p[1] || 24); }
        }
        if (buf) rep.term.write(buf);
        if (rep.pos >= rep.last) { rep.pos = rep.last; rep.playing = false; }
        draw2();
        if (rep.playing) rep.raf = requestAnimationFrame(frame);
    }

    $('play').addEventListener('click', function () {
        if (!rep) return;
        rep.playing = !rep.playing;
        rep.lastTick = 0;
        if (rep.playing) { if (rep.pos >= rep.last) seek(rep.first); rep.raf = requestAnimationFrame(frame); }
        draw2();
    });
    $('timeline').addEventListener('click', function (e) {
        if (!rep) return;
        var b = this.getBoundingClientRect();
        seek(rep.first + (e.clientX - b.left) / b.width * (rep.last - rep.first));
    });
    $('back').addEventListener('click', function () {
        if (rep) { rep.playing = false; cancelAnimationFrame(rep.raf); }
        var keep = rep && rep.term; rep = null;
        if (keep) { keep.dispose(); $('replay-term').innerHTML = ''; }
        $('replay-view').classList.add('hidden');
        $('board-view').classList.remove('hidden');
        $('cmd').textContent = board && board.exam ? 'exam board ' + board.exam.id : 'exam board';
        load();
    });

    // Shared with control.js (the Exam, Settings, Security and Results tabs).
    window.examBoard = {
        api: api, esc: esc, mmss: mmss, hms: hms, clock: clock,
        board: function () { return board; },
        refresh: load,
        closeReplay: function () { if (rep) $('back').click(); }
    };

    if (!API) { showLogin('error: the site has no server address (config.js).'); return; }
    if (!token) { showLogin(''); return; }
    api('/api/auth/verify', { method: 'POST' }).then(function (d) {
        if (d.role !== 'admin') { showLogin('Log in with the instructor account.'); return; }
        $('me').textContent = d.user;
        startBoard();
    }).catch(function () { showLogin(''); });
})();
