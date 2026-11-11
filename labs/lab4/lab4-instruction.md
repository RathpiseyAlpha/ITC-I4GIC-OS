# OS Lab 4 — Linux I/O Redirection and Pipelines (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class; about 10 minutes of pre-lab reading |
| Work | Individual; use your own account and personal status words |
| Environment | Shared Ubuntu server or local Linux/WSL ([setup](../SETUP.md)) |
| Tools | `cat`, `grep`, `cut`, `wc`, `tee`, `diff`, `printf`, `oslab` |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |

> **Scenario:** A help desk gives you a small list of service events. Find exactly the requested category, extract its quantities, count matching records, and save normal output separately from errors. Work directly at the terminal: no script is required.

## Lab Objectives

1. Redirect stdout and stderr, replace or append output, and save output with `tee`.
2. Build a pipeline step by step with `grep`, `cut` and `wc -l`.
3. Test exact matching and changed input, and explain what each saved result proves.

No Bash program, `$1`, `if`, loops, command substitution, arithmetic expression, or `awk` program is needed. Reusable scripts belong in Lab 7. The helper's setup line below is supplied infrastructure, not syntax you must reproduce from memory.

## Before the Lab

Read “Commands First” and run:

```bash
oslab doctor
oslab prelab lab4
```

## Commands First

A command receives stdin (stream 0), writes normal output to stdout (1), and writes diagnostics to stderr (2). Both outputs can appear on screen; use redirection to distinguish them.

| Syntax | Meaning |
|---|---|
| `command > file` | Replace file with stdout; create it if missing |
| `command >> file` | Append stdout, preserving earlier contents |
| `command 2> file` | Replace file with stderr |
| `command > file 2>&1` | Save both streams to one file; order matters |
| `a \| b` | Feed stdout of `a` to stdin of `b`; stderr is not piped |
| `command \| tee file` | Display stdout and replace file with the same output |
| `command \| tee -a file` | Display stdout and append it to file |
| `echo $?` | Show the exit status of the immediately previous command |

These are command-line operators, introduced here before you use them. Exit status 0 means success; other values indicate a different outcome. For `grep`, 1 means no matching line and 2 means an error. Check status immediately: another command replaces it. A pipeline normally reports the status of its last command, not every stage.

The input is simple two-field text separated by commas, without quoted commas. `grep '^ready,'` selects lines starting with the whole first field `ready`: `^` means start, and the comma prevents `ready-late` matching. `cut -d, -f2` keeps field 2. `wc -l` counts newline-terminated lines; it does not add the numbers on those lines.

## Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Setup |
| 10–25 | Guided: streams, append and tee |
| 25–35 | Prediction |
| 35–55 | Core 1: select, extract and count |
| 55–70 | Core 2: changed inputs and missing files |
| 70–85 | Instructor demonstration, Plus and Challenge |
| 85–100 | Live checkpoint |
| 100–110 | Debrief |
| 110–120 | Submit |

## Setup (0–10)

```bash
export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
oslab start lab4
cd "$OSLAB_WORKSPACE/lab4"
mkdir -p evidence
oslab values lab4
cat data/events.csv
```

The helper prints `status` and `other`. In this instruction, replace `STATUS` and `OTHER` with those actual words. For example, if your status is `ready`, type `grep '^ready,'`, not `grep '^STATUS,'`. You do not need to create shell variables.

```text
lab4/
├── data/
│   ├── events.csv          # header and six personal records
│   └── expected.txt        # expected matching-record count
└── evidence/
```

`oslab start` preserves existing work. Never reset to fix one command. If you previously did the script-based version, keep your old files separately; this revision checks command evidence, not `report.sh`.

## Guided — Streams, Append and Tee (10–25)

Run one line at a time and inspect the files:

```bash
printf 'first observation\n' > evidence/practice.txt
printf 'second observation\n' >> evidence/practice.txt
cat evidence/practice.txt
printf 'shown and saved\n' | tee evidence/tee-demo.txt
printf 'one more line\n' | tee -a evidence/tee-demo.txt
cat evidence/tee-demo.txt
cat data/not-present.csv > evidence/demo-out.txt 2> evidence/demo-error.txt
echo $?
cat evidence/demo-out.txt
cat evidence/demo-error.txt
cat data/events.csv data/not-present.csv > evidence/both.txt 2>&1
cat evidence/both.txt
```

The missing-file errors are expected. `demo-out.txt` is empty, but the error file is not. `both.txt` contains the existing file's contents and a diagnostic about the missing file. Which operator preserved the first observation? Which command displayed output while saving it?

## Prediction (25–35)

Read your CSV before answering alone, without AI:

```bash
oslab predict lab4
```

Predict the first selected quantity, the matching-record count, and the error stream. Do not confuse the first quantity or a sum of quantities with the number of matching rows.

## Core 1 — Select, Extract and Count (35–55)

Build the pipeline in stages. Replace `STATUS` with your actual word in every command.

```bash
grep '^STATUS,' data/events.csv | tee evidence/selected.txt
grep '^STATUS,' data/events.csv | cut -d, -f2 | tee evidence/fields.txt
grep '^STATUS,' data/events.csv | wc -l > evidence/normal.txt
cat evidence/normal.txt
diff -u data/expected.txt evidence/normal.txt
```

