# Instructor plan — OS Lab 1 — Introduction to Operating Systems (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own names and numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format and is the first time students meet it. It keeps the six tasks and the six objectives of the original Lab 1, with simpler steps, and splits the work into **Part A in class (7 points)** and **Part B homework (3 points)**, both graded as Lab 1. Read the [student instruction](../../../labs/lab1/lab1-instruction.md) and the [report template](../../../labs/lab1/README.md) first.

## Objectives

1. Identify basic operating system and kernel information.
2. Use essential Linux file and directory commands.
3. Install, remove, and purge software using the APT package manager.
4. Understand the difference between a program and a running process.
5. Observe multitasking in a running operating system.
6. Detect whether an operating system is running on a virtualized environment.

What changed from the first revision: no PID, PPID or process-state reading, no shell variables, no `wait`, no `command -v`. Students use only commands the original lab taught. The original screenshots and the GitHub workflow are back, as homework.

## Where Each Task Runs

| Task | Where | Graded in |
|---|---|---|
| 1 OS identification, 2 files, 4 process, 5 multitasking, 6 virtualization | Course server, in class | `oslab check lab1`, 2 points |
| Prediction (`oslab predict`) and live checkpoint (`oslab checkpoint`) | Course server, in class | 2 and 3 points |
| 3 APT install, remove, purge | The student's own Ubuntu (WSL or a virtual machine), at home | Report and homework evidence, 2 and 1 points |
| Push Part A from the server, clone on the student's Ubuntu, report with three screenshots, push, pull on the server | Server and student's computer | Report and homework evidence |

Students have no `sudo` on the server and must not get it, which is why Task 3 is at home.

## Homework: Deadline, Marking and Link to the Class

