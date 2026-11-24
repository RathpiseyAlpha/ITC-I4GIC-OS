# Practice Linux Commands: runbook

Students solve short scenarios in a real shell on the course server, in the exam room's web terminal, for XP, a rank,
badges and a small capped bonus. The plan and the rules are in
[teaching/PRACTICE-SCENARIOS-PLAN.md](../../teaching/PRACTICE-SCENARIOS-PLAN.md); this file is how it runs.

## The pieces

| Piece | Where | Runs as |
|---|---|---|
| Student page | `practice.html`, `app/practice/practice.js`, `app/practice/practice.css` | the browser |
| Instructor page | `practice-board.html`, `app/practice/practice-admin.js` | the browser (admin login) |
| API routes | `app/server/app.py`, `/api/practice/*` and `/api/admin/practice/*` | the API service (the staff account) |
| Terminal | `server/examroom/gateway.py`: a ticket with `x = "practice"` opens `~/practice/<scenario>/` in tmux session `practice-<scenario>` | `examgw`, then SSH as the student |
| Runner | `runner.py`, service `itc-os-practice`, socket `/run/itc-os-practice/runner.sock` (group `itc-exam`) | root |
| Collector | `collect.py`: the student's side of a setup or a check | the student (`runuser`, `env -i`, `python3 -I -S`, a systemd scope with limits) |
| Rules | `practice.py`: catalogue, values, XP, ranks, badges, ledger, bonus | imported by the API and the runner |
| Scenarios | `scenarios/*.py` (Easy to Hard, public), `private/*.py` (Super challenges, git-ignored) | the runner (root) judges; the API reads `META`, `brief` and `hints` |
| Data | `/srv/practice/`: `ledger.jsonl`, `runs/<user>.json`, `profiles.json`, `bonus.json`, `settings.json` | written by the API |
| Recordings | `/srv/exam/rec/<user>/practice/<scenario>/*.cast`, events and the wait lock in `/srv/exam/rec/<user>/practice/` | the gateway; casts older than 14 days are removed |

**One login: the portal's.** The practice page, the exam room and both boards use the portal's sign-in (the same
browser tab). Without one they send the student to `index.html?next=<page>`, the portal's own login page, which
comes back after a successful login. Only the exam room inside Safe Exam Browser keeps its own small login form,
because SEB opens it directly and blocks the portal's other sites.

