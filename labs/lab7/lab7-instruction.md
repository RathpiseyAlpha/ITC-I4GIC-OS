# OS Lab 7 — Bash Scripting, Permissions & Server Automation (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class. Before class: about 10 minutes for the pre-lab |
| Work | Individual. Your two file names and your word counts are different from your neighbour's |
| Environment | Shared Ubuntu server with an individual account for each student. Local Linux/WSL works for practice ([setup](../SETUP.md)) |
| Tools | `bash`, `wc`, `printf`, `chmod`, `nano`, `cmp`, `oslab` |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Builds on | Lab 2 (paths and quoting), Lab 4 (stdout, stderr and exit status) and Lab 6 (the execute bit) |

> **Scenario:** Build a personal TechCorp command that can inspect files in your own server neighborhood. It must preserve argument boundaries before any cross-user automation is considered.

## Lab Objectives

After the required core, you should be able to:

1. Create and invoke a Bash script with understood arguments and execution permissions.
2. Handle spaces, leading-dash filenames and missing input without unintended word splitting.
3. Test a reusable command and explain its exit status and safe filename handling.

**Extension objectives:** Use personal PATH entries, login-message previews and an owned outbox; cross-user mailbox/feedback requires a narrow prepared shared directory. These retain the original lab's wider topics; they are not required to finish the two-hour core. They are in the [optional extensions](extensions.md).

## How This Lab Works

| Command | What it does |
|---|---|
| `oslab values lab7` | Shows **your** two file names. They are already in your `input/` folder |
| `oslab predict lab7` | Saves your prediction once, before the experiment |
| `oslab hint lab7 1` | Gives a hint (levels 1, 2, 3). Hints cost no points |
| `oslab check lab7` | Runs your `count_words.sh` on test files and shows your milestones |
| `oslab checkpoint lab7` | Opens when the instructor says so, near the end |
| `oslab debrief lab7` | After the lab: you give the right answers to your prediction questions |

- **Core** is for everyone. **Plus** and **Challenge** are for students who finish early. Full marks need only Core and the checkpoint.
- AI tools are allowed in Core, Plus and Challenge. They are **not** allowed in the prediction and the checkpoint. Always test what an AI tells you.
- In Core 1 you receive an empty skeleton. You write the script, and you decide how to keep the exit status.

## Before the Lab

Do this before class. It takes about 10 minutes.

```bash
oslab doctor
oslab prelab lab7
```

## Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Setup |
| 10–25 | Guided: script basics |
| 25–35 | Prediction |
| 35–55 | Core 1: build count_words.sh |
| 55–70 | Core 2: test it |
| 70–85 | Instructor demonstration, Plus and Challenge |
| 85–100 | Live checkpoint |
| 100–110 | Debrief |
| 110–120 | Submit |

## Setup (0–10)

