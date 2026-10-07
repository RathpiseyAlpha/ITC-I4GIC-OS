# OS Lab 1 — Introduction to Operating Systems (Hands-on)

| Item | Details |
|---|---|
| Duration | Part A: 120 minutes in class (plus a 10-minute pre-lab). Part B: homework, about 60 minutes, due before the next class |
| Work | Individual. Your file names and numbers are different from your neighbour's |
| Where | Part A on the course server. Part B on **your own Ubuntu** (WSL or a virtual machine). Git keeps the two in step |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Lecture link | [Week 1 notes: introduction to operating systems](../../lectures/notes/week01-introduction-to-os.md) |

> **Scenario:** It is your first day at TechCorp. You log in to a Linux server you have never seen. You find out which system it is, practise the basic commands, and see how the system runs several programs at once. At home you install and remove software, and write your report.

## Lab Objectives

After this lab, you can:

1. Identify basic operating system and kernel information.
2. Use essential Linux file and directory commands.
3. Install, remove, and purge software using the APT package manager.
4. Understand the difference between a program and a running process.
5. Observe multitasking in a running operating system.
6. Detect whether an operating system is running on a virtualized environment.

## How This Lab Works

In class (Part A) you type commands in a terminal on the server and save the results in text files in your `lab1` folder. A few small helper commands (`oslab`) check your work and give you your own names and numbers. At home (Part B) you do the software task, take screenshots, write the report, and bring both machines together with Git.

| Command | What it does |
|---|---|
| `oslab values lab1` | Shows **your** names and number. You use them in Task 2 and Task 5 |
| `oslab predict lab1` | Saves your guess **before** you try things. A wrong guess costs nothing |
| `oslab hint lab1 1` | A hint. Use level 1, then 2, then 3. Hints cost no points |
| `oslab check lab1` | Checks your files and shows what is still missing |
| `oslab checkpoint lab1` | A short test near the end. It opens when the instructor says so |

Two small ideas before you start:

- `>` puts the output of a command **into a file** and replaces what was in the file. `>>` **adds** to the end of the file.
- `man COMMAND` shows the manual of a command, for example `man ls`. Press `q` to leave it.

AI tools are allowed during the tasks. They are **not** allowed for the prediction and the checkpoint. Always test what an AI tells you.

## Before the Lab

Log in to the server once before class, so password problems do not cost you lab time. Then run:

```bash
oslab doctor
oslab prelab lab1
```

For Part B you need a Linux of your own with `sudo`: WSL (Ubuntu) or your virtual machine. Open it once before class.

## Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Setup |
| 10–20 | Task 1: Which system is this? |
| 20–40 | Task 2: Files and folders |
| 40–50 | Prediction, then class discussion |
| 50–65 | Tasks 4 and 5: programs, processes and multitasking |
| 65–75 | Task 6: Is this a virtual machine? |
| 75–90 | Instructor demonstration, then Plus and Challenge |
| 90–105 | Live checkpoint |
| 105–120 | Debrief and homework briefing |

# Part A — In Class

## Setup (0–10)

1. Log in to the server with your own account. Start the lab and go into its folder.

   ```bash
   oslab start lab1
   cd ~/oslab-work/lab1
   oslab values lab1
   ```

2. **Read your personal values.** The last command prints three values that are only yours. For example:

   ```text
   Your personal values for lab1 (your-account):
     count    = 3
     file1    = maple
     file2    = river
   ```

   Your own words and number are different. Write them down.

3. **Understand the capital words.** This instruction cannot know your values, so it writes a word in capitals where your value belongs: `FILE1`, `FILE2` and `COUNT`. These words are placeholders. Never type them. Type your own value in their place.

   | The instruction says | With the example values above, you type |
   |---|---|
   | `touch FILE1.txt FILE2.txt` | `touch maple.txt river.txt` |
   | `echo "This is file FILE1" > FILE1.txt` | `echo "This is file maple" > maple.txt` |
   | type the line `COUNT` times | type the line 3 times |

4. Your folder now looks like this:

   ```text
   lab1/
   └── README.txt       # you add your result files here
   ```

5. Try the checking command once.

   ```bash
   oslab check lab1
   ```

   It prints one line for each part of the lab. `TRY` means "not done yet" and `PASS` means "done". At the start every line says `TRY`, because you have not done anything yet. Run it again whenever you want to see what is still missing.

## Task 1 — Which System Is This? (10–20)

**Goal:** find the operating system and the kernel. The **kernel** is the core of the system. It controls the hardware. The **distribution** (here Ubuntu) is the kernel plus many other programs.