**Who is trusted.** A check never runs through the student's login shell, so `~/.bashrc` cannot fake it. The runner
starts the collector as the student; the collector makes itself non-dumpable, says `ready`, receives the request,
and sends back plain data: the workspace tree (names, modes, inodes, link targets, small files' text), the student's
processes, and the output of the student's script on given inputs. The scenario's `checks` then judge that data as
root, inside the runner. Only the API writes the ledger, and only from a runner result, under a file lock, so a
double-clicked Check awards XP once.

**An exam closes practice.** While an exam is open (or its time is up but it is not closed), the API refuses practice
and the gateway ends practice sessions within 10 seconds. Practice runs in its own tmux server (`itcexam-practice`),
and `examctl open` ends it for every student and kills their processes whose working folder is under `~/practice/`
(the night shift, the zombie farm, leftover sleeps), so nothing from practice runs during the exam. The practice room
never reads `exam.json`'s lock settings.

## Install (part of `examctl install`)

```sh
# the Super challenges are not in git: copy them first, from the instructor's machine
scp server/practice/private/*_super.py USER@SERVER:ITC-I4GIC-OS/server/practice/private/
scp -r server/practice/drills USER@SERVER:ITC-I4GIC-OS/server/practice/   # the roadmap's drills are not in git either (hints and checks give the answers)
sudo python3 server/examroom/examctl.py install --staff pisey --origin https://rathpiseyalpha.github.io \
     --roster /home/pisey/ITC-I4GIC-OS/app/server/roster.json [--practice-url wss://api-os.rathpisey.site/term]
```

It copies the practice files to `/opt/itc-os-exam/practice/` (`private/` as `0640 root:itc-exam`), writes
`/etc/itc-os-exam/practice.json` (the gateway address and the roster), creates `practice.key` (the key for hidden
inputs, root only) and `/srv/practice/` (`2750 pisey:itc-exam`), and starts `itc-os-practice.service`.
`--no-practice` leaves it all out. The gateway key for each student (`examctl keys`) is the same as for the exam.

Then turn on the portal link: `features.practice: true` in `app/js/config.js`, and raise `config.js?v=N` in the pages.

Check it: `systemctl status itc-os-practice`, and the practice board (`practice-board.html`) shows "runner running".

## Adding a scenario

One file in `scenarios/` (or `private/` for a Super challenge), named after its id:

| Part | What it is |
|---|---|
| `META` | `id` (`track-level`), `track`, `level` (`easy`, `medium`, `hard`, `super`), `title`, `learn`; `xp` and `minutes` default by level |
| `values(pick)` | personal values; `pick(label, n)` is the pilot labs' picker, seeded by the student, the scenario and the attempt |
| `fixture(v)` | `{"dirs": [...], "files": {path: text or {"t": text, "m": mode, "age": days} or {"l": target} or {"h": other path}}}`; `{ROOT}` in a link target is the workspace |
| `brief(v)` | blocks: `{"p": text}`, `{"ol": [items]}`, `{"pre": text}`; `` `code` `` and `**bold**` work |
| `hints(v)` | three hints, from a nudge to the commands (none for a Super challenge) |
| `collect(v, hidden)` | what to bring back: `tree`, `texts` (only these files' text), `procs`, `again` (a second look after a few seconds), `runs` (the student's script on given inputs) |
| `checks(data, v, hidden, info)` | a list of `kit.ck(id, label, ok, why)`; `why` points at the problem without giving the answer |
| `hidden(v, hpick)` | Super challenges: the hidden inputs, drawn with the root-only key, new for each attempt |

`kit.py` has the helpers (`Tree`, `ck`, `distinct`, `procs_matching`, `zombies`). A new file is picked up without a
restart; the board lists files that fail to load.

## Tests (Linux or WSL, no root)

`test_practice.py` holds working solutions to every public scenario, so it is git-ignored like `test_examroom.py`;
`private/test_super.py` too.

```sh
python3 server/practice/test_practice.py            # rules, the 12 public scenarios, the gateway room, the API
python3 server/practice/private/test_super.py       # the 4 Super challenges (private, like the checkers)
python3 server/examroom/test_examroom.py            # the exam room is unchanged
python3 server/examroom/devstack.py --phase sealed  # local preview: practice.html and practice-board.html
```

The tests use a development runner (`runner.py --dev`), which runs the collector as you, without `runuser` or a
systemd scope. The root path (`runuser`, `systemd-run`, the socket's group) is only exercised on the server.

## Linux skill roadmap: the engine (build step 1, 2026-11-24)

Plan: `teaching/SKILL-ROADMAP-PLAN.md`. Built so far, tested in WSL (`python3 test_roadmap.py`, plus the whole of
`test_practice.py`); no drills, no quizzes, no page and no API route yet.

- `drillkit.py`: `D(...)` describes a drill and turns into an object shaped like a scenario module; `S(...)` is a
  guided step (lesson line, task, the ids of the checks that decide it, optional hint). A guided drill must declare its
  checks (`checks=[(id, label)]`): every declared check is always reported with a stable id, so steps cannot point at the
  wrong check. Drill files live in `drills/*.py` (`DRILLS = [D(...)]`).
- `practice.py`: `STAGES`, `SKILLS` (57), `drills()`, `exercise(sid)`, `all_metas()`, `steps_of()`, `step_progress()`,
  `stage_badges()`, `skills_summary()`. `catalog()`, `metas()`, `LEVELS`, `LEVEL_NAME` and `TRACK_IDS` still mean the
  scenarios only, so the API is unchanged; step 5 of the plan moves it to `all_metas()`. A drill is 15 XP and 5 minutes,
  a quiz 10 XP and 5 minutes (`BASE_XP`, `MINUTES`); a drill or quiz played again earns no XP; a quiz never adds a skill.
- `collect.py` (runs as the student): read-only facts named in the request (`kernel`, `cpus`, `memtotal_kib`,
  `osrelease`, `pid1`, `ports`, `account`, `owner:<path>`, `mount:<path>|~`, `package:<path>`; a path must be in
  `FACT_PATHS`), a process's `nice` and `sigign`/`sigcgt`, and `.tar.gz` listing without extraction (size, member and
  decompressed-byte limits, `O_NOFOLLOW`).
- `runner.py` sets up and checks drills like scenarios; `examctl install` copies `drillkit.py` and `drills/*.py`
  (public, like the Easy to Hard scenarios). Quiz keys will go in `private/quizzes/`, which `examctl` does not copy yet
  (its `private/*.py` copy is not recursive): add that in build step 2.

## Linux skill roadmap: the quiz engine (build step 2, 2026-11-24)

`quizzes.py`, tested by `test_quizzes.py` (its own sample quizzes; run with `test_roadmap.py` and `test_practice.py`).
No questions yet (steps 3 and 4 write them) and no page or API route (step 5).

- **A quiz file** is `server/practice/private/quizzes/*.py` (git-ignored: it holds the keys): `QUIZZES = [Quiz(id, stage,
  title, learn, questions=[Q(id, skill, variants)], n=5)]`. A variant is `{"q", "right", "wrong": [3 or more]}` or a
  function of `pick` that builds one from the student's personal values. The loader refuses a quiz with a skill of
  another stage, fewer than three wrong choices, a right choice that is also wrong, repeated choices, a duplicate id,
  `n` larger than the questions, or a variant function that fails on any of eight different pickers.
- **Draw.** `draw(quiz, user, attempt)` is recomputed from the student and the attempt each time, so nothing is stored,
  a reload shows the same questions, and a new attempt draws other variants and shuffles the choices (a to d) again.
  `public(draw)` is all the page gets: no key, no skill.
- **Grade.** `grade()` gives the score, pass or fail (80% rounded up: 4 of 5) and the skills to review. It never says
  which choice was right and no question is marked as you go, so the key cannot be found by trying choices.
- **Hint.** One per quiz: `use_hint()` takes two wrong choices away from the question the student is on (asking again
  for the same question is free; a second question is refused).
- **Attempts.** `begin()`, `use_hint()`, `submit()` and `state()` work on a run record the API stores: a 5-minute
  countdown, the one hint, and a 30-second wait after a fail (also after a failed revision attempt). A student who passed
  may play again at once, for no XP. `clear_entry()` is the ledger line of a pass; `practice.standings()` pays the first
  pass only (10 XP, 9 with the hint, half when late) and a quiz never adds a skill.
- **Keys and the API.** The API process reads the quiz files in `/opt/itc-os-exam/practice/private/quizzes/` (root:itc-exam,
  folder 0750, files 0640, copied by `examctl install`), the same trust as the Super challenges' checkers, which it also
  loads. Students cannot read the folder.

## Linux skill roadmap: stages 1 and 2 (build step 3, 2026-11-24)

24 guided drills and 6 quizzes (30 questions), tested in WSL by `test_drills.py` (git-ignored: it holds every solution).

- `drills/stage1_shell.py` (Shell basics, 12) and `drills/stage2_text.py` (Text and pipelines, 12). Each has a lesson
  line and a task per step, two hints, personal values (all but "Where am I?"), and declared checks. `test_drills.py` sets
  up each drill, checks that the fresh workspace fails with a reason for every failed check and the declared ids, solves
  it with real shell commands, checks that it passes with the same ids and all steps done, and tries 27 wrong answers a
  student is likely to type (a copy for a move, `rm -rf old*` that also removes the file to keep, `*.conf*` that also matches
  `.conf.bak`, an `uniq` without `sort`, and so on).
- `private/quizzes/stage1.py` and `stage2.py` (git-ignored): three quizzes per stage, five questions each, two variants
  each (60 variants), two of them built from the student's personal values. Drafted by Claude: **the instructor reviews
  every question before it goes on the server.**
- `Silence the errors` cannot see a screen, so `./scan` writes a note (`.scan-last`) of where its two outputs went in the
  last run (`readlink /proc/$$/fd/1` and `/2`), and the check reads it: results into `found.txt`, errors into `/dev/null`.
- The collector now also returns `realroot` (the workspace's real path), for "Where am I?".
- Not looked at in the practice page: there is no Roadmap tab yet (step 5).

## Linux skill roadmap: stages 3 to 6 (build step 4, 2026-11-24)

33 more drills and 12 more quizzes (60 questions), so the whole roadmap is now written: 57 drills and 18 quizzes (90 questions,
180 variants). Tested in WSL by `test_drills.py` (git-ignored): 465 checks, every drill solved with real commands, 74 wrong answers
rejected, every remix solved with its own values, and the end-to-end XP of the whole roadmap.

- `drills/stage3_perms.py` (8), `stage4_procs.py` (8), `stage5_script.py` (10), `stage6_insight.py` (7).
- **Guidance by stage.** Stages 1 and 2: guided steps. Stages 3 and 4: one step with a lesson line, one Check. Stages 5 and 6:
  goal only (no steps). Ten drills are read-only (they only look at the system); "Biggest folder" works on a folder it is given.
- **Stage 3** judges modes (`octal`, `symbolic`, `umask`, `shared`), the account (`identity`) and fixed facts about a few system
  paths (`owner`, `setuid`: the collector reads them; the student cannot change anything outside `~/practice/`).
- **Stage 4** judges the student's own processes (`procs`: pid, parent, state, command line, niceness, the signals each ignores).
  Background programs are started from `~/practice/`, so `examctl open` stops them before an exam. The drills' scripts write a log
  line when they get a signal, so "stop it with kill's default signal" and "ended by the right signal" are things a check can see.
- **Stage 5** judges a script by running it: `runs` in the collector request starts `bash SCRIPT ARGS` in a copy of the workspace
  (with temporary folders for the files it works on), as the student, and the check reads the output, the exit status and the
  folders afterwards. Some inputs are not shown in the task. `tar` is checked by listing the archive (nothing is extracted).
- **Stage 6** compares the student's answer with the real values the collector reads (`mount`, `memtotal_kib`, `osrelease`, `ports`,
  `package`, `account`). These are the same for every student, except where a drill draws a path.
- The collector's facts gained `cpus_listed`; stage 4 and 6 drills rely on `procs`, `nice`, `sigign`, `facts`, `runs` and `tars`.
- **Whole roadmap:** 57 x 16 + 18 x 10 = 1 092 XP (Power user; Operator is 1 200), all 57 skills, six stage badges and the Linux
  Journeyman. The scenarios are the way to the higher ranks.

## Linux skill roadmap: the page, the API and the board (build step 5, 2026-11-24)

Tested in WSL by `test_roadmap_api.py` (a temporary copy of the app, the development runner and sample quizzes) and by looking at
the page in a browser against a local stack. Not deployed, and not tried with the real gateway terminal.

- **The API (app/server/app.py).** A drill goes through the same routes as a scenario (`scenario`, `start`, `ticket`, `check`, `hint`,
  `reset`, `remix`, `replays`): `_practice_scenario()` now finds a drill too. The reply says `kind: drill`, two hints, the stage and skills,
  and the `steps` (without lesson lines on a remix); a Check on a guided drill returns `progress` (which step is current); an award names
  the new skills. XP, ranks, skills and badges are computed from `prac.all_metas()`; the scenarios' map still uses `prac.metas()`.
  New: `GET /api/practice/quiz?id=`, `POST /api/practice/quiz/start`, `/quiz/hint` and `/quiz/submit` (the key never leaves the server:
  the reply has the questions and four choices, and after Submit only the score and the skills to review). A quiz's run record sits in
  `runs/<user>.json` under its id, with the attempt, the countdown, the hint, the wait and `leaves` (see below).
  `home` carries `roadmap` (six stages with drills, quizzes and skills, the skill tags and `journeyman`), and the profile `skills`.
  The instructor's `overview` carries `roadmap` rows (with "stuck on step N" for guided drills), `stages` and `skills_total`, and the
  students' skill counts; the CSV export counts drill and quiz XP.
- **The page (practice.html, app/practice/practice.js and .css).** Two tabs above the map: **Scenarios** and **Roadmap** (remembered for
  the visit). The Roadmap has a card for each stage with its badge, progress bar, skill tags (green when acquired; a click lists the
  exercises that train it) and its drill and quiz tiles. A drill opens in the practice room like a scenario, with its steps in the task
  panel (the current step open, the next ones closed, a hint labelled with its step). A quiz has its own screen: one question at a
  time, four choices, answers kept in the page until Submit, the one hint (confirmed first), and a result screen with the score,
  the skills to review and the wait before the next attempt.
- **The quiz lock** (superseded the same day by "Quiz lock through the gateway" below; kept here only as history): the first build had
  a fullscreen cover and a counted `leaves`, with nothing on the server.
- **The board (practice-board.html, practice-admin.js).** A **Roadmap** tab lists every drill and quiz by stage (kind, XP, started,
  cleared, median time, hints and checks per clear, and "stuck on step"), and the Students tab has a Skills column.
- `examctl install` now also copies `quizzes.py`.

## Linux skill roadmap: skill tags and steps on the scenarios (build step 6, 2026-11-24)

The roadmap is now complete in code. Tested in WSL by `test_drills.py scenarios` and `test_roadmap_api.py`.

- **Skill tags.** Each of the 16 scenarios has `META["skills"]` (12 public, 4 private Super challenges). A clear acquires them like a
  drill's. They show on the scenario's tile, in its intro card, in the Roadmap's skill tags (a click lists drills, quizzes and scenarios
  that train the skill), and in the clear dialog ("New skill: ...").
