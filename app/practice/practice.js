/* Practice Linux Commands: the map, the profile and leaderboard, and a scenario in the exam room's terminal.
   The room is locked like the exam (fullscreen, Keyboard Lock, the side-panel cover); leaving it starts a wait.
   See server/practice/ and teaching/PRACTICE-SCENARIOS-PLAN.md. */
(function () {
    'use strict';

    var API = ((typeof CONFIG !== 'undefined' && CONFIG.server && CONFIG.server.url) || '').replace(/\/+$/, '');
    var q = new URLSearchParams(location.search);
    if (q.get('api')) API = q.get('api').replace(/\/+$/, '');   // testing against a local API
    var PAGE = 'practice.html';
    var AS = q.get('as') || '';   // the instructor's "view as student": read-only
    function asQ(sep) { return AS ? sep + 'user=' + encodeURIComponent(AS) : ''; }
    function boardLink() {
        var p = new URLSearchParams(location.search); p.delete('as');
        var rest = p.toString();
        return 'practice-board.html' + (rest ? '?' + rest : '');
    }
    var token = sessionStorage.getItem('authToken') || '';
    var home = null, lbTab = 'week', cur = null;        // cur: the scenario view from the API
    var started = false, term = null, fit = null, ws = null, wsOpen = false, connecting = false, stopReconnect = false;
    var retry = 0, retryTimer = null, lastRx = 0, nextTry = 0, offlineAt = 0, netTimer = null, netTick = null;
    var queue = [], awayStart = null, awayWhy = '', noticeTimer = null, tickTimer = null;
    var panel = null, view = null, locked = '', covered = false, busy = false;
    var LOCK_WHY = { fs_exit: 'You left fullscreen.', restart: 'The scenario was started again (the page was reloaded or opened somewhere else).',
        panel: 'A side panel was opened beside the page.', leave: 'You left the page.',
        fs_refused: 'This browser did not go fullscreen. Use Chrome or Edge and allow fullscreen.' };
    var LEVELS = ['easy', 'medium', 'hard', 'super'];
    var RANK_LOOK = { 'Guest': ['G', '--gray'], 'User': ['U', '--green-dim'], 'Power user': ['PU', '--cyan'], 'Operator': ['OP', '--yellow'],
        'Sysadmin': ['SA', '--magenta'], 'Kernel hacker': ['KH', '--red'], 'root': ['#', '--green'] };

    function $(id) { return document.getElementById(id); }
    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function rich(s) { return esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>'); }
    function mmss(sec) { sec = Math.max(0, Math.floor(sec)); return Math.floor(sec / 60) + ':' + ('0' + sec % 60).slice(-2); }
    function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#8b949e'; }

    function api(path, opts) {
        opts = opts || {};
        var headers = { 'Content-Type': 'application/json' };
        if (token) headers.Authorization = 'Bearer ' + token;
        var ctl = window.AbortController ? new AbortController() : null;
        var timer = ctl ? setTimeout(function () { ctl.abort(); }, 60000) : null;
        return fetch(API + path, { method: opts.method || 'GET', headers: headers, mode: 'cors',
            body: opts.body ? JSON.stringify(opts.body) : undefined, signal: ctl ? ctl.signal : undefined })
            .then(function (r) {
                clearTimeout(timer);
                if (opts.raw) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); }
                return r.json().catch(function () { return {}; }).then(function (data) {
                    if (!r.ok) { var e = new Error(data.error || ('HTTP ' + r.status)); e.status = r.status; e.data = data; throw e; }
                    return data;
                });
            });
    }

    // ── Screens ──────────────────────────────────────────
    function show(id) {
        ['screen', 'home', 'intro', 'room', 'quiz'].forEach(function (x) { $(x).classList.toggle('hidden', x !== id); });
    }
    function screen(title, html) {
        show('screen');
        $('screen-title').textContent = title;
        $('screen-body').innerHTML = html;
    }

    // One login for the whole site: the portal's. Without a valid one, go to the portal's login page, which comes
    // back here afterwards (index.html?next=...).
    function toPortal() {
        sessionStorage.removeItem('examToken');
        location.replace('index.html?next=' + encodeURIComponent(PAGE + location.search));
    }

    // ── Glyphs: the rank shield and the badges ──────────
    function shield(label, color, size, on) {
        var c = on === false ? cssVar('--border-strong') : cssVar(color);
        var glow = on === false ? '' : ' style="filter:drop-shadow(0 0 6px ' + c + ')"';
        var fs = label.length > 1 ? 15 : 20;
        return '<svg class="glyph" width="' + size + '" height="' + (size * 1.15) + '" viewBox="0 0 48 55" aria-hidden="true"' + glow + '>' +
            '<path d="M24 2 L44 9 V27 C44 40 35 49 24 53 C13 49 4 40 4 27 V9 Z" fill="none" stroke="' + c + '" stroke-width="2.5"' +
            (on === false ? ' stroke-dasharray="4 3"' : '') + '/>' +
            '<path d="M24 8 L39 13 V27 C39 37 32 44 24 47 C16 44 9 37 9 27 V13 Z" fill="' + c + '" fill-opacity="' + (on === false ? '0' : '0.12') + '"/>' +
            '<text x="24" y="' + (fs > 15 ? 34 : 32) + '" text-anchor="middle" font-size="' + fs + '" fill="' + c + '">' + esc(label) + '</text></svg>';
    }
    function hexagon(label, color, on) {
        var c = on ? cssVar(color) : cssVar('--border-strong');
        return '<svg class="glyph" width="46" height="52" viewBox="0 0 46 52" aria-hidden="true"' + (on ? ' style="filter:drop-shadow(0 0 5px ' + c + ')"' : '') + '>' +
            '<path d="M23 2 L43 14 V38 L23 50 L3 38 V14 Z" fill="' + c + '" fill-opacity="' + (on ? '0.12' : '0') + '" stroke="' + c + '" stroke-width="2"' +
            (on ? '' : ' stroke-dasharray="4 3"') + '/>' +
            '<text x="23" y="31" text-anchor="middle" font-size="14" fill="' + c + '">' + esc(label) + '</text></svg>';
    }
    function initials(name) {
        var w = name.split(/\s+/);
        return (w.length > 1 ? w[0][0] + w[1][0] : name.slice(0, 2)).toUpperCase();
    }

    // ── Home ─────────────────────────────────────────────
    function loadHome() {
        if (!token) { toPortal(); return; }
        api('/api/practice/home' + asQ('?')).then(function (h) {
            home = h;
            renderHome();
        }).catch(function (err) {
            if (err.status === 401) { sessionStorage.removeItem('authToken'); toPortal(); return; }
            if (err.status === 403 && /roster/.test(err.message)) { screen('bash — practice', '<p class="err">error: ' + esc(err.message) + '</p>' + backLinks()); return; }
            if (err.status === 403) { sessionStorage.removeItem('authToken'); toPortal(); return; }
            screen('bash — practice', '<p class="err">error: ' + esc(err.message) + '</p><p class="muted"># this page tries again in 10 seconds.</p>');
            setTimeout(loadHome, 10000);
        });
    }
    function backLinks() { return '<p><a class="btn btn-tool" href="index.html#browse">← menu</a></p>'; }

    function renderHome() {
        var h = home;
        show('home');
        $('h-user').textContent = h.me.user;
        $('h-closed').classList.toggle('hidden', h.open);
        $('h-closed').textContent = h.closed_why || '';
        $('h-preview').classList.toggle('hidden', !h.preview);
        if (h.preview) $('h-preview').innerHTML = 'Viewing as <b>' + esc(h.me.id) + '</b> (' + esc(h.me.user) + '), read-only: what this student sees. ' +
            '<a href="' + esc(boardLink()) + '">← back to the practice board</a>';
        $('h-portal').classList.toggle('hidden', !!h.preview);
        var head = '<thead><tr><th>Track</th>' + LEVELS.map(function (l) { return '<th class="lv-' + l + '">' + esc(h.levels[l]) + '</th>'; }).join('') + '</tr></thead>';
        var body = h.tracks.map(function (t) {
            var any = t.tiles.some(function (x) { return x; });
            return '<tr><td class="track"><b>' + esc(t.title) + '</b><span>' + esc(t.from) + ' · ' + esc(t.badge) + '</span></td>' +
                t.tiles.map(function (x, i) {
                    if (!x) return '<td>' + (any ? '' : (i === 0 ? '<span class="muted">coming</span>' : '')) + '</td>';
                    var st = { 'new': 'new', progress: 'in progress', cleared: 'cleared ✓', cleared_nohint: 'cleared, no hints ✓' }[x.state];
                    if (x.locked) st = 'opens after the Hard one';
                    return '<td><button class="tile st-' + esc(x.state) + '" type="button" data-sc="' + esc(x.id) + '"' + (x.locked ? ' disabled' : '') + '>' +
                        '<span class="t-name">' + esc(x.title) + '</span><span class="t-meta">' + esc(x.xp) + ' XP · ' + esc(x.minutes) + ' min</span>' +
                        '<span class="t-state">' + esc(st) + (x.remixes ? ' · ' + esc(x.remixes) + ' remix' + (x.remixes > 1 ? 'es' : '') : '') + '</span>' +
                        (x.skills && x.skills.length ? '<span class="t-skills">' + x.skills.map(esc).join(' · ') + '</span>' : '') + '</button></td>';
                }).join('') + '</tr>';
        }).join('');
        $('map').innerHTML = head + '<tbody>' + body + '</tbody>';
        renderProfile();
        renderBoard();
        renderRoadmap();
        showTab(tab);
    }

    // ── The Roadmap tab: six stages of drills and quizzes, and the skills they train ──
    var tab = 'map';
    try { tab = sessionStorage.getItem('os-practice-tab') === 'road' ? 'road' : 'map'; } catch (e) {}
    function showTab(name) {
        tab = name;
        try { sessionStorage.setItem('os-practice-tab', name); } catch (e) {}
        ['map', 'road'].forEach(function (t) {
            $('tab-' + t).setAttribute('aria-selected', t === name ? 'true' : 'false');
            $(t + '-win').classList.toggle('hidden', t !== name);
        });
    }
    document.querySelectorAll('.tabs-row [data-tab]').forEach(function (b) { b.addEventListener('click', function () { showTab(b.getAttribute('data-tab')); }); });

    var STATE_TEXT = { 'new': 'new', progress: 'in progress', cleared: 'cleared ✓', cleared_nohint: 'cleared, no hints ✓', passed: 'passed ✓' };
    function exTile(x, quiz) {
        var meta = quiz ? 'quiz · ' + esc(x.xp) + ' XP · ' + esc(x.minutes) + ' min' : esc(x.xp) + ' XP · ' + esc(x.minutes) + ' min' + (x.readonly ? ' · read-only' : '');
        var state = STATE_TEXT[x.state] + (quiz && x.best && x.state !== 'passed' ? ' · best ' + x.best + ' of 5' : '');
        return '<button class="tile st-' + esc(x.state === 'passed' ? 'cleared' : x.state) + (quiz ? ' quiz' : '') + '" type="button" data-ex="' + esc(x.id) + '" data-kind="' + (quiz ? 'quiz' : 'drill') + '">' +
            '<span class="t-name">' + esc(x.title) + '</span><span class="t-meta">' + meta + '</span><span class="t-state">' + esc(state) + '</span></button>';
    }
    function renderRoadmap() {
        var r = home.roadmap;
        if (!r) { $('road').innerHTML = '<p class="muted"># the roadmap is not on this server yet.</p>'; return; }
        var done = r.stages.filter(function (s) { return s.earned; }).length;
        $('road-count').textContent = r.skills.have + ' of ' + r.skills.total;
        var html = '<div class="road-top"><div><b>' + esc(r.skills.have) + '</b> of ' + esc(r.skills.total) + ' skills acquired <span class="muted">· ' + done + ' of ' + r.stages.length +
            ' stage badges' + (r.journeyman ? ' · Linux Journeyman' : '') + '</span></div>' +
            '<div class="xpbar" role="progressbar" aria-valuemin="0" aria-valuemax="' + r.skills.total + '" aria-valuenow="' + r.skills.have + '" aria-label="Skills acquired"><i style="width:' +
            Math.round(100 * r.skills.have / Math.max(1, r.skills.total)) + '%"></i></div>' +
            '<p class="comment"># every stage is open: the order is only a suggestion. A skill is acquired by clearing a drill (or a scenario) that trains it; a quiz gives XP and counts for the stage badge, but never a skill.</p></div>';
        html += r.stages.map(function (s, i) {
            var nd = s.drills.filter(function (x) { return x.state.indexOf('cleared') === 0; }).length, nq = s.quizzes.filter(function (x) { return x.state === 'passed'; }).length;
            return '<section class="stage' + (s.earned ? ' earned' : '') + '" aria-label="' + esc(s.title) + '">' +
                '<header class="stage-head"><span class="stage-n">' + (i + 1) + '</span><span><b>' + esc(s.title) + '</b><span class="stage-badge">' + (s.earned ? '★ ' : '') + esc(s.badge) + '</span></span>' +
                '<span class="stage-count">' + nd + ' of ' + s.drills.length + ' drills · ' + nq + ' of ' + s.quizzes.length + ' quizzes</span></header>' +
                '<div class="xpbar slim" role="progressbar" aria-valuemin="0" aria-valuemax="' + s.total + '" aria-valuenow="' + s.done + '" aria-label="' + esc(s.title) + ' progress"><i style="width:' + Math.round(100 * s.done / Math.max(1, s.total)) + '%"></i></div>' +
                '<div class="skill-tags" role="group" aria-label="Skills of this stage">' + s.skills.map(function (k) {
                    return '<button class="skill ' + (k.have ? 'have' : 'none') + '" type="button" data-skill="' + esc(k.id) + '" aria-pressed="false" title="' + (k.have ? 'acquired' : 'not yet') + '">' + (k.have ? '✓ ' : '') + esc(k.title) + '</button>';
                }).join('') + '</div><div class="skill-ex hidden" data-for="' + esc(s.id) + '"></div>' +
                '<div class="tiles">' + s.drills.map(function (x) { return exTile(x, false); }).join('') + s.quizzes.map(function (x) { return exTile(x, true); }).join('') + '</div></section>';
        }).join('');
        $('road').innerHTML = html;
    }
    $('road').addEventListener('click', function (e) {
        var t = e.target.closest('[data-ex]');
        if (t) { if (t.getAttribute('data-kind') === 'quiz') openQuiz(t.getAttribute('data-ex')); else openScenario(t.getAttribute('data-ex')); return; }
        var k = e.target.closest('[data-skill]');
        if (!k) return;
        var id = k.getAttribute('data-skill'), box = k.closest('.stage').querySelector('.skill-ex');
        var on = k.getAttribute('aria-pressed') === 'true';
        k.closest('.stage').querySelectorAll('[data-skill]').forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
        if (on) { box.classList.add('hidden'); return; }
        k.setAttribute('aria-pressed', 'true');
        var list = (home.roadmap.tags[id] || []);
        var title = k.textContent.replace(/^✓ /, '');
        box.innerHTML = '<p class="comment"># exercises that train “' + esc(title) + '”:</p>' + (list.length ? list.map(function (x) {
            return '<button class="btn-link ex-link" type="button" ' + (x.kind === 'scenario' ? 'data-sc="' + esc(x.id) + '"' : 'data-ex="' + esc(x.id) + '" data-kind="' + esc(x.kind) + '"') + '>' + esc(x.title) + ' <span class="muted">(' + esc(x.kind) + ')</span></button>';
        }).join(' ') : '<span class="muted">none yet</span>');
        box.classList.remove('hidden');
    });
    $('road').addEventListener('click', function (e) {
        var s = e.target.closest('[data-sc]');
        if (s) openScenario(s.getAttribute('data-sc'));
    });

    function renderProfile() {
        var p = home.profile, me = home.me, look = RANK_LOOK[p.rank] || ['?', '--gray'];
        var nxt = p.next, pct = 100;
        if (nxt) pct = Math.max(0, Math.min(100, Math.round(100 * (p.xp - p.rank_xp) / Math.max(1, nxt.xp - p.rank_xp))));
        var need = '';
        if (nxt) {
            need = nxt.xp_left ? esc(nxt.xp_left) + ' XP to ' + esc(nxt.name) : 'XP enough for ' + esc(nxt.name);
            if (nxt.supers_left) need += ', and ' + esc(nxt.supers_left) + ' more Super challenge' + (nxt.supers_left > 1 ? 's' : '');
            if (nxt.needs_nohint_super) need += ', one Super challenge without hints';
        } else need = 'the top rank';
        var html = '<div class="rank-row">' + shield(look[0], look[1], 64) + '<div><div class="rk-name" style="color:' + cssVar(look[1]) + '">' + esc(p.rank) + '</div>' +
            '<div class="rk-sub">' + esc(me.id) + (me.nick ? ' · ' + esc(me.nick) : '') + '</div></div></div>' +
            '<div class="xpbar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + pct + '" aria-label="XP to the next rank"><i style="width:' + pct + '%"></i></div>' +
            '<div class="kv"><span><b>' + esc(p.xp) + '</b> XP</span><span><b>' + esc(p.week) + '</b> this week</span><span><b>' + esc(p.clears) + '</b> cleared</span><span><b>' + esc(p.supers) + '</b> Super</span>' +
            (p.skills ? '<span><b>' + esc(p.skills.have) + '</b> of ' + esc(p.skills.total) + ' skills</span>' : '') + '</div>' +
            '<p class="hint">Next: ' + need + '.</p>' +
            (home.preview ? '<p class="hint">Nickname: ' + (me.nick ? esc(me.nick) : 'none') + '</p><span id="nick-form"></span>' :
            '<form class="nick-form" id="nick-form"><label class="muted" for="nick">nickname</label><input class="input" id="nick" maxlength="20" value="' + esc(me.nick) + '" placeholder="optional, 3 to 20 characters">' +
            '<button class="btn btn-tool" type="submit">Save</button></form>') +
            (me.nick_cleared ? '<p class="err">The instructor cleared your nickname. Choose another one.</p>' : '') + '<p class="err" id="nick-err" role="alert"></p>';
        if (home.bonus) html += '<p class="bonus-line">Bonus on the lab mark: <b>+' + esc(home.bonus.amount) + '</b> (rank ' + esc(home.bonus.rank) + ').</p>';
        $('profile').innerHTML = html;
        $('nick-form').addEventListener('submit', function (e) {
            e.preventDefault();
            api('/api/practice/nick', { method: 'POST', body: { nick: $('nick').value } }).then(loadHome)
                .catch(function (err) { $('nick-err').textContent = 'error: ' + err.message; });
        });
        var colors = ['--green', '--cyan', '--yellow', '--magenta'];
        $('badges').innerHTML = p.badges.map(function (b, i) {
            return '<div class="badge-g' + (b.earned ? ' on' : '') + '" title="' + esc(b.name + ': ' + b.how) + '">' + hexagon(initials(b.name), colors[i % 4], b.earned) +
                '<span class="b-name">' + esc(b.name) + '</span></div>';
        }).join('');
    }

    function renderBoard() {
        var lb = home.leaderboard, rows = lb[lbTab] || [], mine = lb['me_' + lbTab];
        var medals = ['🥇', '🥈', '🥉'];
        var html = rows.map(function (r) {
            return '<tr' + (r.me ? ' class="me"' : '') + '><td class="num">' + (r.pos <= 3 ? '<i class="medal" aria-label="place ' + r.pos + '">' + medals[r.pos - 1] + '</i>' : esc(r.pos)) +
                '</td><td><span class="id">' + esc(r.id) + '</span>' + (r.nick ? ' <span class="muted">' + esc(r.nick) + '</span>' : '') +
                '</td><td>' + esc(r.rank) + '</td><td class="num">' + esc(r.xp) + '</td></tr>';
        }).join('');
        if (mine && mine.pos > 10) html += '<tr class="me"><td class="num">' + esc(mine.pos) + '</td><td><span class="id">' + esc(mine.id) + '</span> <span class="muted">you</span></td><td>' + esc(mine.rank) + '</td><td class="num">' + esc(mine.xp) + '</td></tr>';
        $('lb').innerHTML = html || '<tr><td colspan="4" class="muted"># nobody yet' + (lbTab === 'week' ? ' this week' : '') + '. Clear a scenario to be first.</td></tr>';
    }
    document.querySelectorAll('[data-lb]').forEach(function (b) {
        b.addEventListener('click', function () {
            lbTab = b.getAttribute('data-lb');
            document.querySelectorAll('[data-lb]').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
            renderBoard();
        });
    });
    $('map').addEventListener('click', function (e) {
        var t = e.target.closest('[data-sc]');
        if (t && !t.disabled) openScenario(t.getAttribute('data-sc'));
    });

    // ── A scenario: the intro card ──────────────────────
    function openScenario(id) {
        api('/api/practice/scenario?id=' + encodeURIComponent(id) + asQ('&')).then(function (s) {
            cur = s;
            if (s.run && !(s.meta.level === 'super' && s.run.expired && !s.run.cleared)) { intro(true); return; }
            intro(false);
        }).catch(function (err) { alertBox('error: ' + err.message); });
    }

    function rulesList() {
        var m = cur.meta;
        return '<ul class="rules">' +
            '<li>A real shell on the course server, in <code>~/practice/' + esc(m.id) + '/</code>, with your own values.</li>' +
            '<li><b>The countdown</b>: ' + esc(m.minutes) + ' minutes from Start. It keeps running if you close the page. ' +
            (m.level === 'super' ? 'When it ends, the attempt ends; a Remix gives a new one with new values.' : 'After it ends you can still clear the ' + (m.level === 'drill' ? 'drill' : 'scenario') + ', for half the XP.') + '</li>' +
            (m.level === 'super' ? '<li>No hints. The check runs your work on inputs you have not seen.</li>'
                : m.level === 'drill' ? '<li>Two hints; each one lowers the XP of the clear (90%, then 70%).' + (cur.steps && cur.steps.length ? '' : ' It is a small exercise on one skill.') + '</li>'
                    : '<li>Three hints; each one lowers the XP of the clear (90%, 70%, then 40%).</li>') +
            (m.level === 'drill' ? '<li>A drill earns XP the first time. Playing it again (a new attempt, new values) is practice and earns nothing, and the skill stays yours.</li>' : '') +
            '<li><b>No AI.</b> The page stays in fullscreen. Leaving it, opening a side panel or reloading starts a <b>wait</b>: 30 seconds the first time, doubling each time today.</li>' +
            '<li>Check as often as you like, once every 10 seconds; it never costs XP. Everything you type is recorded; you can watch your replay for 14 days.</li></ul>';
    }

    function intro(resume) {
        var m = cur.meta;
        show('intro');
        $('in-title').textContent = 'scenario — ' + m.id;
        var left = cur.run ? (Date.parse(cur.run.deadline_iso) - Date.now()) / 1000 : m.minutes * 60;
        var facts = '<div class="facts"><div><span class="k">level</span><span class="v lvl ' + esc(m.level) + '">' + esc(cur.level_name) + '</span></div>' +
            '<div><span class="k">XP</span><span class="v">' + esc(m.xp) + '</span></div>' +
            '<div><span class="k">' + (resume ? 'time left' : 'countdown') + '</span><span class="v">' + (resume && left <= 0 ? 'time is up' : esc(mmss(left))) + '</span></div>' +
            (cur.run ? '<div><span class="k">attempt</span><span class="v">' + esc(cur.run.attempt) + '</span></div>' : '') + '</div>';
        var closed = home && !home.open ? '<p class="err">' + esc(home.closed_why) + '</p>' : '';
        if (m.skill_titles && m.skill_titles.length) facts = facts.replace(/<\/div>$/, '<div><span class="k">skill</span><span class="v">' + m.skill_titles.map(esc).join(', ') + '</span></div></div>');
        if (AS) {   // the instructor's preview: the task with this student's values, and all the hints
            var brief = (cur.brief || []).map(function (b) {
                return b.p ? '<p>' + rich(b.p) + '</p>' : b.ol ? '<ol>' + b.ol.map(function (x) { return '<li>' + rich(x) + '</li>'; }).join('') + '</ol>'
                    : b.pre ? '<pre>' + esc(b.pre) + '</pre>' : '';
            }).join('');
            var hints = (cur.hints || []).map(function (x, i) { return '<p class="hintbox"><b>' + (i + 1) + '</b>' + rich(x) + '</p>'; }).join('');
            $('in-body').innerHTML = '<p class="title">' + esc(m.title) + '</p><p class="learn">' + esc(m.learn) + '</p>' + facts +
                '<div class="sec">// the task, with ' + esc(AS) + '\'s values</div><div class="brief">' + brief + '</div>' +
                (hints ? '<div class="sec">// the hints</div>' + hints : '') +
                '<p class="hint">Read-only: the instructor cannot start a scenario as a student.</p>' +
                '<div class="row"><span class="grow"></span><button class="btn-link" type="button" id="in-back">← back to the map</button></div>';
            $('in-back').addEventListener('click', function () { loadHome(); });
            return;
        }
        $('in-body').innerHTML = '<p class="title">' + esc(m.title) + '</p><p class="learn">' + esc(m.learn) + '</p>' + facts + rulesList() + closed +
            '<div class="row"><button class="btn btn-fill" id="in-go" type="button"' + (closed ? ' disabled' : '') + '>' + (resume ? 'Continue' : 'Start') + '</button>' +
            '<span class="muted">The page goes fullscreen.</span><span class="grow"></span><button class="btn-link" type="button" id="in-back">← back to the map</button></div>';
        $('in-go').addEventListener('click', function () { startScenario(); });
        $('in-back').addEventListener('click', function () { loadHome(); });
    }

    function startScenario() {
        if (!goFullscreen()) sendEvent({ k: 'fs_exit', why: 'refused' });   // inside the click, while the browser allows it
        $('in-go').disabled = true;
        api('/api/practice/start', { method: 'POST', body: { id: cur.meta.id } }).then(function (s) {
            cur = s;
            enterRoom();
        }).catch(function (err) {
            if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
            $('in-go').disabled = false;
            alertBox('error: ' + err.message);
        });
    }

    // ── The room ─────────────────────────────────────────
    function enterRoom() {
        started = true;
        stopReconnect = false;
        show('room');
        renderPaper();
        openTerminal();
        sendEvent({ k: 'start' });
        sendEvent({ k: 'screens', detail: screensNow() });
        view = measure();
        clearInterval(tickTimer);
        tickTimer = setInterval(tick, 1000);
        tick();
    }

    function renderPaper(results) {
        if (covered) return;
        var m = cur.meta, run = cur.run || {};
        $('paper-title').textContent = 'task — ' + m.id;
        $('term-title').textContent = (home ? home.me.user : '') + '@itc-os: ~/practice/' + m.id;
        $('s-who').textContent = m.title + ' · ' + cur.level_name + (run.attempt > 1 ? ' · remix ' + (run.attempt - 1) : '');
        var h = '<h1>' + esc(m.title) + '<span class="lvl ' + esc(m.level) + '">' + esc(cur.level_name) + '</span></h1><div class="brief">';
        (cur.brief || []).forEach(function (b) {
            if (b.p) h += '<p>' + rich(b.p) + '</p>';
            if (b.ol) h += '<ol>' + b.ol.map(function (x) { return '<li>' + rich(x) + '</li>'; }).join('') + '</ol>';
            if (b.pre) h += '<pre>' + esc(b.pre) + '</pre>';
        });
        h += '</div>';
        var last = results || run.last;
        if (cur.steps && cur.steps.length) h += stepsHtml(progressOf(cur.steps, last && last.checks));
        if ((cur.hints || []).length) {
            h += '<div class="sec">// hints</div>' + cur.hints.map(function (x, i) {
                var st = cur.hint_steps && cur.hint_steps[i] != null && cur.steps && cur.steps.length > 1 ? ' <span class="muted">step ' + (cur.hint_steps[i] + 1) + '</span>' : '';
                return '<p class="hintbox"><b>' + (i + 1) + '</b>' + rich(x) + st + '</p>';
            }).join('');
        }
        if (last && last.checks) {
            h += '<div class="sec">// last check' + (last.at ? ', ' + esc(new Date(last.at * 1000).toLocaleTimeString('en-GB', { hour12: false })) : '') + '</div><ul class="checks">' +
                last.checks.map(function (c) {
                    return '<li><span class="' + (c.ok ? 'ok' : 'no') + '" aria-label="' + (c.ok ? 'passed' : 'not yet') + '">' + (c.ok ? '✅' : '❌') + '</span><span>' + rich(c.label) + '</span>' +
                        (c.ok ? '' : '<span class="why">' + rich(c.why) + '</span>') + '</li>';
                }).join('') + '</ul>';
        }
        $('paper-body').innerHTML = h;
        updateActions();
    }

    // Where the student is in a guided exercise: the same rule as the server's step_progress (first step with a check not passed).
    function progressOf(steps, checks) {
        var ok = {};
        (checks || []).forEach(function (c) { ok[c.id] = !!c.ok; });
        var cur_ = -1, rows = steps.map(function (s, i) {
            var done = s.checks.every(function (id) { return ok[id]; });
            if (!done && cur_ < 0) cur_ = i;
            return { done: done };
        });
        if (cur_ >= 0) rows[cur_].current = true;
        return { current: cur_ < 0 ? steps.length : cur_, rows: rows };
    }
    function stepsHtml(p) {
        var many = cur.steps.length > 1;
        var h = '<div class="sec">// ' + (many ? 'steps' : 'lesson') + '</div><ol class="steps">';
        cur.steps.forEach(function (s, i) {
            var row = p.rows[i], state = row.done ? 'done' : row.current ? 'current' : 'todo';
            h += '<li class="step st-' + state + '">';
            if (many) h += '<div class="s-head"><span class="s-mark" aria-label="' + (state === 'done' ? 'done' : state === 'current' ? 'now' : 'later') + '">' +
                (state === 'done' ? '✅' : state === 'current' ? '▶' : '○') + '</span><b>Step ' + (i + 1) + ' of ' + cur.steps.length + '</b></div>';
            if (state !== 'todo') {
                if (s.learn) h += '<p class="s-learn">' + rich(s.learn) + '</p>';
                if (many || s.task !== (cur.brief && cur.brief[0] && cur.brief[0].p)) h += '<p class="s-task">' + rich(s.task) + '</p>';
            } else h += '<p class="muted s-later">opens when step ' + i + ' passes</p>';
            h += '</li>';
        });
        return h + '</ol>';
    }

    function updateActions() {
        var m = cur.meta, run = cur.run || {}, sup = m.level === 'super';
        var expired = Date.parse(run.deadline_iso) <= Date.now();
        var total = cur.hints_total == null ? 3 : cur.hints_total;
        $('a-hint').classList.toggle('hidden', sup);
        var used = run.hints || 0;
        $('a-hint').textContent = used >= total ? 'Hints: ' + total + ' of ' + total : 'Hint ' + (used + 1) + ' of ' + total;
        $('a-hint').disabled = used >= total || run.cleared || busy;
        $('a-remix').textContent = cur.kind === 'drill' ? 'Play again' : 'Remix';
        $('cl-remix').textContent = cur.kind === 'drill' ? 'Play again (no XP)' : 'Remix';
        $('a-check').disabled = busy || run.cleared || (sup && expired);
        $('a-reset').disabled = busy || run.cleared;
        $('a-remix').classList.toggle('hidden', !(run.cleared || (sup && expired)));
        $('a-remix').disabled = busy;
    }

    function tick() {
        if (!cur || !cur.run) return;
        var left = (Date.parse(cur.run.deadline_iso) - Date.now()) / 1000, sup = cur.meta.level === 'super';
        $('s-time').textContent = left > 0 ? mmss(left) : '0:00';
        $('s-time').className = 'time' + (left <= 60 ? ' bad' : left <= 180 ? ' warn' : '');
        var note = $('s-note');
        if (cur.run.cleared) { note.textContent = 'cleared'; note.className = 'st-ok'; }
        else if (left <= 0) { note.textContent = sup ? 'time is up: Remix to try again' : 'time is up: a clear now earns half the XP'; note.className = 'st-bad'; }
        else { note.textContent = 'left'; note.className = 'muted'; }
        if (left <= 0 && sup) updateActions();
    }

    function setStatus(text, kind) {
        $('a-status').textContent = text || '';
        $('a-status').className = kind === 'bad' ? 'err' : kind === 'ok' ? 'st-ok' : 'muted';
    }

    $('a-check').addEventListener('click', function () {
        if (busy) return;
        busy = true; updateActions(); setStatus('checking… (up to 20 seconds)');
        api('/api/practice/check', { method: 'POST', body: { id: cur.meta.id } }).then(function (r) {
            busy = false;
            cur.run.last = { at: Date.now() / 1000, ok: r.ok, checks: r.checks };
            cur.run.cleared = r.cleared; cur.run.checks = r.run.checks;
            renderPaper();
            var n = r.checks.filter(function (c) { return c.ok; }).length;
            setStatus(r.ok ? 'all ' + r.checks.length + ' checks pass' : n + ' of ' + r.checks.length + ' checks pass: read the reasons in the task panel', r.ok ? 'ok' : '');
            if (r.award) showClear(r.award);
        }).catch(function (err) {
            busy = false; updateActions();
            setStatus('error: ' + err.message, 'bad');
            if (err.data && err.data.expired) { cur.run.deadline_iso = new Date(Date.now() - 1000).toISOString(); updateActions(); }
        });
    });

    $('a-hint').addEventListener('click', function () {
        var used = cur.run.hints || 0, share = cur.hint_share, total = cur.hints_total == null ? 3 : cur.hints_total;
        ask('Open hint ' + (used + 1) + ' of ' + total + '?', 'A clear will then be worth ' + Math.round(100 * share[used + 1]) + '% of the XP (now ' +
            Math.round(100 * share[used]) + '%). Trying a Check first never costs anything.', 'Open the hint').then(function (yes) {
            if (!yes) return;
            api('/api/practice/hint', { method: 'POST', body: { id: cur.meta.id } }).then(function (r) {
                cur.hints = r.hints; cur.run.hints = r.used; if (r.hint_steps) cur.hint_steps = r.hint_steps;
                renderPaper();
            }).catch(function (err) { setStatus('error: ' + err.message, 'bad'); });
        });
    });

    $('a-reset').addEventListener('click', function () {
        ask('Put back the starting files?', 'Everything in ~/practice/' + cur.meta.id + '/ is replaced by the starting files. The countdown goes on, and the hints you opened stay open.', 'Reset').then(function (yes) {
            if (!yes) return;
            busy = true; updateActions(); setStatus('resetting…');
            api('/api/practice/reset', { method: 'POST', body: { id: cur.meta.id } }).then(function () {
                busy = false; updateActions();
                setStatus('the starting files are back', 'ok');
                typeLine('cd ~/practice/' + cur.meta.id);
            }).catch(function (err) { busy = false; updateActions(); setStatus('error: ' + err.message, 'bad'); });
        });
    });

    function remix() {
        busy = true; updateActions(); setStatus('making a remix…');
        api('/api/practice/remix', { method: 'POST', body: { id: cur.meta.id } }).then(function (s) {
            busy = false;
            cur = s;
            $('clear-dialog').classList.add('hidden');
            renderPaper();
            setStatus('a new attempt with new values; the countdown starts again', 'ok');
            typeLine('cd ~/practice/' + cur.meta.id + ' && clear');
            if (ws) { try { ws.close(); } catch (e) {} }   // reconnects with the new attempt in the ticket
        }).catch(function (err) { busy = false; updateActions(); setStatus('error: ' + err.message, 'bad'); });
    }
    $('a-remix').addEventListener('click', remix);
    $('cl-remix').addEventListener('click', remix);

    function typeLine(text) {   // Ctrl+U clears what was being typed, then the command
        if (wsOpen) ws.send(JSON.stringify({ t: 'i', d: '\x15' + text + '\r' }));
    }

    function leaveRoom() {
        if (wsOpen) { try { ws.send(JSON.stringify({ t: 'e', k: 'stop', cts: Date.now() })); } catch (e) {} }   // a proper exit: no wait next time
        started = false;            // first, so leaving fullscreen now is not a "left fullscreen" event
        stopReconnect = true;
        clearInterval(tickTimer);
        if (ws) { ws.onclose = ws.onmessage = ws.onerror = null; try { ws.close(); } catch (e) {} }
        ws = null; wsOpen = false; connecting = false;
        clearTimeout(retryTimer); clearTimeout(netTimer); clearInterval(netTick);
        ['fs-dialog', 'net-dialog', 'clear-dialog', 'taken-dialog'].forEach(function (d) { $(d).classList.add('hidden'); });
        if (panel || locked) { panel = null; locked = ''; applyCover(); }
        if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(function () {});
        if (term) term.reset();
        setStatus('');
        loadHome();
    }
    $('a-leave').addEventListener('click', leaveRoom);
    $('cl-map').addEventListener('click', leaveRoom);
    $('cl-stay').addEventListener('click', function () { $('clear-dialog').classList.add('hidden'); if (term) term.focus(); });

    function showClear(a) {
        $('cl-xp').textContent = (a.xp > 0 ? '+' : '') + a.xp + ' XP';
        $('cl-why').innerHTML = a.reasons.map(function (r) { return '<li>' + esc(r) + '</li>'; }).join('') + '<li>' + esc(a.total) + ' XP in total.</li>';
        var extra = '';
        if (a.rank_up) {
            var look = RANK_LOOK[a.rank] || ['?', '--gray'];
            extra += '<div class="new-thing">' + shield(look[0], look[1], 44) + '<span>New rank: <b>' + esc(a.rank) + '</b></span></div>';
        }
        (a.skills || []).forEach(function (k) { extra += '<div class="new-thing">' + hexagon('✓', '--green', true) + '<span>New skill: <b>' + esc(k) + '</b></span></div>'; });
        (a.badges || []).forEach(function (b) { extra += '<div class="new-thing">' + hexagon(initials(b), '--cyan', true) + '<span>New badge: <b>' + esc(b) + '</b></span></div>'; });
        $('cl-new').innerHTML = extra;
        $('clear-dialog').classList.remove('hidden');
        $('cl-map').focus();
    }

    function alertBox(text) { ask('Practice', text, 'OK', true); }
    function ask(title, text, yes, only) {
        return new Promise(function (resolve) {
            $('ask-h').textContent = title;
            $('ask-p').textContent = text;
            $('ask-yes').textContent = yes;
            $('ask-no').classList.toggle('hidden', !!only);
            $('ask').classList.remove('hidden');
            $('ask-yes').focus();
            function done(v) { $('ask').classList.add('hidden'); document.removeEventListener('keydown', key); resolve(v); if (term && started) term.focus(); }
            function key(e) { if (e.key === 'Escape') done(false); }
            document.addEventListener('keydown', key);
            $('ask-yes').onclick = function () { done(true); };
            $('ask-no').onclick = function () { done(false); };
        });
    }

    // ── A quiz: questions and four choices, no shell ─────
    // The answers stay in this page until Submit; the server marks them and says only the score and the skills to review.
    // The page runs in fullscreen and holds a socket to the gateway (a quiz session: no shell). The gateway keeps the lock
    // (the practice room's wait, shared with the shell) and the page's events; the API holds the questions, the hint and the
    // submit back unless this attempt's socket is alive and the lock is off. So while locked the page drops the questions
    // and asks for them again when the gateway says "unlocked". Leaving through "roadmap" is a proper exit (a "stop" event).
    var qv = null, qOn = false, qIdx = 0, qAnswers = {}, qLeaves = 0, qTimer = null, qWaitTimer = null, qBusy = false, qDone = null;
    var qWs = null, qWsOpen = false, qConnecting = false, qStopRetry = false, qRetry = 0, qRetryTimer = null, qLastRx = 0, qQueue = [],
        qLocked = '', qLockEnd = 0, qLockTimer = null, qPingTimer = null, qSession = 0;
    var Q_LOCK_WHY = { fs_exit: 'You left fullscreen.', restart: 'The quiz was opened again (the page was reloaded or opened somewhere else).',
        panel: 'A side panel was opened beside the page.', leave: 'You left the page.',
        fs_refused: 'This browser did not go fullscreen. Use Chrome or Edge and allow fullscreen.' };
    function qReady() { return !!(qv && qv.questions && qv.questions.length) && !qLocked; }
    function qKey() { return 'os-quiz-' + qv.meta.id + '-' + (qv.state ? qv.state.attempt : 0); }
    function qSave() { try { sessionStorage.setItem(qKey(), JSON.stringify({ a: qAnswers, l: qLeaves })); } catch (e) {} }
    function qLoad() {
        try { var o = JSON.parse(sessionStorage.getItem(qKey()) || 'null'); if (o) { qAnswers = o.a || {}; qLeaves = o.l || 0; } } catch (e) {}
    }

    function openQuiz(id) {
        api('/api/practice/quiz?id=' + encodeURIComponent(id) + asQ('&')).then(function (g) {
            qv = g;
            quizIntro();
        }).catch(function (err) { alertBox('error: ' + err.message); });
    }

    function quizIntro() {
        var m = qv.meta, r = qv.rules, st = qv.state;
        show('intro');
        $('in-title').textContent = 'quiz — ' + m.id;
        var facts = '<div class="facts"><div><span class="k">stage</span><span class="v">' + esc(qv.stage_title) + '</span></div><div><span class="k">XP</span><span class="v">' + esc(m.xp) + '</span></div>' +
            '<div><span class="k">countdown</span><span class="v">' + esc(m.minutes) + ' min</span></div><div><span class="k">pass</span><span class="v">' + esc(r.pass_mark) + ' of ' + esc(r.questions) + '</span></div>' +
            (st.best ? '<div><span class="k">best</span><span class="v">' + esc(st.best) + ' of ' + esc(r.questions) + '</span></div>' : '') + '</div>';
        var rules = '<ul class="rules">' +
            '<li>' + esc(r.questions) + ' multiple-choice questions on: ' + qv.skill_titles.map(esc).join(', ') + '. Your questions and their order are your own.</li>' +
            '<li>You see no right or wrong while you answer. At the end you get your score and the skills to review, and you pass with ' + esc(r.pass_mark) + ' of ' + esc(r.questions) + '.</li>' +
            '<li><b>One hint</b> for the whole quiz: it takes two wrong choices away from the question you are on, and a pass is then worth ' + Math.round(100 * r.hint_share[1]) + '% of the XP.</li>' +
            '<li>After <b>' + esc(m.minutes) + ' minutes</b> you can still pass, for half the XP. A failed attempt waits ' + esc(r.wait_s) + ' seconds, and the next one asks new questions.</li>' +
            '<li><b>No AI.</b> The page stays in fullscreen and connected to the practice room. Leaving fullscreen, reloading or opening the quiz somewhere else starts a <b>wait</b> (30 seconds, doubling each time today, shared with the shell): the server holds the questions back until it ends.</li>' +
            '<li>XP comes with your first pass only. Passing again is practice, and a quiz never gives a skill: a skill comes from a drill.</li></ul>';
        var closed = !qv.open ? '<p class="err">' + esc(qv.closed_why) + '</p>' : '';
        var seen = st.passed ? '<p class="st-ok">You passed this quiz. You can play it again for practice.</p>' : '';
        $('in-body').innerHTML = '<p class="title">' + esc(m.title) + '</p><p class="learn">' + esc(m.learn) + '</p>' + facts + rules + seen + closed +
            (qv.preview ? '<p class="hint">Read-only: the instructor cannot play a quiz as a student, and never sees its questions here.</p>' : '') +
            '<div class="row">' + (qv.preview ? '' : '<button class="btn btn-fill" id="in-go" type="button">' + (st.open ? 'Continue' : 'Start') + '</button><span class="muted" id="in-wait"></span>') +
            '<span class="grow"></span><button class="btn-link" type="button" id="in-back">← back to the roadmap</button></div>';
        $('in-back').addEventListener('click', function () { clearInterval(qWaitTimer); loadHome(); });
        if (qv.preview) return;
        $('in-go').disabled = !qv.open;
        $('in-go').addEventListener('click', startQuiz);
        var until = Date.now() + (st.retry_s || 0) * 1000;
        clearInterval(qWaitTimer);
        function wait() {
            var left = Math.ceil((until - Date.now()) / 1000);
            if (!$('in-go') || !$('in-wait')) { clearInterval(qWaitTimer); return; }
            if (left > 0) { $('in-go').disabled = true; $('in-wait').textContent = 'wait ' + left + ' s: the next attempt draws new questions'; }
            else { clearInterval(qWaitTimer); $('in-wait').textContent = ''; $('in-go').disabled = !qv.open; }
        }
        if (st.retry_s > 0) { wait(); qWaitTimer = setInterval(wait, 500); }
    }

    function quizFullscreen() {
        var el = document.documentElement;
        if (!el.requestFullscreen) return false;
        el.requestFullscreen().then(function () {
            if (navigator.keyboard && navigator.keyboard.lock) return navigator.keyboard.lock().catch(function () {});
        }).catch(function () { if (qOn && !qDone && !document.fullscreenElement) qEvent({ k: 'fs_exit', why: 'refused' }); });
        return true;
    }

    function startQuiz() {
        quizFullscreen();   // inside the click, while the browser allows it
        $('in-go').disabled = true;
        api('/api/practice/quiz/start', { method: 'POST', body: { id: qv.meta.id } }).then(function (g) {
            qv = g; qIdx = 0; qAnswers = {}; qLeaves = 0; qDone = null;
            qLoad();
            enterQuiz();
        }).catch(function (err) {
            if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(function () {});
            $('in-go').disabled = false;
            if (err.data && err.data.retry_s) { qv.state.retry_s = err.data.retry_s; quizIntro(); }
            else alertBox('error: ' + err.message);
        });
    }

    function enterQuiz() {
        qOn = true; qLocked = '';
        show('quiz');
        $('q-title').textContent = 'quiz — ' + qv.meta.id;
        $('q-who').textContent = qv.meta.title + ' · attempt ' + qv.state.attempt;
        clearInterval(qTimer);
        qTimer = setInterval(qTick, 1000);
        qTick();
        renderQuiz();
        qOpenRoom();
    }

    // ── The quiz's socket to the gateway: the lock, the events, and the heartbeat the API checks ──
    function qEvent(ev) {
        ev.t = 'e'; ev.cts = Date.now();
        if (qWsOpen) { try { qWs.send(JSON.stringify(ev)); } catch (e) {} }
        else if (qQueue.length < 100) qQueue.push(ev);
    }
    function qNotice(text, bad) { $('q-notice').textContent = text || ''; $('q-notice').className = 'notice' + (bad ? ' bad' : ''); }

    function qOpenRoom() {
        qStopRetry = false; qRetry = 0; qSession++;
        qQueue = [{ t: 'e', k: 'start', cts: Date.now() }];   // once per visit; a reconnect does not say "start" again
        clearInterval(qPingTimer);
        qPingTimer = setInterval(function () {
            if (!qWsOpen) return;
            if (Date.now() - qLastRx > 15000) { qLost(); return; }
            try { qWs.send(JSON.stringify({ t: 'ping' })); } catch (e) {}
        }, 5000);
        qConnect();
        // a browser that refuses fullscreen is told to the gateway, like the shell does; it locks with its own reason
        setTimeout(function () {
            if (qOn && !qDone && document.documentElement.requestFullscreen && !document.fullscreenElement) qEvent({ k: 'fs_exit', why: 'refused' });
        }, 900);
    }

    function qConnect() {
        if (!qOn || qDone || qStopRetry || qConnecting || qWsOpen) return;
        var session = qSession;
        qConnecting = true;
        qNotice('connecting to the practice room…');
        api('/api/practice/quiz/ticket', { method: 'POST', body: { id: qv.meta.id } }).then(function (t) {
            if (session !== qSession || !qOn) { qConnecting = false; return; }
            var mine = qWs = new WebSocket(q.get('gw') || t.url);
            setTimeout(function () { if (qWs === mine && !qWsOpen) qLost(); }, 15000);
            mine.onopen = function () { mine.send(JSON.stringify({ t: 'auth', ticket: t.ticket, cols: 80, rows: 24 })); };
            mine.onmessage = function (m) {
                if (qWs !== mine || typeof m.data !== 'string') return;
                qLastRx = Date.now();
                var msg; try { msg = JSON.parse(m.data); } catch (e) { return; }
                if (msg.t === 'hello') {
                    qWsOpen = true; qRetry = 0; qConnecting = false; qNotice('');
                    while (qQueue.length) { var ev = qQueue.shift(); ev.queued_ms = Date.now() - ev.cts; mine.send(JSON.stringify(ev)); }
                    qFetch();
                } else if (msg.t === 'lock') {
                    qShowLock(msg);
                } else if (msg.t === 'unlocked') {
                    qHideLock(); qFetch();
                } else if (msg.t === 'bye') {
                    qBye(msg.why);
                }
            };
            mine.onclose = function () { if (qWs === mine) qLost(); };
            mine.onerror = function () {};
        }).catch(function (err) {
            qConnecting = false;
            if (err.status === 409 || err.status === 401 || err.status === 403) { qStopRetry = true; qNotice(err.status === 409 ? err.message : 'logged out: go back to the portal and log in', true); return; }
            qRetryLater();
        });
    }
    function qRetryLater() {
        clearTimeout(qRetryTimer);
        qRetry = Math.min(qRetry + 1, 5);
        qNotice('offline: reconnecting. Your answers are kept; do not reload.', true);
        $('q-submit').disabled = true;
        qRetryTimer = setTimeout(qConnect, [0, 1000, 2000, 4000, 8000, 10000][qRetry]);
    }
    function qLost() {
        var w = qWs;
        if (w) { w.onclose = w.onmessage = w.onerror = null; try { w.close(); } catch (e) {} }
        qWs = null; qWsOpen = false; qConnecting = false;
        if (!qOn || qDone || qStopRetry) return;
        qRetryLater();
    }
    function qCloseRoom(proper) {
        qSession++; clearTimeout(qRetryTimer); clearInterval(qPingTimer); clearInterval(qLockTimer);
        var w = qWs;
        qWs = null; qWsOpen = false; qConnecting = false;
        if (w) {
            w.onclose = w.onmessage = w.onerror = null;
            try { if (proper) w.send(JSON.stringify({ t: 'e', k: 'stop', cts: Date.now() })); w.close(); } catch (e) {}   // "stop": a proper exit, so the next visit is no reload
        }
        qQueue = []; qLocked = '';
        $('qfs-dialog').classList.add('hidden'); $('quiz').removeAttribute('inert');
    }
    function qBye(why) {
        if (why === 'replaced') { qStopRetry = true; qCloseRoom(false); qOn = false; clearInterval(qTimer); loadHome(); setTimeout(function () { alertBox('The quiz was opened in another tab, or a shell was opened for a drill. Only one practice page is connected at a time. Your attempt is still open: continue it from the roadmap.'); }, 300); }
        else if (why === 'exam') { leaveQuiz(false); setTimeout(function () { alertBox('An exam has started, so practice is closed until it ends.'); }, 300); }
        else if (why === 'ticket') { qStopRetry = true; qNotice('the room refused this page: reload the roadmap and try again', true); }
    }

    // while locked the page drops the questions; the server gives them back only when the lock is off
    function qFetch() {
        if (!qOn || qDone || !qv) return;
        var session = qSession;
        api('/api/practice/quiz?id=' + encodeURIComponent(qv.meta.id)).then(function (g) {
            if (session !== qSession || !qOn || qDone) return;
            qv.state = g.state;
            if (!g.state.open) { qNotice('this attempt is no longer open', true); return; }
            qv.deadline_iso = g.deadline_iso;
            if (g.gate) {
                qv.questions = null;
                if (g.gate.why === 'locked') qShowLock({ why: qLocked || 'fs_exit', left: g.gate.left });
                else { qNotice(g.gate.message, true); renderQuiz(); }
                return;
            }
            qv.questions = g.questions; qv.hint = g.hint;
            if (qIdx >= qv.questions.length) qIdx = 0;
            qNotice(''); qTick(); renderQuiz();
        }).catch(function (err) { qNotice('error: ' + err.message, true); });
    }

    function qLockTick() {
        var left = Math.max(0, Math.ceil((qLockEnd - Date.now()) / 1000));
        $('qfs-count').textContent = left > 0 ? mmss(left) : 'You can continue.';
        $('qfs-back').disabled = left > 0 || !qWsOpen;
        if (left <= 0) { clearInterval(qLockTimer); qLockTimer = null; $('qfs-back').focus(); }
    }
    function qShowLock(msg) {
        qLocked = msg.why || 'fs_exit';
        if (qv) qv.questions = null;
        renderQuiz();
        $('qfs-why').textContent = Q_LOCK_WHY[qLocked] || Q_LOCK_WHY.fs_exit;
        $('qfs-err').textContent = msg.bad === 'early' ? 'error: the wait is not over yet.' : '';
        qLockEnd = Date.now() + Math.max(0, msg.left || 0) * 1000;
        clearInterval(qLockTimer);
        qLockTick();
        if (qLockEnd > Date.now()) qLockTimer = setInterval(qLockTick, 250);
        $('qfs-dialog').classList.remove('hidden');
        $('quiz').setAttribute('inert', '');
    }
    function qHideLock() {
        qLocked = ''; clearInterval(qLockTimer); qLockTimer = null;
        $('qfs-dialog').classList.add('hidden'); $('quiz').removeAttribute('inert');
        $('qfs-err').textContent = '';
    }
    $('qfs-back').addEventListener('click', function () {
        if (!document.fullscreenElement) quizFullscreen();
        if (!qWsOpen) { $('qfs-err').textContent = 'error: not connected. Wait until the page reconnects, then try again.'; return; }
        try { qWs.send(JSON.stringify({ t: 'unlock' })); } catch (e) {}
    });

    function qTick() {
        if (!qv || !qv.deadline_iso) return;
        var left = (Date.parse(qv.deadline_iso) - Date.now()) / 1000;
        $('q-time').textContent = left > 0 ? mmss(left) : '0:00';
        $('q-time').className = 'time' + (left <= 60 ? ' bad' : left <= 120 ? ' warn' : '');
        $('q-note').textContent = left > 0 ? 'left' : 'time is up: a pass now earns half the XP';
        $('q-note').className = left > 0 ? 'muted' : 'st-bad';
    }

    function qAnswered() { return (qv.questions || []).filter(function (x) { return qAnswers[x.qid]; }).length; }

    function renderQuiz() {
        if (!qReady()) {   // connecting, or locked: the server has not given the questions (or has taken them back)
            $('q-body').innerHTML = '<p class="muted"># ' + (qLocked ? 'locked: the questions are held back until the wait ends.' : 'the questions come once this page is connected to the practice room…') + '</p>';
            $('q-count').textContent = '';
            ['q-prev', 'q-next', 'q-hint', 'q-submit'].forEach(function (id) { $(id).disabled = true; $(id).classList.toggle('hidden', !!qDone); });
            return;
        }
        var qs = qv.questions, x = qs[qIdx], removed = (qv.hint && qv.hint.q === qIdx) ? qv.hint.removed : [];
        var dots = qs.map(function (y, i) {
            return '<button class="q-dot' + (i === qIdx ? ' on' : '') + (qAnswers[y.qid] ? ' done' : '') + '" type="button" data-qi="' + i + '" aria-label="Question ' + (i + 1) + (qAnswers[y.qid] ? ', answered' : '') + '"' + (i === qIdx ? ' aria-current="step"' : '') + '>' + (i + 1) + '</button>';
        }).join('');
        $('q-body').innerHTML = '<div class="q-dots" role="group" aria-label="Questions">' + dots + '</div>' +
            '<p class="q-n">Question ' + (qIdx + 1) + ' of ' + qs.length + '</p><h2 class="q-text">' + rich(x.text) + '</h2>' +
            '<div class="choices" role="radiogroup" aria-label="Choices">' + x.choices.map(function (c) {
                var gone = removed.indexOf(c.id) >= 0, sel = qAnswers[x.qid] === c.id;
                return '<button class="choice' + (sel ? ' sel' : '') + (gone ? ' gone' : '') + '" type="button" role="radio" aria-checked="' + (sel ? 'true' : 'false') + '" data-c="' + esc(c.id) + '"' + (gone ? ' disabled' : '') + '>' +
                    '<span class="c-id">' + esc(c.id.toUpperCase()) + '</span><span class="c-text">' + rich(c.text) + '</span>' + (gone ? '<span class="c-note">removed by the hint</span>' : '') + '</button>';
            }).join('') + '</div>';
        $('q-count').textContent = qAnswered() + ' of ' + qs.length + ' answered';
        $('q-prev').disabled = qIdx === 0 || qBusy;
        $('q-next').disabled = qIdx === qs.length - 1 || qBusy;
        var hintUsed = !!qv.hint;
        $('q-hint').textContent = hintUsed ? 'Hint used (question ' + (qv.hint.q + 1) + ')' : 'Hint (1 of 1)';
        $('q-hint').disabled = (hintUsed && qv.hint.q !== qIdx) || (hintUsed && removed.length > 0) || qBusy || !!qDone;
        $('q-submit').disabled = qBusy || !!qDone || !qWsOpen;   // the server would refuse a submit with no live socket
        $('q-submit').classList.toggle('hidden', !!qDone);
        ['q-prev', 'q-next', 'q-hint'].forEach(function (id) { $(id).classList.toggle('hidden', !!qDone); });
        var first = $('q-body').querySelector('.choice:not(.gone)');
        if (first && !qBusy) { /* keep focus where it is: the page is keyboard-friendly through Tab */ }
    }

    $('q-body').addEventListener('click', function (e) {
        if (!qOn || qDone || !qReady()) return;
        var d = e.target.closest('[data-qi]');
        if (d) { qIdx = +d.getAttribute('data-qi'); renderQuiz(); return; }
        var c = e.target.closest('[data-c]');
        if (c && !c.disabled) { qAnswers[qv.questions[qIdx].qid] = c.getAttribute('data-c'); qSave(); renderQuiz(); }
    });
    document.addEventListener('keydown', function (e) {
        if (!qOn || qDone || !qReady() || !$('ask').classList.contains('hidden') || e.target.tagName === 'INPUT') return;
        var k = e.key.toLowerCase(), qs = qv.questions;
        if ('abcd'.indexOf(k) >= 0 && k.length === 1) {
            var c = qs[qIdx].choices.filter(function (y) { return y.id === k; })[0];
            var gone = qv.hint && qv.hint.q === qIdx && qv.hint.removed.indexOf(k) >= 0;
            if (c && !gone) { qAnswers[qs[qIdx].qid] = k; qSave(); renderQuiz(); }
        } else if (e.key === 'ArrowRight' && qIdx < qs.length - 1) { qIdx++; renderQuiz(); }
        else if (e.key === 'ArrowLeft' && qIdx > 0) { qIdx--; renderQuiz(); }
    });
    $('q-prev').addEventListener('click', function () { if (qIdx > 0) { qIdx--; renderQuiz(); } });
    $('q-next').addEventListener('click', function () { if (qReady() && qIdx < qv.questions.length - 1) { qIdx++; renderQuiz(); } });

    $('q-hint').addEventListener('click', function () {
        if (!qReady() || qv.hint || qBusy) return;
        var xp = qv.meta.xp, after = Math.round(xp * qv.rules.hint_share[1]);
        ask('Use the hint on question ' + (qIdx + 1) + '?', 'It takes two wrong choices away from this question. You have one hint for the whole quiz, and a pass is then worth ' + after + ' XP instead of ' + xp + '.', 'Use the hint').then(function (yes) {
            if (!yes) return;
            qBusy = true; renderQuiz();
            api('/api/practice/quiz/hint', { method: 'POST', body: { id: qv.meta.id, q: qIdx } }).then(function (r) {
                qBusy = false; qv.hint = { q: r.q, removed: r.removed };
                var cur_ = qv.questions[qIdx];
                if (r.removed.indexOf(qAnswers[cur_.qid]) >= 0) delete qAnswers[cur_.qid];   // an answer that was taken away is no answer
                qSave(); renderQuiz();
            }).catch(function (err) { qBusy = false; renderQuiz(); $('q-status').textContent = 'error: ' + err.message; if (err.status === 423) qFetch(); });
        });
    });

    $('q-submit').addEventListener('click', function () {
        if (!qReady()) return;
        var left = qv.questions.length - qAnswered();
        var go = function () {
            qBusy = true; renderQuiz(); $('q-status').textContent = 'marking…';
            api('/api/practice/quiz/submit', { method: 'POST', body: { id: qv.meta.id, answers: qAnswers, leaves: qLeaves } }).then(function (r) {
                qBusy = false; qDone = r; qv.state = r.state;
                try { sessionStorage.removeItem(qKey()); } catch (e) {}
                clearInterval(qTimer);
                qCloseRoom(true);   // the attempt is over: a proper exit from the room
                quizResult(r);
            }).catch(function (err) { qBusy = false; renderQuiz(); $('q-status').textContent = 'error: ' + err.message; if (err.status === 423) qFetch(); });
        };
        if (left) ask('Submit with ' + left + ' unanswered?', 'An unanswered question counts as wrong. You cannot change your answers after this.', 'Submit').then(function (y) { if (y) go(); });
        else ask('Submit your answers?', 'You cannot change them after this.', 'Submit').then(function (y) { if (y) go(); });
    });

    function quizResult(r) {
        var res = r.result, a = r.award, m = qv.meta;
        var h = '<div class="q-result ' + (res.passed ? 'pass' : 'fail') + '"><p class="q-score">' + esc(res.score) + ' of ' + esc(res.total) + '</p>' +
            '<h2>' + (res.passed ? 'Passed' : 'Not yet') + '</h2><p class="muted">You need ' + esc(res.pass_mark) + ' of ' + esc(res.total) + ' to pass.' + (res.late ? ' The countdown had ended.' : '') + '</p>';
        if (a) h += '<p class="xp-big">' + (a.xp > 0 ? '+' : '') + esc(a.xp) + ' XP</p><ul class="rules">' + a.reasons.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '<li>' + esc(a.total) + ' XP in total.</li></ul>';
        if (a && a.rank_up) { var look = RANK_LOOK[a.rank] || ['?', '--gray']; h += '<div class="new-thing">' + shield(look[0], look[1], 44) + '<span>New rank: <b>' + esc(a.rank) + '</b></span></div>'; }
        if (a) (a.badges || []).forEach(function (b) { h += '<div class="new-thing">' + hexagon(initials(b), '--cyan', true) + '<span>New badge: <b>' + esc(b) + '</b></span></div>'; });
        if (res.review.length) h += '<div class="sec">// skills to review</div><p>' + res.review.map(function (x) { return '<span class="skill none">' + esc(x.title) + '</span>'; }).join(' ') + '</p>' +
            '<p class="comment"># you are not told which choice was right. A drill on the same skill is the best way to learn it.</p>';
        h += '<div class="row"><button class="btn btn-fill" type="button" id="qr-map">Back to the roadmap</button><button class="btn btn-go" type="button" id="qr-again">' + (res.passed ? 'Play again (no XP)' : 'Try again') + '</button><span class="muted" id="qr-wait"></span></div></div>';
        $('q-status').textContent = '';
        renderQuiz();   // sets the buttons for a finished quiz, and draws the question under the result …
        $('q-body').innerHTML = h;   // … which the result then replaces
        $('qr-map').addEventListener('click', leaveQuiz);
        var until = Date.now() + (r.state.retry_s || 0) * 1000;
        function wait() {
            var left = Math.ceil((until - Date.now()) / 1000), b = $('qr-again');
            if (!b) { clearInterval(qWaitTimer); return; }
            if (left > 0) { b.disabled = true; $('qr-wait').textContent = 'wait ' + left + ' s: the next attempt draws new questions'; }
            else { b.disabled = false; $('qr-wait').textContent = ''; clearInterval(qWaitTimer); }
        }
        clearInterval(qWaitTimer);
        if (r.state.retry_s > 0) { wait(); qWaitTimer = setInterval(wait, 500); }
        $('qr-again').addEventListener('click', function () {
            $('qr-again').disabled = true;
            api('/api/practice/quiz/start', { method: 'POST', body: { id: m.id } }).then(function (g) {
                qv = g; qIdx = 0; qAnswers = {}; qLeaves = 0; qDone = null; qLoad();
                enterQuiz();
            }).catch(function (err) { $('qr-again').disabled = false; $('qr-wait').textContent = 'error: ' + err.message; });
        });
    }

    function leaveQuiz(proper) {
        // "stop" tells the gateway this is a proper exit (not a reload), so coming back later does not start a wait
        qCloseRoom(proper !== false);   // the "map" button passes its click event, which is not false
        qOn = false; qDone = null;
        clearInterval(qTimer); clearInterval(qWaitTimer);
        if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(function () {});
        loadHome();
    }
    $('q-leave').addEventListener('click', function () {
        if (qDone || !qv || !qv.state.open) { leaveQuiz(); return; }
        ask('Leave the quiz?', 'Your attempt stays open and the countdown keeps running. Your answers are kept in this tab, and you can continue from the roadmap. The questions come back only while this page is connected to the room.', 'Leave').then(function (y) { if (y) leaveQuiz(); });
    });

    // The record and the lock: leaving fullscreen goes to the gateway, which starts the wait and says so; this page
    // then drops the questions (qShowLock). The side panel is not watched here: the quiz has no terminal to cover.
    document.addEventListener('fullscreenchange', function () {
        if (!qOn || qDone) return;
        if (!document.fullscreenElement) { qLeaves++; qEvent({ k: 'fs_exit' }); }
        else qEvent({ k: 'fs_enter' });
        qSave();
    });
    var qAway = null;
    function qLeave(why) { if (!qOn || qDone || qAway) return; qAway = { at: Date.now(), why: why }; qEvent({ k: 'leave', why: why }); }
    function qBack() {
        if (!qOn || qDone || !qAway || document.hidden || !document.hasFocus()) return;
        qEvent({ k: 'back', away_ms: Date.now() - qAway.at, why: qAway.why }); qAway = null;
    }
    document.addEventListener('visibilitychange', function () { if (!qOn || qDone) return; if (document.hidden) { qLeaves++; qSave(); qLeave('tab'); } else qBack(); });
    window.addEventListener('blur', function () { setTimeout(function () { if (qOn && !qDone && !document.hasFocus()) qLeave('window'); }, 50); });
    window.addEventListener('focus', qBack);
    window.addEventListener('beforeunload', function (e) { if (qOn && !qDone) { e.preventDefault(); e.returnValue = ''; } });

    // ── Replay of my own session ────────────────────────
    var rp = null;
    $('cl-replay').addEventListener('click', function () { openReplay(cur.meta.id); });
    function openReplay(id) {
        $('replay').classList.remove('hidden');
        api('/api/practice/replays?id=' + encodeURIComponent(id)).then(function (r) {
            if (!r.casts.length) { $('rp-pick').innerHTML = '<option>no recording yet</option>'; return; }
            $('rp-pick').innerHTML = r.casts.map(function (c) {
                return '<option value="' + esc(c.name) + '">' + esc(new Date(c.start * 1000).toLocaleString('en-GB', { hour12: false })) + '</option>';
            }).reverse().join('');
            rp = { id: id, speed: 4 };
        }).catch(function (err) { $('rp-note').textContent = 'error: ' + err.message; });
    }
    $('rp-close').addEventListener('click', function () { stopReplay(); $('replay').classList.add('hidden'); });
    document.querySelectorAll('#rp-speeds [data-s]').forEach(function (b) {
        b.addEventListener('click', function () {
            if (rp) rp.speed = +b.getAttribute('data-s');
            document.querySelectorAll('#rp-speeds [data-s]').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        });
    });
    function stopReplay() { if (rp && rp.timer) clearTimeout(rp.timer); }
    $('rp-play').addEventListener('click', function () {
        if (!rp) return;
        stopReplay();
        api('/api/practice/cast?id=' + encodeURIComponent(rp.id) + '&name=' + encodeURIComponent($('rp-pick').value), { raw: true }).then(function (text) {
            var lines = text.split('\n').filter(Boolean), head = JSON.parse(lines[0]);
            var frames = lines.slice(1).map(function (l) { try { return JSON.parse(l); } catch (e) { return null; } }).filter(function (f) { return f && f[1] === 'o'; });
            if (!rp.term) {
                rp.term = new window.Terminal({ fontFamily: '"Fira Code", monospace', fontSize: 14, disableStdin: true, cursorBlink: false, scrollback: 2000,
                    theme: { background: '#0d1117', foreground: '#c9d1d9' } });
                rp.term.open($('rp-term'));
            }
            rp.term.reset();
            rp.term.resize(Math.min(200, head.width || 100), Math.min(60, head.height || 30));
            var i = 0;
            (function step() {
                if (i >= frames.length) return;
                rp.term.write(frames[i][2]);
                var gap = i + 1 < frames.length ? (frames[i + 1][0] - frames[i][0]) : 0;
                i += 1;
                rp.timer = setTimeout(step, Math.min(2000, gap * 1000) / rp.speed);   // pauses over 2 s are shortened
            })();
        }).catch(function (err) { $('rp-note').textContent = 'error: ' + err.message; });
    });

    // ── Terminal ─────────────────────────────────────────
    function makeTerm() {
        term = new window.Terminal({
            fontFamily: '"Fira Code", ui-monospace, Consolas, monospace', fontSize: 16, lineHeight: 1.25, cursorBlink: false, scrollback: 5000,
            theme: { background: '#0d1117', foreground: '#c9d1d9', cursor: '#00ff41', cursorAccent: '#0d1117', selectionBackground: '#00d4ff40',
                black: '#0d1117', brightBlack: '#8b949e', red: '#ff5f56', brightRed: '#ff7b72', green: '#00cc33', brightGreen: '#00ff41',
                yellow: '#ffb627', brightYellow: '#ffd166', blue: '#6cb6ff', brightBlue: '#9ccaff', magenta: '#d2a8ff', brightMagenta: '#e2c5ff',
                cyan: '#00d4ff', brightCyan: '#7ee7ff', white: '#c9d1d9', brightWhite: '#ffffff' }
        });
        fit = new window.FitAddon.FitAddon();
        term.loadAddon(fit);
        term.open($('term'));
        fitNow();
        term.onData(function (d) { if (wsOpen) ws.send(JSON.stringify({ t: 'i', d: d })); });
        term.onResize(function (sz) { if (wsOpen) ws.send(JSON.stringify({ t: 'r', cols: sz.cols, rows: sz.rows })); });
        window.addEventListener('resize', fitNow);
        $('term').addEventListener('paste', function (e) {
            var text = (e.clipboardData && e.clipboardData.getData('text')) || '';
            sendEvent({ k: 'paste', n: text.length });
        }, true);
    }
    function fitNow() {
        try { fit.fit(); } catch (e) {}
        if (term && term.cols < 80) term.resize(80, term.rows);
    }

    function openTerminal() {
        if (!term) makeTerm();
        if (stopReconnect || connecting || wsOpen || !started) return;
        if (!offlineAt) { $('s-conn').textContent = 'connecting…'; $('s-conn').className = 'conn'; }
        connecting = true;
        api('/api/practice/ticket', { method: 'POST', body: { id: cur.meta.id } }).then(function (t) {
            var url = q.get('gw') || t.url;
            var mine = ws = new WebSocket(url);
            ws.binaryType = 'arraybuffer';
            setTimeout(function () { if (ws === mine && !wsOpen && !mine._queued) lost(); }, 15000);
            ws.onopen = function () { ws.send(JSON.stringify({ t: 'auth', ticket: t.ticket, cols: term.cols, rows: term.rows })); };
            ws.onmessage = function (m) {
                lastRx = Date.now();
                if (typeof m.data !== 'string') { term.write(new Uint8Array(m.data)); return; }
                var msg; try { msg = JSON.parse(m.data); } catch (e) { return; }
                if (msg.t === 'hello') {
                    wsOpen = true; retry = 0; connecting = false;
                    $('s-conn').textContent = '';
                    netBack(); flushQueue(); term.focus();
                } else if (msg.t === 'queue') {
                    mine._queued = true;
                    $('s-conn').textContent = 'the room is full: you are number ' + msg.pos + ' in the queue';
                    $('s-conn').className = 'conn';
                } else if (msg.t === 'bye') {
                    onBye(msg.why);
                } else if (msg.t === 'lock') {
                    showLock(msg.why, msg.bad, msg);
                } else if (msg.t === 'unlocked') {
                    locked = ''; stopWait(); applyCover();
                } else if (msg.t === 'note' && msg.what === 'shell_end') {
                    term.write('\r\n\x1b[33m[the shell ended; a new one opens]\x1b[0m\r\n');
                }
            };
            ws.onclose = lost;
            ws.onerror = function () {};
        }).catch(function (err) {
            connecting = false;
            if (err.status === 409) { stopReconnect = true; $('s-conn').textContent = err.message; $('s-conn').className = 'conn bad'; return; }
            if (err.status === 401 || err.status === 403) { stopReconnect = true; $('s-conn').textContent = 'logged out: go back to the portal and log in'; $('s-conn').className = 'conn bad'; return; }
            reconnect();
        });
    }

    function onBye(why) {
        if (why === 'replaced') { stopReconnect = true; $('taken-dialog').classList.remove('hidden'); }
        else if (why === 'exam') {
            leaveRoom();
            setTimeout(function () { alertBox('An exam has started, so practice is closed until it ends. Your files are kept.'); }, 300);
        } else if (why === 'idle') {
            stopReconnect = true;
            $('s-conn').textContent = 'disconnected after 15 minutes without typing';
            $('s-conn').className = 'conn bad';
            term.write('\r\n\x1b[33m[disconnected after 15 minutes without typing: press any key to reconnect]\x1b[0m\r\n');
            var d = term.onData(function () { d.dispose(); stopReconnect = false; retry = 0; openTerminal(); });
        } else if (why === 'shell_end') {
            if (ws) { ws.onclose = ws.onmessage = ws.onerror = null; }
            ws = null; wsOpen = false; connecting = false;
            setTimeout(openTerminal, 500);
        } else if (why === 'unavailable') {
            $('s-conn').textContent = 'the server refused the shell; tell the instructor'; $('s-conn').className = 'conn bad';
        }
    }

    function reconnect() {
        clearTimeout(retryTimer);
        retry = Math.min(retry + 1, 5);
        var wait = [0, 1000, 2000, 4000, 8000, 10000][retry];
        $('s-conn').textContent = 'offline: do not reload';
        $('s-conn').className = 'conn bad';
        nextTry = Date.now() + wait;
        retryTimer = setTimeout(openTerminal, wait);
        netDown();
    }
    function lost() {
        var w = ws, was = wsOpen;
        if (w) { w.onclose = w.onmessage = w.onerror = null; try { w.close(); } catch (e) {} }
        ws = null; wsOpen = false; connecting = false;
        if (stopReconnect || !started) return;
        if (was) term.write('\r\n\x1b[33m[connection lost: it reconnects by itself. Do not reload the page.]\x1b[0m\r\n');
        reconnect();
    }
    setInterval(function () {
        if (!wsOpen) return;
        if (Date.now() - lastRx > 15000) { lost(); return; }
        try { ws.send(JSON.stringify({ t: 'ping' })); } catch (e) {}
    }, 5000);
    window.addEventListener('offline', function () { if (wsOpen) lost(); });
    window.addEventListener('online', tryNow);
    function tryNow() { if (!started || stopReconnect || wsOpen || connecting) return; clearTimeout(retryTimer); openTerminal(); }
    $('nd-try').addEventListener('click', tryNow);
    function netDown() {
        if (!offlineAt) offlineAt = Date.now();
        if (!netTimer && $('net-dialog').classList.contains('hidden')) netTimer = setTimeout(showNet, 3000);
    }
    function showNet() {
        netTimer = null;
        if (wsOpen || stopReconnect || !started) return;
        $('net-dialog').classList.remove('hidden');
        clearInterval(netTick);
        netTick = setInterval(updateNet, 1000);
        updateNet();
    }
    function updateNet() {
        if ($('net-dialog').classList.contains('hidden')) return;
        var away = offlineAt ? Math.round((Date.now() - offlineAt) / 1000) : 0;
        var why = navigator.onLine === false ? 'This computer is offline: check the Wi-Fi or the cable.' : 'The server cannot be reached.';
        var next = connecting ? ' Connecting…' : ' Trying again in ' + Math.max(0, Math.ceil((nextTry - Date.now()) / 1000)) + ' s.';
        $('nd-status').textContent = why + next + ' Offline for ' + mmss(away) + '.';
        $('nd-try').disabled = connecting;
    }
    function netBack() {
        clearTimeout(netTimer); netTimer = null; clearInterval(netTick);
        $('net-dialog').classList.add('hidden');
        offlineAt = 0;
    }
    $('tk-back').addEventListener('click', function () { $('taken-dialog').classList.add('hidden'); stopReconnect = false; retry = 0; openTerminal(); });

    // ── Events for the record, and the lock ─────────────
    function sendEvent(ev) {
        ev.t = 'e';
        ev.cts = Date.now();
        if (wsOpen) ws.send(JSON.stringify(ev));
        else if (queue.length < 200) queue.push(ev);
    }
    function flushQueue() {
        while (queue.length && wsOpen) { var ev = queue.shift(); ev.queued_ms = Date.now() - ev.cts; ws.send(JSON.stringify(ev)); }
    }
    function leave(why) { if (!started || awayStart) return; awayStart = Date.now(); awayWhy = why; sendEvent({ k: 'leave', why: why }); }
    function back() {
        if (!started || !awayStart || document.hidden || !document.hasFocus()) return;
        var ms = Date.now() - awayStart;
        awayStart = null;
        sendEvent({ k: 'back', away_ms: ms, why: awayWhy });
        if (term) term.focus();
    }
    document.addEventListener('visibilitychange', function () { if (document.hidden) leave('tab'); else back(); });
    window.addEventListener('blur', function () { setTimeout(function () { if (!document.hasFocus()) leave('window'); }, 50); });
    window.addEventListener('focus', back);
    function notice(text) {
        var el = $('s-notice');
        el.innerHTML = '<i class="ico" aria-hidden="true">⚠️</i>' + esc(text);
        clearTimeout(noticeTimer);
        noticeTimer = setTimeout(function () { el.textContent = ''; }, 8000);
    }

    document.addEventListener('fullscreenchange', function () {
        if (!started) return;
        if (!document.fullscreenElement) {
            sendEvent({ k: 'fs_exit' });
            if (!locked) { $('fs-dialog').classList.remove('hidden'); $('fs-back').focus(); }
        } else {
            sendEvent({ k: 'fs_enter' });
            $('fs-dialog').classList.add('hidden');
            if (term) { fitNow(); term.focus(); }
        }
    });
    $('fs-back').addEventListener('click', function () { if (!goFullscreen()) $('fs-dialog').classList.add('hidden'); });

    function goFullscreen() {
        var el = document.documentElement;
        if (!el.requestFullscreen) return false;
        el.requestFullscreen().then(function () {
            if (!(navigator.keyboard && navigator.keyboard.lock)) { sendEvent({ k: 'kb_lock', detail: 'unsupported' }); return; }
            return navigator.keyboard.lock().then(function () { sendEvent({ k: 'kb_lock', detail: 'on' }); });
        }).catch(function () { if (!document.fullscreenElement && started) sendEvent({ k: 'fs_exit', why: 'refused' }); });
        return true;
    }

    var waitEnd = 0, waitTimer = null;
    function stopWait() { clearInterval(waitTimer); waitTimer = null; $('lk-werr').textContent = ''; }
    function waitTick() {
        var left = Math.max(0, Math.ceil((waitEnd - Date.now()) / 1000));
        $('lk-count').textContent = left > 0 ? mmss(left) : 'You can continue.';
        $('lk-go').disabled = left > 0;
        if (left <= 0) { clearInterval(waitTimer); waitTimer = null; $('lk-go').focus(); }
    }
    function showLock(why, bad, msg) {
        locked = why || 'fs_exit';
        $('fs-dialog').classList.add('hidden');
        $('lk-why').textContent = LOCK_WHY[locked] || LOCK_WHY.fs_exit;
        waitEnd = Date.now() + Math.max(0, (msg && msg.left) || 0) * 1000;
        $('lk-werr').textContent = bad === 'early' ? 'error: the wait is not over yet.' : '';
        clearInterval(waitTimer);
        waitTick();
        if (waitEnd > Date.now()) waitTimer = setInterval(waitTick, 250);
        applyCover();
    }
    $('lk-go').addEventListener('click', function () {
        if (!document.fullscreenElement) goFullscreen();
        if (!wsOpen) { $('lk-werr').textContent = 'error: not connected. Wait until the terminal reconnects, then try again.'; return; }
        ws.send(JSON.stringify({ t: 'unlock' }));
    });

    function screensNow() {
        var x = window.screen && window.screen.isExtended;
        return x === true ? 'extended' : x === false ? 'single' : 'unknown';
    }
    if (window.screen && window.screen.addEventListener) {
        window.screen.addEventListener('change', function () { if (started) { sendEvent({ k: 'screens', detail: screensNow() }); if (screensNow() === 'extended') notice('A second screen was connected. This is recorded.'); } });
    }

    // Side panel: the page gets narrower while the window keeps its size (see exam.js).
    function measure() {
        var dpr = window.devicePixelRatio || 1;
        var r = (window.innerWidth * dpr) / Math.max(1, window.outerWidth);
        return { r: r, dpr: dpr, last: r };
    }
    var panelTimer = null;
    window.addEventListener('resize', function () { checkPanel(); clearTimeout(panelTimer); panelTimer = setTimeout(checkPanel, 400); });
    function applyCover() {
        var on = !!panel || !!locked;
        $('panel-cover').classList.toggle('hidden', !panel);
        $('lock-dialog').classList.toggle('hidden', !locked);
        if (on === covered) return;
        covered = on;
        $('room').classList.toggle('covered', on);
        if (on) {
            $('room').setAttribute('inert', '');
            $('room').setAttribute('aria-hidden', 'true');
            $('paper-body').innerHTML = '';
        } else {
            $('room').removeAttribute('inert');
            $('room').removeAttribute('aria-hidden');
            if (started && cur) renderPaper();
            if (term) { fitNow(); term.focus(); }
        }
    }
    function checkPanel() {
        if (!started || !view || !window.outerWidth) return;
        var m = measure();
        if (m.dpr !== view.dpr) { view.r = panel ? view.r * m.r / view.last : m.r; view.dpr = m.dpr; view.last = m.r; return; }
        view.last = m.r;
        if (!panel) {
            if (m.r > view.r) view.r = m.r;
            if (m.r < view.r * 0.85) { panel = { at: Date.now() }; applyCover(); sendEvent({ k: 'panel_open', n: Math.round(100 * (1 - m.r / view.r)) }); }
        } else if (m.r > view.r * 0.95) {
            sendEvent({ k: 'panel_close', away_ms: Date.now() - panel.at });
            panel = null;
            applyCover();
        }
    }

    window.addEventListener('beforeunload', function (e) { if (started) { e.preventDefault(); e.returnValue = ''; } });
    $('paper-btn').addEventListener('click', function () {
        var open = $('paper').classList.toggle('open');
        this.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    if (!API) { screen('bash — practice', '<p class="err">error: the site has no server address (config.js).</p>'); return; }
    if (!window.Terminal) { screen('bash — practice', '<p class="err">error: the terminal library did not load. Reload the page.</p>'); return; }
    window.practicePage = { state: function () { return { home: home, cur: cur, started: started, locked: locked, wsOpen: wsOpen }; } };
    loadHome();
})();