1. Save the kernel information in a file, then add the distribution information to the same file.

   ```bash
   uname -a > task1_os_info.txt
   lsb_release -a >> task1_os_info.txt
   ```

2. Read the file.

   ```bash
   cat task1_os_info.txt
   ```

3. Write down for your report: which number is the version of the kernel, and which is the version of Ubuntu?

## Task 2 — Files and Folders (20–40)

**Goal:** practise the basic commands. In the commands, `FILE1` and `FILE2` stand for your own `file1` and `file2` from `oslab values lab1`. Type your own words, never the capitals.

The commands you use:

| Command | Meaning |
|---|---|
| `pwd` | Shows the folder you are in |
| `ls` | Lists the files in the folder |
| `mkdir` | Makes a folder |
| `cd` | Goes into a folder (`cd ..` goes up one folder) |
| `touch` | Makes an empty file |
| `echo` | Prints text. With `>` it writes the text into a file |
| `cat` | Shows what is inside a file |
| `cp` | Copies a file |
| `mv` | Moves or renames a file |
| `rm` | Deletes a file |

`..` always means "the folder above". So `../task2_file_commands.txt` is a file in the folder above the one you are in.

1. Make a working folder and go into it. Save where you are and what is in it.

   ```bash
   mkdir task2_files
   cd task2_files
   pwd > ../task2_file_commands.txt
   ls >> ../task2_file_commands.txt
   ```

2. Create the two files and list them.

   ```bash
   touch FILE1.txt FILE2.txt
   ls >> ../task2_file_commands.txt
   ```

3. Write one line into each file and save what is inside them.

   ```bash
   echo "This is file FILE1" > FILE1.txt
   echo "This is file FILE2" > FILE2.txt
   cat FILE1.txt FILE2.txt >> ../task2_file_commands.txt
   ```

4. Copy the first file. Rename the second. Delete the copy. List after each step.

   ```bash
   cp FILE1.txt FILE1_copy.txt
   ls >> ../task2_file_commands.txt
   mv FILE2.txt FILE2_renamed.txt
   ls >> ../task2_file_commands.txt
   rm FILE1_copy.txt
   ls >> ../task2_file_commands.txt
   ```

5. Go back to the lab folder and read your record.

   ```bash
   cd ..
   cat task2_file_commands.txt
   ```

   At the end of the file you see the final list: `FILE1.txt` and `FILE2_renamed.txt`.

## Prediction (40–50)

Guess first, then try. Answer alone, without AI.

```bash
oslab predict lab1
```

It asks three questions and one sentence. The answers come from Tasks 4 and 5, and from Task 3 at home. After this, the class looks together at what everybody guessed.

## Task 4 — Program or Process? (50–60)

**Goal:** see the difference between a program (a file on the disk) and a process (a program that is running).

1. Find the program file of `sleep`. `sleep` is a small program that just waits.

   ```bash
   which sleep
   ```

2. Run it for 30 seconds in the background. The `&` at the end means: run it, and give me my prompt back. Then list the running processes and save the list.

   ```bash
   sleep 30 &
   ps > task4_process_list.txt
   cat task4_process_list.txt
   ```

   `ps` lists the processes that run in your terminal.

3. Wait 30 seconds, then run `ps` again, and run `which sleep` again.

   ```bash
   ps
   which sleep
   ```

   Write down for your report: what did you see before, during and after? Where was the program, and where was the process?

## Task 5 — Multitasking (60–65)

**Goal:** see several programs at the same time.

1. Start `COUNT` copies of `sleep` in the background. Type this line `COUNT` times. (Press the up-arrow key to get the previous line again.)

   ```bash
   sleep 300 &
   ```

2. List the processes and save the list.

   ```bash
   ps > task5_multitasking.txt
   cat task5_multitasking.txt
   ```

3. **Take a screenshot** of your terminal now (it must show your prompt and the `ps` result). Keep it for your report as `task5.png`.

## Task 6 — Is This a Virtual Machine? (65–75)

**Goal:** find out whether the system runs on real hardware or inside a virtual machine.

1. Run the four commands. The `|` sends the output of `lscpu` into `grep`, which keeps only the lines that contain the words `hypervisor vendor`. A **hypervisor** is the program that runs virtual machines.

   ```bash
   systemd-detect-virt > task6_virtualization_check.txt
   lscpu | grep -i "hypervisor vendor" >> task6_virtualization_check.txt
   uname -r >> task6_virtualization_check.txt
   hostname >> task6_virtualization_check.txt
   cat task6_virtualization_check.txt
   ```

