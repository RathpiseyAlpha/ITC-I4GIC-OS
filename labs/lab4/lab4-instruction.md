# OS Lab 4 — Linux I/O Redirection, Pipelines & Process Management (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class. Before class: about 10 minutes for the pre-lab |
| Work | Individual. Your status words and your numbers are different from your neighbour's |
| Environment | Shared Ubuntu server with an individual account for each student. Local Linux/WSL works for practice ([setup](../SETUP.md)) |
| Tools | `printf`, `cat`, `grep`, `cut`, `awk`, `wc`, `diff`, `bash`, `oslab` |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Lecture link | [Week 3 notes: processes](../../lectures/notes/week03-processes.md) |

> **Scenario:** TechCorp receives small CSV event logs. You must produce a success-count report that can be trusted, and you must tell normal output apart from error messages.

## Lab Objectives

After the required core, you should be able to:

1. Use redirection and pipelines while distinguishing stdout, stderr and exit status.
2. Filter and aggregate a CSV fixture, checking intermediate stages.
3. Diagnose incorrect selection/aggregation using normal and changed-input tests.

**Extension objectives:** Monitor and signal bounded owned processes; observe orphan/zombie lifecycle in a disposable local environment. These retain the original lab's wider topics; they are not required to finish the two-hour core. They are in the [optional extensions](extensions.md).

## How This Lab Works

| Command | What it does |
|---|---|
| `oslab values lab4` | Shows **your** status word and the other word. Use them everywhere in this lab |
| `oslab predict lab4` | Saves your prediction once, before the experiment |
| `oslab hint lab4 1` | Gives a hint (levels 1, 2, 3). Hints cost no points |
| `oslab check lab4` | Runs your `report.sh` on test files and shows your milestones |
| `oslab checkpoint lab4` | Opens when the instructor says so, near the end |
| `oslab debrief lab4` | After the lab: you give the right answers to your prediction questions |

- **Core** is for everyone. **Plus** and **Challenge** are for students who finish early. Full marks need only Core and the checkpoint.
- AI tools are allowed in Core, Plus and Challenge. They are **not** allowed in the prediction and the checkpoint. Always test what an AI tells you.
- In Core 1 nobody gives you the full script. You write `report.sh` yourself.

## Before the Lab

Do this before class. It takes about 10 minutes.

```bash
oslab doctor
oslab prelab lab4
```

## Three Ideas First

**Streams.** Every command has three numbered channels. Number 0 is input, number 1 is the normal output (*stdout*), number 2 is the error messages (*stderr*). Both outputs show on the screen, so you cannot tell them apart by looking.

| You write | It sends |
|---|---|
| `command > file` | stdout (1) into the file; the file is replaced |
| `command >> file` | stdout (1) to the end of the file |
| `command 2> file` | stderr (2) into the file |
| `command > file 2>&1` | both into the same file; `2>&1` means "error goes where output goes now" |
| `command >&2` | the output of this command goes to stderr; you use it to print an error message |

**Pipes.** `a | b` sends the stdout of `a` into the input of `b`. Only stdout goes through; error messages still reach the screen.

**Exit status.** Every command ends with a number. `0` means success; any other number means failure. `echo $?` shows the status of the last command. `grep` returns `1` when it finds no line, which is not an error in reading the file.

## Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Setup |
| 10–25 | Guided: redirection and pipelines |
| 25–35 | Prediction |
| 35–55 | Core 1: write report.sh |
| 55–70 | Core 2: test your report |
| 70–85 | Instructor demonstration, Plus and Challenge |
| 85–100 | Live checkpoint |
| 100–110 | Debrief |
| 110–120 | Submit |

## Setup (0–10)

