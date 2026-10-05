# Validation record — first revision

Local checks on Ubuntu in WSL, October 5, 2026 (Asia/Phnom_Penh teaching date):

- `python3 -m py_compile server/oslab.py server/lab10_cron.py` passed on Python 3.8.10.
- `bash -n server/install.sh server/initialize-students.sh server/test_local.sh` passed.
- `bash server/test_local.sh` passed all 11 starts, repeat start preserving student work, Lab 2 behavioural check, reset archive, cleanup preserving unrelated files, symlink/path rejection, and Lab 10 cron marker installation/removal using a fake personal crontab. The fake crontab retained an unrelated entry. It also reproduced two stale-read sales in the deliberately flawed Lab 8 script, observed one accepted sale under the full lock, detected an opposite-order Lab 9 lock timeout, and completed both workers in ordered mode.
- `bash server/install.sh --dry-run --allowlist=server/students.example.txt` printed the plan and made no changes. The example list is intentionally empty; real account selection needs a private allowlist.
- `python tools/validate_revision.py` checked all 11 student routes, exact 120-minute totals, 10-point instructor rubrics, and relative Markdown links.
- `node --check app/js/config.js`, `node --check app/js/github.js`, and `git diff --check` passed.

The race and deadlock labs use bounded, owned-process exercises. Their successful runs are demonstrations, not proofs of race absence. Public fixture checks are not secure grading. Actual student implementations and an administrator installation were not executed in this local test.

Before class, validate on the real shared Ubuntu server: the account allowlist, ownership/traversal, disk quotas, installed commands, cron availability and timezone, locked-down home directories, optional FUSE and filesystem-image permissions, multi-user permission preparations if used, and disposable VM snapshot/recovery for the GRUB extension. Do not use a production bootloader for validation.

Technical references used: [util-linux flock manual](https://man7.org/linux/man-pages/man1/flock.1.html), [crontab format manual](https://man7.org/linux/man-pages/man5/crontab.5.html), and [GNU du manual](https://man7.org/linux/man-pages/man1/du.1.html).