2. Write down for your report: what did the first line say, and what does it mean? A word such as `kvm`, `vmware` or `wsl` means a virtual machine. The word `none` means real hardware.

3. **Take a screenshot** of this result. Keep it as `task6.png`.

4. Check your work. All four milestones must show `PASS`.

   ```bash
   oslab check lab1
   ```

## Instructor Demonstration, Plus and Challenge (75–90)

First, watch the instructor show what the system does when programs really compute. `sleep` waits and uses no processor, so it shows that several processes exist at the same time, but not how the processor is shared.

Then, if you finish early, try these on the server. They are not needed for full marks.

**Plus**

- Run `top`. The line that begins with `Tasks:` counts all processes on the server. Press `q` to leave. Why are there more than the ones you started?
- Run `nproc`. It prints the number of processors. Compare it with the number of `sleep` processes you started.

**Challenge**

Run `ps -e | wc -l`. `ps -e` lists **all** processes of the server. `wc -l` counts the lines. How many processes are running? You started only a few of them. Who started the others? Write two sentences for your report.

## Live Checkpoint (90–105)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab1
```

1. Answer the questions.
2. Then do the small file task that the command prints (make a folder, create a file, copy it, rename it, save the list).
3. Run `oslab check lab1`. A fifth milestone, `checkpoint`, must show `PASS`.

## Debrief and Homework Briefing (105–120)

1. Look at your prediction again. You will test the third answer at home.

   ```bash
   cat ~/oslab-work/.records/lab1-predict.json
   ```

2. The instructor explains Part B. If there is time, do Step 1 of Part B now (push your Part A files from the server), so the instructor can help with GitHub.

# Part B — Homework (due before the next class)

Part B is part of Lab 1 and is graded with it. It takes about 60 minutes.

In this course you do **not** hand in Word or PDF reports. You use **Markdown and Git**. Your work lives in one GitHub repository, and you keep two machines in step with it by pushing and pulling.

## How Your Work Travels

```text
┌──────────────────────────── Course server (SSH) ───────────────────────────┐
│                                                                             │
│   Part A files            copy into              git push                   │
│   task1 … task6    ──▶    os-gic-YOUR_ID   ──▶   to GitHub                   │
│                                                                             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Step 1
                                       ▼
                         ┌───────────────────────────┐
                         │  GitHub: OS-GIC-YOUR_ID   │
                         └─────────────┬─────────────┘
                                       │ Step 2: git clone
                                       ▼
┌──────────────────────── Your own computer (Ubuntu) ────────────────────────┐
│                                                                             │
│   Task 3: APT       ──▶   screenshots and   ──▶   git push                  │
│   task3_apt.txt           README.md               to GitHub                 │
│                                                                             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Step 3
                                       ▼
                         ┌───────────────────────────┐
                         │  GitHub: OS-GIC-YOUR_ID   │
                         └─────────────┬─────────────┘
                                       │ Step 4: git pull
                                       ▼
┌──────────────────────────── Course server (SSH) ───────────────────────────┐
│                                                                             │
│   git pull          ──▶   tree: check that everything is there              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

The server pushes first, your computer pushes second, and the server only pulls after that. If you keep this order, the two machines never disagree.

## Step 1 — On the Server: Push Your Part A Files

Do this at the end of the class if there is time, so the instructor can help.

1. On GitHub, create an **empty** repository named `OS-GIC-YOUR_ID` (no README, no license). Replace `YOUR_ID` with your student ID.
2. On the server, tell Git who you are. First time only.

   ```bash
   git config --global user.name "YOUR NAME"
   git config --global user.email "YOUR_EMAIL"
   ```

3. Make your course folder and copy your Part A files into it.

   ```bash
   mkdir -p ~/os-gic-YOUR_ID/os-lab-YOUR_ID/lab1
   cp ~/oslab-work/lab1/task*.txt ~/os-gic-YOUR_ID/os-lab-YOUR_ID/lab1/
   cp -r ~/oslab-work/lab1/task2_files ~/os-gic-YOUR_ID/os-lab-YOUR_ID/lab1/
   ```

4. Turn the folder into a Git repository and push it. Replace `YOUR_USERNAME` with your GitHub name.

   ```bash
   cd ~/os-gic-YOUR_ID
   git init
   git add .
   git commit -m "Lab 1: Part A files"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/OS-GIC-YOUR_ID.git
   git push -u origin main
   ```

   GitHub asks for your user name and a **personal access token**. It does not accept your GitHub password here. The instructor shows how to create a token.