- **Deadline.** Set the Lab 1 deadline on the website's admin page (the same deadline mechanism as the other labs). The late penalty is applied from the dates of the Git commits on the server, so the student must have **pulled** the repository there. Students who push but do not pull show as missing.
- **Website progress.** The grader counts `README.md`, the six `taskN_...` files, and the folders `task2_files` and `images`. It measures what was handed in, not whether it is correct.
- **Marking the 3 homework points.** Report understanding (2): read the four short answers and the correction of the prediction. About two minutes each; skim for answers that do not use the student's own results (their file names, their `count`, their purge screenshot). Homework evidence (1): the APT file, three screenshots, README, pulled to the server on time.
- **Where AI enters.** Homework is unsupervised. The report is the part most easily written by AI, so it carries 2 of the 10 points. The 7 in-class points cannot be earned that way when you walk the room.
- **Optional link back.** At the start of the next class, ask one question aloud or on paper: "After `apt-get remove`, did `/etc/mc` still exist?" A student who skipped Task 3 will not know.
- **Students without a working Ubuntu.** Offer a lab computer for 30 minutes, or let them do Task 3 on a friend's machine with their own screenshot. A student must not lose points only because their WSL does not start.

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md). Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab1.checkpoint` does **not** exist.
- As an ordinary test account: `oslab doctor` must say `class inbox: connected`; `oslab start lab1`; `oslab check lab1` (expect 0/4). On the server, `lsb_release`, `systemd-detect-virt`, `lscpu`, `ps`, `top`, `nproc`, `git` and `tree` must work.
- Send every student the host name and account name at least two days before. Ask them to log in once and run `oslab prelab lab1`. Ask them to open their own Ubuntu once too.
- Test the Part B route once yourself: `git push` over HTTPS from the server with a personal access token, `git clone` on another machine, `git push` there, and `git pull` on the server. Each student needs a GitHub account and a token. Prepare a two-minute demonstration of creating a token.
- `tree` must be installed on the server; Step 4 of Part B uses it.
- Set the homework deadline on the website.
- Prepare a roster file with one account name per line. All `oslab-teach` commands below take `--roster FILE`.
- The evening before, run `sudo oslab-teach board lab1 --roster FILE`. Students with an empty `prelab` column have probably never logged in; contact them.

## The Lab 1 Guide Slides

Project the guide during Part A: [guides/slides.html](../../../labs/lab1/guides/slides.html) (arrow keys to move; the same slides as a [PDF](../../../labs/lab1/guides/lab1-guides.pdf)). Students can open it on their own screens. The slides are wider than 16:9, so they fill a normal laptop browser window. Commands are shown in dark terminal windows; the words in orange are the ones a student must replace. Slide numbers:

| Slides | Content | Use at minute |
|---|---|---|
| 1 to 3 | Cover, objectives, opening question | 0–10 |
| 4 to 19 | Linux in brief, kept from the earlier guide: why Linux matters, its origin, the kernel, distributions, families, package management, DPKG and APT, the shell, the prompt and `~` | Before the lab |
| 20 to 27 | The two parts, timetable, helper commands and why, rules, setup, and what the personal values and the capital placeholders mean | 0–10 |
| 28 to 29 | Task 1: kernel and distribution | 10–20 |
| 30 to 37 | Task 2: the ten commands, where output goes, the syntax of `>` and `>>`, `..`, the steps | 20–40 |
| 38 to 39 | The prediction | 40–50 |
| 40 to 43 | Tasks 4 and 5: program and process, several at once | 50–65 |
| 45 to 47 | Task 6: virtual machine | 65–75 |
| 44, 48 | What multitasking really is (the demonstration), Plus and Challenge | 75–90 |
| 49 to 54 | The live checkpoint: why it exists, the steps, an example run, the file task, marking | 90–105 |
| 55 to 64 | Part B: how the work travels, push from the server, clone, Task 3, screenshots, push, pull, the tree (homework briefing) | 105–120 |
| 65 to 68 | Grading, common mistakes, takeaways, the next lab | 105–120 |

**The 16 background slides (4 to 19) are not in the 120-minute timetable.** They take about 15 to 20 minutes. Show them in the lecture before the lab, or ask students to read them as part of the pre-lab. If you show them at the start of the lab, shorten the 75–90 block.

The background pictures (Linux is everywhere, the kernel diagram, the layers table, the two timelines, the command-line picture and the portrait of Linus Torvalds) come from the earlier guide. Check that you may redistribute them before you share the slides outside the class.

The deck is built from `lectures/files/decks/lab-01/gen.py`. Change the text there, never in the generated files.

## Timetable and What You Do

Keep `sudo oslab-teach board lab1 --roster FILE --watch 20` open on your own screen. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–10 | Setup | Login support. Use the `started` column to find who is not in yet. Show the five `oslab` commands once with your own test account |
| 10–20 | Task 1: Which system is this? | Type along. Ask: "Which number is the kernel, which is Ubuntu?" |
| 20–40 | Task 2: Files and folders | The longest typing task. Expect the placeholder mistake (`FILE1.txt` typed literally) and `>` where `>>` was needed; hint 3 covers both. Explain `..` on the board |
| 40–50 | Prediction, then class discussion | At minute 45 read the **prediction spread** aloud without names. The `remove` question splits the class; let two students argue each side, and tell them they will test it at home |
| 50–65 | Tasks 4 and 5 | Task 4 has a 30-second wait; use it to answer questions. The up-arrow trick for repeating `sleep 300 &` is new to most students. Remind them to take the Task 5 screenshot |
| 65–75 | Task 6: Is this a virtual machine? | Write the `|` pipe on the board: output of one command goes into the next. Remind them to take the Task 6 screenshot |
| 75–90 | Instructor demonstration, then Plus and Challenge | Demonstrate real multitasking on the projector (see below). Then work only with students whose `checks` column is below 4/4 |
| 90–105 | Live checkpoint | At minute 90 say "close AI tools" and run `sudo oslab-teach release lab1` |
| 105–120 | Debrief and homework briefing | Use the script below. Show the Part B route once on the projector: push from the server, clone, Task 3, README, push, pull. Run `sudo oslab-teach export lab1 --roster FILE > lab1.csv` |

### The demonstration (75–90)

`sleep` waits and uses no processor, so Task 5 shows several processes, not how the processor is shared. Show it with a **bounded** load, on your own account, not the students':

```bash
nproc
for i in 1 2 3 4 5 6; do timeout 30 yes > /dev/null & done
top
```

Ask: "There are more busy processes than processors. What does each get?" Point at the `%CPU` column. Press `q`; the loads end by themselves after 30 seconds. Do not ask 60 students to run the loop at once.

## Expected Results

- **Task 1:** the first line of `uname -a` starts with `Linux`, then the host name and the kernel release. `lsb_release -a` gives the distribution (here Ubuntu 26.04). The two version numbers differ.
- **Task 2:** `task2_files` holds `FILE1.txt` (`This is file FILE1`) and `FILE2_renamed.txt`. `task2_file_commands.txt` holds the working-folder path and four listings.
- **Task 3 (homework):** after install, `which mc` prints `/usr/bin/mc` and `/etc/mc` exists. After `remove`, `/etc/mc` still exists (the settings stay). After `purge`, `ls -ld /etc/mc` prints "No such file or directory". Run it once on the current Ubuntu release before class to confirm.
- **Task 4:** `ps` lists `bash`, `sleep` and `ps`. After 30 seconds the `sleep` line is gone, but `which sleep` still prints a path.
- **Task 5:** `COUNT` `sleep` lines at once (the Task 4 one has ended). If a student started them more than 300 seconds before running `ps`, some are gone: they start again.
- **Task 6:** the server is a virtual machine (`kvm` on the first line, `Hypervisor vendor: KVM`). WSL prints `wsl`. A physical machine prints `none` and no vendor line.
- **Plus and Challenge:** `top` shows a `Tasks:` count in the hundreds; most are system services started when the server booted.

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab1 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. The numeric, yes/no and kernel-release answers are marked automatically: `ps` shows `n` sleep lines, `which sleep` still prints a path (yes), the kernel release equals `uname -r` on the server, and the new folder holds 2 files after step 4. The kernel answer cannot be guessed: the student has to run `uname -r`. The task is: make a folder, create a file with one line of text, copy it, rename the original, and save the listing.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The four marked answers (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points_of_2` in the export |
| The folder, file, copy, rename and saved listing are right | 1 | same column |
| The sentence says a program is a file and a process is a running copy of it | 1 | read `checkpoint_sentence` in the export; about 10 seconds each |

