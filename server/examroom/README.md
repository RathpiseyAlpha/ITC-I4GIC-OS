# Exam room: runbook

The exam room is a web page where a student sits a practical exam in a real shell on the course server. The paper is
beside the shell, and the instructor watches a live board. The plan and the reasons are in
[`teaching/EXAM-TERMINAL-SPEC.md`](../../teaching/EXAM-TERMINAL-SPEC.md). This file says how to install it, test it
and run an exam.

**Status, 22 November 2026:** built and tested on a development machine (WSL, Ubuntu 20.04). It has not yet run on the
course server, in Safe Exam Browser, or in a computer room.

## The pieces

| File | What it is |
|---|---|
| `exam.html`, `app/exam/exam.js` | The student page: login, waiting room, paper, terminal, proctoring events |
| `exam-board.html`, `app/exam/board.js` | The instructor board (every 5 seconds) and the session replay |
| `app/exam/control.js` | The board's Exam, Settings, Security and Results tabs (see "The control panel") |
| `app/exam/exam.css`, `app/vendor/` | Styles, xterm.js 5.5.0 with the fit add-on, and Fira Code, all self-hosted so SEB can block every other host |
| `app/server/app.py` | `/api/exam/state`, `/api/exam/ticket`, `/api/admin/exam/board`, `/api/admin/exam/replay`, `/api/admin/exam/cast`, and for the panel `/api/admin/exam/control`, `request`, `unlock`, `report.csv` |
| `server/examroom/gateway.py` | The websocket-to-SSH-to-tmux gateway, its own service (`itc-os-examgw`), port 5010 |
| `server/examroom/common.py` | Config, state, signed tickets, SEB check, the board summary |
| `server/examroom/midterm.py` | **Not in git.** The midterm: the blueprint (what each slot tests), the written questions, the paper, starting files and checks, built on the scenario bank |
| `server/examroom/exambank.py` | The scenario bank engine (no exam content): scenarios, validation, the balanced draw, the draw file |
| `server/examroom/bank/` | **Not in git.** The scenarios, one file per part (`part_a.py` …): story, personal values, starting files, tasks, checks. Scenario 1 of each part is the first paper's, unchanged |
| `server/examroom/examctl.py` | The root tool: install, config, group, keys, open, extend, close, report, harden |
| `server/examroom/tmux.conf` | tmux with no prefix key and no status line, so students never notice it |
| `server/examroom/exam.example.json` | The exam config to copy and edit |
| `server/examroom/loadtest.py` | N scripted terminals at once, with timings and free memory |
| `server/examroom/devstack.py` | A local preview: an API copy, the gateway with a local shell, and the site |
| `server/examroom/test_examroom.py` | **Not in git** (it holds a model solution). End-to-end tests, no root needed |
| `server/examroom/test_exambank.py` | **Not in git.** The bank: parity with the first paper, every scenario solved and attacked, the draw, the draw file |

`midterm.py`, `bank/`, `test_examroom.py`, `test_exambank.py` and the backups of the first paper (`midterm-v1-backup.py`,
`test_examroom-v1-backup.py`) are in `.gitignore`, because the repository feeds the public Pages site and the paper must
not be published before the exam. After the exam they can be committed.

**The scenario bank** (its plan is kept privately). A part has a pool of scenarios; a
student gets one per part. `midterm.py` fixes the blueprint (each part's folder and the skill each slot tests, so A1 to D4
mean the same thing in every scenario); `bank/part_*.py` hold the scenarios; `exambank.py` loads them **strictly** (a file
that does not load or validate, a part with no scenario or a duplicate id stops the exam, nothing is skipped) and draws.
Every part has a pool of scenarios. Scenario 1 of each part is the first paper unchanged, with the same personal values (checked against the
first paper for 200 students with the other scenarios switched off). The draw is balanced over the roster (the roster sorted by a hash of the seed,
the part and the user, the scenarios dealt out in turn: counts differ by at most one). The draw file
`/srv/exam/<exam id>/draw/<user>.json` (values and scenario per part, the bank's content hash, format version 1) is read by
`paper()`, `fixture()` and `checks()`. **`examctl open` writes it** (the whole roster at once, into a temporary folder renamed to
`draw/`, `0750 root:itc-exam` with `0640` files; the bank is loaded first, so a broken bank leaves the exam sealed), unless the
exam has already drawn, in which case it keeps that draw. Before the draw, a student's draw is computed **over the roster with
the same balanced deal**, so the Paper tab's preview, "view as student" and what open writes agree (the API's roster is the
students whose account exists on the server, as `examctl open` skips the rest). Once an exam has a draw folder, a student with
no draw, an unreadable file or a scenario the bank no longer has is an error, never a guess: the student sees "your paper is
not available, tell the invigilator" and the board and CSV show "draw problem" on that row.