1. Log in to the server with your own account. Start the lab and go into its folder.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab4
   cd "$OSLAB_WORKSPACE/lab4"
   mkdir -p evidence
   oslab values lab4
   ```

2. **Read your personal values.** The last command prints two words that are only yours. For example:

   ```text
   Your personal values for lab4 (your-account):
     status   = ready
     other    = done
   ```

   Your own words are different. Write them down.

3. **Understand the capital words.** This instruction cannot know your values, so it writes a word in capitals where your value belongs: `STATUS` and `OTHER`. These words are placeholders. Never type them. Type your own value in their place.

   | The instruction says | With the example values above, you type |
   |---|---|
   | `grep '^STATUS,' data/events.csv` | `grep '^ready,' data/events.csv` |
   | `printf 'OTHER,5\n'` | `printf 'done,5\n'` |
   | the label `STATUS total: NUMBER` | the label `ready total: NUMBER` |

4. Your folder now looks like this. The numbers inside `events.csv` are also only yours.

   ```text
   lab4/
   ├── .oslab-managed.json
   ├── data/
   │   ├── events.csv      # a header and six records
   │   └── expected.txt    # the report you must produce
   └── evidence/
   ```

5. Try the checking command once. At the start every line says `TRY`, because there is no `report.sh` yet.

   ```bash
   oslab check lab4
   ```

## Guided — Redirection and Pipelines (10–25)

**Goal:** see where output goes, and how a pipeline passes data from one command to the next. The examples use small data you create yourself.

1. Send normal output and an error to different files. The second command fails on purpose.

   ```bash
   printf 'normal output\n' > evidence/stdout-demo.txt
   cat missing-demo.txt 2> evidence/stderr-demo.txt
   cat evidence/stdout-demo.txt
   cat evidence/stderr-demo.txt
   ```

   `>` sent stream 1 to the first file. `2>` sent stream 2 to the second file.

2. Send both streams to one file, and check the status of a failing command.

   ```bash
   bash -c 'printf "out\n"; printf "err\n" >&2' > evidence/both.txt 2>&1
   cat evidence/both.txt
   cat missing-demo.txt 2> /dev/null
   echo "status: $?"
   ```

   `/dev/null` throws away what you send to it. The status is not `0`, because `cat` failed.

3. Build a pipeline one stage at a time. Run each line and read the result before you add the next stage.

   ```bash
   printf 'STATUS,3\nOTHER,2\n' | grep '^STATUS,'
   printf 'STATUS,3\nOTHER,2\n' | grep '^STATUS,' | cut -d, -f2
   ```

   `cut -d, -f2` cuts each line at the commas and keeps the second field. The last stage prints `3`.

4. Look at your data. The lab uses a simple two-field CSV without quoted commas.

   ```bash
   cat data/events.csv
   cat data/expected.txt
   ```

   **Observe:** Which rows have your status? Is there a row whose name only *starts* like your status? What does `wc -l` count: records or a sum?

## Prediction (25–35)

Guess first, then try. Answer alone, without AI.

```bash
oslab predict lab4
```

It asks three questions and one sentence about your own `events.csv`. A wrong guess costs nothing. You compare it with the real result later, in the debrief.

## Core 1 — Write report.sh (35–55)

**Goal:** a script that reads a CSV file and prints one line with the total of your status. Make it from the pieces you already know.

`report.sh` must:

- take **one argument**: the path of a CSV file,
- select every record whose first field is **exactly** your status (a look-alike such as `STATUS-late` must not count),
- add up field 2 of those records,
- print the result once, in the form `STATUS total: NUMBER`, for example `ready total: 8`,
- print `STATUS total: 0` when no record matches,
- when the input file does not exist: print a message on **stderr** (`>&2`), print nothing on stdout, and end with a status other than 0.

1. Look at what an incomplete pipeline gives you. Run the three lines, then compare with your prediction.

   ```bash
   grep '^STATUS,' data/events.csv
   grep '^STATUS,' data/events.csv | cut -d, -f2
   grep '^STATUS,' data/events.csv | cut -d, -f2 | head -n 1
   ```

2. Two tools you may need. `awk` can add numbers; `+0` makes an empty sum print `0`. This demonstration does not solve the lab:

   ```bash
   printf '2\n4\n' | awk '{ total += $1 } END { print total+0 }'
   ```

   An error message to stderr, and a stop with a failing status, look like this:

   ```bash
   if [ ! -f "$1" ]; then
       echo "report.sh: no such file: $1" >&2
       exit 1
   fi
   ```

3. **Your decision.** Write `report.sh` in the lab4 folder. Open it with `nano report.sh`. Decide where the selection, the field extraction and the sum belong. A staged pipeline and a single `awk` program are both fine.

4. Run it on your file and compare it with the expected report.

   ```bash
   bash report.sh data/events.csv > evidence/normal.txt
   diff -u data/expected.txt evidence/normal.txt
   ```

   No output from `diff` means the files are the same. `oslab check lab4` also runs your script.

**Hints:** `oslab hint lab4 1`, `2` and `3`. AI is allowed here; test every suggestion on these small files.

## Core 2 — Test Your Report (55–70)

**Goal:** show that your script is right for more than one file. One matching file is useful, but it does not prove the script for every CSV.

1. Create two changed inputs without changing the original file.

   ```bash
   printf 'status,count\nOTHER,2\n' > data/no-match.csv
   cp -- data/events.csv data/changed.csv
   printf 'STATUS,7\n' >> data/changed.csv
   ```

2. Run the report on both files, and on a file that does not exist. Save everything, with the stderr message and the status.

   ```bash
   {
     bash report.sh data/no-match.csv
     bash report.sh data/changed.csv
     bash report.sh data/missing.csv
     printf 'missing-input status=%s\n' "$?"
   } > evidence/edge.txt 2>&1
   cat evidence/edge.txt
   ```

   Expect `STATUS total: 0`, then your normal total plus 7, then your error message, then a status that is not 0.

3. Check your work. The four Core milestones must show `PASS`.

   ```bash
   oslab check lab4
   ```

4. Write down for your report: what does each test contradict? Counting rows, using only the first match, counting a look-alike, and ignoring a missing input all give a wrong answer somewhere. Which test would catch each one? State one kind of CSV your script cannot read (for example a quoted comma).

## Instructor Demonstration, Plus and Challenge (70–85)

First, watch the instructor show a pipeline in which one stage fails and the pipe still "succeeds". Then, if you finish early, try these. They are not needed for full marks. Save your answers in `evidence/plus.txt`.

**Plus**

- Count how many records each status has in your file.

  ```bash
  cut -d, -f1 data/events.csv | sort | uniq -c
  ```

  `sort` puts equal lines next to each other, and `uniq -c` counts each group. Why does the header line `status` appear in the result?

**Challenge**

- Do the same sum without `awk`. `paste -sd+ -` joins the lines with a plus sign, and `$(( ))` calculates it:

  ```bash
  echo $(( $(grep '^STATUS,' data/events.csv | cut -d, -f2 | paste -sd+ -) ))
  ```

  What does this print for your own data? What happens when no row matches, and why?

## Live Checkpoint (85–100)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab4
```

