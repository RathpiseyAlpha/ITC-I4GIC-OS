# OS Lab 6 — Linux Security, Users, Groups & File Permissions (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class. Before class: about 10 minutes for the pre-lab |
| Work | Individual. Your notice policy and your demo folder name are different from your neighbour's |
| Environment | Shared Ubuntu server with an individual account for each student. Local Linux/WSL works for practice ([setup](../SETUP.md)) |
| Tools | `id`, `stat`, `chmod`, `ls`, `namei`, `oslab`. No administrator access |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Lecture link | [Week 12 notes: file systems](../../lectures/notes/week12-file-systems.md) |

> **Scenario:** TechCorp needs a private record and a notice that staff can eventually read. Configure your owned copy first and justify the full access path before an administrator prepares any multi-user exercise.

## Lab Objectives

After the required core, you should be able to:

1. Interpret owner/group/other mode bits and symbolic versus octal notation.
2. Set least-privilege modes on owned files/directories and explain directory traversal.
3. Diagnose an access failure using path/mode evidence, distinguishing observed access from a hypothetical peer decision.

**Extension objectives:** Inspect accounts/groups, ACLs and special bits; use narrowly prepared identities or disposable VM accounts for actual cross-user experiments. These retain the original lab's wider topics; they are not required to finish the two-hour core. They are in the [optional extensions](extensions.md).

## How This Lab Works

| Command | What it does |
|---|---|
| `oslab values lab6` | Shows **your** notice policy (a sentence) and the name of your demo folder |
| `oslab predict lab6` | Saves your prediction once, before the experiment |
| `oslab hint lab6 1` | Gives a hint (levels 1, 2, 3). Hints cost no points |
| `oslab check lab6` | Reads the modes of your files and shows your milestones |
| `oslab checkpoint lab6` | Opens when the instructor says so, near the end |
| `oslab debrief lab6` | After the lab: you give the right answers to your prediction questions |

- **Core** is for everyone. **Plus** and **Challenge** are for students who finish early. Full marks need only Core and the checkpoint.
- AI tools are allowed in Core, Plus and Challenge. They are **not** allowed in the prediction and the checkpoint. Always test what an AI tells you.
- In Core 1 nobody gives you the modes. You turn your policy sentence into numbers yourself.
- You only change your own files. You never use `sudo`, never change your home folder, and never try to read a neighbour's files.

## Before the Lab

Do this before class. It takes about 10 minutes.

```bash
oslab doctor
oslab prelab lab6
```

## Mode Bits First

Every file and folder has an **owner**, a **group**, and a **mode**: three triples of permissions, for the owner, for the group, and for everybody else (*others*).

| Letter | Number | On a file | On a folder |
|---|---|---|---|
| `r` | 4 | read the content | list the names inside |
| `w` | 2 | change the content | create, rename or delete names inside |
| `x` | 1 | run it as a program | **enter it** (search): reach the files inside by name |

Add the numbers of each triple. So `rw-r-----` is 4+2=**6**, 4, 0, and the octal mode is `640`. Symbolic notation writes the same thing in letters: `chmod u=rw,g=r,o= file` gives `640`.

The system checks **every folder on the path**, one after the other. A file with mode `644` inside a folder that you may not enter cannot be read by you.

## Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Setup |
| 10–25 | Guided: permission basics |
| 25–35 | Prediction |
| 35–55 | Core 1: set the modes |
| 55–70 | Core 2: prove it |
| 70–85 | Instructor demonstration, Plus and Challenge |
| 85–100 | Live checkpoint |
| 100–110 | Debrief |
| 110–120 | Submit |

## Setup (0–10)

