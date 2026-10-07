# Validation record

## Pilot format for Labs 1, 2 and 8 — checked October 7, 2026

Checked in WSL Ubuntu as an ordinary user (UID 1000, Python 3.8.10), with a temporary inbox and release folder. Nothing was installed on, or deployed to, the teaching server.

- `python3 tools/validate_revision.py`: 11 routes pass; Labs 1, 2 and 8 are recognized as pilot format (contiguous 120-minute timetable matching the instructor plan, 2/2/2/3/1 rubric, all five `oslab` commands named).
- `python3 tools/test_lab_walkthroughs.py`: every Bash fence passes a syntax check; setup and guided fences of all 11 labs run. For the pilot labs the test replaces the example values with the test account's own values and runs the Core fences plus a model of the student-written steps: Lab 1 (revised on October 7 to the six original tasks, with no process IDs) runs Tasks 1, 2, 4, 5 and 6 exactly as written and reaches 4/4 in-class milestones, while a placeholder typed literally does not pass; Lab 2 reaches 4/4, Lab 8 shows the double sale with the supplied script, a double sale with wrong answer `a.sh`, and 3/3 with the public repaired model.
- `bash server/test_local.sh`: the earlier lifecycle and isolation checks still pass with personal Lab 2 file names. New checks: values are stable for one name and differ between two names; a second prediction is refused; the checkpoint is refused before release and a second release is refused; `check lab8` fails the supplied script and each of the three wrong answers on the two-buyer milestone and passes the repaired model; after release the limit change turns the fourth milestone from TRY to PASS; the board and CSV export show the test student with 3/3 answers, task done and 2 automatic points.
- A two-student run of Lab 2 through the checkpoint: the board showed the prediction spread, marked one student 4/4 and the other 1/4, and flagged the student who removed the local record and sent a second prediction as `rewritten` while keeping the first answer. A roster name with no records appears as an empty row.
- `bash server/install.sh --dry-run --term=2026-s1` prints the new inbox, release folder and term file and changes nothing.

Task 3 of Lab 1 (`apt-get install`, `remove`, `purge`) is homework on the student's own machine and needs `sudo` and a real package install, so it was not run; only its syntax was tested. The Part B route (`scp` from the server, clone, push, pull on the server) was also not run. Run it once on an Ubuntu VM before class to confirm that `/etc/mc` survives `remove` and disappears after `purge` on the current Ubuntu release.

Not checked, and required before class: the real inbox with mode `1733` owned by root and many accounts writing at once; `oslab-teach` under `sudo` (the tests use one UID and trust the name inside the record, which the real tool does not); `flock` on the server's home filesystem; `initialize-students.sh --apply`; and whether the new timetables fit a real session. `oslab check` for Labs 1 and 2 reads files the student wrote, so it shows that the evidence exists and is consistent, not when or how it was produced.

## Second revision — checked October 5, 2026

Checked October 5, 2026, using an ordinary Ubuntu/WSL account (UID 1000), Python 3.8.10, Bash and GCC. Tests use fresh temporary homes/workspaces, including paths with spaces. No live student accounts, personal cron entries, boot configuration, mounts or deployed services were changed.

## Document and Command Checks

- `python tools/validate_revision.py`: all 11 routes have three core objectives, explicit workspace entry, starting/submission trees, guided examples, tests, public checkpoint keys, exact contiguous 120-minute timetables, 10-point rubrics and valid local teaching links.
- `python tools/build_lab_revision.py --check`: index matches the authored lab titles. The tool updates only `labs/INDEX.md`; it does not rewrite instructions or plans.
- Rendered each instruction with the website's `marked` Markdown library: every Bash fence and all starting/submission trees became the expected code blocks. This is a rendering check, not browser interaction.
- `python3 tools/test_lab_walkthroughs.py`: all Bash command fences in student instructions, extension guides, setup and instructor plans passed syntax checking. All 11 core setup/guided command sequences ran in fresh fixtures. The following behavior checks passed:

| Lab | Executed check |
|---|---|
| 1 | Kernel/distribution record; two owned live sleep processes followed by wait/post-exit sample |
| 2 | Quoted reports moved/copied into the company tree; cmp and path from HR |
| 3 | Hard-link inode survives rename, soft-link failure/repair, new source bytes differ; compiled/loaded user-local shared library |
| 4 | Public reporting model: normal total 8, no-match 0, changed total 15, not-ok excluded, missing input rejected |
| 5 | Guided single worker, unfinished two-worker starter, repaired joins/results 6/12, changed B result 6 and zero steps; public C model compiled with warnings as errors |
| 6 | Ordinary-user directory-search denial with mode 600 and restoration to 700 |
| 7 | Public command model: spaces, leading-dash operand, no arguments and missing-plus-valid input with aggregate nonzero status |
| 8 | Exact student naive script exhibits stale-read sales; repaired student script accepts one concurrent sale; invalid/insufficient inputs preserve state; held lock gives bounded failure |
| 9 | Exact student opposite-order script shows a second-lock timeout; repaired ordered workers both finish; solo opposite worker reaches bounded barrier failure |
| 10 | Starter produces archive; public repair retains three recognized archives and preserves unrelated text/archive names; restricted environment from another directory; restored bytes match |
| 11 bonus | Sparse/written 8 MiB files; bounded regular 32 MiB image formatted and ext4 header inspected, without mounting |

The walkthrough test uses representative repairs in disposable copies. It does not grade all possible student implementations or prove all concurrency interleavings safe.

## Helper and Isolation Checks

`bash server/test_local.sh` passed all 11 fixture starts, repeat-start preservation, Lab 2 feedback, bounded reset/archive, cleanup preserving unrelated files, internal and dangling symbolic-link preservation, escaping-link/path rejection, and cron marker idempotence/removal using a **fake** personal crontab that retained an unrelated entry. It also reproduced the flawed/public repaired Lab 8 behavior and opposite/ordered Lab 9 models.

Python compilation, Bash syntax checks, static website JavaScript syntax and `git diff --check` passed as final local gates. Linux scripts are pinned to LF in `.gitattributes` so Windows checkouts do not introduce Bash shebang/line-ending failures.

## Required Checks Before Class

Real shared-server validation remains: individual account ownership/home traversal, quotas, helper installation/allowlist, installed topic tools, actual personal cron daemon and timezone, filesystem-specific flock behavior, narrow peer/group/ACL directories if used, optional FUSE mount/unmount, optional unmounted image resize, and disposable VM GRUB boot/recovery. The FUSE utility is absent in the local test environment. Mountpoint rejection is implemented; no actual FUSE mount was created to exercise that guard.

No browser interaction or full teaching session was run. Command syntax and executable cases cannot establish that the planned pace fits every student; pilot one session and adjust optional scope if needed. Existing visual guides were retained and may show the older route.

References checked for technical wording: [pthread_join](https://man7.org/linux/man-pages/man3/pthread_join.3.html), [flock](https://man7.org/linux/man-pages/man1/flock.1.html), [crontab format](https://man7.org/linux/man-pages/man5/crontab.5.html), [GNU GRUB configuration](https://www.gnu.org/software/grub/manual/grub/html_node/Simple-configuration.html), [GNU GRUB manual](https://www.gnu.org/software/grub/manual/grub/grub.html), [e2fsck](https://man7.org/linux/man-pages/man8/e2fsck.8.html), and [resize2fs](https://man7.org/linux/man-pages/man8/resize2fs.8.html). GNU GRUB full-page fetches timed out; the configuration/menu-edit details were available through indexed official manual excerpts. Optional VM procedures still require local instructor rehearsal.