- **Steps.** The 8 Easy and Medium scenarios have a `steps(v, remix=False)` function (see `kit.guided`), so the practice room shows them
  one step at a time like a guided drill: Easy has up to three steps that name the commands, Medium one or two that say what to reach.
  Hard and the Super challenges stay goal only. A step names checks the scenario always reports; a test checks that the steps name
  every check once, that a fresh workspace is on step 1 and that a solved one has every step done. A remix has no lesson lines.
- **Counts of steps:** links-easy 3, links-medium 1, paths-easy 1, paths-medium 2, pipes-easy 2, pipes-medium 1, processes-easy 2,
  processes-medium 2. A check that already passes on a fresh workspace (such as "the originals are still there") is put in the same
  step as an action, never in a step of its own, so a step never shows as done before the student has done anything.
- **The board** shows "stuck on step N" in the Scenarios tab too, and the numbers of guided scenarios.

## Linux skill roadmap: quiz lock through the gateway (2026-11-24)

A quiz is now locked on the server, the way the shell is, by a **quiz session** in the gateway and a **gate** in the API.

- **Gateway** (`server/examroom/gateway.py`). `POST /api/practice/quiz/ticket` signs a practice ticket with `k = "quiz"`. The gateway opens
  a session with no shell, no recording and no place in the queue (the `max_sessions` cap counts shells only). It keeps the page's
  events, the practice room's **wait lock** (the same `rec/<user>/practice/lock.json` as the shell: leaving fullscreen starts a wait of
  30 s that doubles each time that day, up to 5 minutes, shared across drills, scenarios and quizzes) and a heartbeat:
  `rec/<user>/practice/status.json` with `kind: "quiz"`, the quiz id and the attempt, refreshed every 5 s. A reload (a new "start" without
  the "stop" of a proper exit) locks with the reason `restart`. An exam that opens ends quiz sockets within 10 s like the shells. A quiz
  socket replaces a drill's shell socket of the same student (one practice page is connected at a time) and the other way round.
