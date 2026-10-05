# Lab 10 — Optional Extensions

Follow [the required instruction](lab10-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. Schedule the Actual Backup — Personal Crontab Only

This optional task needs a working cron daemon, personal `crontab` permission, and a completed backup script. The core heartbeat helper is separate. Cron has **five time fields and no year field**; date-like month/day settings recur, not a one-off event.

1. Inspect `date -Is`, `date '+%Z %z'`, `command -v bash`, and `crontab -l`. Record an unavailable daemon/permission instead of claiming execution. Do not paste a full private crontab into a public report.
2. Test the backup from a different working directory and restricted environment first. Use the actual absolute script path; if it contains spaces, quote it in the cron command. Verify that the script owns its paths and retention is bounded.
3. Use `crontab -e` to add **one** temporary entry with your actual paths. Preserve all unrelated lines. Example (replace `YOUR_USERNAME` before use):

   ```cron
   * * * * * /usr/bin/flock -n /home/YOUR_USERNAME/oslab-work/lab10/backup-cron.lock /bin/bash /home/YOUR_USERNAME/oslab-work/lab10/backup.sh >> /home/YOUR_USERNAME/oslab-work/lab10/cron-backup.log 2>&1 # OSLAB-LAB10-BACKUP
   ```

   The nonblocking lock prevents overlapping backups. The script should not depend on an interactive PATH. `%` in crontab command text has special handling; keep date-format expressions inside the script. This entry repeats every minute until removed.
4. Observe at most two minutes (or inspect supplied logs if cron unavailable), verify a new archive and restore one file, then promptly remove only the `# OSLAB-LAB10-BACKUP` entry with `crontab -e`. Confirm unrelated entries remain. Remove the core heartbeat with `lab10-cron remove` separately.
5. Keep this a short experiment, not ongoing service configuration. A successful `crontab` installation is not evidence the daemon executed the job.

## B. Health Report and Restore Capstone

1. Write an owned report script that prints timestamp, `df -h "$PWD"`, `du -sh project backups`, latest archive name and `tar -tzf` verification result. Use absolute paths derived from the script; avoid listing secrets.
2. Create one damaged project copy under the lab, choose a known archive, and restore into a **fresh separate directory**. Compare the expected report/config with `cmp`; do not restore over your original project.
3. Save two selected observations and cap/delete only the owned demonstration log once no scheduled job can write to it. Retention in this lab keeps three recognized backup archives; it does not impose a universal disk quota or promise crash recovery.
