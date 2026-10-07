# OS Lab 1 — Introduction to Operating Systems (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class, plus a 10-minute pre-lab |
| Work | Individual. Your values are different from your neighbour's |
| Environment | Shared Ubuntu server with an individual account for each student. Local Linux/WSL works for practice ([setup](../SETUP.md)) |
| Tools | `bash`, `uname`, `ps`, `sleep`, `oslab` |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Lecture link | [Week 1 notes: introduction to operating systems](../../lectures/notes/week01-introduction-to-os.md) |

> **Scenario:** It is your first day at TechCorp. You log in to a server you have never seen. Find out which system it runs, then show that one program on the disk can run as several processes at the same time.

## Lab Objectives

After the Core, you can:

1. Find the kernel and the distribution of a Linux machine, and say how they differ.
2. Create and read files in your own folder with basic commands.
3. Start several processes from one program and explain their PID, parent PID and lifetime.

## How This Lab Works

You will use the same five commands in every lab of this kind.

| Command | What it does |
|---|---|
| `oslab values lab1` | Shows **your** numbers. Use them everywhere in this lab |
| `oslab predict lab1` | Saves your prediction once, before the experiment |
| `oslab hint lab1 1` | Gives a hint (levels 1, 2, 3). Hints cost no points |
| `oslab check lab1` | Looks at your evidence files and shows your milestones |
| `oslab checkpoint lab1` | Opens when the instructor says so, near the end |

- **Core** is for everyone. **Plus** and **Challenge** are for students who finish early. Full marks need only Core and the checkpoint.
- AI tools are allowed in Core, Plus and Challenge. They are **not** allowed in the prediction and the checkpoint.
- The first time you need a command, the lab shows it in full. The second time, you write it yourself.

## Before the Lab

Log in to the server once before class, so that password problems do not cost you lab time. Then run:

```bash
oslab doctor
oslab prelab lab1
```

## Timetable

| Minutes | Activity |
|---|---|
| 0–15 | Setup and a tour of `oslab` |
| 15–30 | Guided: which system is this? |
| 30–40 | Prediction, then class discussion |
| 40–65 | Core 1: one program, several processes |
| 65–75 | Core 2: choose your own timing |
| 75–90 | Plus and Challenge (or finish Core) |
| 90–105 | Live checkpoint |
| 105–115 | Debrief |
| 115–120 | Submit |

## Setup and Tour (0–15)

