# Operating Systems course materials — ITC

Institute of Technology of Cambodia, Department of Information and Communication Engineering. This repository contains lecture resources, class activities, 11 lab instructions (Lab 11 is an optional bonus), and the existing course web application and exam functionality.

The revised labs use **120 minutes per lab**, individual solutions, a short optional peer exchange, and an independent changed-case checkpoint. Each instruction restores explicit objectives, the original topic/task progression, numbered guided commands, expected observations, starting and submission trees, and topic-specific evidence. AI is permitted for investigation and testing, but not for the initial prediction or checkpoint. The primary environment is a shared Ubuntu server with an individual account for each student; local Linux/WSL is an unprivileged fallback. GRUB recovery needs a disposable VM with a snapshot.

## Start here

- [Course outline](course-outline.md), [exam briefing](EXAM-BRIEFING.md), [lecture notes](lectures/notes/README.md), [class activities](lectures/class-activity/README.md), and [visualizations](lectures/visualizations/README.md)
- [Environment setup](labs/SETUP.md), [complete lab index](labs/INDEX.md), and [shared lab report template](labs/REPORT-TEMPLATE.md)
- [Per-lab audit](teaching/REVISION-AUDIT.md), [implementation record](teaching/IMPLEMENTATION-PLAN.md), [validation](teaching/VALIDATION.md)
- [Server deployment runbook](server/RUNBOOK.md) and [per-user scenario helper](server/oslab.py)

| Lab | Core topic | Instruction |
|---|---|---|
| 1 | OS inspection and owned processes | [Lab 1](labs/lab1/lab1-instruction.md) |
| 2 | Navigation and file placement | [Lab 2](labs/lab2/lab2-instruction.md) |
| 3 | Links and user-local libraries | [Lab 3](labs/lab3/lab3-instruction.md) |
| 4 | Pipelines, redirection and owned processes | [Lab 4](labs/lab4/lab4-instruction.md) |
| 5 | Processes, threads and joins | [Lab 5](labs/lab5/lab5-instruction.md) |
| 6 | Permissions and access decisions | [Lab 6](labs/lab6/lab6-instruction.md) |
| 7 | Bash arguments and safe paths | [Lab 7](labs/lab7/lab7-instruction.md) |
| 8 | Stock race and complete critical section | [Lab 8](labs/lab8/lab8-instruction.md) |
| 9 | Deadlock diagnosis and recovery | [Lab 9](labs/lab9/lab9-instruction.md) |
| 10 | Backup retention and scoped scheduling | [Lab 10](labs/lab10/lab10-instruction.md) |
| 11 (bonus) | Regular-file disk images and filesystem evidence (bonus) | [Lab 11](labs/lab11/lab11-instruction.md) |

Students work in their own repositories and save only concise artifacts, selected tests, prediction/correction, and conceptual explanation. Each instruction maps its 10-point rubric to that lab's objectives; the checkpoint is collected separately. Optional extension guides give procedures for the broader original topics. Older slides/HTML guides remain background references; the Markdown instructions define the current required route.

Instructor files in this public repository are also public. Prepare fresh graded variants and keep confidential keys in a private distribution system. Public scenario checks give feedback, not secure grading.

## Website and repository origin

The static course site is in `index.html` and `app/`. Its GitHub file tree defaults to the new destination, [RathpiseyAlpha/ITC-I4GIC-OS](https://github.com/RathpiseyAlpha/ITC-I4GIC-OS), through `app/js/config.js`. The original source of this revision is [RathpiseyAlpha/ITC-OS-2026](https://github.com/RathpiseyAlpha/ITC-OS-2026). The application backend and exam features were preserved. Review and configure deployment separately; this revision does not deploy to the live server.