No output from `diff` means the counts agree. You should have three selected records, three quantities, and a count of 3. The look-alike `STATUS-late` must be absent. Do not add quantities: this task asks for a record count.

**Your decision:** In `evidence/commands.txt`, use `nano` to save the three actual commands you used (one per line). This is a plain-text command record, not an executable script; the helper never runs it. Explain in your report what changed between stages.

```bash
oslab check lab4
```

The first two milestones check selected rows/fields, then the normal count. The remaining milestones need Core 2. Hints: `oslab hint lab4 1`, `2`, `3`.

## Core 2 — Changed Inputs and Missing Files (55–70)

First create a file with no exact match, and another with an extra matching row plus a look-alike. Keep the original unchanged.

```bash
printf 'status,count\nOTHER,2\n' > data/no-match.csv
cp -- data/events.csv data/changed.csv
printf 'STATUS,7\nSTATUS-late,99\n' >> data/changed.csv
grep '^STATUS,' data/no-match.csv | wc -l > evidence/edge.txt
grep '^STATUS,' data/changed.csv | wc -l >> evidence/edge.txt
cat evidence/edge.txt
```

Expect two lines: 0 and 4. A quantity of 7 adds one record, not seven. The look-alike must not increase the count. `>>` preserves the first test's result.

Now save a missing-file result. Run `echo $?` immediately after `cat`, before inspecting any file:

```bash
cat data/missing.csv > evidence/stdout.txt 2> evidence/stderr.txt
echo $? > evidence/status.txt
cat evidence/stdout.txt
cat evidence/stderr.txt
cat evidence/status.txt
oslab check lab4
```

Expect empty stdout, a diagnostic naming `missing.csv` on stderr, and nonzero status. This tests `cat` directly, not the status of a pipeline. All four Core milestones should pass.

Add these actual test commands to `evidence/commands.txt` with `nano`. In your report explain which test catches prefix matching, counting quantities instead of records, and discarding earlier results with `>`.

## Instructor Demonstration, Plus and Challenge (70–85)

The instructor demonstrates:

```bash
cat data/missing.csv | wc -l
echo $?
```

The error still appears, `wc` prints 0, and the pipeline normally reports 0 because the final command succeeded. A successful last stage does not prove the input was read successfully.

### Plus — Inspect a No-Match Status

```bash
grep '^STATUS,' data/no-match.csv
echo $?
```

Expect no selected line and status 1. Compare this with the missing-file diagnostic and nonzero `cat` status. Save observations in your report; do not turn “no matching record” into “file missing.”

### Challenge — Display and Save Both Streams

Using only `cat`, redirection, a pipe and `tee`, display both `data/events.csv` and the missing-file diagnostic while saving them to `evidence/challenge.txt`. Work out where `2>&1` belongs so stderr enters the pipe. Explain why `cat ... | tee ...` alone does not save the diagnostic. No script is needed.

## Live Checkpoint (85–100)

Wait until the instructor releases it; close AI tools and work alone.

```bash
oslab checkpoint lab4
```

Answer the questions about new records. The helper prints a command to create a fresh file and tells you what evidence to save. You write the selection pipeline yourself: save matching lines to `evidence/checkpoint-selected.txt` and their record count to `checkpoint.txt`. Use your own status and the new filename. Do not reuse the Core result.

```bash
oslab check lab4
```

The checkpoint adds a fifth milestone. The helper checks the fresh input, selected rows and count; it does not execute submitted commands or scripts.

## Debrief (100–110)

```bash
oslab debrief lab4
```

Compare your prediction with observation. Discuss: what does each pipeline stage receive and produce? Why is `wc -l` not a sum? How did you prove the missing-file message used stderr? Why can a pipeline print 0 and still have an input failure?

## Submit (110–120)

Use your actual submission repository path in place of `YOUR_ID`. The following supplied copy commands use the folder layout from earlier labs.

```bash
mkdir -p "$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID/lab4/evidence"
cp -- evidence/*.txt "$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID/lab4/evidence/"
cp -- checkpoint.txt "$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID/lab4/"
```

Fill in the [report template](README.md). Required files are:

```text
lab4/
├── README.md
├── checkpoint.txt
└── evidence/
    ├── commands.txt
    ├── selected.txt
    ├── fields.txt
    ├── normal.txt
    ├── edge.txt
    ├── stdout.txt
    ├── stderr.txt
    ├── status.txt
    └── checkpoint-selected.txt
```

Commit and push using the Lab 1 submission workflow. No `.sh` file is required.

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Correct command results: four Core milestones | 2 |
| Actual commands and explanations of changed-input/stream tests | 2 |
| Prediction saved in time and corrected debrief | 2 |
| Live checkpoint: answers, fresh selection/count and explanation | 3 |
| Complete submission in the repository, on time | 1 |

Saved files show observed results, not proof that a particular command was used. The instructor reviews `commands.txt`, explanations and the live checkpoint. AI may assist practice but is not allowed in predictions/checkpoints. Optional work is not required for full credit.

## Help and Later Topics

Use `man grep`, `man cut`, `man wc`, `man tee`, and `oslab hint lab4 1` to `3`. [Extensions](extensions.md) are for later study with explicit prerequisites; they are not required now. Scripting and numerical aggregation are deferred until their syntax is taught.