1. Log in to the server with your own account. Start the lab and go into its folder.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab6
   cd "$OSLAB_WORKSPACE/lab6"
   mkdir -p evidence
   oslab values lab6
   ```

2. **Read your personal values.** The last command prints your notice policy and a name. For example:

   ```text
   Your personal values for lab6 (your-account):
     notice   = The owner may change the file. The owner's group may read it and list the folder. Others have no access.
     box      = sealed-maple
   ```

   Your own policy and name are different. Write them down.

3. **Understand the capital word.** This instruction cannot know your name, so it writes `BOX` where your `box` value belongs. Never type `BOX`. Type your own value in its place.

   | The instruction says | With the example value above, you type |
   |---|---|
   | `mkdir -p demo/BOX` | `mkdir -p demo/sealed-maple` |

4. Your folder now looks like this:

   ```text
   lab6/
   ├── .oslab-managed.json
   ├── private/
   │   └── record.txt
   ├── shared/
   │   └── notice.txt
   └── evidence/
   ```

5. Try the checking command once. At the start every line says `TRY`.

   ```bash
   oslab check lab6
   ```

## Guided — Permission Basics (10–25)

**Goal:** read modes, and change them on a demo file that is not part of your answer.

1. Show who you are, and the modes of your folders and files.

   ```bash
   id
   ls -ld . private shared
   stat -c '%A %a %U:%G %n' private/record.txt shared/notice.txt
   ```

   `%A` is the mode in letters, `%a` in octal, `%U:%G` the owner and the group, `%n` the name.

2. Compare octal and symbolic notation on a separate demo file.

   ```bash
   mkdir -p demo
   printf 'demo content\n' > demo/note.txt
   chmod 600 demo/note.txt
   stat -c '%A %a %n' demo/note.txt
   chmod u=rw,g=r,o= demo/note.txt
   stat -c '%A %a %n' demo/note.txt
   ```

   The two modes are `600` (`rw-------`) and `640` (`rw-r-----`). The second gives the owning group read permission. It does not make any folder on the path enterable.

3. Look at every folder on a path.

   ```bash
   namei -l "$PWD/demo/note.txt"
   ```

   If `namei` is missing, list each parent with `ls -ld`. **Observe:** does mode `644` on a file inside a `700` folder mean that other users can reach the file?

## Prediction (25–35)

Guess first, then try. Answer alone, without AI.

```bash
oslab predict lab6
```

It asks four questions and one sentence, about a folder with mode 600 and about your own notice policy. A wrong guess costs nothing. You compare it with the real result in the debrief.

## Core 1 — Set the Modes (35–55)

**Goal:** turn two policies into modes, apply them to your own files, and save the result.

1. **Policy for the private record** (the same for everybody): only you may read and change `private/record.txt`, and nobody else may even enter `private/`.
2. **Policy for the notice** (your own sentence from `oslab values lab6`): it applies to `shared/notice.txt` and to the folder `shared/`.
3. **Your decision.** Write the four `chmod` commands yourself: one for `private/`, one for `private/record.txt`, one for `shared/`, one for `shared/notice.txt`. Work out each mode from the table in [Mode Bits First](#mode-bits-first): which digits do you need for the owner, the group and the others? Does the folder need the `x` bit for the people who may read the file inside it?
4. Save the result. Run this **after** your last `chmod`.

   ```bash
   stat -c '%A %a %U:%G %n' private private/record.txt shared shared/notice.txt | tee evidence/policy.txt
   ```

5. Check your work. The first two Core milestones must show `PASS`.

   ```bash
   oslab check lab6
   ```

**Hints:** `oslab hint lab6 1`, `2` and `3`. AI is allowed here; test every suggestion with `stat`.

## Core 2 — Prove It (55–70)

**Goal:** show that the modes work, and show a failure that you can explain.

1. Use the private record as its owner. Append a line and check that the file is not executable. Do not try to run a data file to test read permission.

   ```bash
   cat private/record.txt
   printf 'owner update\n' >> private/record.txt
   if test -x private/record.txt; then printf 'unexpected execute bit\n'; else printf 'not executable\n'; fi
   ```

2. Test a folder without search permission, on a demo folder. The failing `cat` is **intended**. Restore the folder right after.

   ```bash
   mkdir -p demo/BOX
   printf 'inside\n' > demo/BOX/item.txt
   chmod 600 demo/BOX
   ls demo/BOX | tee evidence/traversal.txt
   cat demo/BOX/item.txt 2>&1 | tee -a evidence/traversal.txt
   chmod 700 demo/BOX
   cat demo/BOX/item.txt | tee -a evidence/traversal.txt
   ```

   `ls` shows the name because the folder has `r`. `cat` fails because the folder has no `x`. `2>&1` saves the error message in the file too. Which bit of `demo/BOX` caused the failure?

3. Check your work. All four Core milestones must show `PASS`.

   ```bash
   oslab check lab6
   ```

4. **A hypothetical peer.** Could another student read `shared/notice.txt` under your policy? Look at **every** parent of the file, including your workspace folder `oslab-work` and your home folder. Do **not** change them to try it out.

   ```bash
   namei -l "$PWD/shared/notice.txt"
   ```

   Write down for your report: the notice's own mode is not enough. Which parent decides? What was a real test above, and what is only your reasoning?

## Instructor Demonstration, Plus and Challenge (70–85)

First, watch the instructor show two accounts on a prepared machine: a file with mode 644 inside a folder with mode 711, then 700. Then, if you finish early, try these. They are not needed for full marks. Save your answers in `evidence/plus.txt`.

**Plus**

- Write the **symbolic** `chmod` command that gives `shared/notice.txt` the same mode as your numbers (for example `u=rw,g=r,o=` for `640`). Run it. Check with `stat -c '%A %a %n' shared/notice.txt` that nothing changed.

**Challenge**

- `umask` shows which bits a new file does **not** get. With `umask` = `0022`, a new file is created with mode `644`, and a new folder with `755`. Predict the mode of a file you create after `umask 077`, then test it in a subshell so that your session keeps its umask:

  ```bash
  ( umask 077; touch demo/umask-test.txt; stat -c '%A %a %n' demo/umask-test.txt )
  ```

## Live Checkpoint (85–100)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab6
```

