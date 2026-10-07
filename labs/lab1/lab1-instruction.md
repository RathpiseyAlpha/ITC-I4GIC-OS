# OS Lab 1 — Introduction to Operating Systems (Hands-on)

| Item | Details |
|---|---|
| Duration | Part A: 120 minutes in class (plus a 10-minute pre-lab). Part B: homework, about 60 minutes, due before the next class |
| Work | Individual. Your file names and numbers are different from your neighbour's |
| Where | Part A on the course server. Part B on **your own Ubuntu** (WSL or a virtual machine) and your own PC |
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

In class (Part A) you type commands in a terminal on the server and save the results in text files in your `lab1` folder. A few small helper commands (`oslab`) check your work and give you your own names and numbers. At home (Part B) you do the software task, take screenshots, write the report and push everything to GitHub.

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

   Write down your values. In this lab, they are called `file1`, `file2` and `count`. In the commands below, replace `FILE1` with your `file1`, `FILE2` with your `file2` and `COUNT` with your `count`.

2. Your folder now looks like this:

   ```text
   lab1/
   └── README.txt       # you add your result files here
   ```

3. Try the helper once. It shows `TRY` for everything. That is correct: you have not done anything yet.

   ```bash
   oslab check lab1
   ```

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

**Goal:** practise the basic commands. You use two file names that are only yours: `FILE1` and `FILE2` from `oslab values lab1`. The example below uses `maple` and `river`. Replace them with yours.

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

2. The instructor explains Part B. Make sure you can log in to your own Ubuntu and that you know your student ID and the server address.

# Part B — Homework (due before the next class)

Part B is part of Lab 1 and is graded with it. It takes about 60 minutes. It needs `sudo`, so you do not do it on the server.

## Task 3 — Install, Remove and Purge Software

**Goal:** see the difference between **remove** and **purge**. APT is the program that installs software on Ubuntu.

| Command | What it does |
|---|---|
| `sudo apt-get update` | Refreshes the list of available software. Installs nothing |
| `sudo apt-get install NAME` | Downloads and installs a package |
| `sudo apt-get remove NAME` | Uninstalls the program, but **keeps** its settings in `/etc` |
| `sudo apt-get purge NAME` | Uninstalls the program **and deletes** its settings |

Do this on **your own Ubuntu** (WSL or a virtual machine). We use the package `mc` (Midnight Commander). It puts settings in the folder `/etc/mc`.

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

## Bring Your Work Together and Write the Report

You now have files on the server (Part A) and on your own Ubuntu (this task). Put them in one folder on your PC, write the report, and push.

1. On GitHub, create an **empty** repository named `OS-SE-YOUR_ID` (no README, no license). First lab only.
2. On your PC, clone it into a folder named `os-se-YOUR_ID` and make the lab folder. Replace `YOUR_USERNAME` with your GitHub name.

   ```bash
   git clone https://github.com/YOUR_USERNAME/OS-SE-YOUR_ID.git os-se-YOUR_ID
   cd os-se-YOUR_ID
   mkdir -p os-lab-YOUR_ID/lab1/images
   ```

3. Copy your files from the server into it. Replace `SERVER_USER` with your server account and `SERVER_ADDRESS` with the address your instructor gave you. The server asks for your password.

   ```bash
   scp 'SERVER_USER@SERVER_ADDRESS:oslab-work/lab1/task*.txt' os-lab-YOUR_ID/lab1/
   scp -r SERVER_USER@SERVER_ADDRESS:oslab-work/lab1/task2_files os-lab-YOUR_ID/lab1/
   ```

4. Add `task3_apt.txt` (from your Ubuntu) to the `lab1` folder, and your three screenshots to its `images` folder.
5. Copy the [report template](README.md) to `os-lab-YOUR_ID/lab1/README.md`. Fill it in, and show your screenshots in it. Press `Ctrl+Shift+V` in VS Code to preview it.
6. Push everything.

   ```bash
   git add .
   git commit -m "Lab 1 report"
   git push
   ```

7. Pull it to the server. Log in to the server, clone your repository into your home folder (first time), and look at the result. Only **pull** on the server later; never edit files there.

   ```bash
   cd ~
   git clone https://github.com/YOUR_USERNAME/OS-SE-YOUR_ID.git os-se-YOUR_ID
   ls -R os-se-YOUR_ID
   ```

   Your repository must look like this:

   ```text
   os-se-YOUR_ID/
   └── os-lab-YOUR_ID/
       └── lab1/
           ├── README.md
           ├── images/
           │   ├── task3.png
           │   ├── task5.png
           │   └── task6.png
           ├── task1_os_info.txt
           ├── task2_file_commands.txt
           ├── task2_files/
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
- More about APT and virtualization is in the [optional extensions](extensions.md).