1. Answer the four questions. They use new records that were made for you at this moment.
2. Then do the small task that the command prints: create the new CSV file, run **your own** `report.sh` on it, and save the output in `checkpoint.txt`.
3. Run `oslab check lab4`. A fifth milestone, `checkpoint`, must show `PASS`.

## Debrief (100–110)

Look at your prediction again. `oslab` saved it in a hidden folder, `.records`.

```bash
cat "$OSLAB_WORKSPACE/.records/lab4-predict.json"
```

Now give the right answer to each prediction question:

```bash
oslab debrief lab4
```

Your prediction stays saved as it was, so the comparison shows which answers you confirmed and which you corrected. Then the class discusses: why is the number from `wc -l` a different quantity from the total?

## Submit (110–120)

1. Copy your work to your course repository. Replace `YOUR_ID` with your own ID.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab4/evidence"
   cp -- report.sh "$SUBMISSION_REPO/lab4/"
   cp -- evidence/normal.txt evidence/edge.txt "$SUBMISSION_REPO/lab4/evidence/"
   ```

   If you did Plus or Challenge, copy `evidence/plus.txt` the same way.

2. Fill in the [report template](README.md) as `lab4/README.md`. Your repository then has:

   ```text
   lab4/
   ├── README.md
   ├── report.sh
   └── evidence/
       ├── normal.txt
       └── edge.txt
   ```

   The course website checks that these exact names are there.

3. Commit and push. `git pull` comes first, in case you pushed from your own computer since.

   ```bash
   cd ~/os-gic-YOUR_ID
   git pull
   git add os-lab-YOUR_ID/lab4
   git commit -m "Lab 4"
   git push
   ```

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Report: `oslab check lab4` passes the four Core milestones (your own events.csv, no match, extra records, missing input) | 2 |
| Tests: `normal.txt` and `edge.txt` show the results, and the README says what each test contradicts | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab4` | 2 |
| Live checkpoint: the four answers and your `report.sh` working on the new file | 3 |
| Complete submission: the required files in your repository, on time | 1 |

Every row is marked from your `oslab` records and the files in your repository, so run `oslab check lab4` until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.

## Help and References

- `oslab hint lab4 1`, `2`, `3`
- `man grep`, `man cut`, `man awk`
- The original post-lab challenge is in [lab4-challenge.md](lab4-challenge.md). Process tools and orphan/zombie processes are in the [optional extensions](extensions.md).