1. Log in to the server with your own account. Start the lab and go into its folder.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab7
   cd "$OSLAB_WORKSPACE/lab7"
   mkdir -p evidence
   oslab values lab7
   ```

2. **Read your personal values.** The last command prints two file names that are only yours. For example:

   ```text
   Your personal values for lab7 (your-account):
     file1    = bridge candle.txt
     file2    = -silver.txt
   ```

   `file1` has spaces in its name. `file2` starts with a dash. Your own names are different. Write them down.

3. **Understand the capital words.** This instruction cannot know your names, so it writes `FILE1` and `FILE2` where your values belong. Never type these capital words. Type your own name in their place, between single quotes when it has a space.

   | The instruction says | With the example values above, you type |
   |---|---|
   | `bash show_args.sh 'FILE1' 'FILE2'` | `bash show_args.sh 'bridge candle.txt' '-silver.txt'` |
   | `wc -w -- 'input/FILE1'` | `wc -w -- 'input/bridge candle.txt'` |

4. Your folder now looks like this:

   ```text
   lab7/
   ├── .oslab-managed.json
   ├── count_words.sh      # editable starter skeleton
   ├── input/
   │   ├── FILE1           # your name with spaces; a few words
   │   └── FILE2           # your name with a leading dash; a few words
   └── evidence/
   ```

5. Try the checking command once. At the start every line says `TRY`.

   ```bash
   oslab check lab7
   ```

## Guided — Script Basics (10–25)

**Goal:** see how a script receives its arguments, and why quotes matter.

1. Create a complete argument viewer. The quoted `'SH'` after `<<` stops your own shell from changing the script's variables while it is written.

   ```bash
   cat > show_args.sh <<'SH'
   #!/usr/bin/env bash
   printf 'argument count=%s\n' "$#"
   for argument in "$@"; do
       printf '<%s>\n' "$argument"
   done
   SH
   bash show_args.sh 'FILE1' 'FILE2'
   ```

   The output is a count of 2, then each argument between angle brackets. `"$@"` gives each argument separately and keeps the spaces inside it.

2. Compare running through `bash` with direct execution.

   ```bash
   chmod u+x show_args.sh
   ./show_args.sh 'FILE1' 'FILE2'
   ```

   The first line, `#!/usr/bin/env bash`, is the **shebang**: it chooses the interpreter for direct execution. `./` says "in the current folder"; the folder does not need to be in `PATH`.

3. See what happens to the file names when the quotes are missing.

   ```bash
   bash show_args.sh FILE1
   ```

   Type your own name for `FILE1` here, **without** quotes. How many arguments does the script receive? Why?

4. Count words safely. `--` ends the list of options for `wc`, so a name that starts with a dash is read as a file.

   ```bash
   wc -w -- 'input/FILE1'
   cd input
   wc -w -- 'FILE2'
   cd ..
   ```

   **Observe:** inside `input/`, what would `wc -w FILE2` do without the `--`? Try it once; the error is intended.

## Prediction (25–35)

Guess first, then try. Answer alone, without AI.

```bash
oslab predict lab7
```

It asks three questions and one sentence, with your own file names. A wrong guess costs nothing. You compare it with the real result in the debrief.

## Core 1 — Build count_words.sh (35–55)

**Goal:** a reusable command that counts the words of the files it is given.

`count_words.sh` must:

- with **no arguments**: print a usage message on stderr (`>&2`) and end with a status other than 0,
- for each regular file: print one line with the file's name and its word count (the wording of the label is yours),
- for a missing or non-regular file: print a message on stderr, **continue** with the next arguments, and make the final status other than 0,
- keep each argument in one piece and pass file names to `wc` after `--`. Do not use `eval`.

1. Read the skeleton and your input files.

   ```bash
   cat count_words.sh
   cat 'input/FILE1' 'input/FILE2'
   ```

2. **Your decision.** Open the script with `nano count_words.sh` and write it. Start with one valid file, then two, and test each step before you add the error handling:

   ```bash
   bash count_words.sh 'input/FILE1'
   bash count_words.sh 'input/FILE1' 'input/FILE2'
   ```

3. Keep the status in a variable that starts at `0`. Change it when an input fails, and finish the script with `exit "$status"`. Why is the variable better than relying on the last command?

4. Make the script executable for you, and run it directly, then through `bash`.

   ```bash
   chmod u+x count_words.sh
   ./count_words.sh 'input/FILE1'
   bash count_words.sh 'input/FILE1'
   ```

**Hints:** `oslab hint lab7 1`, `2` and `3`. AI is allowed here; test every suggestion with your own file names.

## Core 2 — Test It (55–70)

**Goal:** show that the command keeps names intact and reports failures.

1. Save the normal run with both files.

   ```bash
   bash count_words.sh 'input/FILE1' 'input/FILE2' | tee evidence/normal.txt
   ```