- **API gate** (`_quiz_gate` in `app/server/app.py`). A quiz has no typed input to drop, so the API holds things back: the questions
  (`GET /api/practice/quiz`), the hint and the submit are refused (423) unless this attempt has a live socket (status `kind` quiz, this quiz,
  this attempt, seen in the last 15 s) and the practice lock is **off**. A finished wait does not count as off: the gateway releases the
  lock when the page, back in fullscreen, asks. `Start` therefore returns no questions; the page connects, then asks for them.
- **Page** (`practice.js`). After Start the page opens the socket, sends `start`, and fetches the questions once connected. Leaving
  fullscreen sends `fs_exit`; the gateway answers with the wait and the page **drops the questions** (and asks again after "unlocked"),
  so nothing stays in the page's memory while locked. A browser that refuses fullscreen is locked with its own reason. "← roadmap" and
  Submit send `stop` (a proper exit, so coming back is not a reload). A lost connection shows "offline: reconnecting", disables Submit
  and retries with a back-off; the answers are kept in the tab.
- **What it is, and is not.** Like the shell's lock it depends on the page reporting fullscreen exits, so it deters and records; it does
  not stop a second device. What is checked on the server: no questions, hint or submit without a live socket for that attempt (a plain
  `fetch` from the console is refused), no answers during a wait, reloads and reconnects lock, and the wait doubles across the whole
  practice room. The board's Live list shows a student in a quiz with the quiz id as the scenario.
- Tests: `test_practice.py gateway` (quiz session: no shell or recording, status, lock, reload, stop, no queue place, exam ends it) and
  `test_roadmap_api.py` (the gate: no socket, other attempt, other quiz, a shell session, a stale or closed socket, locked, wait over but
  not released). Also tried in the browser against a local gateway (the pane refuses fullscreen, which gave the `fs_refused` lock and its
  doubling 8, 16, 32 s).