**The exam config's `bank` section** (set from the Paper tab, or `examctl config`): `{"mode": "balanced"|"random", "seed": "",
"disabled": [scenario ids], "pins": {user: {part: scenario id}}}`. The seed defaults to the exam id (a makeup exam has another
id, so another draw). These can change only before the draw, and the helper refuses them while the exam is open or drawn.

**`examctl draw ACTION [USER] --roster FILE`**: `write` (what Open does, ahead of time: the "Draw now" button), `show USER`,
`report` (counts per scenario and each student), `check` (a missing, unreadable or wrong draw; a bank that changed since the
draw is a note, the recorded scenario and values still hold), `add USER` (a late student, after the draw: a stable pick or the
student's pin), `redraw USER --scenario B=B-office` (replace one student's scenarios; refused once the exam was opened, because
it would destroy the student's work: not built for during the exam), `discard` (only before the exam was ever opened).

**The Paper tab** of the exam board (needs web control to act; read-only without it): the bank's parts and scenarios with a
tick for each in play, the mode and the seed, **Draw now** and **Discard the draw**, a table of every student's drawn
scenarios with the counts per scenario (a preview before the draw), pins, and a CSV of the draw. Its data comes from
`GET /api/admin/exam/draw`, which reports a bad bank or draw as data. The actions are `settings` (the `bank.*` keys), `draw`,
`undraw` and `correct` in the root helper's whitelist; the API checks them against the bank and the roster before it queues
them, and the helper checks again.

**Results**: `report.csv` and `examctl report` have one column per part naming the scenario, then the slots, then `auto_points`,
`auto_of`, `raw_points` and `corrections`. The Results tab adds **Per scenario** (`GET /api/admin/exam/results`: how many
students drew each scenario and how many got each slot) and **Corrections**: *give* awards a slot of a scenario to every student
who drew it, *ignore* takes it out of their total (marked out of fewer marks, `n/a` in the CSV). They live in
`/srv/exam/<exam id>/corrections.json` (written by the helper, `0640 root:itc-exam`, with who and why); the raw points stay in the CSV.

Tests: `python3 server/examroom/test_exambank.py` (the engine, a bank with 3 scenarios per part as files, the preview equal to the
recorded draw, the report and corrections), `test_examroom.py` (`open` and the helper's draw, undraw and correct actions, a broken
bank leaving the exam sealed, `examctl draw`, the new API routes, a student with an unreadable draw).

## The midterm as built

| Choice | Default | Where to change it |
|---|---|---|
| Length | 60 minutes | `duration_min` in the config, or `examctl open --minutes` |
| Parts | A to D, one per lab (1 to 4), 10 marks each, 40 in all | `parts` in the config (any subset) |
| Marks in a part | Four tasks of 2 marks, checked automatically from the files; one short written answer of 2 marks, marked by hand | `midterm.py` |
| Where students work | `~/midterm/`, made when the exam opens | `folder` in the config |
| Submission | A root snapshot of every `~/midterm/` at close. No `git push`, so no remote host is needed and no password is typed while the session is recorded | `examctl close` |
| Personal values | The pilot labs' scheme (`oslab.picker`, term name from `/opt/itc-os-labs/term.conf`, label `midterm`), so neighbours' answers differ | `midterm.values` |
| What students see of their progress | Which files exist (`3 of 5`), never whether they are right | `show_progress` (only `presence` is built) |
| Matrix rain in the exam room | Off; the faint scanlines stay | `rain: true` turns on a still rain |
| SEB | Not required | `seb.required`, `seb.config_keys` |
| Flags | review: more than 60 s away in total, one large paste, a second screen, or a side panel opened. high: more than 5 min away, 3 large pastes, or offline more than 2 min while open. A large paste is more than 200 characters | `flags` (`second_screen` and `side_panel` take `"review"`, `"high"` or `""` to ignore them, for example in a room whose computers all have two screens) |
| Exam lock | On: leaving fullscreen locks the exam, and so does starting it a second time (a reload or a second tab leaves fullscreen without the page saying so). The paper and the terminal are hidden and the gateway drops what the student types until they enter the 4-digit code the board shows next to their name (hidden as `••••` until you press **show**). Every lock has its own code; 3 wrong codes in a minute make the student wait, and the board shows the wrong codes | `lock.on` (`[]` turns it off; `"panel"` and `"leave"` lock on a side panel or on leaving the page too), `lock.max_attempts` |
| Keyboard Lock | On in Chrome and Edge once the page is fullscreen: Esc, Ctrl+W and Ctrl+T reach the terminal, and leaving fullscreen takes a press-and-hold of Esc | `app/exam/exam.js` (`goFullscreen`) |
| Presets and the wait | The **Exam** preset is the strict room above (the default). The **Practice** preset, for Practice Linux Commands, keeps the room locked the same way (fullscreen and side panel) but a locked student **waits** instead of asking for a code: 30 s the first time, doubling each time that day, at most 5 min. The page shows the countdown, then "Continue in fullscreen". The board shows "waiting" with the time left, and **unlock** ends a wait early | `lock.mode` (`code` or `wait`), `lock.wait_s`, `lock.wait_max_s`, `profile`; or the preset buttons on the Settings tab |

Every task uses only commands from the core of its lab, not from the extensions, Plus or Challenge. Part A covers files
and processes (`mkdir`, `echo >`, `cp`, `mv`, `sleep &`, `ps`, `uname -r`). Part B covers paths and names with spaces
(`mv`, `cp`, relative paths, `find -type f`). Part C covers wildcards and links (`ls` with `?`, `ln`, `ln -s`, `mv`,
`rm --`, `ls -li`). Part D covers `grep '^word,'`, `wc -l`, `cut -d, -f2` and `>` with `2>`.

## One-time setup on the server

Keep a second root shell open while you change sshd.

1. Packages, and check versions (`websockets` must be 13 or later):

   ```bash
   sudo apt install tmux acl python3-websockets python3-asyncssh
   python3 -c 'import websockets, asyncssh; print(websockets.__version__, asyncssh.__version__)'
   ```

2. Pull the repository as usual (`deploy.sh`), then copy the paper. It is not in git, and students have shell
   accounts on this server, so make it private straight away:

   ```bash
   scp -i ~/.ssh/DEPLOY_KEY server/examroom/midterm.py USER@SERVER:ITC-I4GIC-OS/server/examroom/
   ssh USER@SERVER 'chmod 600 ~/ITC-I4GIC-OS/server/examroom/midterm.py; ls -ld ~ ~/ITC-I4GIC-OS/server/examroom/midterm.py'
   ```

   Copy the scenarios the same way (`scp -r server/examroom/bank USER@SERVER:ITC-I4GIC-OS/server/examroom/`, then
   `chmod -R go-rwx` on it). `install` copies the paper to `/opt/itc-os-exam/midterm.py` as `0640 root:itc-exam`, and the
   scenarios to `/opt/itc-os-exam/bank/` (a `0750 root:itc-exam` folder, files `0640`; a file no longer in the repository
   is removed; it refuses to install with no scenario files): root and the website service can read them,
   students cannot. When the API builds a student's paper, it shows only that student's paper, and only while the
   exam is open. Students never run the paper's code: `examctl open` builds each student's starting files as root and
   hands them over.

3. Install. Read the dry run first.

   ```bash
   cd ~/ITC-I4GIC-OS
   sudo python3 server/examroom/examctl.py --dry-run install --staff pisey --origin https://rathpiseyalpha.github.io
   sudo python3 server/examroom/examctl.py install --staff pisey --origin https://rathpiseyalpha.github.io
   ```

   To run the exam from the instructor board as well (open, extend, close, hardening, settings: see "The control
   panel" below), add `--web-control --roster ~/ITC-I4GIC-OS/app/server/roster.json`. Without it the board still
   shows everything, unlocks students and downloads the report, and the other buttons stay off.

   This creates the `itc-exam` group (pisey and the gateway), the `examgw` service account, `/opt/itc-os-exam`,
   `/etc/itc-os-exam` (ticket key, gateway SSH key, known hosts) and `/srv/exam`. It also writes
   `/etc/ssh/sshd_config.d/20-itc-exam-keys.conf`, so sshd also reads the root-owned `/etc/ssh/exam_keys/<user>`.
   Students' own keys keep working. Then it starts `itc-os-examgw` and restarts `itc-os-presence`, whose drop-in
   adds the `itc-exam` group. From then on, run `sudo examctl ...` (a link in `/usr/local/sbin`).

4. Route the gateway through the Cloudflare tunnel. Add a rule **before** the API's rule, so `/term` on the same host
   goes to port 5010. In a locally managed tunnel's `config.yml`:

   ```yaml
   ingress:
     - hostname: api-os.rathpisey.site
       path: ^/term
       service: http://127.0.0.1:5010
     - hostname: api-os.rathpisey.site
       service: http://127.0.0.1:5000
     - service: http_status:404
   ```

   With a dashboard-managed tunnel, add the same public hostname with the path `^/term` and the service
   `http://127.0.0.1:5010`, above the existing one. Check it: `curl https://api-os.rathpisey.site/term/health` prints
   `ok`.

