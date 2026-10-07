# Teaching roadmap after the lab pilot

Labs 1, 2 and 8 now use a new format. This page says what to check when they run in class, how to convert the other labs, and what to improve in lectures. Items are in priority order. Each one says what it needs from you.

## What the pilot changes

| Problem seen in lab sessions | What Labs 1, 2 and 8 do about it |
|---|---|
| Students copy and paste without understanding | The script arrives as a file. Students read and trace it first, then write the commands or the repair themselves. Each lab has at least one step marked "your decision" |
| Wide ability gap | One file with Core, Plus and Challenge. Core is written in short, plain English. A 10-minute pre-lab moves setup out of the session. Hints are specific to the lab and come in three levels |
| You cannot check everyone | `oslab-teach board` shows one row per student: pre-lab, started, prediction, milestones, hints, checkpoint. `oslab check` tests real behaviour. The export gives most of the marks |
| AI does the work | Every student has different values. The prediction is saved before the experiment. The checkpoint opens late with fresh values and asks for a change to the student's own work. Lab 8 makes students test three wrong AI answers |

The rubric moved one point from the artefact to the checkpoint: 2 / 2 / 2 / 3 / 1.

## 1. Run Labs 1 and 2, then write a short retrospective

The format has not been taught yet. The first two sessions are the test. After each one, add a section to this file with these six numbers and notes; the board and the export give you most of them.

| Question | Where to look |
|---|---|
| How many students did the pre-lab before class? | `prelab` column the evening before |
| At what minute had 80% saved a prediction? | Watch the board |
| How many reached all Core milestones by minute 75? | `checks` column at minute 75 |
| How many used hint level 3? | `hints` column |
| How many finished the checkpoint, and how long did marking take you? | `checkpoint`, `task`, and your own clock |
| What did students say was unclear about the `oslab` commands? | Ask in the Lab 1 debrief |

Decide after Lab 2:

- If fewer than half the class reach full Core by minute 75, cut one Core step, not the checkpoint.
- If the prediction takes more than 10 minutes, drop one question.
- If more than a third need hint 3, the step before it is too large; split it.

## 2. Convert the other labs

Convert each lab before the week it is taught, using what Labs 1 and 2 showed. The helper already supports this: add the lab's values, prediction, checkpoint, hints and check to the tables in [`server/oslab.py`](../server/oslab.py), add the `| Lab format | Pilot` row to the instruction, and `tools/validate_revision.py` applies the new rules to it.

| Lab | The student's own work today | Change | Personal values | Live checkpoint idea |
|---|---|---|---|---|
| 5 Threads | Pastes a complete C file and fills two TODO lines | Supply the file; the student decides where each join goes and what `main` may read before it | Worker step counts and identifiers | One worker is not joined: what can `main` print? |
| 9 Deadlock | Pastes a complete worker and changes one line | Supply the file; the student chooses the global lock order and argues why it removes the cycle | Three resources; which worker takes which first | A third worker joins: does your order still hold? |
| 10 Backup | Pastes a starting script, then writes the retention rule | Supply the script; keep the retention task | Number of archives to keep; name pattern | A new retention number on the student's own script |
| 7 Bash arguments | Writes `count_words.sh` from a skeleton | Keep the task; `oslab check` can run the script | The awkward file names (spaces, leading dash) | A new awkward name passed to the student's own script |
| 4 Pipelines | Builds `report.sh` for a CSV | Keep the task; `oslab check` can compare the output | The CSV rows and the status to total | A changed input: what does your script print, and why? |
| 6 Permissions | Chooses modes from a policy | Keep the task; `oslab check` can read the modes | The policy sentence (who may read, who may enter) | A new policy sentence: give the octal mode, then prove it |
| 3 Links | Follows guided `ln` steps, then repairs one link | Keep the repair; make the first steps a prediction | File names; which name is renamed | A new chain of links: which names still open? |
| 11 Bonus | Optional | Leave as it is | | |

The table is in order of benefit. Labs 5 and 9 gain the most: today the student pastes a complete program and edits one or two lines, as in the old Lab 8. Labs 3, 4, 6 and 7 already ask for real decisions; for them the gain is personal values, the saved prediction, the automatic check and the live checkpoint.

**Needs from you:** nothing until Lab 2 has run. Then say which labs to convert next.

## 3. One calendar for the whole course

Three documents describe the semester and they disagree.

| Document | Weeks | Lab plan |
|---|---|---|
| Course specification (`GIC_Course Spec_OS.pdf`) | 15, midterm in week 8, project work in weeks 12–14 | Navigation, files, redirection and pipes, ownership and permissions, process management, scripting (three sessions), cron (two sessions) |
| [`course-outline.md`](../course-outline.md) | 12 | Links only Labs 1–5, to the old slide guides |
| The repository's labs | 11 labs | Adds links and libraries (3), threads (5), race conditions (8), deadlock (9), disk images (11); has no separate lab on process management |

