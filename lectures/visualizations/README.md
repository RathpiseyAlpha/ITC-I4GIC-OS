# 🎬 Interactive Visualizations

Step-through, animated explanations of OS concepts. Each file is **self-contained HTML** (no dependencies, works offline). Controls: **Next / Prev / Play / Reset**, or keyboard **→ ← Space**.

| Visualization | Topic | Activity |
|---------------|-------|----------|
| [producer-consumer.html](producer-consumer.html) | Semaphores & producer/consumer (bounded buffer): why FIFO buffering, precedence with a semaphore = 0, counting semaphores (`chars`/`space`), and `lock = 1` as a mutex for two producers — each shown broken ✗ then fixed ✓ | Week 8 (Ch 8) |
| [rag-deadlock.html](rag-deadlock.html) | Resource Allocation Graph & cycle-based deadlock detection (single-instance) | Activity 7 · Task 1 |
| [bankers-algorithm.html](bankers-algorithm.html) | Banker's Algorithm: safety check + resource requests | Activity 7 · Task 2 |
| [deadlock-detection.html](deadlock-detection.html) | Multi-instance deadlock detection (reduction algorithm) — shows a cycle that is *not* a deadlock | Activity 7 · Task 1 extension |
| [paging-translation.html](paging-translation.html) | Paging address translation: logical → page + offset → page-table lookup → physical address, with valid/invalid bits | Activity 8 · Task 1 (Ch 9) |
| [tlb.html](tlb.html) | TLB cache: reference-stream step-through with hits, misses, LRU eviction, and running hit ratio | Chapter 9 |
| [page-replacement.html](page-replacement.html) | Demand paging & page replacement: FIFO / LRU / OPT step-through, fault counts, Belady's anomaly | Activity 8 · Task 2 (Ch 10) |
| [demand-paging.html](demand-paging.html) | Demand paging & virtual memory: page faults, swap in / swap out, victim eviction, valid/invalid bits and page-table updates | Chapter 9 |
| [contiguous-allocation.html](contiguous-allocation.html) | Contiguous allocation with First / Best / Worst fit, external fragmentation, and compaction | Chapter 9 |
| [eat-calculator.html](eat-calculator.html) | Effective Access Time vs TLB hit ratio — interactive sliders + live graph | Chapter 9 |

Each one has two modes:

- **Examples / Safety check** — the guided, pre-built scenarios from Activity 7.
- **Build your own / Custom data** — a sandbox where students define their own scenario:
  - *RAG*: add processes, resources, and request/assignment edges, then run cycle detection on their own graph.
  - *Banker's*: choose the number of resource types and processes, edit the Allocation / Max / Total matrices (Available is computed live), and test their own resource request for grant/deny.

> ⚠️ **GitHub does not run `.html` files** — clicking the links above on github.com shows the *source code*, not the animation. Use one of the live options below.

---

## Open the visualizations

Open [the visualization index](index.html) on the course site or download/clone the repository and open any HTML file locally. GitHub shows HTML source rather than running the animation. If this repository is published with GitHub Pages, the same relative links above work on that site. Configure the destination repository and Pages URL before advertising a hosted address.