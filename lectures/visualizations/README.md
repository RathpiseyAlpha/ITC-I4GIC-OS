# 🎬 Interactive Visualizations

Step-through, animated explanations of OS concepts. Each file is **self-contained HTML** (no dependencies, works offline). Controls: **Next / Prev / Play / Reset**, or keyboard **→ ← Space**.

| Visualization | Topic | Activity |
|---------------|-------|----------|
| [interrupts-dual-mode.html](interrupts-dual-mode.html) | Interrupts and dual-mode operation: a device interrupt, a system call, the timer and an illegal instruction each switch the CPU from user mode to kernel mode and back | Week 1 (Ch 1) |
| [system-call-path.html](system-call-path.html) | One request from a C program down to the hardware, through a monolithic, a layered and a microkernel operating system | Week 2 (Ch 2) |
| [process-states.html](process-states.html) | Process states and the PCB: fire events and watch processes move between new, ready, running, waiting and terminated, with a context switch at each change | Week 3 (Ch 3) |
| [fork-tree.html](fork-tree.html) | `fork()` process trees: step through small C programs and count the processes and the lines of output | Week 3 (Ch 3) |
| [threading-models.html](threading-models.html) | Many-to-one, one-to-one and many-to-many threading models, and what stops when one thread blocks | Week 4 (Ch 4) |
| [amdahls-law.html](amdahls-law.html) | Amdahl's law: how the serial fraction limits the speedup from more cores | Week 4 (Ch 4) |
| [cpu-scheduling.html](cpu-scheduling.html) | FCFS, SJF, SRTF, Round Robin and Priority on the same processes, one time unit at a time, with waiting-time comparison | Weeks 5–6 (Ch 5–6) |
| [mlfq.html](mlfq.html) | Multilevel feedback queue: demotion after a full quantum, staying up after early I/O, and the priority boost | Week 6 (Ch 6) |
| [critical-section.html](critical-section.html) | Race conditions: you choose which thread runs each instruction and test six attempts at mutual exclusion, from no lock to Peterson and test-and-set | Week 7 (Ch 7) |
| [producer-consumer.html](producer-consumer.html) | Semaphores & producer/consumer (bounded buffer): why FIFO buffering, precedence with a semaphore = 0, counting semaphores (`chars`/`space`), and `lock = 1` as a mutex for two producers — each shown broken ✗ then fixed ✓ | Week 8 (Ch 8) |
| [pc-sandbox.html](pc-sandbox.html) | Semaphore sandbox: place `wait()` and `signal()` yourself, interleave producer and consumer, and see data loss, races or deadlock reported live | Week 8 (Ch 8) |
| [dining-philosophers.html](dining-philosophers.html) | Dining philosophers: find the schedule that deadlocks the table, then try three fixes | Week 8 (Ch 8) |
| [readers-writers.html](readers-writers.html) | Readers–writers: who gets in, who waits and who starves under three policies | Week 8 (Ch 8) |
| [rag-deadlock.html](rag-deadlock.html) | Resource Allocation Graph & cycle-based deadlock detection (single-instance) | Activity 7 · Task 1 |
| [bankers-algorithm.html](bankers-algorithm.html) | Banker's Algorithm: safety check + resource requests | Activity 7 · Task 2 |
| [deadlock-detection.html](deadlock-detection.html) | Multi-instance deadlock detection (reduction algorithm) — shows a cycle that is *not* a deadlock | Activity 7 · Task 1 extension |
| [paging-translation.html](paging-translation.html) | Paging address translation: logical → page + offset → page-table lookup → physical address, with valid/invalid bits | Activity 8 · Task 1 (Ch 9) |
| [tlb.html](tlb.html) | TLB cache: reference-stream step-through with hits, misses, LRU eviction, and running hit ratio | Chapter 9 |
| [page-replacement.html](page-replacement.html) | Demand paging & page replacement: FIFO / LRU / OPT step-through, fault counts, Belady's anomaly | Activity 8 · Task 2 (Ch 10) |
| [demand-paging.html](demand-paging.html) | Demand paging & virtual memory: page faults, swap in / swap out, victim eviction, valid/invalid bits and page-table updates | Chapter 9 |
| [contiguous-allocation.html](contiguous-allocation.html) | Contiguous allocation with First / Best / Worst fit, external fragmentation, and compaction | Chapter 9 |
| [eat-calculator.html](eat-calculator.html) | Effective Access Time vs TLB hit ratio — interactive sliders + live graph | Chapter 9 |
| [file-allocation.html](file-allocation.html) | Contiguous, linked and indexed file allocation on a 40-block disk: fragmentation and access cost | Week 12 (File systems) |
| [file-permissions.html](file-permissions.html) | UNIX permissions: toggle the rwx bits, type `chmod` commands, and test who may do what to a file or directory | Week 12 · Lab 6 |

Each one has two modes:

- **Examples / Safety check** — the guided, pre-built scenarios from Activity 7.
- **Build your own / Custom data** — a sandbox where students define their own scenario:
  - *RAG*: add processes, resources, and request/assignment edges, then run cycle detection on their own graph.
  - *Banker's*: choose the number of resource types and processes, edit the Allocation / Max / Total matrices (Available is computed live), and test their own resource request for grant/deny.

> ⚠️ **GitHub does not run `.html` files** — clicking the links above on github.com shows the *source code*, not the animation. Use one of the live options below.

---

## Open the visualizations

Open [the visualization index](index.html) on the course site or download/clone the repository and open any HTML file locally. GitHub shows HTML source rather than running the animation. If this repository is published with GitHub Pages, the same relative links above work on that site. Configure the destination repository and Pages URL before advertising a hosted address.