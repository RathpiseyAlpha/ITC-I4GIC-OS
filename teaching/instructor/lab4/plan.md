# Instructor plan — Lab 4: Redirection and Pipelines

**Public repository notice:** values, checkers and this plan are public. Use fresh private variants when secrecy is needed; personal values are not secrets. The [student instruction](../../../labs/lab4/lab4-instruction.md) defines the route.

## Objectives and Prerequisites

Teach command use, stdout/stderr, pipes, exact field matching, extraction and record counts. Students have not learned Bash programming: do not require scripts, positional parameters, conditions, loops, command substitution, arithmetic or awk programs. Lab 7 introduces scripting. The data's numeric second field helps distinguish quantities from records; students do not calculate a total.

## Before Class

- Update the deployed helper and website together; Lab 4 now grades command evidence, not `report.sh`. Follow the [runbook](../../../server/RUNBOOK.md). Use a fresh practice account to check the complete route.
- Do not mix old script-era predictions/checkpoint releases/grade records with this revision. Preserve/export old records first and use a fresh class state or revision-specific deployment. Never erase student work to migrate the lesson.
- Check `oslab doctor`, `oslab values lab4`, `oslab start lab4`, and initial `oslab check lab4` (0/4).
- Ensure the class inbox is configured and the Lab 4 checkpoint is not released. Prepare a roster of Linux account names. Ask students to complete `oslab prelab lab4`.
- Use the revised [HTML guide](../../../labs/lab4/guides/slides.html); the corresponding PDF is regenerated from it.

## Timetable

Keep `sudo oslab-teach board lab4 --roster FILE --watch 20` on your private screen; it contains names.

| Minutes | Students and instructor |
|---|---|
| 0–10 | Setup; demonstrate replacing STATUS/OTHER with personal words |
| 10–25 | Guided streams, append and tee; introduce each operator before use |
| 25–35 | Prediction without AI; discuss counts versus quantities |
| 35–55 | Core 1; ask students to inspect each stage separately |
| 55–70 | Core 2; inspect 0/4 counts and separate stdout/stderr/status |
| 70–85 | Pipeline-failure demonstration; optional Plus/Challenge |
| 85–100 | Release checkpoint with `sudo oslab-teach release lab4`; no AI |
| 100–110 | Debrief; students correct answers before group discussion |
| 110–120 | Submission and `sudo oslab-teach export lab4 --roster FILE > lab4.csv` |

## Model Commands and Expected Results

For the example status `ready` only; students substitute their actual word:

```bash
grep '^ready,' data/events.csv | tee evidence/selected.txt
grep '^ready,' data/events.csv | cut -d, -f2 | tee evidence/fields.txt
grep '^ready,' data/events.csv | wc -l > evidence/normal.txt
grep '^ready,' data/no-match.csv | wc -l > evidence/edge.txt
grep '^ready,' data/changed.csv | wc -l >> evidence/edge.txt
cat data/missing.csv > evidence/stdout.txt 2> evidence/stderr.txt
echo $? > evidence/status.txt
```

Three original exact matches; edge counts 0 then 4. Field values remain individual quantities, not a sum. A missing file gives empty stdout, a diagnostic naming `missing.csv` and nonzero status. Diagnostic language may differ; do not require English wording. Do not require a particular nonzero cat status across implementations.

Challenge model: `cat data/events.csv data/not-present.csv 2>&1 | tee evidence/challenge.txt`. The first command's stderr must be redirected before the pipe.

## Checkpoint and Marking

Key: `sudo oslab-teach key lab4 --roster FILE`. After release, students receive fresh records and a filename. Questions ask exact-match count (2), first selected quantity, stderr stream (2), and an explanation. They create the file with the supplied printf command, write their own selection pipeline, and save selected lines plus count.

The helper checks four Core milestones: selected rows plus extracted fields; normal count; changed/no-match fixture and counts; missing-file streams/status. The optional fifth milestone checks fresh checkpoint input, selected rows and count. It never executes submitted shell text. Evidence can be fabricated; assess explanations and live work rather than treating artifact checks as secure proof of command use.

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Four Core milestones | 2 |
| Actual command record and explanations of tests | 2 |
| Prediction in time and corrected debrief | 2 |
| Checkpoint answers, fresh file task and explanation | 3 |
| Complete submission on time | 1 |

The dashboard continues suggesting the same rubric rows. Checkpoint: 1 point for marked answers, 1 for the fresh file task, 1 for the explanation. Read `commands.txt` and the report for row 2; file checks cannot prove command authorship. Explain the changed task to any student with an old script-era workspace, and preserve their old evidence.

## Debrief and Fallback

Ask which stage removes look-alikes, whether the numbers printed by cut are the number of records, and why a pipeline can report success after input failure. File existence and readable input are different from zero matches. No output from diff means identical contents.

Without a class inbox, use practice mode; records remain local. Old files are not deleted. Use the [report template](../../../labs/lab4/README.md) and required submission tree. Advanced process exercises and the old script model are later-reference material only, not prerequisite work.