1. Read the new policy. Answer the four questions: two octal modes, one yes/no and one sentence.
2. Then do the file task that the command prints: make the new folder and `data.txt`, set **your** two modes, and save the `stat` output in `checkpoint.txt`.
3. Run `oslab check lab6`. A fifth milestone, `checkpoint`, must show `PASS`.

## Debrief (100–110)

Look at your prediction again. `oslab` saved it in a hidden folder, `.records`.

```bash
cat "$OSLAB_WORKSPACE/.records/lab6-predict.json"
```

Now give the right answer to each prediction question:

```bash
oslab debrief lab6
```

Your prediction stays saved as it was, so the comparison shows which answers you confirmed and which you corrected. Then the class discusses: a file is readable by its mode, but you still got `Permission denied`. Where do you look?

## Submit (110–120)

1. Copy your work to your course repository. Replace `YOUR_ID` with your own ID.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab6/evidence"
   cp -- evidence/policy.txt evidence/traversal.txt "$SUBMISSION_REPO/lab6/evidence/"
   ```

   If you did Plus or Challenge, copy `evidence/plus.txt` the same way.

2. Fill in the [report template](README.md) as `lab6/README.md`. Your repository then has:

   ```text
   lab6/
   ├── README.md
   └── evidence/
       ├── policy.txt
       └── traversal.txt
   ```

   The course website checks that these exact names are there.

3. Commit and push. `git pull` comes first, in case you pushed from your own computer since.

   ```bash
   cd ~/os-gic-YOUR_ID
   git pull
   git add os-lab-YOUR_ID/lab6
   git commit -m "Lab 6"
   git push
   ```

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Modes: `oslab check lab6` passes the four Core milestones (private, your notice policy, the traversal test, `policy.txt`) | 2 |
| Tests: `policy.txt` and `traversal.txt` show the modes and the failure, and the README separates what you tested from what you reasoned | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab6` | 2 |
| Live checkpoint: the answers and the new folder with the right modes | 3 |
| Complete submission: the required files in your repository, on time | 1 |

Every row is marked from your `oslab` records and the files in your repository, so run `oslab check lab6` until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.

## Help and References

- `oslab hint lab6 1`, `2`, `3`
- `man chmod`, `man stat`, `man namei`, `man path_resolution`
- A normal user cannot `chown` a file to another account. Never edit sudoers and never create accounts for this lab.
- Accounts, groups, ACLs and special bits are in the [optional extensions](extensions.md). Peer experiments need an instructor-prepared account.