5. The exam config, the class group and the gateway key for each student:

   ```bash
   sudo cp /opt/itc-os-exam/exam.example.json /root/midterm.json   # edit id, title, times, flags
   sudo examctl config /root/midterm.json
   sudo examctl group --roster ~/ITC-I4GIC-OS/app/server/roster.json
   sudo examctl keys  --roster ~/ITC-I4GIC-OS/app/server/roster.json
   ```

   `group` puts exactly the roster's accounts in `osclass`. It refuses if a staff account is on the roster. Students
   get the group at their next login.

6. Check sshd does what it should, still with a root shell open:

   ```bash
   sudo sshd -t
   sudo sshd -T -C user=STUDENT,addr=127.0.0.1,host=localhost | grep -i authorizedkeysfile
   ```

   The second line must list both `.ssh/authorized_keys` and `/etc/ssh/exam_keys/%u`.

## Dry run (before the first exam)

Use test accounts, not students. Every session leaves a recording and a tmux session in its account.

```bash
for n in 01 02 03; do sudo useradd -m -s /bin/bash ostest$n; echo "ostest$n:CHOOSE-A-PASSWORD" | sudo chpasswd; done
printf '{"t01":{"user":"ostest01","name":"TEST One"},"t02":{"user":"ostest02","name":"TEST Two"},"t03":{"user":"ostest03","name":"TEST Three"}}\n' | sudo tee /root/test-roster.json
```

