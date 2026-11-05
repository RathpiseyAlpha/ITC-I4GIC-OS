# OS Lab 3 — Wildcards, Hard Links and Symbolic Links (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class. Before class: about 20 minutes to read [Concepts First](#concepts-first) and do the pre-lab |
| Work | Individual. Your file names and your version numbers are different from your neighbour's |
| Environment | Shared Ubuntu server with an individual account for each student. Local Linux/WSL works for practice ([setup](../SETUP.md)) |
| Tools | `ls`, `ln`, `readlink`, `mv`, `rm`, `cat`, `printf`, `tee`, `oslab` |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Lecture link | [Week 12 notes: file systems](../../lectures/notes/week12-file-systems.md) |
| Optional work | GRUB and shared libraries are in the [extensions](extensions.md); they are not graded in this core |

> **Scenario:** You look after a report that other names refer to. Today you rename the report, find out which references break, repair a symbolic link, and meet a new file that takes the old name.

## Lab Objectives

By the end, you should be able to:

1. Explain which filenames a Bash wildcard selects and what quoting changes.
2. Use inode numbers to distinguish a hard link from a separate copy.
3. Explain and repair a symbolic link after its target is renamed.

## How This Lab Works

| Command | What it does |
|---|---|
| `oslab values lab3` | Shows **your** report name, the word for the renamed file and your two version numbers. Use them everywhere in this lab |
| `oslab predict lab3` | Saves your prediction once, before the experiment |
| `oslab hint lab3 1` | Gives a hint (levels 1, 2, 3). Hints cost no points |
| `oslab check lab3` | Looks at your files and shows your milestones |
| `oslab checkpoint lab3` | Opens when the instructor says so, near the end |
| `oslab debrief lab3` | After the lab: you give the right answers to your prediction questions |

- **Core** is for everyone. **Plus** and **Challenge** are for students who finish early. Full marks need only Core and the checkpoint.
- AI tools are allowed in Core, Plus and Challenge. They are **not** allowed in the prediction and the checkpoint. Always test what an AI tells you.
- In Core 3 nobody gives you the repair commands. You write them yourself.

## Before the Lab

Do this before class. It takes about 20 minutes.

