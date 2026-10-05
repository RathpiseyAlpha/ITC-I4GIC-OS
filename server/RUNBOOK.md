# Shared Ubuntu server deployment

The scenario helper is a read-only installed Python script. It creates per-user fixtures under `~/oslab-work`; it does not create accounts, alter SSH/PAM/shells, install packages or register services. A separate ordinary-user Lab 10 helper changes only its marked practice cron entry when explicitly invoked. Student work is private by the account's home permissions and is never executed by the helper. Public `check` is behavioural feedback, not tamper-proof grading.

## Required changes and capability checks

Required: Python 3.8+, Bash, coreutils, `/usr/local/bin` writable by an administrator, existing individual accounts, and enough home quota for 11 small fixtures plus a 32 MiB optional image. Check with `python3 --version`, `command -v runuser`, `df -h`, `getent passwd USER`, and `stat -c '%a %U %n' /home/USER`. Files installed in `/opt/itc-os-labs` are root owned and world readable; each `~/oslab-work` is user owned and mode 700.

Topic tools: `gcc`/pthread (Lab 5), `flock` (Labs 8–9), `tar` and user cron (Lab 10), `mkfs.ext4`/`dumpe2fs` and optional FUSE (`fuse2fs`, `/dev/fuse`, user namespace policy) for Lab 11. Check availability; use the documented trace or unprivileged fallback if missing. Disposable VM snapshots are required before any GRUB recovery extension. Never alter the shared server's bootloader. Multi-user permissions need separately prepared narrow accounts/groups or use the individual trace fallback.

## Exact local administrator sequence

From the repository root, create a private copy of `server/students.example.txt` outside git with exactly the existing student account names, one per line. The scripts reject malformed names and missing accounts; no prefix matching is used.

```bash
python3 -m py_compile server/oslab.py server/lab10_cron.py
python3 tools/validate_revision.py
python3 tools/build_lab_revision.py --check
bash -n server/install.sh server/initialize-students.sh
sudo bash server/install.sh --dry-run --allowlist=/secure/path/students.txt
sudo bash server/initialize-students.sh --dry-run --allowlist=/secure/path/students.txt
sudo bash server/install.sh --apply --allowlist=/secure/path/students.txt
sudo bash server/initialize-students.sh --apply --allowlist=/secure/path/students.txt
sudo runuser -u EXISTING_STUDENT -- /usr/local/bin/oslab doctor
sudo runuser -u EXISTING_STUDENT -- /usr/local/bin/oslab start lab2
sudo runuser -u EXISTING_STUDENT -- /usr/local/bin/oslab check lab2
```

The install is rerunnable and replaces only the managed helper. Initializing again preserves existing work. Dry runs print plans and make no changes. Inspect `/opt/itc-os-labs/.itc-oslab-install` before an update. Back up the installed `oslab.py`, rerun install from a reviewed commit, then validate as an ordinary account. Existing workspaces are not migrated automatically; fixture version changes need an explicit new workspace or a student's `oslab reset` after they save work.

## Before class and cleanup

Check each student can run `oslab doctor`, `start`, `status`, `hint`, and `check` without sudo. Check ownership and space, topic tools, cron availability and timezone (`date '+%F %T %Z'`), and VM snapshot/fallback materials. Set class date/time in the course announcement; `lab10-cron install` adds an observable one-minute practice entry with a unique marker, not a hard-coded future date. `lab10-cron status` checks it and `lab10-cron remove` removes only that entry. Cron's ordinary five fields have no year field. The scenario helper creates no processes; students should wait for their own bounded jobs to exit, not kill by name or reuse stale PID files. Optional `oslab clean labN` removes only the marked current fixture; saved attempts remain for manual inspection.

Lab 3 requires internal symbolic links, including temporarily dangling targets. The helper permits links resolving inside the managed lab and never follows them during cleanup; links escaping that tree are refused. It also refuses detected mountpoints: unmount optional FUSE images before lifecycle operations. Recheck these behaviors after updating an existing helper installation.

## Rollback and uninstall

To roll back the helper, restore the backed-up `oslab.py` and `lab10_cron.py` and validate as a student. For uninstall, first confirm `/opt/itc-os-labs/.itc-oslab-install` and the expected wrapper content, then remove `/usr/local/bin/oslab`, `/usr/local/bin/lab10-cron`, and `/opt/itc-os-labs` using administrator review. Keep student `~/oslab-work` untouched; students can archive or remove their own work. Do not delete accounts, crontabs, or unrelated `/opt` contents.

No live deployment was performed while preparing this revision. Real-server validation still needs account ownership, FUSE policy, cron timezone, disk quota, and optional VM recovery checks.