The website's roster must contain the test accounts while you try the page. Add them to `app/server/roster.json` and
restart `itc-os-presence`, then remove them afterwards. Then:

1. Make a practice config (`"id": "practice-1"`), then run `examctl config`, `group`, `keys` and
   `open --roster /root/test-roster.json`.
2. Open `https://rathpiseyalpha.github.io/ITC-I4GIC-OS/exam.html`, log in as `ostest01`, and press **Start the exam**.
   Type in the terminal, reload the page (the shell must come back), and open a second tab (the first must say the
   exam is open somewhere else). Paste a long text and switch tabs.
3. Open `exam-board.html` as `pisey`. The test account is `connected`, its flag shows `review`, and **▶ replay** plays
   the session. Back in the exam, hold Esc to leave fullscreen: the exam locks, the board shows `locked` and a code,
   and typing that code unlocks it. Count how often honest testers get locked by accident (notifications, permission
   prompts, the laptop sleeping) before relying on the lock in a room of 40.
4. `sudo examctl harden on --roster /root/test-roster.json`, then:
   - SSH from your laptop as `ostest02`: it must print the "exam is running" message and close;
   - the web terminal must still work;
   - `curl https://example.com` inside the web terminal must fail;
   - `sudo examctl harden status --roster /root/test-roster.json`.