1. Read [Concepts First](#concepts-first) below, and try its examples in a practice folder in your home on the server.
2. Then check the helper and answer the three pre-lab questions.

   ```bash
   oslab doctor
   oslab prelab lab3
   ```

## Concepts First

This section explains the ideas the lab uses. Your instructor goes through it again at the start of the class.

### 1. Wildcards are expanded by the shell

A **wildcard** (also called a glob) is a pattern that stands for file names. You type the pattern; **Bash** looks in the folder, replaces the pattern with the names that match, and only then starts the command. The command never sees the `*`.

| Pattern | Matches | Example |
|---|---|---|
| `*` | any number of characters, also none | `*.txt` is every name that ends in `.txt` |
| `?` | exactly one character | `report?.txt` matches `report1.txt`, not `report12.txt` |
| `[12]` | one character out of the list | `report[12].txt` matches `report1.txt` and `report2.txt` |
| `[!1]` | one character that is **not** in the list | `report[!1].txt` |

Three rules that surprise people:

- A name that starts with `.` is **hidden**. `*` does not match it, so `*.txt` skips `.draft.txt`.
- **Quotes switch the expansion off.** `printf '%s\n' '*.txt'` prints the two characters `*.txt`, because the quoted text is not a pattern any more.
- If nothing matches, Bash leaves the pattern as it is, and the command gets the literal `*.txt`.

To see what a pattern expands to, put it after `printf '<%s>\n'`. `printf` prints each name it receives between `<` and `>` on its own line:

```text
student@server:~$ ls
a.txt  b.txt  c.log
student@server:~$ printf '<%s>\n' *.txt
<a.txt>
<b.txt>
student@server:~$ printf '<%s>\n' '*.txt'
<*.txt>
```

### 2. A file is an inode with one or more names

Linux stores a file in two parts. The **inode** holds the file's information (size, owner, permissions, where the data is) and has a number. A **directory** is a table of names, and each name points to an inode number. So a *name* and the *file* are not the same thing.

![A directory maps filenames to inode numbers; the inode holds file metadata and points to the data.](figures/inode.svg)

`ls -li` shows the inode number in the first column, and the number of names in the third column:

```text
student@server:~/demo$ ls -li
total 8
1310725 -rw-r--r-- 1 student student 6 Nov  5 10:00 a.txt
```

### 3. Hard links: another name for the same inode

`ln a.txt b.txt` adds a second name, `b.txt`, for the **same inode**. There is one file with two names. Both names show the same inode number, and the number after the permissions (the **link count**) becomes 2. Rename or delete one name, and the other still reaches the data. A hard link must stay on the same filesystem.

A **copy** (`cp`) is different: it makes a new inode with the same bytes. Equal contents do not mean equal files; only the inode number tells them apart.

### 4. Symbolic links: a name that stores a path

`ln -s a.txt s.txt` makes a new file, `s.txt`, with **its own inode**. Its content is only the text `a.txt`: the path of its target. `readlink s.txt` prints that stored path. Opening `s.txt` makes Linux read that path and open the file it finds there.

![Two hard-linked names share an inode. A symbolic link has a separate inode storing the target path.](figures/hard-soft-links.svg)

A **relative target starts from the folder that holds the link**, not from where you are. A link `links/s.txt` that stores `a.txt` means `links/a.txt`. A link that stores `links/a.txt` would look for `links/links/a.txt`.

### 5. A link stores a name, not a file

A symbolic link does not know which file it was made for. It only repeats a name every time it is opened. Two things follow:

- If the file with that name is **renamed**, the link keeps the old name, and no file has it any more. The link is **dangling**: `cat` says `No such file or directory`, although the link itself exists.
- If a **new file** is later created with the old name, the link works again, but it now reads the new file. A hard link never does this, because it points to the inode, not to a name.

### 6. Commands used in this lab

| Command | What it does | Example |
|---|---|---|
| `ln A B` | Makes the hard link `B` to the file `A` | `ln report.txt report-hard.txt` |
| `ln -s TARGET LINK` | Makes the symbolic link `LINK` that stores the path `TARGET` | `ln -s report.txt report-soft.txt` |
| `ls -li` | Lists with the inode number first and the link count in the third column | `ls -li report.txt report-hard.txt` |
| `readlink LINK` | Prints the path a symbolic link stores | `readlink report-soft.txt` |
| `mv -- A B` | Renames `A` to `B` (the file keeps its inode) | `mv -- report.txt report-old.txt` |
| `rm -- LINK` | Deletes one name. For a symbolic link it deletes the link, not the target | `rm -- report-soft.txt` |
| `printf 'text %s\n' "$x"` | Prints text with the value of `$x` in place of `%s` | `printf 'version %s\n' "$v2" > a.txt` |
| `{ ...; } \| tee -a F` | Runs several commands as one group, shows their output and **adds** it to the file `F` (`tee` without `-a` replaces the file) | see Core 2 |

`{ command1; command2; }` groups commands so that one pipe takes all their output. Each command goes on its own line, or ends with `;`. `2>&1` sends the error messages to the same place as the normal output, so `tee` saves them too (Lab 4 explains it fully).

## Timetable

| Minutes | Activity |
|---|---|
| 0–5 | Setup |
| 5–20 | Guided: names, inodes and links |
| 20–30 | Prediction, then class discussion |
| 30–40 | Core 1: wildcards on your own files |
| 40–60 | Core 2: rename, break, and reuse the old name |
| 60–75 | Core 3: repair and prove it |
| 75–90 | Plus and Challenge (or finish Core) |
| 90–105 | Live checkpoint |
| 105–115 | Debrief |
| 115–120 | Submit |

## Setup (0–5)

1. Start the lab and go into its folder.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab3
   cd "$OSLAB_WORKSPACE/lab3"
   mkdir -p evidence
   oslab values lab3
   ```

   The first line gives the shell variable `OSLAB_WORKSPACE` the value `~/oslab-work`, the folder where `oslab` keeps your labs. `export` lets the `oslab` command see it too. Type it as it is.

2. Type **your** values into shell variables: `name=value` with **no spaces** around `=`. The values below are only an example.

   ```bash
   name=maple
   tag=old
   v1=417
   v2=463
   ```

   If you open a new terminal, run `cd` and set these variables again.

3. **Understand the variables and the placeholders.** After step 2 the shell replaces `"$name"` with your report name, `"$tag"` with your word for the renamed file, and `"$v1"` and `"$v2"` with your two version numbers. Where this instruction cannot use a variable, it writes the value's name in angle brackets, like `<name>`. Never type the brackets: type your own value, or the variable in double quotes.

   | The instruction says | With the example values above, you type | Or, with the variables |
   |---|---|---|
   | `ln "$name.txt" "$name-hard.txt"` | `ln maple.txt maple-hard.txt` | the same line |
   | `<name>-<tag>.txt` | `maple-old.txt` | `"$name-$tag.txt"` |
   | `version <v2>` | `version 463` | `printf 'version %s\n' "$v2"` |

   `"$name-hard.txt"` works because `-` cannot be part of a variable name: the shell reads `$name`, then the text `-hard.txt`.

4. Your folder looks like this, with your own names:

   ```text
   lab3/
   ├── links/
   │   └── (name).txt        # your report: it holds "version (v1)"
   ├── notes/
   │   ├── (name)1.txt
   │   ├── (name)2.txt
   │   ├── (name)12.txt
   │   ├── (name).log
   │   └── .(name).txt       # a hidden file
   └── evidence/
   ```

   `oslab start` keeps your work when you run it again. Do not reset the lab to fix one link. No step needs `sudo`.

## Guided — Names, Inodes and Links (5–20)

Your instructor first goes through [Concepts First](#concepts-first) with the guide, for about five minutes. Then type along. This part uses a separate folder, `practice/`, and fixed names, so it does not touch your own files.

1. Make three small files and look at what a pattern selects. Nothing is saved here.

   ```bash
   mkdir -p practice
   printf 'one\n' > practice/report1.txt
   printf 'two\n' > practice/report2.txt
   printf 'log\n' > practice/report.log
   printf '<%s>\n' practice/*.txt
   printf '<%s>\n' practice/report?.txt
   printf '<%s>\n' 'practice/*.txt'
   ```

   `*` and `?` are expanded by Bash before `printf` runs. The last pattern is quoted, so `printf` receives the literal text. Which names does each command print, and why is `report.log` never in the list?

2. Make a hard link and a symbolic link to `report1.txt`, and compare.

   ```bash
   ln practice/report1.txt practice/hard-demo.txt
   ln -s report1.txt practice/soft-demo.txt
   ls -li practice/report1.txt practice/hard-demo.txt practice/soft-demo.txt
   readlink practice/soft-demo.txt
   ```

   Compare the inode numbers in the first column. `report1.txt` and `hard-demo.txt` show the same number and the link count 2: one file, two names. `soft-demo.txt` has its own number, and `readlink` prints the text it stores.

3. Read the stored target. `soft-demo.txt` is inside `practice/`, and it stores only `report1.txt`. Linux reads that path from the folder that holds the link, so it means `practice/report1.txt`. Which path would be wrong, and what would Linux look for?

## Prediction (20–30)

```bash
oslab predict lab3
```

Answer alone, without AI, before the experiment. The questions use **your** names and numbers. A wrong prediction costs nothing. The class will look at the spread of answers together.

## Core 1 — Wildcards on Your Own Files (30–40)

Your `notes/` folder holds five files with your own names. Which of them does each pattern select?

1. Look at the folder, hidden names included.

   ```bash
   cd "$OSLAB_WORKSPACE/lab3"
   ls -a notes
   ```

2. Run three `printf` commands and save what they print. **You write the middle command**: it must print only your two files with a **one-digit** number, `<name>1.txt` and `<name>2.txt`, and not `<name>12.txt`. Write the pattern with `"$name"` in double quotes, and the `?` outside the quotes. Replace the comment line with your command.

   ```bash
   {
     printf '<%s>\n' notes/*.txt
     # write the middle command here
     printf '<%s>\n' 'notes/*.txt'
   } | tee evidence/wildcards.txt
   ```

   **You should see** three names, then two names, then the literal `<notes/*.txt>`. The hidden file is not in the first list, and `<name>.log` is in none of them. `{` and `}` group the three commands so that one `tee` saves all their output.

Stuck for more than five minutes? Use `oslab hint lab3 1`, then `2`, then `3`.

## Core 2 — Rename, Break, and Reuse the Old Name (40–60)

You make two links to your report, rename the report, and watch what happens. Keep your own names: `oslab check` looks for them.

1. **Make the references and save the starting state.** Go into `links/`. Check that your report holds `version <v1>`, then make a hard link and a symbolic link. The `tee` at the end starts your evidence file; later commands add to it.

   ```bash
   cd "$OSLAB_WORKSPACE/lab3/links"
   cat "$name.txt"
   ln "$name.txt" "$name-hard.txt"
   ln -s "$name.txt" "$name-soft.txt"
   {
     printf '\n=== BEFORE RENAME ===\n'
     ls -li "$name.txt" "$name-hard.txt" "$name-soft.txt"
     printf 'hard: '; cat "$name-hard.txt"
     printf 'soft: '; cat "$name-soft.txt"
     printf 'stored target: '; readlink "$name-soft.txt"
   } | tee ../evidence/links.txt
   ```

   **You should see** `version <v1>` three times, and the same inode number for your report and `<name>-hard.txt`. If `ln` says `File exists`, look at what is there; do not overwrite it.

2. **Rename the report and read each reference.** The error in this step is **expected**: save it too.

   ```bash
   mv -- "$name.txt" "$name-$tag.txt"
   {
     printf '\n=== AFTER RENAME, BEFORE REPAIR ===\n'
     ls -li "$name-$tag.txt" "$name-hard.txt" "$name-soft.txt"
     printf 'hard: '; cat "$name-hard.txt"
     printf 'stored target: '; readlink "$name-soft.txt"
     printf 'soft: '; cat "$name-soft.txt"
   } 2>&1 | tee -a ../evidence/links.txt
   ```

   **You should see** the hard link still printing `version <v1>`, and `cat` failing for the symbolic link with `No such file or directory`. The link still exists, but the name it stores belongs to no file now: it is *dangling*.

3. **Create a new file with the old name.** Somebody else makes a new report with your old file name, and the new one holds `version <v2>`. Then look at all four names.

   ```bash
   printf 'version %s\n' "$v2" > "$name.txt"
   {
     printf '\n=== NEW FILE USING THE OLD NAME ===\n'
     ls -li "$name.txt" "$name-$tag.txt" "$name-hard.txt" "$name-soft.txt"
     printf '%s: ' "$name.txt"; cat "$name.txt"
     printf 'hard: '; cat "$name-hard.txt"
     printf 'soft: '; cat "$name-soft.txt"
   } 2>&1 | tee ../evidence/replacement.txt
   ```

   **You should see** that the symbolic link works again, but it prints `version <v2>`: it reads the **new** file. The hard link still prints `version <v1>`, because it points to the inode of your original report, and the new file has another inode. Write in your report which of the two was a surprise.

## Core 3 — Repair and Prove It (60–75)

1. **Repair only the symbolic link. Your decision.** The report now has the name `<name>-<tag>.txt`. Make `<name>-soft.txt` read your **original** report again, with a **relative** target. Write the two commands yourself: delete the link with `rm --`, then make it again with `ln -s TARGET LINK`. Ask: from which folder is the stored target read, and which path leads from there to `<name>-<tag>.txt`?

   Do not touch the hard link, and do not rename the report back. Check with `cat "$name-soft.txt"`: it must print `version <v1>`.

2. **Save the repaired state**, still in `links/`:

   ```bash
   {
     printf '\n=== AFTER REPAIR ===\n'
     ls -li "$name-$tag.txt" "$name-hard.txt" "$name-soft.txt"
     printf 'stored target: '; readlink "$name-soft.txt"
     printf 'hard: '; cat "$name-hard.txt"
     printf 'soft: '; cat "$name-soft.txt"
   } | tee -a ../evidence/links.txt
   ```

   Then add **one more line at the end** of `evidence/links.txt` with `nano ../evidence/links.txt`. It starts with `Decision:` and says why you stored a relative target, and what would break if the link stored an absolute path and you moved the whole folder. Save with `Ctrl+O` and `Enter`, and leave with `Ctrl+X`.

3. **Check your milestones.**

   ```bash
   cd "$OSLAB_WORKSPACE/lab3"
   oslab check lab3
   ```

   **You should see** five `PASS` lines, with your own names:

   ```text
   PASS: wildcards: evidence/wildcards.txt holds your three expansions
   PASS: hard link: maple-hard.txt and maple-old.txt are the same file (version 417)
   PASS: symbolic link: maple-soft.txt stores a relative target that reaches maple-old.txt
   PASS: new file: maple.txt holds version 463 and is separate from the version 417 file
   PASS: evidence/links.txt records the failure after the rename and the repaired link
   milestones: 5/5
   ```

   A line that starts with `TRY` names what is still missing, and the `why:` lines under it say what `oslab` found instead. Fix that part, then run `oslab check lab3` again. `oslab hint lab3 1` can help.

**Core is complete when** `oslab check lab3` shows `milestones: 5/5`.

## Plus — One More Pattern (75–90)

In square brackets, `[12]` matches one character, either `1` or `2`, and `[!1]` matches one character that is not `1`.

```bash
cd "$OSLAB_WORKSPACE/lab3"
printf '<%s>\n' notes/"$name"[12].txt
printf '<%s>\n' notes/"$name"[!1]*
```

**Before you run them**, write down which names you expect each command to print. Then run them and save one sentence in `evidence/plus.txt`: where did your guess differ from the result? Hint for the second pattern: one character that is not `1`, then anything.

## Challenge

A file's data stays on the disk as long as **at least one name** points to its inode. In a new folder, give one file three names and take them away one by one:

```bash
mkdir -p extra
cd extra
printf 'keep me\n' > one.txt
ln one.txt two.txt
ln one.txt three.txt
ls -l one.txt two.txt three.txt
```

The number after the permissions is the link count. Then `rm -- one.txt`, look again with `ls -l`, and `cat two.txt`. Answer in `evidence/challenge.txt` (in the lab folder, not in `extra/`):

- What link count do the remaining names show after each `rm`?
- After you delete `one.txt`, is the data gone? When would it be gone?

## Live Checkpoint (90–105)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab3
```

1. Answer the five questions. They use a **new folder and new names, made for you at this moment**, and a chain of two symbolic links.
2. Then build the case with the commands that `oslab` prints, **repair it yourself**, and save the output in `evidence/checkpoint.txt`. It prints a line with `{ ...; } | tee …`: it shows what the hard link and the end of the chain read, and saves it.
3. Run `oslab check lab3`. A sixth milestone, `checkpoint`, must pass.

## Debrief (105–115)

Look at your prediction again. `oslab` saved your answers in a hidden folder, `.records`, in your workspace. The file is in JSON, a text format of names and values.

```bash
cat "$OSLAB_WORKSPACE/.records/lab3-predict.json"
```

Now give the right answer to each prediction question. Type your answer again where your prediction was right, and the correct one where it was wrong:

```bash
oslab debrief lab3
```

Your prediction stays saved as it was, so the comparison shows which answers you confirmed and which you corrected. The debrief is marked: each answer must now be right. You may run it again if you mistype. Then the class discusses together: why can a symbolic link work and still read the wrong file?

## Submit (115–120)

1. Copy your work to your course repository. Replace `YOUR_ID` with your own ID. `SUBMISSION_REPO` is a variable like `name`: it keeps the long path, so the next lines stay short.

   ```bash
   cd "$OSLAB_WORKSPACE/lab3"
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab3/evidence"
   cp -- evidence/wildcards.txt evidence/links.txt evidence/replacement.txt "$SUBMISSION_REPO/lab3/evidence/"
   cp -- evidence/checkpoint.txt "$SUBMISSION_REPO/lab3/evidence/"
   ```

   If you did Plus or Challenge, copy `evidence/plus.txt` or `evidence/challenge.txt` the same way.

2. Fill in the [report template](README.md) as `lab3/README.md`. Your repository then has:

   ```text
   lab3/
   ├── README.md
   └── evidence/
       ├── checkpoint.txt   # the output you saved in the checkpoint
       ├── links.txt        # before, after the rename, after the repair, and your Decision: line
       ├── replacement.txt  # the new file that took the old name
       └── wildcards.txt    # your three expansions
   ```

   The course website checks that `README.md`, `wildcards.txt`, `links.txt` and `replacement.txt` are there, with these exact names.

3. Commit and push, as in Lab 1. `git pull` comes first, in case you pushed from your own computer since.

   ```bash
   cd ~/os-gic-YOUR_ID
   git pull
   git add os-lab-YOUR_ID/lab3
   git commit -m "Lab 3"
   git push
   ```

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Correct files: `oslab check lab3` passes Core milestones 1 to 4 | 2 |
| Tests: the failure after the rename and the repaired link in `links.txt` (milestone 5) | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab3` | 2 |
| Live checkpoint: the four answers, the repaired chain and the saved output, and your sentence | 3 |
| Complete submission: the required files in your repository, on time | 1 |

Every row is marked from your `oslab` records and the files in your repository, so run `oslab check lab3` until it shows what you expect. Your prediction earns its first point for being made, not for being right; the debrief earns the second when your answers are right after the lab. Plus and Challenge are not needed for full marks. They are noted in your feedback.

## Help and References

- `oslab hint lab3 1`, `2`, `3`
- `man ln`, `man readlink`, and `man bash` (search for "Pathname Expansion")
- GRUB, shared libraries and more wildcard practice are in the [optional extensions](extensions.md).
