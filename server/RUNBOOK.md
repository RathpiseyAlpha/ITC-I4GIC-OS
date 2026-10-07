# Shared Ubuntu server deployment

The scenario helper is a read-only installed Python script. It creates per-user fixtures under `~/oslab-work`; it does not create accounts, alter SSH/PAM/shells, install packages or register services. A separate ordinary-user Lab 10 helper changes only its marked practice cron entry when explicitly invoked. Student work is private by the account's home permissions. The helper never runs with privileges; `oslab check lab8` runs the calling student's own `buy.sh`, as that student, in a temporary copy of their store (at most two short processes at a time, each stopped after 15 seconds). Public `check` is behavioural feedback, not tamper-proof grading.

## Required changes and capability checks

Required: Python 3.8+, Bash, coreutils, `/usr/local/bin` writable by an administrator, existing individual accounts, and enough home quota for 11 small fixtures plus a 32 MiB optional image. Check with `python3 --version`, `command -v runuser`, `df -h`, `getent passwd USER`, and `stat -c '%a %U %n' /home/USER`. Files installed in `/opt/itc-os-labs` are root owned and world readable; each `~/oslab-work` is user owned and mode 700.

Topic tools: `gcc`/pthread (Lab 5), `flock` (Labs 8–9), `tar` and user cron (Lab 10), `mkfs.ext4`/`dumpe2fs` and optional FUSE (`fuse2fs`, `/dev/fuse`, user namespace policy) for Lab 11. Check availability; use the documented trace or unprivileged fallback if missing. Disposable VM snapshots are required before any GRUB recovery extension. Never alter the shared server's bootloader. Multi-user permissions need separately prepared narrow accounts/groups or use the individual trace fallback.

## Class inbox, term name and instructor tool (pilot labs 1, 2 and 8)

`install.sh --apply` also creates:

| Path | Owner and mode | Purpose |
|---|---|---|
| `/opt/itc-os-labs/term.conf` | root, `0644` | One line, the term name (for example `2026-s1`). It seeds every student's personal values. Created once from `--term=NAME`, or `term-YEAR` if you give none, and never replaced by a later install. Changing it during a term changes every student's values |
| `/var/lib/itc-oslab/inbox` | root, `1733` | Students' `oslab` drops small JSON records here: pre-lab, start, prediction, hints, checks, checkpoint. Students can add files but cannot list the folder. A student can remove only files they own |
| `/var/lib/itc-oslab/release` | root, `0755` | `oslab-teach release labN` writes `labN.checkpoint` here. Until that file exists, `oslab checkpoint labN` refuses to start |
| `/usr/local/bin/oslab-teach` | root, `0755` | Instructor tool. It must list the inbox, so run it with `sudo` |
| `/opt/itc-os-labs/inbox-reader` | root, `0644` | Only with `--inbox-reader=ACCOUNT`. Names the one account, besides root, that may list the inbox |

### Marking from the website

The admin dashboard (Labs tab, **view and mark**) shows each student's files, their lab records and a form for the rubric points. The lab records come from the inbox, so the account that runs the website service must be able to list it:

```bash
sudo bash server/install.sh --apply --inbox-reader=pisey
sudo systemctl restart itc-os-presence
getfacl -p /var/lib/itc-oslab/inbox
```

`getfacl` must print `user:pisey:r-x`, and `stat` now prints `1773` for the inbox because of that entry. Students still cannot list the folder. The name is kept in `inbox-reader`, so later installs keep the access; to remove it, delete that file and install again.

- Marks are saved in `app/server/marks.json` (mode `0600`, not in git). Back it up with the roster. A student sees a mark and its comment only after you tick **Show this mark and comment to the student** or use **Show all labN marks to students**.
- The suggested points on the form come from the lab records. They are a starting value; the saved points are always the ones you typed.
- The website keeps its own list of first-seen records in the service account's `~/.oslab-teach/`, separate from the one `sudo oslab-teach` keeps. Its `sent more than once` note counts from the first time anyone opened that student's mark screen.

Instructor commands, each with `--roster FILE` (one account name per line, the same file as the allowlist):

```bash
sudo oslab-teach board lab8 --roster /secure/path/students.txt --watch 20
sudo oslab-teach release lab8
sudo oslab-teach key lab8 --roster /secure/path/students.txt
sudo oslab-teach export lab8 --roster /secure/path/students.txt > lab8.csv
```

What this is and is not:

