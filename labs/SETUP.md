# Student environment and local fallback

The primary environment is a **shared Ubuntu server with an individual account for each student**. Use the announced hostname and your assigned username. A classmate's login is not your account. The instructor prepares tools before class; students do not need sudo on the server.

## If `oslab` is already installed

Run the setup commands in your lab. `oslab start labN` creates or preserves your workspace; it does not enter it. You must run `cd` separately. Paths default to `~/oslab-work`, and an instructor may configure `OSLAB_WORKSPACE` to another directory below your home.

## Pilot-format labs (Labs 1, 2 and 8)

These labs give every student different values and collect answers through `oslab`, not on paper.

| Command | When |
|---|---|
| `oslab prelab labN` | Before class: three short questions, with explanations |
| `oslab values labN` | Any time: shows your own numbers, names or folders |
| `oslab predict labN` | Once, before the experiment. The first answer is kept |
| `oslab hint labN 1` | When you are stuck (levels 1 to 3). Hints cost no points |
| `oslab check labN` | As often as you like: shows which milestones pass |
| `oslab checkpoint labN` | Near the end, after the instructor opens it |
| `oslab status labN` | Shows what you have already saved |

`oslab doctor` tells you whether the class inbox is connected. On the server it is, and your answers go to the instructor. On your own Linux or WSL it is not: this is **practice mode**. Everything works, your answers stay in `~/oslab-work/.records/`, the checkpoint uses practice numbers, and your values may differ from the ones you get on the server.

Task 3 of Lab 1 (installing and removing software with APT) is homework. It needs `sudo`, so you do it on your own Ubuntu (WSL or a virtual machine), not on the server. Students have no `sudo` on the server.

## Local Linux or WSL, or a missing wrapper

These commands use Bash and Python 3.8+ as your ordinary user. First obtain the course repository, or use an existing clone. Do not clone a second copy over existing files.

```bash
cd "$HOME"
git clone https://github.com/RathpiseyAlpha/ITC-I4GIC-OS.git
```

Set `COURSE_REPO` to that clone's actual absolute path. The example below matches the clone above. If it already exists elsewhere, change only this path.

```bash
COURSE_REPO="$HOME/ITC-I4GIC-OS"
test -f "$COURSE_REPO/server/oslab.py"
```

If that check succeeds, define these session-local functions. They are wrappers around the same fixture/helper scripts; they do not install packages or edit your shell startup files.

```bash
oslab() { python3 "$COURSE_REPO/server/oslab.py" "$@"; }
lab10-cron() { python3 "$COURSE_REPO/server/lab10_cron.py" "$@"; }
oslab doctor
oslab list
```

Then follow the lab's `start`, `cd`, and `pwd` steps. These functions last for this Bash session. A new terminal needs them defined again. A missing compiler, personal cron daemon or filesystem tool has a topic-specific fallback in the lab; do not claim that a printed trace establishes executable behavior.

## Working directory versus submission repository

```text
~/oslab-work/labN/             # experiments and editable fixtures
~/os-se-YOUR_ID/
└── os-lab-YOUR_ID/            # existing personal course Git repository
    └── labN/                 # selected sources, evidence and README
```

Use your actual course repository path. Change the `SUBMISSION_REPO` example in each lab before copying. Save only the listed sources and selected records, not every generated file. Never copy credentials, compiled binaries, large images or full AI histories into the submission.

## Preserving work and collecting evidence

`oslab start` preserves existing work. `reset` explicitly archives a marked workspace (at most three attempts, each at most 2 MB) before creating a fresh one. Large images exceed that archive limit. `clean` removes the marked current workspace after evidence is saved; remove Lab 10's practice cron entry and unmount any optional FUSE image first.

Guided code may create or replace named demo files. On a resumed session, inspect those names first and save a copy of a script you have already changed. Do not reset a whole lab to correct one error.

Record a short terminal transcript with commands, inputs and decisive output. `tee evidence/normal.txt` displays and saves output; `tee -a` appends. The labs show where to use it. If you add handwritten interpretation to a text record, use an editor and keep raw observations distinguishable from explanations. A screenshot is useful for a GUI/VM boot screen, but repeated command screenshots are unnecessary.

To review a submitted script, recreate a fresh fixture with `oslab start labN` in a separate practice workspace below your home, then copy the source back to its original workspace location (for example `store/buy.sh`, `vault/worker.sh`, or `backup.sh` next to `project/`). The concise submission intentionally omits binaries and mutable fixture data; do not expect a copied script to find that data merely because it is in the submission folder.

In Labs 1, 2 and 8, predictions and checkpoint answers are saved by `oslab predict` and `oslab checkpoint`. In the other labs they are written on paper or the existing course worksheet before executing the relevant case; a final README can record that prediction but cannot prove when it was written.
