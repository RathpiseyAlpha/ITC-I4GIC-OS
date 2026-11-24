/* Exam room page: login, waiting room, the paper, the terminal (xterm.js over the gateway websocket),
   and the proctoring events (left the page, came back, paste, fullscreen, a second screen, a side panel).
   See server/examroom/README.md. */
(function () {
    'use strict';

    var API = ((typeof CONFIG !== 'undefined' && CONFIG.server && CONFIG.server.url) || '').replace(/\/+$/, '');
    var q = new URLSearchParams(location.search);
    if (q.get('api')) API = q.get('api').replace(/\/+$/, '');   // testing against a local API
    var TOKEN_KEY = 'examToken';
    var PAGE = 'exam.html';
    var AS = q.get('as') || '';   // the instructor's "view as student": the paper with this student's values, no terminal
    // Safe Exam Browser opens this page directly and blocks the portal's other sites, so it keeps a login form here.
    var SEB = /\bSEB\//.test(navigator.userAgent);
    var token = sessionStorage.getItem('authToken') || sessionStorage.getItem(TOKEN_KEY) || '';
    var state = null, skew = 0, started = false, term = null, fit = null, ws = null;
    var wsOpen = false, retry = 0, retryTimer = null, stopReconnect = false;
    var queue = [], awayStart = null, awayWhy = '', noticeTimer = null, pollTimer = null, tickTimer = null;
    var largePaste = 200, rained = false;
    var panel = null, view = null, lastScreens = '';
    var locked = '', covered = false;
    var connecting = false, lastRx = 0, nextTry = 0, offlineAt = 0, netTimer = null, netTick = null;   // locked: why the gateway locked the exam ('' = not locked)
    var LOCK_WHY = { fs_exit: 'You left fullscreen.', restart: 'The exam was started again (the page was reloaded or opened somewhere else).',
        panel: 'A side panel was opened beside the exam.', leave: 'You left the exam page.',
        fs_refused: 'This browser did not go fullscreen. Use Chrome or Edge and allow fullscreen.' };

    function $(id) { return document.getElementById(id); }
    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    // Paper text: escaped, then `code` and **bold** marks.
    function rich(s) {
        return esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    }
    function fmt(sec) {
        sec = Math.max(0, Math.floor(sec));
        var h = Math.floor(sec / 3600), m = Math.floor(sec % 3600 / 60), s = sec % 60;
        function p(n) { return (n < 10 ? '0' : '') + n; }
        return p(h) + ':' + p(m) + ':' + p(s);
    }
    function now() { return Date.now() + skew; }

    function api(path, opts) {
        opts = opts || {};
        var headers = { 'Content-Type': 'application/json' };
        if (token) headers.Authorization = 'Bearer ' + token;
        var ctl = window.AbortController ? new AbortController() : null;
        var timer = ctl ? setTimeout(function () { ctl.abort(); }, 20000) : null;
        return fetch(API + path, { method: opts.method || 'GET', headers: headers, mode: 'cors',
            body: opts.body ? JSON.stringify(opts.body) : undefined, signal: ctl ? ctl.signal : undefined })
            .then(function (r) {
                clearTimeout(timer);
                return r.json().catch(function () { return {}; }).then(function (data) {
                    if (!r.ok) { var e = new Error(data.error || ('HTTP ' + r.status)); e.status = r.status; throw e; }
                    return data;
                });
            });
    }

    // ── Card screens ──────────────────────────────────────
    function screen(title, html) {
        $('exam').classList.add('hidden');
        $('screen').classList.remove('hidden');
        $('screen-title').textContent = title;
        $('screen-body').innerHTML = html;
    }

    // One login for the whole site: the portal's. Without a valid one, go to the portal's login page, which comes
    // back here afterwards (index.html?next=...).
    function toPortal() {
        sessionStorage.removeItem('examToken');
        location.replace('index.html?next=' + encodeURIComponent(PAGE + location.search));
    }

    function showLogin(msg) {
        if (!SEB) { toPortal(); return; }
        screen('bash — login',
            '<p class="prompt"><span class="p-host">itc-os</span> exam room</p>' +
            '<form id="login" autocomplete="on">' +
            '<div class="field"><label for="lu">server account</label><input class="input" id="lu" autocomplete="username" required></div>' +
            '<div class="field"><label for="lp">password</label><input class="input" id="lp" type="password" autocomplete="current-password" required></div>' +
            '<div class="row"><button class="btn btn-fill" type="submit">Log in</button><span class="muted">The same password as for SSH.</span></div>' +
            (msg ? '<p class="err" role="alert">' + esc(msg) + '</p>' : '') + '</form>');
        $('lu').focus();
        $('login').addEventListener('submit', function (e) {
            e.preventDefault();
            var btn = e.target.querySelector('button');
            btn.disabled = true;
            api('/api/auth/login', { method: 'POST', body: { username: $('lu').value.trim(), password: $('lp').value } })
                .then(function (d) {
                    token = d.token;
                    sessionStorage.setItem(TOKEN_KEY, token);
                    loadState();
                })
                .catch(function (err) { showLogin('error: ' + err.message); });
        });
    }

    function rulesList(exam) {
        return '<ul class="rules">' +
            '<li>' + esc(exam.duration_min) + ' minutes, ' + esc(exam.parts.length) + ' parts, ' + esc(exam.total) + ' marks. Labs 1 to 4.</li>' +
            '<li>You work in a shell on the course server, in <code>~/' + esc(exam.folder) + '/</code>. Your files are collected when the time is up.</li>' +
            '<li>No AI and no other websites. Everything you type in the exam terminal is recorded.</li>' +
            '<li>The page notes when you leave it, leave fullscreen, open a side panel (such as an AI assistant), use a second screen, ' +
            'or paste a long text. The instructor sees those notes.</li>' +
            lockRule(exam.lock_on || [], exam.lock_mode) +
            '<li><b>Before you start</b>, connect to the network you will use for the whole exam (Wi-Fi or cable) and check it works. ' +
            'Changing the network during the exam means leaving fullscreen' +
            ((exam.lock_on || []).indexOf('fs_exit') >= 0 ? ', which locks the exam.' : '.') + '</li>' +
            '<li>If the network drops, wait: the page reconnects by itself, and your shell and files are kept. Do not reload the page.</li></ul>';
    }

    function lockRule(on, mode) {
        if (on.indexOf('fs_exit') < 0) return '<li>If the page reloads, open it again: your shell and files are still there.</li>';
        var also = (on.indexOf('panel') >= 0 ? ', open a side panel' : '') + (on.indexOf('leave') >= 0 ? ', switch to another window or tab' : '');
        return '<li><b>The exam locks</b> if you leave fullscreen' + also + ', reload the page, or open it in another tab or on another computer. ' +
            (mode === 'wait'
                ? 'Then you wait before you can continue, and the wait doubles each time you leave again today. '
                : 'Then raise your hand: the invigilator gives you a code to unlock it. ') +
            'Your shell and files are kept, but the timer keeps running.</li>';
    }

    function render() {
        var s = state;
        if (!s.exam) { screen('bash — exam room', '<p class="title">No exam is set up</p><p class="muted"># nothing to do here yet.</p>'); return; }
        largePaste = s.exam.large_paste_chars || 200;
        if (AS && s.me.admin) { preview(); return; }
        if (s.exam.rain && !rained) { rained = true; rain(); }
        var who = s.me.id ? (s.me.id + ' ' + s.me.name) : s.me.user;
        var admin = s.me.admin ? '<p><a class="btn btn-tool" href="exam-board.html' + (q.get('api') ? '?api=' + encodeURIComponent(API) : '') + '">Open the instructor board ▶</a></p>' : '';
        if (!s.me.participant && !s.me.admin) {
            screen('bash — exam room', '<p class="title">' + esc(s.exam.title) + '</p><p class="err">error: this account (' + esc(s.me.user) +
                ') is not on the exam roster. Ask the invigilator.</p>' + logoutLink());
            return;
        }
        if (!s.seb_ok) {
            screen('bash — exam room', '<p class="title">' + esc(s.exam.title) + '</p><p class="err">error: open this exam in Safe Exam Browser, with the configuration the invigilator gave you.</p>' + logoutLink());
            return;
        }
        if (!s.me.participant) {
            screen('bash — exam room', '<p class="title">' + esc(s.exam.title) + '</p><p>Signed in as <span class="p-user">' + esc(s.me.user) +
                '</span>, an instructor account. Phase: <b>' + esc(s.phase) + '</b>.</p>' + admin + logoutLink());
            return;
        }
        if (s.phase === 'sealed') {
            screen('bash — exam room', '<p class="prompt"><span class="p-user">' + esc(s.me.user) + '</span>@<span class="p-host">itc-os</span>:<span class="p-path">~</span>$ wait</p>' +
                '<p class="title">' + esc(s.exam.title) + '</p><p>' + esc(who) + '</p>' + rulesList(s.exam) + screensWarning() +
                '<p class="muted"># the paper opens when the invigilator starts the exam. This page checks every 5 seconds.</p>' + logoutLink());
            schedulePoll(5000);
            return;
        }
        if (s.phase === 'ended' || s.phase === 'closed') {
            finish();
            return;
        }
        if (s.phase === 'open' && !started && s.paper_error) {   // the draw of this student cannot be read: never start on a guess
            screen('bash — exam room', '<p class="title">' + esc(s.exam.title) + '</p><p>' + esc(who) + '</p><p class="err">error: ' + esc(s.paper_error) + '</p>' + logoutLink());
            schedulePoll(15000);
            return;
        }
        if (s.phase === 'open' && !started) {
            screen('bash — exam room', '<p class="title">' + esc(s.exam.title) + '</p><p>' + esc(who) + '</p>' + rulesList(s.exam) + screensWarning() +
                '<div class="row"><button class="btn btn-fill" id="go" type="button">Start the exam</button>' +
                '<span class="muted">The page goes fullscreen.</span></div>' + logoutLink());
            $('go').addEventListener('click', start);
            schedulePoll(15000);
            return;
        }
        if (started) updateExam();
    }

    function preview() {
        var s = state;
        var back = new URLSearchParams(location.search); back.delete('as');
        var link = 'exam-board.html' + (back.toString() ? '?' + back.toString() : '');
        if (!s.paper) {
            screen('bash — exam room', '<p class="err">' + esc(AS) + ' is not on the exam roster.</p><p><a class="btn btn-tool" href="' + esc(link) + '">← back to the board</a></p>');
            return;
        }
        $('screen').classList.add('hidden');
        $('exam').classList.remove('hidden');
        renderPaper();
        updateExam();
        $('s-who').textContent = 'Viewing as ' + (s.me.id || s.me.user) + ' ' + (s.me.name || '') + ' (read-only, phase ' + s.phase + ')';
        $('s-conn').innerHTML = '<a href="' + esc(link) + '">← back to the board</a>';
        $('term-title').textContent = 'no terminal in the preview';
        var checks = s.checks || {}, rows = '';
        Object.keys(checks).forEach(function (p) {
            checks[p].forEach(function (i) {
                var mark = i.ok === null ? (i.present ? 'written answer' : 'missing') : (i.ok ? '✅ right' : (i.present ? '❌ not right' : 'missing'));
                rows += '<tr><td>' + esc(i.id) + '</td><td>' + esc(mark) + '</td><td class="muted">' + esc(i.note || '') + '</td></tr>';
            });
        });
        $('term').innerHTML = '<div style="padding:12px 16px;overflow:auto;height:100%"><p class="muted"># the checks on this student\'s folder now, as on the board</p>' +
            '<table class="tbl"><thead><tr><th>Task</th><th>Check</th><th>Note</th></tr></thead><tbody>' + (rows || '<tr><td colspan="3" class="muted">no checks yet</td></tr>') + '</tbody></table></div>';
        if (s.end) { clearInterval(tickTimer); tickTimer = setInterval(tick, 1000); tick(); }
    }

    function screensWarning() {
        return screensNow() === 'extended' ? '<p class="err" role="alert">This computer has a second screen connected. ' +
            'Disconnect it, or close everything on it, before you start. The instructor sees that a second screen is connected.</p>' : '';
    }

    function logoutLink() {
        return '<p class="row" style="margin-top:20px"><a class="btn btn-tool" href="index.html#browse">← menu</a>' +
            '<button class="btn-link" type="button" onclick="examLogout()">log out ↩</button></p>';
    }
    window.examLogout = function () {
        api('/api/auth/logout', { method: 'POST' }).catch(function () {});
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem('authToken');
        token = '';
        showLogin('');
    };

    function finish() {
        stopReconnect = true;
        if (ws) { try { ws.close(); } catch (e) {} }
        clearInterval(tickTimer);
        if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(function () {});
        $('fs-dialog').classList.add('hidden');
        clearTimeout(netTimer); clearInterval(netTick); $('net-dialog').classList.add('hidden');
        if (panel || locked) { panel = null; locked = ''; applyCover(); }
        started = false;
        screen('bash — exam room', '<p class="title">Time is up</p><p>Your terminal is closed. The files in <code>~/' +
            esc(state.exam.folder) + '/</code> are collected by the instructor; you do not need to do anything else.</p>' +
            '<p class="muted"># you can close this window.</p><p><a class="btn btn-tool" href="index.html#browse">← menu</a></p>');
    }

    // ── State polling (also keeps the login session alive) ──
    function schedulePoll(ms) {
        clearTimeout(pollTimer);
        pollTimer = setTimeout(loadState, ms);
    }

    function loadState() {
        if (!token) { showLogin(''); return; }
        api('/api/exam/state' + (AS ? '?user=' + encodeURIComponent(AS) : '')).then(function (s) {
            state = s;
            if (s.now) skew = Date.parse(s.now) - Date.now();
            render();
            if (started) schedulePoll(15000);
        }).catch(function (err) {
            if (err.status === 403 || err.status === 401) {
                sessionStorage.removeItem(TOKEN_KEY);
                sessionStorage.removeItem('authToken');
                token = '';
                if (started) { $('s-conn').textContent = 'logged out: reload and log in'; $('s-conn').className = 'conn bad'; return; }
                showLogin('Your login expired. Log in again.');
            } else {
                if (!started) screen('bash — exam room', '<p class="err">error: could not reach the exam server. Check the network; this page tries again in 10 seconds.</p>');
                schedulePoll(10000);
            }
        });
    }

    // ── The exam ─────────────────────────────────────────
    function start() {
        started = true;
        if (!goFullscreen()) sendEvent({ k: 'fs_exit', why: 'refused' });
        $('screen').classList.add('hidden');
        $('exam').classList.remove('hidden');
        renderPaper();
        updateExam();
        openTerminal();
        sendEvent({ k: 'start' });
        lastScreens = screensNow();
        sendEvent({ k: 'screens', detail: lastScreens });
        view = measure();
        tickTimer = setInterval(tick, 1000);
        tick();
        schedulePoll(15000);
    }

    function renderPaper() {
        var p = state.paper, exam = state.exam;
        if (!p) { $('paper-body').innerHTML = '<p class="muted"># the paper is not available.</p>'; return; }
        $('paper-title').textContent = 'paper — ' + exam.folder;
        var h = '<h1>' + esc(exam.title) + '</h1>';
        h += p.intro.map(function (t) { return '<p class="intro">' + rich(t) + '</p>'; }).join('');
        p.parts.forEach(function (part) {
            h += '<h2><span>Part ' + esc(part.id) + ', ' + esc(part.title.toLowerCase()) + '</span><span class="m">' + esc(part.lab) + ' · ' + esc(part.marks) + ' marks</span></h2><ol>';
            part.tasks.forEach(function (t) {
                h += '<li><span class="tid">' + esc(t.id) + '</span><span>' + rich(t.text) + '</span><span class="tm">' + esc(t.marks) + '</span></li>';
            });
            h += '<li><span class="tid">' + esc(part.id) + 'Q</span><span class="q">' + rich(part.question) + ' Write it in <code>answers.md</code>.</span><span class="tm">2</span></li></ol>';
        });
        h += '<div class="prog" id="prog"></div>';
        $('paper-body').innerHTML = h;
        $('term-title').textContent = state.me.user + '@itc-os: ~/' + exam.folder;
        $('s-who').textContent = (state.me.id || state.me.user) + ' ' + (state.me.name || '') + ', ' + exam.title;
    }

    function updateExam() {
        if (state.phase === 'ended' || state.phase === 'closed') { finish(); return; }
        if (covered) return;  // nothing of the exam goes back into the page while a panel is open or the exam is locked
        var prog = state.progress, parts = state.exam.parts, h = '<div class="sec">// your progress (files in place)</div>', strip = '';
        parts.forEach(function (part) {
            var p = prog && prog[part.id];
            var n = p ? p.present : 0, of = p ? p.of : 5, pct = of ? Math.round(100 * n / of) : 0;
            var kind = n === of ? 'ok' : n > 0 ? 'partial' : 'none';
            h += '<div class="prog-row"><span class="st-' + kind + '">' + esc(part.id) + '</span><span class="bar' + (kind === 'partial' ? ' partial' : '') +
                '"><i style="width:' + pct + '%"></i></span><span class="muted">' + n + ' of ' + of + '</span></div>';
            var icon = kind === 'ok' ? '✅' : kind === 'partial' ? '⚠️' : '';
            strip += '<span class="st-' + kind + '">' + (icon ? '<i class="ico" aria-hidden="true">' + icon + '</i>' : '') + esc(part.id) + '</span>';
        });
        if (!prog) h += '<p class="muted"># progress is not available right now.</p>';
        h += '<p class="muted" style="font-size:13px"># this shows which files exist, not whether they are right.</p>';
        var el = $('prog');
        if (el) el.innerHTML = h;
        $('s-parts').innerHTML = strip;
    }

    function tick() {
        if (!state || !state.end) return;
        var left = (Date.parse(state.end) - now()) / 1000;
        var t = $('s-time'), note = $('s-note');
        t.textContent = fmt(left);
        t.className = 'time' + (left <= 120 ? ' bad' : left <= 600 ? ' warn' : '');
        note.className = left <= 120 ? 'st-bad' : left <= 600 ? 'st-partial' : 'muted';
        note.textContent = left <= 120 ? 'left: save your files now' : left <= 600 ? Math.ceil(left / 60) + ' min left' : 'left';
        if (left <= 0) loadState();
    }

    // ── Terminal ─────────────────────────────────────────
    function makeTerm() {
        term = new window.Terminal({
            fontFamily: '"Fira Code", ui-monospace, Consolas, monospace', fontSize: 16, lineHeight: 1.25,
            cursorBlink: false, scrollback: 5000, allowProposedApi: false,
            theme: { background: '#0d1117', foreground: '#c9d1d9', cursor: '#00ff41', cursorAccent: '#0d1117',
                selectionBackground: '#00d4ff40', black: '#0d1117', brightBlack: '#8b949e', red: '#ff5f56', brightRed: '#ff7b72',
                green: '#00cc33', brightGreen: '#00ff41', yellow: '#ffb627', brightYellow: '#ffd166', blue: '#6cb6ff',
                brightBlue: '#9ccaff', magenta: '#d2a8ff', brightMagenta: '#e2c5ff', cyan: '#00d4ff', brightCyan: '#7ee7ff',
                white: '#c9d1d9', brightWhite: '#ffffff' }
        });
        fit = new window.FitAddon.FitAddon();
        term.loadAddon(fit);
        term.open($('term'));
        fitNow();
        term.onData(function (d) { if (wsOpen) ws.send(JSON.stringify({ t: 'i', d: d })); });
        term.onResize(function (sz) { if (wsOpen) ws.send(JSON.stringify({ t: 'r', cols: sz.cols, rows: sz.rows })); });
        window.addEventListener('resize', fitNow);
        // Paste: xterm reads the clipboard from its hidden textarea; listen in the capture phase for the length.
        $('term').addEventListener('paste', function (e) {
            var text = (e.clipboardData && e.clipboardData.getData('text')) || '';
            sendEvent({ k: 'paste', n: text.length });
        }, true);
        term.focus();
    }

    function fitNow() {
        try { fit.fit(); } catch (e) {}
        if (term && term.cols < 80) term.resize(80, term.rows);  // never fewer than 80 columns
    }

    function openTerminal() {
        if (!term) makeTerm();
        if (stopReconnect) return;
        if (connecting || wsOpen) return;
        if (!offlineAt) { $('s-conn').textContent = 'connecting…'; $('s-conn').className = 'conn'; }
        connecting = true;
        updateNet();
        api('/api/exam/ticket', { method: 'POST' }).then(function (t) {
            var url = t.url || state.gateway_url;
            if (q.get('gw')) url = q.get('gw');
            var mine = ws = new WebSocket(url);
            ws.binaryType = 'arraybuffer';
            setTimeout(function () { if (ws === mine && !wsOpen) lost(); }, 15000);
            ws.onopen = function () {
                ws.send(JSON.stringify({ t: 'auth', ticket: t.ticket, cols: term.cols, rows: term.rows }));
            };
            ws.onmessage = function (m) {
                lastRx = Date.now();
                if (typeof m.data !== 'string') { term.write(new Uint8Array(m.data)); return; }
                var msg; try { msg = JSON.parse(m.data); } catch (e) { return; }
                if (msg.t === 'hello') {
                    wsOpen = true; retry = 0; connecting = false;
                    $('s-conn').textContent = '';
                    netBack();
                    flushQueue();
                    term.focus();
                } else if (msg.t === 'bye') {
                    onBye(msg.why);
                } else if (msg.t === 'lock') {
                    showLock(msg.why, msg.bad, msg);
                } else if (msg.t === 'unlocked') {
                    locked = '';
                    stopWait();
                    $('lk-code').value = '';
                    $('lk-err').textContent = '';
                    applyCover();
                } else if (msg.t === 'note' && msg.what === 'shell_end') {
                    term.write('\r\n\x1b[33m[the shell ended; a new one opens]\x1b[0m\r\n');
                }
            };
            ws.onclose = lost;
            ws.onerror = function () {};
        }).catch(function (err) {
            connecting = false;
            if (err.status === 409) { loadState(); return; }
            if (err.status === 403 && /Safe Exam Browser|roster/.test(err.message)) { stopReconnect = true; $('s-conn').textContent = err.message; $('s-conn').className = 'conn bad'; return; }
            if (err.status === 403 || err.status === 401) { loadState(); return; }
            reconnect();
        });
    }

    function onBye(why) {
        if (why === 'replaced') {
            stopReconnect = true;
            $('taken-dialog').classList.remove('hidden');
        } else if (why === 'ended') {
            stopReconnect = true;
            loadState();
        } else if (why === 'shell_end') {
            if (ws) { ws.onclose = ws.onmessage = ws.onerror = null; }
            ws = null; wsOpen = false; connecting = false;
            setTimeout(openTerminal, 500);
        } else if (why === 'unavailable') {
            $('s-conn').textContent = 'the server refused the shell; tell the invigilator';
            $('s-conn').className = 'conn bad';
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

    // The connection is gone: closed by the network, or silent for 15 s (a Wi-Fi that drops often closes nothing).
    function lost() {
        var w = ws, was = wsOpen;
        if (w) { w.onclose = w.onmessage = w.onerror = null; try { w.close(); } catch (e) {} }
        ws = null;
        wsOpen = false;
        connecting = false;
        if (stopReconnect) return;
        if (was) term.write('\r\n\x1b[33m[connection lost: wait, it reconnects by itself. Do not reload the page. What you type now is not sent.]\x1b[0m\r\n');
        reconnect();
    }
    setInterval(function () {
        if (!wsOpen) return;
        if (Date.now() - lastRx > 15000) { lost(); return; }
        try { ws.send(JSON.stringify({ t: 'ping' })); } catch (e) {}
    }, 5000);
    window.addEventListener('offline', function () { if (wsOpen) lost(); else updateNet(); });
    window.addEventListener('online', tryNow);

    function tryNow() {
        if (!started || stopReconnect || wsOpen || connecting) return;
        clearTimeout(retryTimer);
        openTerminal();
    }
    $('nd-try').addEventListener('click', tryNow);

    // The "Connection lost" dialog: after 3 s without a connection, until the terminal is back.
    function netDown() {
        if (!offlineAt) offlineAt = Date.now();
        if (!netTimer && $('net-dialog').classList.contains('hidden')) netTimer = setTimeout(showNet, 3000);
    }
    function showNet() {
        netTimer = null;
        if (wsOpen || stopReconnect || !started) return;
        $('nd-lock').classList.toggle('hidden', !(state && state.exam && (state.exam.lock_on || []).indexOf('fs_exit') >= 0));
        $('net-dialog').classList.remove('hidden');
        clearInterval(netTick);
        netTick = setInterval(updateNet, 1000);
        updateNet();
    }
    function updateNet() {
        if ($('net-dialog').classList.contains('hidden')) return;
        var away = offlineAt ? Math.round((Date.now() - offlineAt) / 1000) : 0;
        var since = ' Offline for ' + Math.floor(away / 60) + ':' + ('0' + away % 60).slice(-2) + '.';
        var why = navigator.onLine === false ? 'This computer is offline: check the Wi-Fi or the cable.' : 'The exam server cannot be reached.';
        var next = connecting ? ' Connecting…' : ' Trying again in ' + Math.max(0, Math.ceil((nextTry - Date.now()) / 1000)) + ' s.';
        $('nd-status').textContent = why + next + since;
        $('nd-try').disabled = connecting;
    }
    function netBack() {
        clearTimeout(netTimer);
        netTimer = null;
        clearInterval(netTick);
        var shown = !$('net-dialog').classList.contains('hidden');
        $('net-dialog').classList.add('hidden');
        if (shown && offlineAt) {  // in the strip: tmux redraws the terminal on reattach and would wipe a note there
            var t = Math.round((Date.now() - offlineAt) / 1000);
            notice('Reconnected after ' + Math.floor(t / 60) + ':' + ('0' + t % 60).slice(-2) + '. Your shell is as you left it.', true);
        }
        offlineAt = 0;
    }

    $('tk-back').addEventListener('click', function () {
        $('taken-dialog').classList.add('hidden');
        stopReconnect = false;
        retry = 0;
        openTerminal();
    });

    // ── Proctoring events ────────────────────────────────
    function sendEvent(ev) {
        ev.t = 'e';
        ev.cts = Date.now();
        if (wsOpen) ws.send(JSON.stringify(ev));
        else if (queue.length < 200) queue.push(ev);
    }
    function flushQueue() {
        while (queue.length && wsOpen) {
            var ev = queue.shift();
            ev.queued_ms = Date.now() - ev.cts;
            ws.send(JSON.stringify(ev));
        }
    }

    function leave(why) {
        if (!started || awayStart) return;
        awayStart = Date.now();
        awayWhy = why;
        sendEvent({ k: 'leave', why: why });
    }
    function back() {
        if (!started || !awayStart) return;
        if (document.hidden || !document.hasFocus()) return;
        var ms = Date.now() - awayStart;
        awayStart = null;
        sendEvent({ k: 'back', away_ms: ms, why: awayWhy });
        notice('You left the exam page for ' + Math.max(1, Math.round(ms / 1000)) + ' s. This is recorded.');
        if (term) term.focus();
    }
    document.addEventListener('visibilitychange', function () { if (document.hidden) leave('tab'); else back(); });
    window.addEventListener('blur', function () { setTimeout(function () { if (!document.hasFocus()) leave('window'); }, 50); });
    window.addEventListener('focus', back);

    function notice(text, plain) {
        var el = $('s-notice');
        el.innerHTML = (plain ? '' : '<i class="ico" aria-hidden="true">⚠️</i>') + esc(text);
        clearTimeout(noticeTimer);
        noticeTimer = setTimeout(function () { el.textContent = ''; }, 8000);
    }

    document.addEventListener('fullscreenchange', function () {
        if (!started) return;
        if (!document.fullscreenElement) {
            sendEvent({ k: 'fs_exit' });
            if (!locked) {
                $('fs-dialog').classList.remove('hidden');
                $('fs-back').focus();
            }
        } else {
            sendEvent({ k: 'fs_enter' });
            $('fs-dialog').classList.add('hidden');
            if (term) { fitNow(); term.focus(); }
        }
    });
    $('fs-back').addEventListener('click', function () {
        if (!goFullscreen()) $('fs-dialog').classList.add('hidden');
    });

    // Fullscreen, then Keyboard Lock (Chrome and Edge): Esc, Ctrl+W, Ctrl+T and the like reach the terminal, and
    // leaving fullscreen takes a press-and-hold of Esc. The browser drops the lock by itself when fullscreen ends.
    function goFullscreen() {
        var el = document.documentElement;
        if (!el.requestFullscreen) return false;
        el.requestFullscreen().then(function () {
            if (!(navigator.keyboard && navigator.keyboard.lock)) { sendEvent({ k: 'kb_lock', detail: 'unsupported' }); return; }
            return navigator.keyboard.lock().then(function () { sendEvent({ k: 'kb_lock', detail: 'on' }); });
        }).catch(function () {
            // The browser refused fullscreen (settings, an old browser): that counts as leaving it, so the lock cannot be
            // avoided by never entering fullscreen.
            if (!document.fullscreenElement && started) sendEvent({ k: 'fs_exit', why: 'refused' });
        });
        return true;
    }

    // Exam lock: the gateway decides (leaving fullscreen, by default) and drops typed input until the code is right.
    var waitEnd = 0, waitTimer = null, CODE_HOW = $('lk-how').textContent;
    function stopWait() {
        clearInterval(waitTimer);
        waitTimer = null;
        $('lk-werr').textContent = '';
    }
    function waitTick() {
        var left = Math.max(0, Math.ceil((waitEnd - Date.now()) / 1000));
        $('lk-count').textContent = left > 0 ? Math.floor(left / 60) + ':' + ('0' + (left % 60)).slice(-2) : 'You can continue.';
        $('lk-go').disabled = left > 0;
        if (left <= 0) { clearInterval(waitTimer); waitTimer = null; $('lk-go').focus(); }
    }
    function showLock(why, bad, msg) {
        locked = why || 'fs_exit';
        $('fs-dialog').classList.add('hidden');
        $('lk-why').textContent = LOCK_WHY[locked] || LOCK_WHY.fs_exit;
        var wait = msg && msg.mode === 'wait';
        $('lk-form').classList.toggle('hidden', wait);
        $('lk-wait').classList.toggle('hidden', !wait);
        if (wait) {
            $('lk-h').lastChild.textContent = 'Wait, then continue';
            $('lk-how').textContent = 'The task and the terminal are hidden until the countdown ends. Each time you leave again today, the wait doubles. Your shell and files are kept, and the timer keeps running.';
            waitEnd = Date.now() + Math.max(0, msg.left || 0) * 1000;
            $('lk-werr').textContent = bad === 'early' ? 'error: the wait is not over yet.' : '';
            stopWaitTimerOnly();
            waitTick();
            if (waitEnd > Date.now()) waitTimer = setInterval(waitTick, 250);
            applyCover();
            return;
        }
        $('lk-h').lastChild.textContent = 'The exam is locked';
        $('lk-how').textContent = CODE_HOW;
        $('lk-err').textContent = bad === 'wrong' ? 'error: that code is not right. Check it with the invigilator.'
            : bad === 'wait' ? 'error: too many wrong codes. Wait a minute, then try again.' : '';
        applyCover();
        if (!panel) { $('lk-code').focus(); $('lk-code').select(); }
    }
    function stopWaitTimerOnly() { clearInterval(waitTimer); waitTimer = null; }
    $('lk-go').addEventListener('click', function () {
        if (!document.fullscreenElement) goFullscreen();  // inside the click, while the browser allows it
        if (!wsOpen) { $('lk-werr').textContent = 'error: not connected. Wait until the terminal reconnects, then try again.'; return; }
        ws.send(JSON.stringify({ t: 'unlock' }));
    });
    $('lk-form').addEventListener('submit', function (e) {
        e.preventDefault();
        var code = $('lk-code').value.replace(/\D/g, '');
        if (!code) return;
        if (!document.fullscreenElement) goFullscreen();  // inside the click or Enter, while the browser allows it
        if (!wsOpen) { $('lk-err').textContent = 'error: not connected. Wait until the terminal reconnects, then try again.'; return; }
        $('lk-err').textContent = 'checking…';
        ws.send(JSON.stringify({ t: 'unlock', code: code }));
    });

    // Screens: Chrome and Edge say whether the desktop spans more than one screen. Other browsers: "unknown".
    function screensNow() {
        var x = window.screen && window.screen.isExtended;
        return x === true ? 'extended' : x === false ? 'single' : 'unknown';
    }
    if (window.screen && window.screen.addEventListener) {
        window.screen.addEventListener('change', function () {
            var now = screensNow();
            if (now === lastScreens) return;
            lastScreens = now;
            if (started) {
                sendEvent({ k: 'screens', detail: now });
                if (now === 'extended') notice('A second screen was connected. This is recorded.');
            } else if (state) {
                render();
            }
        });
    }

    // Side panel: the page gets narrower while the browser window keeps its size (an AI side panel, a docked
    // developer tools pane). The ratio of the page's width in device pixels to the window's width does not change
    // with zoom or when the window is resized, only when something takes part of the window.
    function measure() {
        var dpr = window.devicePixelRatio || 1;
        var r = (window.innerWidth * dpr) / Math.max(1, window.outerWidth);
        return { r: r, dpr: dpr, last: r };
    }
    var panelTimer = null;
    window.addEventListener('resize', function () {
        checkPanel();
        clearTimeout(panelTimer);
        panelTimer = setTimeout(checkPanel, 400);
    });
    // While a panel is open or the exam is locked, the paper is taken out of the page and the terminal is hidden and
    // inert, so an assistant that reads the page finds only the cover. Both come back as they were afterwards.
    function applyCover() {
        var on = !!panel || !!locked;
        $('panel-cover').classList.toggle('hidden', !panel);
        $('lock-dialog').classList.toggle('hidden', !locked);
        if (on === covered) return;
        covered = on;
        $('exam').classList.toggle('covered', on);
        if (on) {
            $('exam').setAttribute('inert', '');
            $('exam').setAttribute('aria-hidden', 'true');
            $('paper-body').innerHTML = '';
        } else {
            $('exam').removeAttribute('inert');
            $('exam').removeAttribute('aria-hidden');
            if (started && state) { renderPaper(); updateExam(); }
            if (term) { fitNow(); term.focus(); }
        }
    }

    function checkPanel() {
        if (!started || !view || !window.outerWidth) return;
        var m = measure();
        // Zoom, or a move to a screen with another scale: keep the same baseline relative to the new measure.
        if (m.dpr !== view.dpr) { view.r = panel ? view.r * m.r / view.last : m.r; view.dpr = m.dpr; view.last = m.r; return; }
        view.last = m.r;
        if (!panel) {
            if (m.r > view.r) view.r = m.r;  // the widest page seen so far is the baseline
            if (m.r < view.r * 0.85) {
                panel = { at: Date.now() };
                applyCover();
                sendEvent({ k: 'panel_open', n: Math.round(100 * (1 - m.r / view.r)) });
            }
        } else if (m.r > view.r * 0.95) {
            sendEvent({ k: 'panel_close', away_ms: Date.now() - panel.at });
            panel = null;
            applyCover();
            if (locked) $('lk-code').focus();
        }
    }

    window.addEventListener('beforeunload', function (e) {
        if (started && state && state.phase === 'open') { e.preventDefault(); e.returnValue = ''; }
    });

    $('paper-btn').addEventListener('click', function () {
        var open = $('paper').classList.toggle('open');
        this.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    // Optional faint, still rain (off unless the exam config turns it on).
    function rain() {
        var c = $('rain'); c.classList.remove('hidden');
        var x = c.getContext('2d'); c.width = innerWidth; c.height = innerHeight;
        x.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--green'); x.globalAlpha = 0.04; x.font = '15px monospace';
        var s = 7; function r() { s = (s * 9301 + 49297) % 233280; return s / 233280; }
        for (var i = 0; i < c.width; i += 18) { var h = r() * c.height; for (var y = 0; y < h; y += 19) x.fillText(String.fromCharCode(0x30A0 + Math.floor(r() * 96)), i, y); }
    }

    if (!API) { screen('bash — exam room', '<p class="err">error: the site has no server address (config.js).</p>'); return; }
    if (!window.Terminal) { screen('bash — exam room', '<p class="err">error: the terminal library did not load. Reload the page.</p>'); return; }
    loadState();
})();
