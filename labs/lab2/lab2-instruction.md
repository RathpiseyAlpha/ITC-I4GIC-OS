# OS Lab 2 — Linux Navigation & File Management (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class, plus a 10-minute pre-lab |
| Work | Individual. Your file names and folders are different from your neighbour's |
| Environment | Shared Ubuntu server with an individual account for each student. Local Linux/WSL works for practice ([setup](../SETUP.md)) |
| Tools | `pwd`, `ls`, `mkdir`, `cp`, `mv`, `find`, `cmp`, `oslab` |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Lecture link | [Week 2 notes: OS structures and interfaces](../../lectures/notes/week02-os-structures-interfaces.md) |

> **Scenario:** Two reports arrived in TechCorp's `incoming` folder. You must put them in the right places in the company's folders, keep their contents unchanged, and be able to reach them from any department.

## Lab Objectives

After the Core, you can:

1. Move around with absolute and relative paths, and explain `.` and `..`.
2. Build a folder tree, then move and copy files without changing their contents.
3. Find the cause of a path error and prove that a copy is identical.

## How This Lab Works

| Command | What it does |
|---|---|
| `oslab values lab2` | Shows **your** file names and folders. Use them everywhere in this lab |
| `oslab predict lab2` | Saves your prediction once, before the experiment |
| `oslab hint lab2 1` | Gives a hint (levels 1, 2, 3). Hints cost no points |
| `oslab check lab2` | Looks at your folders and shows your milestones |
| `oslab checkpoint lab2` | Opens when the instructor says so, near the end |

- **Core** is for everyone. **Plus** and **Challenge** are for students who finish early. Full marks need only Core and the checkpoint.
- AI tools are allowed in Core, Plus and Challenge. They are **not** allowed in the prediction and the checkpoint.
- In Core 2 nobody gives you the commands. You write every path yourself.

## Before the Lab

Do this before class. It takes about 10 minutes.

```bash
oslab doctor
oslab prelab lab2
```

## Timetable

| Minutes | Activity |
|---|---|
| 0–5 | Setup |
| 5–20 | Guided: where am I? |
| 20–30 | Prediction, then class discussion |
| 30–40 | Core 1: build the company folders |
| 40–65 | Core 2: move and copy with your own paths |
| 65–75 | Core 3: prove it |
| 75–90 | Plus and Challenge (or finish Core) |
| 90–105 | Live checkpoint |
| 105–115 | Debrief |
| 115–120 | Submit |

## Setup (0–5)