## Step 2 — On Your Own Ubuntu: Clone the Repository

Open a terminal in **your own Ubuntu** (WSL or a virtual machine). You have `sudo` there.

```bash
git clone https://github.com/YOUR_USERNAME/OS-GIC-YOUR_ID.git os-gic-YOUR_ID
cd os-gic-YOUR_ID/os-lab-YOUR_ID/lab1
mkdir images
ls
```

`ls` shows the files you made on the server. They travelled through GitHub.

## Task 3 — Install, Remove and Purge Software

**Goal:** see the difference between **remove** and **purge**. APT is the program that installs software on Ubuntu.

| Command | What it does |
|---|---|
| `sudo apt-get update` | Refreshes the list of available software. Installs nothing |
| `sudo apt-get install NAME` | Downloads and installs a package |
| `sudo apt-get remove NAME` | Uninstalls the program, but **keeps** its settings in `/etc` |
| `sudo apt-get purge NAME` | Uninstalls the program **and deletes** its settings |

Stay in the `lab1` folder of your clone, so the result file is saved in the right place. We use the package `mc` (Midnight Commander). It puts settings in the folder `/etc/mc`.

1. Install it, and save the path of the program and the state of the folder.

   ```bash
   sudo apt-get update
   sudo apt-get install mc -y
   which mc > task3_apt.txt
   ls -ld /etc/mc >> task3_apt.txt
   ```

2. Remove it. Look at the folder again.

   ```bash
   sudo apt-get remove mc -y
   ls -ld /etc/mc >> task3_apt.txt
   ```

3. Purge it. Look at the folder one more time. `2>&1` also saves the error message in the file.

   ```bash
   sudo apt-get purge mc -y
   ls -ld /etc/mc >> task3_apt.txt 2>&1
   cat task3_apt.txt
   ```

4. **Take a screenshot** that shows the last `ls -ld /etc/mc` after the purge. Keep it as `task3.png`. Compare it with your prediction.

## Step 3 — Write the Report and Push

1. Put your three screenshots (`task3.png`, `task5.png`, `task6.png`) into the `images` folder. In WSL, `explorer.exe .` opens the current folder in Windows Explorer.
2. Copy the [report template](README.md) into the `lab1` folder as `README.md`. Fill it in, and show your screenshots in it. In VS Code, `Ctrl+Shift+V` previews it.
3. Push everything from the top folder of your clone.

   ```bash
   cd ../..
   git add .
   git commit -m "Lab 1: Task 3, screenshots and report"
   git push
   ```

## Step 4 — On the Server: Pull

Log in to the server and pull. From now on, **only pull** on the server. Never edit your repository files there.

```bash
cd ~/os-gic-YOUR_ID
git pull
tree
```

`tree` must show this structure, with your own ID and file names:

```text
os-gic-YOUR_ID
└── os-lab-YOUR_ID
    └── lab1
        ├── images
        │   ├── task3.png
        │   ├── task5.png
        │   └── task6.png
        ├── README.md
        ├── task1_os_info.txt
        ├── task2_file_commands.txt
        ├── task2_files
        │   ├── FILE1.txt
        │   └── FILE2_renamed.txt
        ├── task3_apt.txt
        ├── task4_process_list.txt
        ├── task5_multitasking.txt
        └── task6_virtualization_check.txt
```

## Plus and Challenge for Homework

The Plus and Challenge from class are optional here too. You may also install two programs at once on your own Ubuntu (`sudo apt-get install htop tmux -y`) and check them with `which htop tmux`. More is in the [optional extensions](extensions.md).

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Files: `oslab check lab1` passes the four Core milestones (class) | 2 |
| Report (homework): kernel and distribution, remove and purge, program and process, virtual machine, written from your own results | 2 |
| Prediction saved in time, and an honest confirmed/corrected note (class) | 2 |
| Live checkpoint: answers, the file task, and your sentence (class) | 3 |
| Homework evidence: the APT file, three screenshots, README, pushed and pulled to the server on time | 1 |

Seven points are earned in class and three at home. Plus and Challenge are not needed for full marks. Your prediction is marked for being made and corrected, not for being right.

## Help and References

- `oslab hint lab1 1`, `2`, `3`
- `man uname`, `man ls`, `man apt-get`
- The slides for this lab: [Lab 1 guide](guides/slides.html) (also as a [PDF](guides/lab1-guides.pdf))
- More about APT and virtualization is in the [optional extensions](extensions.md).