1. Start the lab and go into its folder.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab1
   cd "$OSLAB_WORKSPACE/lab1"
   mkdir -p evidence
   oslab values lab1
   ```

2. Type **your** two numbers into shell variables. The numbers below are only an example.

   ```bash
   count=3
   seconds=40
   ```

   If you open a new terminal, run `cd` and set these variables again.

3. Try the helper commands once, so you know them.

   ```bash
   oslab hint lab1 1
   oslab check lab1
   ```

   The check shows `TRY` three times. That is correct: you have not done anything yet.

4. Your folder looks like this:

   ```text
   lab1/
   ├── process.txt       # a short reminder
   └── evidence/         # you save your results here
   ```

## Guided — Which System Is This? (15–30)

1. Ask the kernel about itself. Run each command alone and read the answer.

   ```bash
   uname -s
   uname -r
   uname -m
   ```

2. Read the file that describes the distribution. Find `NAME` and `VERSION_ID`.

   ```bash
   cat /etc/os-release
   ```

   The **kernel** is the core program that manages the hardware. The **distribution** (for example Ubuntu) is the kernel plus many other programs, packaged together. They have different version numbers.

3. Practise files in your own folder.

   ```bash
   mkdir -p practice
   printf 'My first OS observation\n' > practice/notes.txt
   cp -- practice/notes.txt practice/notes-copy.txt
   ls -l practice
   cat practice/notes-copy.txt
   ```

   `>` creates a file or replaces what is in it. `>>` adds to the end.

4. Save a short record of the system.

   ```bash
   {
     uname -srm
     grep -E '^(NAME|VERSION_ID)=' /etc/os-release
   } > evidence/os-info.txt
   cat evidence/os-info.txt
   ```

## Prediction (30–40)

```bash
oslab predict lab1
```

Answer alone, without AI, before the experiment. A wrong prediction costs nothing. The class will look at the spread of answers together.

## Core 1 — One Program, Several Processes (40–65)

1. Find the program file, then start it once in the background.

   ```bash
   command -v sleep
   sleep "$seconds" &
   pid1=$!
   echo "first PID: $pid1"
   ```

   `&` starts the command in the background. `$!` is the PID of the command you just started. Save it at once.

2. **Now you.** You need `count` processes in total. Start the others in the same way and save each PID in its own variable (`pid2`, `pid3`, …).
3. Look at the first process while it is alive.

   ```bash
   ps -o pid,ppid,stat,comm -p "$pid1"
   ```

4. **Now you.** Run the same `ps` for **all** your PIDs. Separate them with commas. Add `| tee evidence/processes.txt` at the end to show the result and save it. Be quick: the processes end after your number of seconds.
5. Answer by experiment in `evidence/answers.txt` (use `nano evidence/answers.txt`). The toolbox below has what you need.
   - Who is the parent of your processes? Give its PID and say what program it is.
   - What does the letter in the `STAT` column mean?
   - All rows show the same name in `COMM`. How does the system tell the processes apart?

   | Toolbox | Use |
   |---|---|
   | `echo $$` | PID of the shell you are typing in |
   | `jobs -l` | Background jobs of this shell |
   | `man ps` | Search for `PROCESS STATE CODES` with `/` |
   | `wait PID` | Pause until that process ends |

6. Wait for the first process to end, then run your `ps` command from step 4 again, this time with `| tee -a evidence/processes.txt`. Write in `evidence/answers.txt` what changed, and whether the file from `command -v sleep` still exists.

## Core 2 — Choose Your Own Timing (65–75)

A process that lives five seconds is easy to miss.

1. Start one `sleep 5` in the background and save its PID.
2. **Your decision:** when do you run `ps` to see it alive once, and gone once? Do it, and save both results in `evidence/timing.txt`.
3. Add one sentence: what can a late `ps` **not** tell you about a process?
4. Run `oslab check lab1` until all three milestones pass.

Stuck for more than five minutes? Use `oslab hint lab1 1`, then `2`, then `3`.

**Core is complete when** `oslab check lab1` shows `milestones: 3/3` and you have answered the three questions.

## Plus — A Different Parent (75–90)

1. Start a second shell inside your shell by typing `bash`. Run `echo $$`.
2. In that second shell, start `sleep 20 &` and look at it with `ps -o pid,ppid,comm -p $!`.
3. Type `exit` to go back. Compare the PPID with the one from Core 1.
4. In `evidence/plus.txt`, draw the three levels (first shell, second shell, `sleep`) with their PIDs. Check your drawing with `ps -o pid,ppid,comm --forest`.

## Challenge

In a second shell (`bash`), start `sleep 40 &`, print its PID, and type `exit` at once. Back in the first shell, look at that PID with `ps -o pid,ppid,comm -p`. Who is the parent now? Explain in `evidence/challenge.txt` why a process always has a parent, and what the system did here.

## Live Checkpoint (90–105)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab1
```

1. Answer the questions. They use new numbers, made for you at this moment.
2. Then do what the command prints, and save the `ps` output in `evidence/checkpoint.txt`.
3. Run `oslab check lab1`. A fourth milestone, `checkpoint`, must pass.

## Debrief (105–115)

Look at your prediction again.

```bash
cat "$OSLAB_WORKSPACE/.records/lab1-predict.json"
```

In your report, write **confirmed** or **corrected** for each answer, and explain in 3–5 sentences the difference between a program and a process.

## Submit (115–120)

1. Copy your work to your course repository. Replace the path with your own.

   ```bash
   SUBMISSION_REPO="$HOME/os-se-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab1/evidence"
   cp -- evidence/os-info.txt evidence/processes.txt evidence/answers.txt evidence/timing.txt "$SUBMISSION_REPO/lab1/evidence/"
   ```

2. Fill in the [report template](README.md) as `lab1/README.md`. Add `checkpoint.txt`, and `plus.txt` or `challenge.txt` if you did them.

   ```text
   lab1/
   ├── README.md
   └── evidence/
       ├── os-info.txt       # kernel and distribution
       ├── processes.txt     # your processes alive, then after the first one ended
       ├── answers.txt       # the three questions
       └── timing.txt        # the five-second process, seen and missed
   ```

3. Commit and push in the usual way.

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| System record and your processes: `oslab check lab1` passes the three Core milestones | 2 |
| Tests: processes alive and ended, and your own timing for the short process | 2 |
| Prediction saved in time, and an honest confirmed/corrected explanation | 2 |
| Live checkpoint: answers, the saved `ps` output, and your sentence | 3 |
| Clear, complete evidence files and report | 1 |

Plus and Challenge are not needed for full marks. They are noted in your feedback. Your prediction is marked for being made and corrected, not for being right.

## Help and References

- `oslab hint lab1 1`, `2`, `3`
- `man uname`, `man ps`
- Old wider topics (packages with APT, virtualization) are in the [optional extensions](extensions.md).