5. Load test with as many test accounts as students, if you can create them (the spec's Capacity section):
   `sudo python3 /opt/itc-os-exam/loadtest.py --users /root/test-users.txt --minutes 5`. Watch memory available.
   It sends the Origin `https://rathpiseyalpha.github.io`, the one `install --origin` allowed; change it with
   `--origin` if you installed another.
6. `sudo examctl close --roster /root/test-roster.json`. The page says "Time is up". The snapshot is in
   `/srv/exam/practice-1/collect/`. Then `sudo examctl report --roster /root/test-roster.json`.
7. `sudo examctl harden off --roster /root/test-roster.json`. SSH works again.

## The control panel

The exam board (`exam-board.html`) has five tabs:

| Tab | What it does | Needs web control |
|---|---|---|
| Live | The board and the replay, as before. A locked student's row has **show** (the code) and **unlock** (no code needed) | no |
| Exam | Phase and time left; **Open the exam** (minutes), **Extend** (+5, +10, +15 or any), **Close and collect**, **Unlock all**; the history of every action with who did it | open, extend, close: yes. Unlock: no |
| Settings | The Exam and Practice presets, exam lock on or off and its triggers, code or wait (and the wait times), wrong codes allowed, the flag levels and thresholds, title, length, SEB, rain. Title, length and SEB are fixed while the exam is open | yes |
| Security | Hardening on or off (with ending outside SSH sessions), **Prepare accounts from the roster** (`group` + `keys`), and whether the gateway and web control are running | yes |
| Results | **Download CSV** of the automatic points, from the snapshot after close or the live folders before | no |

Every button that changes the exam for everyone asks first and names the effect ("Close the exam for 40 students and
collect their files"). The CLI keeps working the same; use either.

**How it works, and what it means for security.** The website runs as an ordinary account and cannot do root
work. With `--web-control`, the board's buttons queue a request in `/srv/exam/requests/queue/`; a systemd path unit
(`itc-os-examctl.path`) starts `examctl agent` as root, which runs it and writes the result back (the panel shows it).

- An instructor login on the website can then start these root actions: open, extend, close, hardening on and off,
  prepare accounts, and the settings above. Nothing else: a request is an action name and small numbers, checked by
  the website and again by the agent. The roster path comes from the root-owned `/etc/itc-os-exam/agent.json`.
- The agent runs only the root-owned copy in `/opt/itc-os-exam` (rerun `install` after updating the code), and every
  root action refuses a roster with `root`, staff, the gateway or any account under uid 1000 on it.
- Unlocking does not use root: the website drops `/srv/exam/control/<user>.json` and the gateway picks it up.
- After updating the code (`deploy.sh`), run `sudo python3 server/examroom/examctl.py install ...` again with the same
  options: it copies the files to `/opt/itc-os-exam`, which the website, the gateway and the agent use, and restarts
  them. Until then the board runs new code against the old copy and shows errors.
- Turn web control off: `sudo systemctl disable --now itc-os-examctl.path; sudo rm /etc/itc-os-exam/agent.json`.
  If the panel says "waiting for the server" for more than 15 seconds, check `systemctl status itc-os-examctl.path`
  and `journalctl -u itc-os-examctl`.

## Exam day

| When | What |
|---|---|
| The day before | `sudo examctl config` with the real `id`, `group` and `keys` with the real roster, `sudo examctl status`. Students make sure they know their server password. Put the exam link in the course announcement |
| 15 minutes before | Students open the page and log in. They see the waiting room. Open the board |
| Start | `sudo examctl harden on --roster ROSTER --kick` (`--kick` ends SSH sessions from outside), then `sudo examctl open --roster ROSTER`; or, with web control, **Turn hardening on** (Security) and **Open the exam** (Exam). Students press **Start the exam** |
| During | A student whose exam locked raises a hand: press **show** under `locked` in the Connection column and read them the 4-digit code (the `locked` filter lists only them). Codes stay hidden as `••••` until you press **show**, so a screen others can see does not give them away. Watch the board. `sudo examctl extend 10` gives everyone ten more minutes; do it before the end time (after it, students whose page already says "Time is up" must reload the page). A flag is a reason to watch the replay, never a mark |
| End | The page closes the terminals by itself at the end time. Run `sudo examctl close --roster ROSTER` (or **Close and collect**): it waits 12 seconds for the last terminals to close, then takes the snapshot. Then `sudo examctl harden off --roster ROSTER` (or **Turn hardening off**) |
| Marking | `sudo examctl report --roster ROSTER > midterm.csv`, or **Download CSV** on the Results tab, gives the automatic points (32 of 40). Read each `answers.md` in `/srv/exam/<id>/collect/<user>/<time>/` for the four written answers. The replay is in the board |

The waiting room asks students to connect to the network they will use for the whole exam before they start: changing
Wi-Fi during the exam means leaving fullscreen, which locks it (a page cannot switch networks itself).

If a student's network drops: they wait. After 3 seconds the page shows "Connection lost" with what it is doing
("This computer is offline: check the Wi-Fi", "Trying again in 4 s"), and it reconnects by itself, at most 10 seconds
after the network is back, to the same shell. It tells them not to reload, because with the lock on a reload locks the
exam. A network that goes silent without closing anything is noticed by a missed heartbeat within about 20 seconds.
What they type while offline is not sent; they type it again.

If a student's computer breaks: they log in on another computer. The shell and the files are the same; the board shows
a reconnect. With the lock on, starting on the new computer locks the exam: read them the code.

## Safe Exam Browser

When the exam runs in computer rooms with SEB (Windows or macOS):

- Start URL: the `exam.html` address. URL filter: allow only `rathpiseyalpha.github.io` and `api-os.rathpisey.site`
  (the page loads nothing else).
- In the config, set `"seb": {"required": true, "config_keys": ["<the Config Key from SEB Config Tool>"],
  "public_api": "https://api-os.rathpisey.site"}`. The API then gives the paper and terminal tickets only to requests
  with the matching `X-SafeExamBrowser-ConfigKeyHash` header. Test this at the dry run: SEB versions differ in which
  requests carry the header.
- Turn off SEB shortcuts that take Ctrl+C, Ctrl+D, Ctrl+Z, Ctrl+R, Ctrl+L or Tab. tmux has no prefix key, so nothing
  else is needed.
- Keep the clipboard inside SEB if AI and outside text are not allowed.

## What the page can and cannot see

Switching tab or window, leaving fullscreen, paste length and everything typed are recorded. So are two signals that
only Chrome and Edge give fully:

- **A second screen.** The browser says whether the desktop spans more than one screen (`screen.isExtended`). The
  waiting room asks the student to disconnect it, and the board's Screen column shows `2 screens`. Firefox and Safari
  show `unknown`. The page cannot see what is on that screen.
- **A side panel.** When the page gets narrower while the browser window keeps its size, something opened beside it:
  an AI side panel (Gemini in Chrome, Copilot in Edge) or docked developer tools. The page notes when it opened and
  for how long. While it is open, a cover says "Close the side panel to continue": the paper is taken out of the page
  and the terminal is hidden and cannot be typed in, so an assistant that reads the page finds only the cover. Both
  come back as they were when the panel closes; the timer keeps running. Zoom and resizing the window are not counted.
  Typing in the panel also takes the focus away, which is recorded as leaving the page. A page cannot close the panel
  itself: on managed computers, turn the assistant off by browser policy, or use SEB.

**What the lock does not do.** It fires on what the page reports, so a student who edits the page's script can
suppress it: it stops the ordinary "press Esc, look, come back" and not a determined student. Alt+Tab and the Windows
key leave Chrome in fullscreen, so with only `fs_exit` they are recorded as leaving the page, not locked (add `"leave"`
to lock on them too, at the cost of more accidental locks). Time spent locked is not given back: the board shows it
(`unlocked 2 × 1:30`), and `examctl extend` gives time to everyone.

Which site was opened, what an AI assistant read from the page, a phone, or a second computer cannot be seen. See the
spec's table. Students are told in the waiting room that the session is recorded.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| The page says "the server refused the shell" | No key for that account (`examctl keys`), sshd not reloaded, or the account is locked. `journalctl -u itc-os-examgw` names the reason |
| The strip says "reconnecting…" for everyone | The tunnel has no `/term` route, or the gateway stopped: `curl https://api-os.rathpisey.site/term/health`, `systemctl status itc-os-examgw` |
| "The exam server is not ready (ticket key)" | `itc-os-presence` is not in the `itc-exam` group: `systemctl restart itc-os-presence` after install |
| Board says `unreadable` under Progress | A student removed the staff ACL from `~/midterm`. The snapshot at close is taken by root and still has everything |
| Students cannot log in all at once | The login limiter now counts only failed attempts, per account (a room shares one address). Check the API was restarted after the update |
| A student is locked again right after unlocking, with "the browser refused fullscreen" | The browser cannot or will not go fullscreen (Firefox with fullscreen turned off, an old browser). They move to Chrome or Edge; read them the new code there |
| A student says the unlock code does not work | Each lock has its own code: read the one on the board now (it refreshes every 5 s). After 3 wrong codes in a minute the page says to wait a minute.  Many wrong codes on the board means guessing: watch the replay. A locked student who reloads stays locked |
| The clock on the page is wrong | The page uses the server's time from `/api/exam/state`. Check `timedatectl` on the server |

## Testing without the server

On a Linux machine or WSL with `tmux`, `sshd` and `pip install websockets asyncssh flask flask-cors`:

```bash
python3 server/examroom/test_examroom.py        # midterm, gateway (local shell), gateway over real SSH, API
python3 server/examroom/devstack.py             # local preview; prints the two URLs (password: test)
```

The SSH test starts an unprivileged sshd on 127.0.0.1 as yourself. Nothing needs root.
