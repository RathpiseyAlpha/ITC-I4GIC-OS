/* Instructor control panel: the Exam, Paper, Settings, Security and Results tabs of the exam board.
   Root actions (open, extend, close, harden, settings) are queued for the server's root helper and only work when
   the server was installed with `examctl install --web-control`; unlocking goes to the gateway. See
   server/examroom/README.md. */
(function () {
    'use strict';
    var B = window.examBoard;
    if (!B) return;
    var esc = B.esc;
    var TABS = ['live', 'exam', 'paper', 'settings', 'security', 'results'];
    var ctl = null, tab = 'live', timer = null, job = null, dirty = false;

    function $(id) { return document.getElementById(id); }
    function on() { return ctl && ctl.web_control; }

    // ── Tabs ─────────────────────────────────────────────
    function showTab(name) {
        tab = name;
        TABS.forEach(function (t) {
            $('tab-' + t).setAttribute('aria-selected', t === name ? 'true' : 'false');
            $('tab-' + t).tabIndex = t === name ? 0 : -1;
            $(t + '-view').classList.toggle('hidden', t !== name);
        });
        if (name !== 'live') B.closeReplay();
        if (!job) $('job').className = 'job hidden';  // a finished result belongs to the tab it came from
        $('wc-off').classList.toggle('hidden', name === 'live' || !ctl || on());
        clearInterval(timer);
        if (name !== 'live') {
            load();
            timer = setInterval(load, 5000);  // load() leaves a half-edited settings form alone
        }
    }
    document.querySelector('.tabs').addEventListener('click', function (e) {
        var t = e.target.closest('[data-tab]');
        if (t) showTab(t.getAttribute('data-tab'));
    });
    document.querySelector('.tabs').addEventListener('keydown', function (e) {  // arrow keys move between tabs
        var i = TABS.indexOf(tab);
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
            i = (i + (e.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length;
            showTab(TABS[i]);
            $('tab-' + TABS[i]).focus();
            e.preventDefault();
        }
    });

    function load() {
        return B.api('/api/admin/exam/control').then(function (c) {
            ctl = c;
            $('wc-off').classList.toggle('hidden', tab === 'live' || on());
            renderExam();
            if (!dirty) renderSettings();
            renderSecurity();
            renderResults();
            if (tab === 'paper') loadPaper();
            if (tab === 'results') loadScenarios();
        }).catch(function (err) { showJob('error', 'error: ' + err.message); });
    }

    // ── Confirmation ─────────────────────────────────────
    function confirmBox(title, text, yes, danger) {
        return new Promise(function (resolve) {
            $('cf-h').textContent = title;
            $('cf-p').textContent = text;
            $('cf-yes').textContent = yes;
            $('cf-yes').className = 'btn ' + (danger ? 'btn-danger' : 'btn-fill');
            $('confirm').classList.remove('hidden');
            $('cf-no').focus();
            function done(v) {
                $('confirm').classList.add('hidden');
                $('cf-yes').onclick = $('cf-no').onclick = null;
                document.removeEventListener('keydown', key);
                resolve(v);
            }
            function key(e) { if (e.key === 'Escape') done(false); }
            document.addEventListener('keydown', key);
            $('cf-yes').onclick = function () { done(true); };
            $('cf-no').onclick = function () { done(false); };
        });
    }

    // ── Requests to the server's root helper ─────────────
    function showJob(kind, html) {
        var el = $('job');
        el.className = 'job ' + kind;
        el.innerHTML = html;
    }
    function run(action, params, label) {
        if (job) { showJob('error', 'error: wait for “' + esc(job.label) + '” to finish.'); return Promise.resolve(false); }
        return B.api('/api/admin/exam/request', { method: 'POST', body: { action: action, params: params || {} } }).then(function (r) {
            job = { id: r.id, label: label, t0: Date.now() };
            showJob('busy', esc(label) + ': sent…');
            return poll();
        }).catch(function (err) { showJob('error', esc(label) + ': ' + esc(err.message)); return false; });
    }
    function poll() {
        return new Promise(function (resolve) {
            (function tick() {
                B.api('/api/admin/exam/request?id=' + job.id).then(function (st) {
                    var waited = Math.round((Date.now() - job.t0) / 1000);
                    if (st.status === 'done') {
                        showJob(st.ok ? 'ok' : 'error', esc(job.label) + (st.ok ? ': done.' : ': failed.') +
                            (st.output ? '<pre class="out">' + esc(st.output.trim()) + '</pre>' : ''));
                        job = null;
                        load();
                        B.refresh();
                        resolve(st.ok);
                        return;
                    }
                    var msg = esc(job.label) + ': ' + (st.status === 'running' ? 'running on the server' : 'waiting for the server') + '… ' + waited + ' s';
                    if (st.status === 'queued' && waited >= 15) {
                        msg += '<br>The server’s helper has not picked it up. Is web control installed and running? ' +
                            '<code>systemctl status itc-os-examctl.path</code>';
                    }
                    showJob('busy', msg);
                    if (waited > 180) { showJob('error', esc(job.label) + ': no answer after 3 minutes. Check <code>journalctl -u itc-os-examctl</code>.'); job = null; resolve(false); return; }
                    setTimeout(tick, 1000);
                }).catch(function (err) {
                    showJob('error', esc(job.label) + ': ' + esc(err.message));
                    job = null;
                    resolve(false);
                });
            })();
        });
    }

    // ── Exam tab ─────────────────────────────────────────
    var ACTION_NAMES = { open: 'Open the exam', extend: 'Extend', close: 'Close and collect', harden_on: 'Hardening on',
        harden_off: 'Hardening off', prepare: 'Prepare accounts', settings: 'Settings', draw: 'Draw now', undraw: 'Discard the draw', correct: 'Correction' };

    function left() {
        if (!ctl || !ctl.state.end) return null;
        return (Date.parse(ctl.state.end) - Date.parse(ctl.now)) / 1000;
    }

    function renderExam() {
        var s = ctl.state, ph = s.phase, n = ctl.students, dis = on() ? '' : ' disabled';
        var names = { sealed: 'not started', open: 'open', ended: 'time is up', closed: 'closed' };
        $('x-phase').textContent = names[ph] || ph;
        $('x-phase').className = 'num ' + (ph === 'open' ? 'st-ok' : ph === 'ended' ? 'st-partial' : 'muted');
        $('x-times').textContent = s.start ? s.start.slice(11, 16) + ' to ' + (s.end || '').slice(11, 16) : '';
        var l = left();
        $('x-left').textContent = ph === 'open' && l != null ? B.hms(l) : '—';
        $('x-ext').textContent = s.extended_min ? 'extended ' + s.extended_min + ' min' : '';
        $('x-students').textContent = n;
        $('x-exam').textContent = ctl.exam.id + ', ' + ctl.exam.duration_min + ' min';
        $('x-locked').textContent = ctl.locked.length;
        var h = '';
        if (!ctl.running) {
            h += '<p class="hint">' + (ph === 'closed' ? 'The exam is closed and the snapshot is taken. Opening again restarts the clock; students’ files are kept.'
                : 'Opening makes each student’s starting files in <code>~/' + esc(ctl.exam.folder) + '/</code>, then the paper and the terminals open and the clock starts.') + '</p>' +
                '<div class="row"><label class="inline" for="x-min">Minutes <input class="input small" type="number" id="x-min" min="5" max="300" value="' + esc(ctl.exam.duration_min) + '"></label>' +
                '<button class="btn btn-fill" type="button" id="x-open"' + dis + '>' + (ph === 'closed' ? 'Open again' : 'Open the exam') + '</button></div>';
        } else {
            h += '<p class="hint">Extra time goes to everyone. Give it before the end: students whose page already says “Time is up” must reload.</p>' +
                '<div class="row"><span>Extend by</span>' + [5, 10, 15].map(function (m) {
                    return '<button class="btn btn-tool" type="button" data-ext="' + m + '"' + dis + '>+' + m + ' min</button>';
                }).join('') + '<label class="inline" for="x-ext-n">or <input class="input small" type="number" id="x-ext-n" min="1" max="120" placeholder="min"></label>' +
                '<button class="btn btn-tool" type="button" id="x-ext-go"' + dis + '>Extend</button></div>' +
                '<p class="hint">Closing ends every terminal within 10 seconds and copies each exam folder for marking. It cannot be undone.</p>' +
                '<div class="row"><button class="btn btn-danger" type="button" id="x-close"' + dis + '>Close and collect</button></div>';
        }
        h += '<p class="hint">Unlocking does not need web control: it goes straight to the terminal server.</p>' +
            '<div class="row"><button class="btn btn-tool" type="button" id="x-unlock"' + (ctl.locked.length ? '' : ' disabled') + '>Unlock all (' + ctl.locked.length + ')</button></div>';
        $('x-actions').innerHTML = h;
        $('x-history').innerHTML = ctl.history.map(function (r) {
            var when = r.done_at ? B.clock(r.done_at) : '';
            var what = (ACTION_NAMES[r.action] || r.action) + (r.params && r.params.minutes ? ' ' + r.params.minutes + ' min' : '') +
                (r.params && r.params.changes ? ': ' + Object.keys(r.params.changes).join(', ') : '');
            return '<tr><td class="num">' + esc(when) + '</td><td>' + esc(r.by) + '</td><td>' + esc(what) + '</td><td>' +
                (r.ok ? '<span class="st-ok">done</span>' : '<span class="st-bad">failed</span>') +
                (r.output ? ' <details><summary>output</summary><pre class="out">' + esc(r.output.trim()) + '</pre></details>' : '') + '</td></tr>';
        }).join('') || '<tr><td colspan="4" class="muted"># nothing yet.</td></tr>';
    }

    $('exam-view').addEventListener('click', function (e) {
        var t = e.target;
        if (t.id === 'x-open') {
            var m = parseInt($('x-min').value, 10);
            if (!(m >= 5 && m <= 300)) { showJob('error', 'error: minutes must be 5 to 300.'); return; }
            confirmBox('Open the exam?', 'Open “' + ctl.exam.title + '” for ' + ctl.students + ' students now, for ' + m +
                ' minutes. Their starting files are made and the clock starts.', 'Open for ' + m + ' min', false)
                .then(function (ok) { if (ok) run('open', { minutes: m }, 'Open the exam'); });
        } else if (t.hasAttribute('data-ext') || t.id === 'x-ext-go') {
            var n = t.id === 'x-ext-go' ? parseInt($('x-ext-n').value, 10) : parseInt(t.getAttribute('data-ext'), 10);
            if (!(n >= 1 && n <= 120)) { showJob('error', 'error: extend by 1 to 120 minutes.'); return; }
            confirmBox('Give everyone ' + n + ' more minutes?', 'The end moves from ' + (ctl.state.end || '').slice(11, 16) + ' for all ' + ctl.students + ' students.',
                'Extend by ' + n + ' min', false).then(function (ok) { if (ok) run('extend', { minutes: n }, 'Extend by ' + n + ' min'); });
        } else if (t.id === 'x-close') {
            confirmBox('Close the exam and collect?', 'The terminals of all ' + ctl.students + ' students close within 10 seconds and every exam folder is copied for marking. This cannot be undone.',
                'Close and collect', true).then(function (ok) { if (ok) run('close', {}, 'Close and collect'); });
        } else if (t.id === 'x-unlock') {
            confirmBox('Unlock ' + ctl.locked.length + ' students?', 'Every locked student gets the exam back now, without a code.', 'Unlock all', false)
                .then(function (ok) {
                    if (!ok) return;
                    B.api('/api/admin/exam/unlock', { method: 'POST', body: { all: true } }).then(function (r) {
                        showJob('ok', 'Unlock sent to ' + r.sent + ' students; their pages open within a few seconds.');
                        setTimeout(load, 2000);
                        setTimeout(B.refresh, 2000);
                    }).catch(function (err) { showJob('error', 'Unlock: ' + esc(err.message)); });
                });
        }
    });

    // ── Settings tab ─────────────────────────────────────
    var FIELDS = [  // setting key, input id, kind
        ['lock.mode', 's-mode', 'choice'], ['lock.wait_s', 's-wait', 'int'], ['lock.wait_max_s', 's-wait-max', 'int'],
        ['lock.max_attempts', 's-max', 'int'], ['flags.second_screen', 's-second', 'choice'], ['flags.side_panel', 's-side', 'choice'],
        ['flags.review_away_s', 's-away-review', 'int'], ['flags.high_away_s', 's-away-high', 'int'],
        ['flags.large_paste_chars', 's-paste', 'int'], ['flags.high_pastes', 's-pastes', 'int'], ['flags.high_offline_s', 's-offline', 'int'],
        ['title', 's-title', 'text'], ['duration_min', 's-duration', 'int'], ['seb.required', 's-seb', 'bool'], ['rain', 's-rain', 'bool']
    ];
    var TRIGGERS = ['fs_exit', 'panel', 'leave'];

    function renderSettings() {
        var st = ctl.settings, fixed = ctl.running ? ctl.fixed_while_open : [];
        TRIGGERS.forEach(function (t) {
            var box = $('s-lock-' + t);
            box.checked = (st['lock.on'] || []).indexOf(t) >= 0;
            box.disabled = !on();
        });
        FIELDS.forEach(function (f) {
            var el = $(f[1]), v = st[f[0]];
            if (f[2] === 'bool') el.checked = !!v; else el.value = v == null ? '' : v;
            el.disabled = !on() || fixed.indexOf(f[0]) >= 0 || (f[0] === 'seb.required' && !ctl.seb_keys && !v);
        });
        var notes = [];
        if (ctl.running) notes.push('Title, length and Safe Exam Browser are fixed while the exam is open (use Extend for more time).');
        if (!ctl.seb_keys) notes.push('Safe Exam Browser needs its config keys in the exam config first (examctl config).');
        $('s-fixed').textContent = notes.join(' ');
        $('s-save').disabled = !on();
        document.querySelectorAll('[data-preset]').forEach(function (b) { b.disabled = !on(); });
        showProfile(st.profile);
        showWaitFields();
        dirty = false;
        $('s-dirty').textContent = '';
    }

    var PROFILE_NAME = { exam: 'Exam (strict)', practice: 'Practice', custom: 'custom (a preset changed by hand)' };
    function showProfile(p) { $('s-profile').textContent = 'Current: ' + (PROFILE_NAME[p] || p || 'exam') + '.'; }
    function showWaitFields() {
        var wait = $('s-mode').value === 'wait';
        $('s-max').closest('label').classList.toggle('hidden', wait);
        $('s-wait').closest('label').classList.toggle('hidden', !wait);
        $('s-wait-max').closest('label').classList.toggle('hidden', !wait);
    }

    // The form's values, as settings (only the fields a preset sets are compared)
    function formValue(key) {
        if (key === 'lock.on') return TRIGGERS.filter(function (t) { return $('s-lock-' + t).checked; }).sort();
        var f = FIELDS.filter(function (x) { return x[0] === key; })[0];
        if (!f) return undefined;
        var el = $(f[1]);
        return f[2] === 'bool' ? el.checked : f[2] === 'int' ? parseInt(el.value, 10) : el.value;
    }
    function formProfile() {
        var names = Object.keys(ctl.presets || {});
        for (var i = 0; i < names.length; i++) {
            var p = ctl.presets[names[i]], same = Object.keys(p).every(function (k) {
                return k === 'profile' || JSON.stringify(formValue(k)) === JSON.stringify(Array.isArray(p[k]) ? p[k].slice().sort() : p[k]);
            });
            if (same) return names[i];
        }
        return 'custom';
    }
    document.querySelectorAll('[data-preset]').forEach(function (b) {
        b.addEventListener('click', function () {
            var p = (ctl.presets || {})[b.getAttribute('data-preset')];
            if (!p) return;
            Object.keys(p).forEach(function (k) {
                if (k === 'lock.on') { TRIGGERS.forEach(function (t) { $('s-lock-' + t).checked = p[k].indexOf(t) >= 0; }); return; }
                var f = FIELDS.filter(function (x) { return x[0] === k; })[0];
                if (!f) return;
                if (f[2] === 'bool') $(f[1]).checked = !!p[k]; else $(f[1]).value = p[k];
            });
            $('s-form').dispatchEvent(new Event('input', { bubbles: true }));
        });
    });

    function changes() {
        var st = ctl.settings, out = {};
        var lockOn = formValue('lock.on');
        if (lockOn.join() !== (st['lock.on'] || []).slice().sort().join()) out['lock.on'] = lockOn;
        FIELDS.forEach(function (f) {
            var el = $(f[1]);
            if (el.disabled) return;
            var v = f[2] === 'bool' ? el.checked : f[2] === 'int' ? parseInt(el.value, 10) : el.value;
            if (f[2] === 'text') v = v.trim();
            if (v !== st[f[0]] && !(f[2] === 'int' && isNaN(v))) out[f[0]] = v;
        });
        var prof = formProfile();
        if (prof !== (st.profile || 'exam')) out.profile = prof;
        return out;
    }

    $('s-form').addEventListener('input', function () {
        showWaitFields();
        dirty = Object.keys(changes()).length > 0;
        $('s-dirty').textContent = dirty ? 'unsaved changes' : '';
        showProfile(formProfile());
    });
    $('s-reset').addEventListener('click', function () { dirty = false; renderSettings(); });
    $('s-form').addEventListener('submit', function (e) {
        e.preventDefault();
        var c = changes();
        if (!Object.keys(c).length) { showJob('ok', 'Nothing to save.'); return; }
        run('settings', { changes: c }, 'Save settings').then(function (ok) { if (ok) { dirty = false; } });
    });

    // ── Security tab ─────────────────────────────────────
    function renderSecurity() {
        var hd = ctl.harden, isOn = hd && hd.on, dis = on() ? '' : ' disabled';
        $('sec-state').innerHTML = isOn ? '<span class="badge st-ok">on</span> since ' + esc((hd.since || '').slice(11, 16))
            : '<span class="badge muted">off</span>' + (hd && hd.off_at ? ' since ' + esc(hd.off_at.slice(11, 16)) : '');
        $('sec-actions').innerHTML = isOn
            ? '<button class="btn btn-tool" type="button" id="sec-off"' + dis + '>Turn hardening off</button>'
            : '<label class="check"><input type="checkbox" id="sec-kick" checked> also end students’ SSH sessions from outside</label>' +
              '<button class="btn btn-fill" type="button" id="sec-on"' + dis + '>Turn hardening on</button>';
        $('acc-prepare').disabled = !on();
        $('sys-list').innerHTML = [
            ['Terminal gateway', ctl.gateway_ok ? '<span class="st-ok">running</span>' : '<span class="st-bad">not answering</span> (systemctl status itc-os-examgw)'],
            ['Web control', on() ? '<span class="st-ok">on</span>' + (ctl.preview ? ' (local preview: hardening and accounts are not available)' : '') : '<span class="muted">off</span>'],
            ['Exam', esc(ctl.exam.id) + ', parts ' + esc(ctl.exam.parts.join(', ')) + ', folder ~/' + esc(ctl.exam.folder)],
            ['Roster', ctl.students + ' students']
        ].map(function (x) { return '<li><span class="k">' + x[0] + '</span> ' + x[1] + '</li>'; }).join('');
    }
    $('security-view').addEventListener('click', function (e) {
        var t = e.target;
        if (t.id === 'sec-on') {
            var kick = $('sec-kick').checked;
            confirmBox('Turn hardening on?', 'Students lose SSH from outside' + (kick ? ' (open SSH sessions end now)' : '') +
                ' and network access from their shells. The exam page keeps working.', 'Turn on', false)
                .then(function (ok) { if (ok) run('harden_on', { kick: kick }, 'Hardening on'); });
        } else if (t.id === 'sec-off') {
            confirmBox('Turn hardening off?', 'Students get SSH and network access back.', 'Turn off', false)
                .then(function (ok) { if (ok) run('harden_off', {}, 'Hardening off'); });
        } else if (t.id === 'acc-prepare') {
            confirmBox('Prepare accounts from the roster?', 'The class group becomes exactly the ' + ctl.students + ' roster accounts, and each gets the gateway key.', 'Prepare', false)
                .then(function (ok) { if (ok) run('prepare', {}, 'Prepare accounts'); });
        }
    });

    // ── Paper tab: the scenario bank and the draw ─────────
    // Read-only without web control. The pool, mode, seed and pins are exam settings that can change only before the draw;
    // Draw now and Discard are actions of the root helper. Everything shown here also exists as `examctl draw`.
    var pp = null, ppDirty = false;

    function loadPaper() {
        return B.api('/api/admin/exam/draw').then(function (d) { pp = d; renderPaper(); })
            .catch(function (err) { showJob('error', 'Paper: ' + esc(err.message)); });
    }
    function ppLocked() { return !pp.exam.never_opened || pp.exam.drawn; }
    function ppPins() { return JSON.parse(JSON.stringify((pp.bank.settings && pp.bank.settings.pins) || {})); }

    function renderPaper() {
        if (!pp || !pp.exam) { $('pp-state').textContent = 'No exam is set up.'; return; }
        var b = pp.bank, ex = pp.exam, dis = on() ? '' : ' disabled';
        $('pp-err').classList.toggle('hidden', b.ok);
        if (!b.ok) { $('pp-err').textContent = 'The scenario bank is not usable, so the exam cannot be opened: ' + b.error; $('pp-pool').innerHTML = ''; $('pd-rows').innerHTML = ''; return; }
        var locked = ppLocked(), lockedAttr = (locked || !on()) ? ' disabled' : '';
        $('pp-state').innerHTML = ex.drawn
            ? '<span class="badge st-ok">drawn</span> ' + (ex.never_opened ? 'You can discard the draw until the exam is opened.' : 'The exam has been opened: the draw is final.')
            : '<span class="badge muted">not drawn yet</span> The table below is a preview of what Open will write.' +
              (pp.changed ? ' <span class="st-bad">' + pp.changed + ' draw(s) were made with another version of the bank.</span>' : '');
        if (!ppDirty) {
            $('pp-pool').innerHTML = b.parts.map(function (part) {
                return '<div><b>Part ' + esc(part.id) + '</b> <span class="muted">' + esc(part.title) + ' · slots ' + part.slots.map(function (x) { return esc(x.id) + ' ' + esc(x.skill); }).join(', ') + '</span>' +
                    part.scenarios.map(function (sc) {
                        return '<label class="check"><input type="checkbox" data-sc="' + esc(sc.id) + '"' + (sc.enabled ? ' checked' : '') + lockedAttr + '> ' + esc(sc.id) + ' — ' + esc(sc.title) +
                            (sc.minutes ? ' <span class="muted">(' + esc(sc.minutes) + ' min in the pilot)</span>' : '') + '</label>';
                    }).join('') + '</div>';
            }).join('');
            $('pp-mode').value = (b.settings && b.settings.mode) || 'balanced';
            $('pp-seed').value = (b.settings && b.settings.seed) || '';
        }
        $('pp-mode').disabled = $('pp-seed').disabled = $('pp-save').disabled = locked || !on();
        $('pp-draw').disabled = locked || !on();
        $('pp-undraw').disabled = !(ex.drawn && ex.never_opened) || !on();
        $('pd-counts').innerHTML = Object.keys(pp.counts).sort().map(function (part) {
            return '<b>' + esc(part) + '</b>: ' + Object.keys(pp.counts[part]).sort().map(function (sid) { return esc(sid) + ' ' + pp.counts[part][sid]; }).join(', ');
        }).join(' &nbsp; ');
        $('pd-rows').innerHTML = pp.students.length ? pp.students.map(function (r) {
            return '<tr><td>' + esc(r.id) + '</td><td>' + esc(r.name) + '</td>' + ['A', 'B', 'C', 'D'].map(function (part) { return '<td>' + esc(r.scenarios[part] || '') + '</td>'; }).join('') +
                '<td>' + (r.error ? '<span class="st-bad">' + esc(r.error) + '</span>' : r.recorded ? 'recorded' : 'preview') + '</td></tr>';
        }).join('') : '<tr><td colspan="7" class="muted"># no students on the roster.</td></tr>';
        // pins
        var pins = ppPins(), users = pp.students.map(function (r) { return r.user; });
        if (!$('pn-user').options.length) {
            $('pn-user').innerHTML = pp.students.map(function (r) { return '<option value="' + esc(r.user) + '">' + esc(r.id) + ' ' + esc(r.name) + '</option>'; }).join('');
            $('pn-part').innerHTML = b.parts.map(function (part) { return '<option value="' + esc(part.id) + '">Part ' + esc(part.id) + '</option>'; }).join('');
            fillPinScenarios();
        }
        $('pn-add').disabled = $('pn-user').disabled = $('pn-part').disabled = $('pn-sc').disabled = locked || !on();
        var rows = [];
        Object.keys(pins).sort().forEach(function (u) {
            Object.keys(pins[u]).sort().forEach(function (part) {
                rows.push('<li><span class="k">' + esc(u) + '</span> part ' + esc(part) + ' → ' + esc(pins[u][part]) +
                    ' <button class="btn-link" type="button" data-unpin="' + esc(u) + '|' + esc(part) + '"' + lockedAttr + '>remove</button></li>');
            });
        });
        $('pn-list').innerHTML = rows.join('') || '<li class="muted"># no pins.</li>';
    }
    function fillPinScenarios() {
        var part = pp.bank.parts.filter(function (x) { return x.id === $('pn-part').value; })[0];
        $('pn-sc').innerHTML = (part ? part.scenarios : []).map(function (sc) { return '<option value="' + esc(sc.id) + '">' + esc(sc.id) + '</option>'; }).join('');
    }
    $('pn-part').addEventListener('change', fillPinScenarios);
    $('pp-pool').addEventListener('change', function () { ppDirty = true; });
    $('pp-mode').addEventListener('change', function () { ppDirty = true; });
    $('pp-seed').addEventListener('input', function () { ppDirty = true; });

    $('pp-save').addEventListener('click', function () {
        var off = [].slice.call($('pp-pool').querySelectorAll('input[data-sc]')).filter(function (x) { return !x.checked; }).map(function (x) { return x.getAttribute('data-sc'); });
        var c = { 'bank.disabled': off, 'bank.mode': $('pp-mode').value };
        var seed = $('pp-seed').value.trim();
        if (seed) c['bank.seed'] = seed;
        run('settings', { changes: c }, 'Save scenario settings').then(function (ok) { if (ok) { ppDirty = false; loadPaper(); } });
    });
    $('pn-add').addEventListener('click', function () {
        var pins = ppPins(), u = $('pn-user').value, part = $('pn-part').value, sid = $('pn-sc').value;
        if (!u || !sid) return;
        pins[u] = pins[u] || {};
        pins[u][part] = sid;
        run('settings', { changes: { 'bank.pins': pins } }, 'Pin a scenario').then(function (ok) { if (ok) loadPaper(); });
    });
    $('pn-list').addEventListener('click', function (e) {
        var t = e.target.closest('[data-unpin]');
        if (!t) return;
        var kv = t.getAttribute('data-unpin').split('|'), pins = ppPins();
        if (pins[kv[0]]) { delete pins[kv[0]][kv[1]]; if (!Object.keys(pins[kv[0]]).length) delete pins[kv[0]]; }
        run('settings', { changes: { 'bank.pins': pins } }, 'Remove a pin').then(function (ok) { if (ok) loadPaper(); });
    });
    $('pp-draw').addEventListener('click', function () {
        confirmBox('Draw now?', 'Every student’s scenarios are written down now. Open will keep this draw. You can still discard it until the exam is opened.', 'Draw now', false)
            .then(function (ok) { if (ok) run('draw', {}, 'Draw now').then(function () { ppDirty = false; loadPaper(); }); });
    });
    $('pp-undraw').addEventListener('click', function () {
        confirmBox('Discard the draw?', 'The scenarios are drawn again from the current pool, mode and seed when you press Draw now or Open.', 'Discard', true)
            .then(function (ok) { if (ok) run('undraw', {}, 'Discard the draw').then(function () { loadPaper(); }); });
    });
    $('pp-csv').addEventListener('click', function () {
        if (!pp) return;
        var rows = [['id', 'name', 'user', 'A', 'B', 'C', 'D', 'state']].concat(pp.students.map(function (r) {
            return [r.id, r.name, r.user, r.scenarios.A || '', r.scenarios.B || '', r.scenarios.C || '', r.scenarios.D || '', r.error ? 'problem' : r.recorded ? 'recorded' : 'preview'];
        }));
        var text = rows.map(function (r) { return r.map(function (x) { return '"' + String(x).replace(/"/g, '""') + '"'; }).join(','); }).join('\n');
        var a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv' }));
        a.download = (pp.exam.id || 'exam') + '-draw.csv';
        document.body.appendChild(a);
        a.click();
        setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    });

    // ── Results tab: per scenario, and corrections ────────
    var rs = null;
    function loadScenarios() {
        return B.api('/api/admin/exam/results').then(function (d) { rs = d; renderScenarios(); })
            .catch(function (err) { $('rs-table').innerHTML = '<p class="st-bad">' + esc(err.message) + '</p>'; });
    }
    function renderScenarios() {
        if (!rs || rs.error || !rs.stats) { $('rs-table').innerHTML = '<p class="st-bad">' + esc((rs && rs.error) || 'Nothing to show.') + '</p>'; return; }
        var html = '<table class="tbl"><thead><tr><th>Part</th><th>Scenario</th><th>Students</th><th>Slots right (of those who drew it)</th></tr></thead><tbody>';
        Object.keys(rs.stats).sort().forEach(function (part) {
            Object.keys(rs.stats[part]).sort().forEach(function (sid) {
                var row = rs.stats[part][sid];
                html += '<tr><td>' + esc(part) + '</td><td>' + esc(sid) + '</td><td>' + row.students + '</td><td>' +
                    (rs.slots[part] || []).map(function (slot) {
                        var c = row.slots[slot];
                        return esc(slot) + ' ' + (c ? c.ok + '/' + c.n : '–');
                    }).join(' · ') + '</td></tr>';
            });
        });
        $('rs-table').innerHTML = html + '</tbody></table>' + (rs.problems ? '<p class="st-bad">' + rs.problems + ' student(s) could not be read (draw or folder).</p>' : '');
        var scs = [];
        Object.keys(rs.scenarios).sort().forEach(function (part) { rs.scenarios[part].forEach(function (sid) { scs.push([part, sid]); }); });
        if (!$('cr-sc').options.length) {
            $('cr-sc').innerHTML = scs.map(function (x) { return '<option value="' + esc(x[1]) + '" data-part="' + esc(x[0]) + '">' + esc(x[1]) + '</option>'; }).join('');
            fillSlots();
        }
        $('cr-apply').disabled = !on();
        $('cr-list').innerHTML = rs.corrections.map(function (c) {
            return '<li><span class="k">' + esc(c.scenario) + ' ' + esc(c.slot) + '</span> ' + esc(c.mode) + ' — ' + esc(c.reason) + ' <span class="muted">(' + esc(c.by) + ', ' + esc(String(c.at).slice(0, 16).replace('T', ' ')) + ')</span></li>';
        }).join('') || '<li class="muted"># no corrections.</li>';
    }
    function fillSlots() {
        var o = $('cr-sc').options[$('cr-sc').selectedIndex];
        $('cr-slot').innerHTML = ((o && rs.slots[o.getAttribute('data-part')]) || []).map(function (x) { return '<option>' + esc(x) + '</option>'; }).join('');
    }
    $('cr-sc').addEventListener('change', fillSlots);
    $('cr-apply').addEventListener('click', function () {
        var p = { scenario: $('cr-sc').value, slot: $('cr-slot').value, mode: $('cr-mode').value, reason: $('cr-reason').value.trim() };
        if (p.mode === 'clear' && p.reason.length < 3) p.reason = 'cleared';
        var what = p.mode === 'give' ? 'Every student who drew ' + p.scenario + ' gets the marks for ' + p.slot + '.'
            : p.mode === 'ignore' ? p.slot + ' is taken out of the total of every student who drew ' + p.scenario + ' (they are marked out of fewer marks).'
            : 'The correction on ' + p.scenario + ' ' + p.slot + ' is removed.';
        confirmBox('Apply this correction?', what, 'Apply', false).then(function (ok) {
            if (ok) run('correct', p, 'Correction').then(function (done) { if (done) { $('cr-reason').value = ''; loadScenarios(); } });
        });
    });

    // ── Results tab ──────────────────────────────────────
    function renderResults() {
        $('res-note').textContent = ctl.state.phase === 'closed' ? 'from the snapshot taken at close' : 'the exam is not closed yet: points come from the live folders';
    }
    $('res-csv').addEventListener('click', function () {
        B.api('/api/admin/exam/report.csv', { raw: true }).then(function (text) {
            var a = document.createElement('a');
            a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv' }));
            a.download = (ctl ? ctl.exam.id : 'exam') + '-auto.csv';
            document.body.appendChild(a);
            a.click();
            setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
        }).catch(function (err) { showJob('error', 'Download: ' + esc(err.message)); });
    });
})();