1. Start the lab and go into its folder.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab2
   cd "$OSLAB_WORKSPACE/lab2"
   mkdir -p evidence
   oslab values lab2
   ```

2. Type **your** values into shell variables. The values below are only an example. Keep the quotes: your file names have a space in them.

   ```bash
   file1='budget 2026.txt'
   file2='audit notes.txt'
   owner=Finance
   reader=HR
   third=Support
   ```

   If you open a new terminal, run `cd` and set these variables again.

3. Your folder looks like this, with your own two file names:

   ```text
   lab2/
   ├── incoming/
   │   ├── (your file1)
   │   └── (your file2)
   ├── reports/
   │   └── README.txt
   └── evidence/
   ```

## Guided — Where Am I? (5–20)

1. See where you are and what is here.

   ```bash
   pwd
   ls
   ls -la
   ```

   An **absolute path** starts with `/` and means the same place from anywhere. A **relative path** starts from the folder you are in now.

2. Work in a practice folder, so you do not touch the reports yet.

   ```bash
   mkdir -p practice/notes
   printf 'orientation\n' > 'practice/welcome note.txt'
   cd practice
   pwd
   cp -- 'welcome note.txt' notes/
   cat 'notes/welcome note.txt'
   cd ..
   pwd
   ```

   `cd ..` goes to the parent folder. Always check with `pwd`.

3. Read one file in two ways.

   ```bash
   cat 'practice/welcome note.txt'
   cat "$OSLAB_WORKSPACE/lab2/practice/welcome note.txt"
   ```

   Which of the two commands stops working if you `cd` somewhere else?

4. See why the quotes matter. The second command fails. Read its error message.

   ```bash
   ls -l "incoming/$file1"
   ls -l incoming/$file1 || true
   ```

## Prediction (20–30)

```bash
oslab predict lab2
```

Answer alone, without AI, before the experiment. A wrong prediction costs nothing. The class will look at the spread of answers together.

## Core 1 — Build the Company Folders (30–40)

1. Go back to the lab folder and create the tree for your departments.

   ```bash
   cd "$OSLAB_WORKSPACE/lab2"
   mkdir -p "TechCorp/$owner/archive" "TechCorp/$reader" "TechCorp/$third"
   find TechCorp -type d
   ```

2. Read the two incoming reports and write down their contents. You will need them to prove that nothing changed.

   ```bash
   cat "incoming/$file1" "incoming/$file2"
   ```

## Core 2 — Move and Copy With Your Own Paths (40–65)

Write each command yourself. Run `pwd` before every command that moves or copies. Write every command that worked into `evidence/paths.txt` (use `nano evidence/paths.txt` from the lab folder).

1. Go **into** `incoming/`. Move your first file to `reports/` with a **relative** destination.
2. Go back to the lab folder. Move your second file to `reports/` with **absolute** paths for both source and destination. Start them with `"$OSLAB_WORKSPACE/lab2/…"`.
3. Copy both reports from `reports/` into your owner department, `TechCorp/<owner>/`. The originals must stay in `reports/`.
4. Copy your first report into `TechCorp/<owner>/archive/` with the new name `first-original.txt`.
5. Go **into** your reader department, `TechCorp/<reader>/`. Without leaving it, read the first report in the owner department: once with a relative path and once with an absolute path.
6. **Your decision:** for step 3, did you use relative or absolute paths? Write in `evidence/paths.txt` which you chose and when the other kind would be better.

Stuck for more than five minutes? Use `oslab hint lab2 1`, then `2`, then `3`.

## Core 3 — Prove It (65–75)

1. A name in `ls` does not prove the contents are the same. Compare the bytes. `cmp` prints nothing when two files are identical.

   ```bash
   cd "$OSLAB_WORKSPACE/lab2"
   cmp -- "reports/$file1" "TechCorp/$owner/$file1"
   cmp -- "reports/$file2" "TechCorp/$owner/$file2"
   ```

2. Make one path error on purpose: from your reader department, try to read the report with a path that would only work from the lab folder. Copy the error message into `evidence/paths.txt` and write one line that explains it.
3. Save the final list of files and check your milestones.

   ```bash
   cd "$OSLAB_WORKSPACE/lab2"
   find incoming reports TechCorp -type f | sort | tee evidence/tree.txt
   oslab check lab2
   ```

**Core is complete when** `oslab check lab2` shows `milestones: 4/4`.

## Plus — Find the Lost File (75–90)

1. Create a small mess.

   ```bash
   cd "$OSLAB_WORKSPACE/lab2"
   mkdir -p mess/a/b mess/c
   printf 'lost\n' > 'mess/a/b/lost file.txt'
   ```

2. Go into `mess/c`. Without any `cd`, move `lost file.txt` into the folder you are in and rename it `found.txt`, with **one** command.
3. From inside `mess/a/b`, copy `found.txt` into your third department under `TechCorp/`, using only a relative path. How many `..` did you need?
4. Save both commands and the count in `evidence/plus.txt`.

## Challenge

Copy every `.txt` file from `reports/` into your third department with **one** command that uses `*`. Then answer in `evidence/challenge.txt`:

- Why does the command fail if you put quotes around `*.txt`?
- Create `reports/.hidden.txt`. Does your command copy it? Why?

## Live Checkpoint (90–105)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab2
```

1. Answer the questions. They use a new starting folder and a new target, made for you at this moment.
2. Then do what the command prints, and save the output in `evidence/checkpoint.txt`.
3. Run `oslab check lab2`. A fifth milestone, `checkpoint`, must pass.

## Debrief (105–115)

Look at your prediction again.

```bash
cat "$OSLAB_WORKSPACE/.records/lab2-predict.json"
```

In your report, write **confirmed** or **corrected** for each answer, and explain in 3–5 sentences why a correct file name can still give "No such file or directory".

## Submit (115–120)

1. Copy your work to your course repository. Replace the path with your own.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab2/evidence"
   cp -- evidence/paths.txt evidence/tree.txt "$SUBMISSION_REPO/lab2/evidence/"
   ```

2. Fill in the [report template](README.md) as `lab2/README.md`. Add `checkpoint.txt`, and `plus.txt` or `challenge.txt` if you did them.

   ```text
   lab2/
   ├── README.md
   └── evidence/
       ├── paths.txt   # your commands, your decision, and one explained error
       └── tree.txt    # the final list of files
   ```

3. Commit and push in the usual way.

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Correct folders and files: `oslab check lab2` passes the four Core milestones | 2 |
| Tests: identical copies with `cmp`, and one path error explained | 2 |
| Prediction saved in time, and an honest confirmed/corrected explanation | 2 |
| Live checkpoint: answers, the saved output, and your sentence | 3 |
| Clear, complete evidence files and report | 1 |

Plus and Challenge are not needed for full marks. They are noted in your feedback. Your prediction is marked for being made and corrected, not for being right.

## Help and References

- `oslab hint lab2 1`, `2`, `3`
- `man mv`, `man cp`, `man find`
- Old wider topics (system directory tour, larger company tree, listing options) are in the [optional extensions](extensions.md).