2. Run it with a missing file first and a valid file second. Save the messages and the status.

   ```bash
   {
     bash count_words.sh missing.txt 'input/FILE1'
     printf 'status=%s\n' "$?"
   } > evidence/edge.txt 2>&1
   cat evidence/edge.txt
   ```

   The valid file must still be counted, and the status must not be `0`.

3. Run it from **inside** `input/`, with the file that starts with a dash, and save the result.

   ```bash
   cd input
   bash ../count_words.sh 'FILE2' | tee ../evidence/dash.txt
   cd ..
   ```

4. Check your work. The four Core milestones must show `PASS`.

   ```bash
   oslab check lab7
   ```

5. Write down for your report: what does each test contradict? A loop over unquoted `$@`, a missing `--`, and a status taken from the last command each fail one of the tests above. Which one?

## Instructor Demonstration, Plus and Challenge (70–85)

First, watch the instructor run a script on a file name with a space, with and without quotes. Then, if you finish early, try these. They are not needed for full marks. Save your answers in `evidence/plus.txt`.

**Plus**

- Give your script a **folder** instead of a file (`mkdir -p input/folder`, then `bash count_words.sh input/folder`). What does it print, and what is the final status? Does your test `[[ -f "$file" ]]` treat a folder like a missing file?

**Challenge**

- Compare what your viewer receives with `*` and with `./*`:

  ```bash
  cd input
  bash ../show_args.sh *
  bash ../show_args.sh ./*
  cd ..
  ```

  The shell replaces `*` by the file names *before* the script starts. Which form is safer when a name starts with a dash, and why?

## Live Checkpoint (85–100)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab7
```

1. Answer the four questions. They use a new, awkward file name made for you at this moment.
2. Then do the file task that the command prints: create the new file, run **your own** `count_words.sh` on it, and save the output in `checkpoint.txt`.
3. Run `oslab check lab7`. A fifth milestone, `checkpoint`, must show `PASS`.

## Debrief (100–110)

Look at your prediction again. `oslab` saved it in a hidden folder, `.records`.

```bash
cat "$OSLAB_WORKSPACE/.records/lab7-predict.json"
```

Now give the right answer to each prediction question:

```bash
oslab debrief lab7
```

Your prediction stays saved as it was, so the comparison shows which answers you confirmed and which you corrected. Then the class discusses: your script worked on the files you tested. Which file name could still break it?

## Submit (110–120)

1. Copy your work to your course repository. Replace `YOUR_ID` with your own ID.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab7/evidence"
   cp -- count_words.sh "$SUBMISSION_REPO/lab7/"
   cp -- evidence/normal.txt evidence/edge.txt "$SUBMISSION_REPO/lab7/evidence/"
   ```

   If you did Plus or Challenge, copy `evidence/plus.txt` the same way.

2. Fill in the [report template](README.md) as `lab7/README.md`. Your repository then has:

   ```text
   lab7/
   ├── README.md
   ├── count_words.sh
   └── evidence/
       ├── normal.txt
       └── edge.txt
   ```

   The course website checks that these exact names are there.

3. Commit and push. `git pull` comes first, in case you pushed from your own computer since.

   ```bash
   cd ~/os-gic-YOUR_ID
   git pull
   git add os-lab-YOUR_ID/lab7
   git commit -m "Lab 7"
   git push
   ```

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Script: `oslab check lab7` passes the four Core milestones (direct run, two files, leading dash, errors and status) | 2 |
| Tests: `normal.txt` and `edge.txt` show the runs, and the README says what each test contradicts | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab7` | 2 |
| Live checkpoint: the answers and your script counting the new file | 3 |
| Complete submission: the required files in your repository, on time | 1 |

Every row is marked from your `oslab` records and the files in your repository, so run `oslab check lab7` until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.

## Help and References

- `oslab hint lab7 1`, `2`, `3`
- `man bash` (search for `Special Parameters`), `man wc`
- Personal `PATH` entries, login-message previews and an owned outbox are in the [optional extensions](extensions.md).