The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (about 8 minutes)

1. Show the prediction spread. Ask who was surprised by Task 4, and who thinks `remove` deletes the settings. Tell them they will see the answer at home.
2. Ask: "`sleep` ended. Is the program gone?" Lead to program (file) versus process (running copy).
3. Ask: "How many programs ran at once in Task 5, and how many processors does the server have?" Lead to multitasking by fast switching.
4. Tell students that every pilot-format lab uses the same five commands, and ask what was unclear about them. Write the answers down for the retrospective in the [roadmap](../../ROADMAP.md).

## Misconceptions

- A program and a process are the same thing.
- `remove` and `purge` do the same: students expect `/etc/mc` to vanish after `remove`.
- `>` and `>>` are interchangeable; a record file then shows only the last command.
- An empty `ps` result means `sleep` is missing, not that it already ended.
- Several `sleep` processes prove that the processor is shared. They do not; they only exist at the same time.

Use the hints in order (`oslab hint lab1 1` to `3`).

## Caveats Moved Out of the Student Text

- `oslab check lab1` reads the result files in the workspace. It cannot prove when they were written. The homework evidence is judged from the repository on the server.
- `ps` without options lists only the processes of the terminal the student is typing in. This is why students see only a few lines.
- 60 students with up to four `sleep 300` processes each is a trivial load. The processes end by themselves.
- The Python web server on port 8080 from the original lab is left out: only one student could use that port on a shared server.
- Pushing from the server is the first hurdle of Part B: GitHub refuses the account password and wants a personal access token. Let students do Step 1 in the last minutes of class, while you can help. A student who cannot push from the server can still do the rest; they then copy their Part A files by hand.
- The order matters: the server pushes once (Step 1), the student's computer pushes after that (Step 3), and from then on the server only pulls. A student who commits on the server again after Step 1 gets a merge problem when pulling.

## Fallback

Without the class inbox, everything works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. If the server is down, students can do Part A in WSL or a local Linux with the [local setup](../../../labs/SETUP.md); Part B is already local.

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| Files: `oslab check lab1` passes the four Core milestones (class) | 2 |
| Report (homework): kernel and distribution, remove and purge, program and process, virtual machine, written from the student's own results | 2 |
| Prediction saved in time, and an honest confirmed/corrected note (class) | 2 |
| Live checkpoint: answers, the file task, and the sentence (class) | 3 |
| Homework evidence: the APT file, three screenshots, README, pushed and pulled to the server on time | 1 |

The export gives you the first and third rows and most of the fourth. Read only the report for the second.