- A record is attributed to the account that owns the file, not to the name written inside it.
- The tool remembers every record it has seen in `~/.oslab-teach/` of the account that runs it (root's home under `sudo`). If a student sends a second prediction or checkpoint, or removes one, the board shows `rewritten` for that student. Open the board at least once before the prediction and once after it, so the first answers are on record.
- The value and answer code is public. Personal values prevent copying between neighbours; they are not secrets. The checkpoint values depend on a random release value, so they cannot be prepared before you release.
- This is class feedback and marking support, not tamper-proof grading. A student who sets `OSLAB_INBOX` or `OSLAB_RELEASE_DIR` to another place only puts themselves in practice mode; their records do not reach the board.
- Inbox files are small (under 1 KB each, about 20 per student per lab). Remove old ones between terms with `sudo find /var/lib/itc-oslab/inbox -type f -name 'lab*.json' -mtime +200 -delete` after exporting.
- To reopen a checkpoint released by mistake before any student answered, remove `/var/lib/itc-oslab/release/labN.checkpoint` by hand and release again.

## Exact local administrator sequence

From the repository root, create a private copy of `server/students.example.txt` outside git with exactly the existing student account names, one per line. The scripts reject malformed names and missing accounts; no prefix matching is used.

```bash
python3 -m py_compile server/oslab.py server/oslab_teach.py server/lab10_cron.py
python3 tools/validate_revision.py
python3 tools/build_lab_revision.py --check
bash -n server/install.sh server/initialize-students.sh
sudo bash server/install.sh --dry-run --allowlist=/secure/path/students.txt --term=2026-s1
sudo bash server/initialize-students.sh --dry-run --allowlist=/secure/path/students.txt
sudo bash server/install.sh --apply --allowlist=/secure/path/students.txt --term=2026-s1
sudo bash server/initialize-students.sh --apply --allowlist=/secure/path/students.txt
stat -c '%a %U %n' /var/lib/itc-oslab/inbox /var/lib/itc-oslab/release /opt/itc-os-labs/term.conf
sudo runuser -u EXISTING_STUDENT -- /usr/local/bin/oslab doctor
sudo runuser -u EXISTING_STUDENT -- /usr/local/bin/oslab values lab2
sudo runuser -u EXISTING_STUDENT -- /usr/local/bin/oslab start lab2
sudo runuser -u EXISTING_STUDENT -- /usr/local/bin/oslab check lab2
sudo oslab-teach board lab2 --roster /secure/path/students.txt
```

`stat` must print `1733 root` for the inbox and `755 root` for the release folder. `oslab doctor` must print `class inbox: connected`. The board must show `yes` under `started` and `0/4 x1` under `checks` for the test student. Run `install.sh` **before** `initialize-students.sh`: Lab 2's files are made from each student's values, and those depend on `term.conf`.

The install is rerunnable and replaces only the managed helper. Initializing again preserves existing work. Dry runs print plans and make no changes. Inspect `/opt/itc-os-labs/.itc-oslab-install` before an update. Back up the installed `oslab.py`, rerun install from a reviewed commit, then validate as an ordinary account. Existing workspaces are not migrated automatically; fixture version changes need an explicit new workspace or a student's `oslab reset` after they save work.

## Before class and cleanup

Check each student can run `oslab doctor`, `start`, `status`, `hint`, and `check` without sudo. Check ownership and space, topic tools, cron availability and timezone (`date '+%F %T %Z'`), and VM snapshot/fallback materials. Set class date/time in the course announcement; `lab10-cron install` adds an observable one-minute practice entry with a unique marker, not a hard-coded future date. `lab10-cron status` checks it and `lab10-cron remove` removes only that entry. Cron's ordinary five fields have no year field. Apart from the bounded `check lab8` test, the scenario helper creates no processes; students should wait for their own bounded jobs to exit, not kill by name or reuse stale PID files. Optional `oslab clean labN` removes only the marked current fixture; saved attempts remain for manual inspection.

Lab 3 requires internal symbolic links, including temporarily dangling targets. The helper permits links resolving inside the managed lab and never follows them during cleanup; links escaping that tree are refused. It also refuses detected mountpoints: unmount optional FUSE images before lifecycle operations. Recheck these behaviors after updating an existing helper installation.

## Rollback and uninstall

To roll back the helper, restore the backed-up `oslab.py`, `oslab_teach.py` and `lab10_cron.py` and validate as a student. Keep `term.conf`. For uninstall, first confirm `/opt/itc-os-labs/.itc-oslab-install` and the expected wrapper content, export any marks you still need, then remove `/usr/local/bin/oslab`, `/usr/local/bin/oslab-teach`, `/usr/local/bin/lab10-cron`, `/opt/itc-os-labs` and `/var/lib/itc-oslab` using administrator review. Keep student `~/oslab-work` untouched; students can archive or remove their own work. Do not delete accounts, crontabs, or unrelated `/opt` contents.

No live deployment was performed while preparing this revision. Real-server validation still needs account ownership, FUSE policy, cron timezone, disk quota, and optional VM recovery checks.
