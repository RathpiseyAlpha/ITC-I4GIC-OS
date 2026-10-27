```
 ██████╗ ██████╗ ███████╗██████╗  █████╗ ████████╗██╗███╗   ██╗ ██████╗
██╔═══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██║████╗  ██║██╔════╝
██║   ██║██████╔╝█████╗  ██████╔╝███████║   ██║   ██║██╔██╗ ██║██║  ███╗
██║   ██║██╔═══╝ ██╔══╝  ██╔══██╗██╔══██║   ██║   ██║██║╚██╗██║██║   ██║
╚██████╔╝██║     ███████╗██║  ██║██║  ██║   ██║   ██║██║ ╚████║╚██████╔╝
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝

███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗███████╗
██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████║██╔════╝
███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║███████╗
╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║╚════██║
███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║███████║
╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝╚══════╝
```

<div align="center">

**Institute of Technology of Cambodia** · Department of Information and Communication Engineering

📖 Course Materials for **Operating Systems (GICI4OS)**

[![GitHub](https://img.shields.io/badge/GitHub-ITC--I4GIC--OS-181717?logo=github&style=for-the-badge)](https://github.com/RathpiseyAlpha/ITC-I4GIC-OS)
[![License](https://img.shields.io/badge/License-Educational-blue?style=for-the-badge)](#)
[![Web View](https://img.shields.io/badge/🖥️_Web_View-Terminal_Theme-00ff41?style=for-the-badge&logo=html5&logoColor=white)](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/)

---

> **🌐 [View the interactive terminal-themed web page →](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/)**

</div>

## ⚡ Quick Start

```bash
$ git clone https://github.com/RathpiseyAlpha/ITC-I4GIC-OS.git
$ cd ITC-I4GIC-OS
$ tree -L 2
```

> You do not need to install or run anything to use the course website. Open it in a browser and log in with your server account to see your lab progress and marks.

---

## 📂 Repository Structure

```
ITC-I4GIC-OS/
├── README.md                  # ← You are here
├── course-outline.md          # Course outline & weekly learning objectives
│
├── lectures/
│   ├── files/                 # Lecture slides
│   │   ├── Converted Slides/  #   This term's slides, one PDF per week (Weeks 1–6, 9–13)
│   │   │   └── Labs/          #     Lab guide PDFs (Lab 1, Lab 2)
│   │   └── ch1.pdf … ch10.pdf #   Earlier chapter slides
│   │
│   ├── notes/                 # 📝 Note-taking templates (one per week)
│   │   ├── README.md          #   Guide & template structure
│   │   └── week01-… week12-…  #   One template per topic
│   │
│   ├── class-activity/        # 🧪 Hands-on programming activities
│   │   ├── README.md          #   Activity index & submission structure
│   │   └── class-activity1.md … class-activity8.md
│   │
│   └── visualizations/        # 🎬 Interactive step-through animations (open in a browser)
│       ├── index.html         #   Index of all 24 visualizations
│       └── *.html
│
└── labs/
    ├── SETUP.md               # Student environment (server account, oslab helper, local fallback)
    ├── INDEX.md               # Complete lab index
    ├── REPORT-TEMPLATE.md     # Shared lab report template
    ├── lab1/                  # Lab 1 — Introduction to Operating Systems
    │   ├── lab1-instruction.md
    │   ├── README.md          #   Report template
    │   ├── extensions.md      #   Optional extensions
    │   └── guides/            #   Slide guide (HTML + PDF)
    ├── lab2/ … lab10/         # Same layout
    └── lab11/                 # Bonus lab
```

---

## 📖 Course Overview

> *This course provides a comprehensive understanding of how operating systems function, focusing on their architecture, resource management, concurrency, scheduling, and memory handling.*

**Instructor:** Heng Rathpisey  
**Course:** GICI4OS — Operating Systems, 3 credits  
**Department:** Information and Communication Engineering  
**Institute:** Institute of Technology of Cambodia  
**Textbook:** Silberschatz, Galvin & Gagne, *Operating System Concepts*, 10th edition

### 🎯 Learning Objectives

- Understand the architecture and core functions of operating systems
- Analyze process management, memory allocation, and file systems
- Compare and apply scheduling and resource management algorithms
- Solve synchronization and concurrency problems
- Understand real-world implementations in Linux, Windows, and macOS

---

## 📅 Weekly Schedule

| Wk | Topic | Slides | Visualizations |
|:--:|-------|:------:|----------------|
| 1 | Introduction to Operating Systems | [Week 1](<lectures/files/Converted Slides/Operating Systems — Week 1.pdf>) | [Interrupts & dual mode](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/interrupts-dual-mode.html) |
| 2 | Operating System Structure | [Week 2](<lectures/files/Converted Slides/Operating Systems — Week 2.pdf>) | [System calls & kernel structures](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/system-call-path.html) |
| 3 | Processes | [Week 3](<lectures/files/Converted Slides/Operating Systems — Week 3.pdf>) | [Process states](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/process-states.html) · [fork() tree](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/fork-tree.html) |
| 4 | Threads & Multicore Programming | [Week 4](<lectures/files/Converted Slides/Operating Systems — Week 4.pdf>) | [Threading models](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/threading-models.html) · [Amdahl's law](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/amdahls-law.html) |
| 5 | CPU Scheduling | [Week 5](<lectures/files/Converted Slides/Operating Systems — Week 5.pdf>) | [Scheduling simulator](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/cpu-scheduling.html) · [MLFQ](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/mlfq.html) |
| 6 | Critical Section & Synchronization | [Week 6](<lectures/files/Converted Slides/Operating Systems — Week 6.pdf>) | [Critical section](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/critical-section.html) |
| 7–8 | Review & Midterm | — | — |
| 9 | Synchronization I: Semaphores & Monitors | [Week 9](<lectures/files/Converted Slides/Operating Systems — Week 9.pdf>) | [Producer / consumer](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/producer-consumer.html) · [Semaphore sandbox](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/pc-sandbox.html) |
| 10 | Synchronization II: Classical Problems | [Week 10](<lectures/files/Converted Slides/Operating Systems — Week 10.pdf>) | [Dining philosophers](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/dining-philosophers.html) · [Readers–writers](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/readers-writers.html) |
| 11 | Deadlock | [Week 11](<lectures/files/Converted Slides/Operating Systems — Week 11.pdf>) | [RAG](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/rag-deadlock.html) · [Banker's](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/bankers-algorithm.html) · [Detection](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/deadlock-detection.html) |
| 12 | Memory Management | [Week 12](<lectures/files/Converted Slides/Operating Systems — Week 12.pdf>) | [Paging](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/paging-translation.html) · [TLB](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/tlb.html) · [EAT](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/eat-calculator.html) · [Contiguous allocation](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/contiguous-allocation.html) |
| 13 | Virtual Memory | [Week 13](<lectures/files/Converted Slides/Operating Systems — Week 13.pdf>) | [Demand paging](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/demand-paging.html) · [Page replacement](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/page-replacement.html) |
| 14–16 | Review & Examinations | — | — |

> 📋 See [course-outline.md](course-outline.md) for the learning objectives of each topic.

---

## 🔬 Labs

Each lab is a 120-minute individual session on the course server. Start with the [environment setup](labs/SETUP.md); the [lab index](labs/INDEX.md) lists every lab with its report template and optional extensions.

| Lab | Title | Status | Link |
|:---:|-------|:------:|:----:|
| 1 | Introduction to Operating Systems | ✅ Available | [Instructions](labs/lab1/lab1-instruction.md) · [Guide](<lectures/files/Converted Slides/Labs/Operating Systems — Lab 1.pdf>) |
| 2 | Linux Navigation & File Management | ✅ Available | [Instructions](labs/lab2/lab2-instruction.md) · [Guide](labs/lab2/guides/lab2-guides.pdf) |
| 3 | Wildcards, Links, GRUB & Shared Libraries | ✅ Available | [Instructions](labs/lab3/lab3-instruction.md) |
| 4 | I/O Redirection, Pipelines & Process Management | ✅ Available | [Instructions](labs/lab4/lab4-instruction.md) |
| 5 | Threads, Kernel Workers & Process Signals | ✅ Available | [Instructions](labs/lab5/lab5-instruction.md) |
| 6 | Linux Security, Users, Groups & File Permissions | ✅ Available | [Instructions](labs/lab6/lab6-instruction.md) |
| 7 | Bash Scripting, Permissions & Server Automation | ✅ Available | [Instructions](labs/lab7/lab7-instruction.md) |
| 8 | Secure Bash Scripting, Race Conditions & File Locking | ✅ Available | [Instructions](labs/lab8/lab8-instruction.md) |
| 9 | Vault Deadlock, Resource Ordering & Recovery | ✅ Available | [Instructions](labs/lab9/lab9-instruction.md) |
| 10 | Backups, Archiving, Scheduling & cron Automation | ✅ Available | [Instructions](labs/lab10/lab10-instruction.md) |
| 11 | Linux Disk Management Utilities (bonus) | ✅ Available | [Instructions](labs/lab11/lab11-instruction.md) |

### Lab 1 Highlights

Lab 1 covers foundational Linux skills through **6 hands-on tasks**. Tasks 1, 2 and 4–6 are done in class on the server; Task 3 needs `sudo`, so it is homework on your own Ubuntu:

```
Task 1 ─ Which System Is This?           (uname, lsb_release)
Task 2 ─ Files and Folders               (pwd, ls, mkdir, cp, mv, rm)
Task 3 ─ Install, Remove, Purge Software  (apt — homework)
Task 4 ─ Program or Process?             (sleep, ps, background jobs)
Task 5 ─ Multitasking                    (several sleep jobs, ps)
Task 6 ─ Is This a Virtual Machine?       (systemd-detect-virt, lscpu)
```

### The `oslab` helper

On the course server, `oslab` gives you your own values for a lab and checks your progress:

```
oslab values labN       # your own numbers, names or folders
oslab predict labN      # save your prediction (the first answer is kept)
oslab hint labN 1       # a hint when you are stuck (levels 1 to 3)
oslab check labN        # which milestones pass — run it as often as you like
oslab checkpoint labN   # the live checkpoint, once the instructor opens it
```

> ⚠️ Lab 3's optional GRUB extension needs a **virtual machine with a snapshot** — WSL does not have GRUB, and the server is shared.

---

## 📚 Lecture Slides

| Week | Topic | Download |
|:----:|-------|:--------:|
| 1 | Introduction to Operating Systems | [📄 Week 1](<lectures/files/Converted Slides/Operating Systems — Week 1.pdf>) |
| 2 | Operating System Structure | [📄 Week 2](<lectures/files/Converted Slides/Operating Systems — Week 2.pdf>) |
| 3 | Processes | [📄 Week 3](<lectures/files/Converted Slides/Operating Systems — Week 3.pdf>) |
| 4 | Threads & Multicore Programming | [📄 Week 4](<lectures/files/Converted Slides/Operating Systems — Week 4.pdf>) |
| 5 | CPU Scheduling | [📄 Week 5](<lectures/files/Converted Slides/Operating Systems — Week 5.pdf>) |
| 6 | Critical Section & Synchronization | [📄 Week 6](<lectures/files/Converted Slides/Operating Systems — Week 6.pdf>) |
| 9 | Synchronization I: Semaphores & Monitors | [📄 Week 9](<lectures/files/Converted Slides/Operating Systems — Week 9.pdf>) |
| 10 | Synchronization II: Classical Problems | [📄 Week 10](<lectures/files/Converted Slides/Operating Systems — Week 10.pdf>) |
| 11 | Deadlock | [📄 Week 11](<lectures/files/Converted Slides/Operating Systems — Week 11.pdf>) |
| 12 | Memory Management | [📄 Week 12](<lectures/files/Converted Slides/Operating Systems — Week 12.pdf>) |
| 13 | Virtual Memory | [📄 Week 13](<lectures/files/Converted Slides/Operating Systems — Week 13.pdf>) |

> The earlier chapter slides (`ch1.pdf` … `ch10.pdf`) are still in [`lectures/files/`](lectures/files/).

---

## 📝 Lecture Notes Templates

Standardized note-taking templates are provided for every topic of the course. Each template includes sections for key concepts, detailed notes, diagrams, comparisons, examples, review questions, and personal reflection.

→ Browse them in [`lectures/notes/`](lectures/notes/)

| # | Template |
|:-:|----------|
| 1 | [Introduction to OS](lectures/notes/week01-introduction-to-os.md) |
| 2 | [OS Structures & Interfaces](lectures/notes/week02-os-structures-interfaces.md) |
| 3 | [Processes](lectures/notes/week03-processes.md) |
| 4 | [Threads & Multicore](lectures/notes/week04-threads-multicore.md) |
| 5 | [CPU Scheduling I](lectures/notes/week05-cpu-scheduling-1.md) |
| 6 | [CPU Scheduling II](lectures/notes/week06-cpu-scheduling-2.md) |
| 7 | [Critical Sections](lectures/notes/week07-critical-sections.md) |
| 8 | [Semaphores & Sync Problems](lectures/notes/week08-semaphores-sync.md) |
| 9 | [Deadlocks](lectures/notes/week09-deadlocks.md) |
| 10 | [Memory Management I](lectures/notes/week10-memory-management.md) |
| 11 | [Virtual Memory](lectures/notes/week11-virtual-memory.md) |
| 12 | [File Systems](lectures/notes/week12-file-systems.md) |

---

## 🎬 Interactive Visualizations

Step-through animations of the main algorithms: scheduling, synchronization, deadlock, memory and file systems. Each one runs in the browser with **Next / Prev / Play** or the keys **→ ← Space**.

→ **[Open the visualization index](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/)** (GitHub shows the HTML source instead of running it, so use the web page or open the files locally.)

The file-system topics have two more: [file allocation methods](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/file-allocation.html) and [UNIX file permissions](https://rathpiseyalpha.github.io/ITC-I4GIC-OS/lectures/visualizations/file-permissions.html) (useful for Lab 6).

---

## 🧪 Class Activities

Hands-on programming activities that accompany the lecture topics.

| # | Activity | Topic |
|---|----------|-------|
| 1 | [System Calls in Practice](lectures/class-activity/class-activity1.md) | POSIX System Calls (Linux) + Optional Windows API |
| 2 | [Processes & Inter-Process Communication](lectures/class-activity/class-activity2.md) | Processes & IPC (Linux + Windows) |
| 3 | [Socket Communication & Multithreading](lectures/class-activity/class-activity3.md) | Sockets, pthreads, Java threading, thread observation |
| 4 | [Shared File API](lectures/class-activity/class-activity4.md) | Client/server API, shared file, C++ mutex, Java synchronization |
| 5 | [Semaphores: Particle Pairs & HELLO Ordering](lectures/class-activity/class-activity5.md) | Producer/consumer semaphores, ordering constraints, deadlock checks |
| 6 | [Deadlock Simulation: Bank Account Transfers](lectures/class-activity/class-activity6.md) | Deadlock, circular wait, lock ordering, prevention |
| 7 | [Reasoning about Deadlock](lectures/class-activity/class-activity7.md) | Resource allocation graphs & Banker's algorithm (no code, uses the visualizations) |
| 8 | [Paging & Page Replacement](lectures/class-activity/class-activity8.md) | Hand-tracing and simulating paging and page replacement |

→ Browse them in [`lectures/class-activity/`](lectures/class-activity/)

---

## 🛠️ Tools & Environment

| Tool | Purpose |
|------|---------|
| **Course server** | Your own Ubuntu account; the main environment for labs |
| **`oslab`** | Lab helper on the server: your values, hints, checks and checkpoints |
| **Ubuntu (WSL or VM)** | Your own Linux for homework that needs `sudo` |
| **VS Code** | Code editor & Markdown documentation |
| **Git & GitHub** | Version control and submission |
| **GCC / Python3** | Programming & scripting |

---

## 🚀 Getting Started for Students

```bash
# 1. Clone the course repo for reference
$ git clone https://github.com/RathpiseyAlpha/ITC-I4GIC-OS.git

# 2. On GitHub, create an EMPTY repository named OS-GIC-<YourStudentID>

# 3. On the server, create your course folder
$ mkdir -p ~/os-gic-<YourStudentID>/os-lab-<YourStudentID>/lab1
$ cd ~/os-gic-<YourStudentID>

# 4. Initialize git and connect to your GitHub repo
$ git init
$ git branch -M main
$ git remote add origin https://github.com/<YourUsername>/OS-GIC-<YourStudentID>.git

# 5. Start working on labs! (Lab 1 walks you through the first push)

# 6. When class activities are assigned, create the activity folder you need:
$ mkdir -p os-class-activities-<YourStudentID>/activity1
```

### 📂 Your Submission Repo Structure

```
os-gic-<YourStudentID>/
├── os-lab-<YourStudentID>/                # Lab submissions
│   ├── lab1/
│   │   ├── README.md                      # Your lab report
│   │   ├── images/                        # Screenshots
│   │   └── task1_os_info.txt …            # Files listed in the lab
│   ├── lab2/
│   └── ...
│
└── os-class-activities-<YourStudentID>/   # Class activity submissions
    ├── activity1/
    │   ├── README.md                      # Screenshots + answers + reflection
    │   ├── screenshots/
    │   ├── task1/
    │   ├── task2/
    │   └── task3/
    ├── activity2/
    │   ├── README.md
    │   └── ...
    └── ...
```

> Each lab lists the exact files it expects. Each activity folder must contain a **README.md** with your name, student ID, and screenshot evidence of your programs running; the full layout is in the [activity index](lectures/class-activity/README.md#submission-structure).

---

<div align="center">

**Operating Systems — ITC 2026**

Made with 🖥️ at the Institute of Technology of Cambodia

</div>