Also:

- The specification says the final exam has five scheduling problems. The repository has two lecture weeks on scheduling and nothing else: no lab, no class activity, no visualization.
- The specification's lab-report rubric rewards screenshots and formatting. The labs now ask for short text evidence. One of the two should change.
- The specification names a programming project (weeks 12–14, part of the 30% lab mark). The repository has no project material.

**Needs from you:** one decision per row below. Then `course-outline.md` can be rebuilt as a single table: week, lecture, class activity, lab, visualization, quiz.

1. Which lab runs in which week, and which weeks have no lab (midterm, project)?
2. Are Labs 8 and 9 (race, deadlock) the official synchronization labs, in place of the third scripting session?
3. Does the project exist this year? If yes, it needs a brief and a rubric.
4. Which rubric is official for lab reports?

## 4. A lecture pattern that uses what already exists

The lecture notes in [`lectures/notes/`](../lectures/notes/README.md) already contain a "Hook" and a list of "Questions you should be asking" for every subtopic. The visualizations already step through most of weeks 8–12. The course specification promises a flipped class. What is missing is a routine that connects them.

Proposed routine for each lecture:

1. **Before class (10 minutes):** students read the hook questions of the week and answer a three-question entry quiz. The Moodle midterm pool built by `tools/create-2026-expanded-qbank.ps1` is organized by lecture and can supply questions.
2. **In class, two or three times per lecture:** show one question, students predict (hands, cards or a poll), you run the visualization or a live command, and two students explain the result. This is the same predict-then-test cycle as the labs, so students meet it twice a week.
3. **End of class (3 minutes):** one sentence on paper: "what is still unclear?" Read ten of them before the lab and open the lab with the most common one.

Start with the weeks that already have a visualization:

| Week | Vote question | Tool |
|---|---|---|
| 7–8 | "Two producers, one buffer, no lock: what is in the buffer?" | [`producer-consumer.html`](../lectures/visualizations/producer-consumer.html), [`pc-sandbox.html`](../lectures/visualizations/pc-sandbox.html) |
| 9 | "This graph has a cycle. Is it deadlocked?" | [`rag-deadlock.html`](../lectures/visualizations/rag-deadlock.html), [`deadlock-detection.html`](../lectures/visualizations/deadlock-detection.html) |
| 10 | "Which hole does best-fit choose, and what is left?" | [`contiguous-allocation.html`](../lectures/visualizations/contiguous-allocation.html) |
| 11 | "More frames, more faults: possible?" | [`page-replacement.html`](../lectures/visualizations/page-replacement.html) |

**Needs from you:** try it in one lecture and note whether the vote changed what you explained.

## 5. Close the scheduling gap

Scheduling carries the most exam weight for the least practice. Two additions, in the style of what already works:

- A Gantt-chart visualization for FCFS, SJF, SRTF, round robin and priority, with the same Next / Prev / Build-your-own controls as the other pages, showing waiting and turnaround time per process.
- A class activity in the style of [Activity 7](../lectures/class-activity/class-activity7.md): hand-trace on personal data first, then check with the tool.

**Needs from you:** confirm the algorithm list and the time quantum values you use in exams.

## 6. Shorten Class Activities 1–3

Activities 1, 2 and 3 are about 1,200 lines each and are mostly code to type. Activities 7 and 8 are 340–500 lines, are personalized by student ID, and ask students to predict and hand-trace before they use a tool. Rewrite 1–3 on that model: one concept each, a prediction first, a short program, and a required note when the result differs from the prediction.

## 7. Link each lab to its lecture

Only Lab 9 links to a visualization today. Labs 1, 2 and 8 now have a "Lecture link" row. When you convert a lab, add the row and, where one exists, the visualization:

| Lab | Lecture | Visualization |
|---|---|---|
| 5 | Week 4 threads | none yet |
| 8 | Week 7 critical sections | `pc-sandbox.html` |
| 9 | Week 9 deadlocks | `rag-deadlock.html` |

## 8. Old slide guides

`labs/lab1` to `labs/lab6` each have a `guides/slides.html`, and Labs 1, 2 and 7 have a PDF, that show the old three-hour route with fixed file names. `course-outline.md` still links to them. Either remove the links or add a first slide that says "background only; follow the Markdown instruction".

## Limits of the pilot

- Tested locally in WSL only. The inbox permissions, 30 students at once, and the real home filesystem's `flock` behaviour are untested on the teaching server. The [runbook](../server/RUNBOOK.md) lists the checks.
- The board is feedback and marking support. A student can delete and resend their own prediction; the board flags this but cannot prevent it.
- Personal values are computed by public code. A student who reads `oslab.py` can compute their own answers. This costs more effort than doing the lab.
- Whether the timetables fit a real class is unknown until Labs 1 and 2 run.
