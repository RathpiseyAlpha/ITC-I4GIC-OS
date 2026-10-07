"""Check the authored lab routes, linked teaching resources and rubric/timing gates."""
import re
from pathlib import Path
from build_lab_revision import index

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [(0, 10), (10, 25), (25, 35), (35, 70), (70, 85), (85, 100), (100, 110), (110, 120)]
# A lab opts in to the pilot format with this row in its metadata table.
PILOT = "| Lab format | Pilot"


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def links(file):
    text = file.read_text(encoding="utf-8")
    # Ignore fenced command examples, whose bracket syntax is not a Markdown link.
    text = re.sub(r"^\s*```.*?^\s*```\s*$", "", text, flags=re.M | re.S)
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        if file.name == "README.md" and target.startswith("images/"):
            continue  # report template: screenshots are added by the student
        path = (file.parent / target.split("#")[0]).resolve()
        require(path.exists(), f"Missing link: {file.relative_to(ROOT)} -> {target}")


def timetable(file):
    return [(int(a), int(b)) for a, b in re.findall(r"^\| (\d+)–(\d+) \|", file.read_text(encoding="utf-8"), re.M)]


def rubric(file):
    return [int(x) for x in re.findall(r"^\| [^\n|]+ \| ([1-3]) \|$", file.read_text(encoding="utf-8"), re.M)]


pilots = []
for number in range(1, 12):
    lab = ROOT / "labs" / f"lab{number}"
    student = lab / f"lab{number}-instruction.md"
    instructor = ROOT / "teaching" / "instructor" / f"lab{number}" / "plan.md"
    files = (student, lab / "README.md", lab / "extensions.md", instructor)
    for file in files:
        require(file.is_file(), f"Missing: {file}")
        links(file)
        text = file.read_text(encoding="utf-8")
        require("shared Ubuntu account" not in text, f"Ambiguous account wording: {file}")
    text = student.read_text(encoding="utf-8")
    objectives = text.split("## Lab Objectives", 1)[1].split("\n## ", 1)[0].split("**Extension objectives:**", 1)[0]
    wanted = range(3, 7) if PILOT in text else (3,)
    require(len(re.findall(r"^\d+\. ", objectives, re.M)) in wanted, f"Unexpected number of core objectives: {student}")
    require(f'cd "$OSLAB_WORKSPACE/lab{number}"' in text or f"cd ~/oslab-work/lab{number}" in text, f"Missing explicit workspace cd: {student}")
    require(len(re.findall(r"^\s*```text$", text, re.M)) >= 2, f"Missing starting/submission trees: {student}")
    require("120 minutes" in text, f"Missing duration: {student}")
    require("3 Hours" not in text and "2026-06" not in text, f"Stale duration/date: {student}")
    plan = instructor.read_text(encoding="utf-8")
    require("Public repository notice" in plan and "private" in plan and "Key:" in plan, f"Missing public-key/private-variant notice: {instructor}")
    if PILOT in text:
        pilots.append(number)
        for label in ("## Before the Lab", "## Timetable", "## Prediction", "## Live Checkpoint", "## Debrief",
                      "## Grading Criteria"):
            require(label in text, f"Missing {label}: {student}")
        for word in ("Plus", "Challenge"):
            require(re.search(rf"^#+ .*{word}", text, re.M), f"Missing a {word} heading: {student}")
        require("## Core 1" in text or "## Task 1" in text, f"Missing first task section: {student}")
        require("## Submit" in text or "and Submit" in text or "# Part B" in text, f"Missing submit or homework section: {student}")
        for command in ("prelab", "values", "predict", "check", "checkpoint"):
            require(f"oslab {command} lab{number}" in text, f"Missing oslab {command}: {student}")
        spans = timetable(student)
        contiguous = all(a < b for a, b in spans) and all(spans[i][1] == spans[i + 1][0] for i in range(len(spans) - 1))
        require(spans and spans[0][0] == 0 and spans[-1][1] == 120 and contiguous, f"Bad timetable: {student}")
        require(timetable(instructor) == spans, f"Instructor timetable differs from the student one: {instructor}")
        require("oslab-teach" in plan, f"Missing board instructions: {instructor}")
        for file in (student, instructor):
            require(rubric(file) == [2, 2, 2, 3, 1], f"Bad rubric: {file}: {rubric(file)}")
        continue
    for label in ("## Lab Setup", "## Prediction", "Guided", "Example", "## Individual Changed-case Checkpoint", "## Cleanup and Final Submission", "## Grading Criteria"):
        require(label in text, f"Missing {label}: {student}")
    require(re.search(r"^## .*Tests.*\(70–85\)", text, re.M), f"Missing test/feedback section: {student}")
    for file in (student, instructor):
        spans = timetable(file)
        require(spans == EXPECTED and sum(b-a for a,b in spans) == 120, f"Bad timetable: {file}")
        require(rubric(file) == [3, 2, 2, 2, 1], f"Bad rubric: {file}: {rubric(file)}")

for file in (ROOT / "labs/SETUP.md", ROOT / "labs/INDEX.md", ROOT / "README.md", ROOT / "labs/REPORT-TEMPLATE.md",
             ROOT / "teaching/ROADMAP.md"):
    links(file)
require((ROOT / "labs/INDEX.md").read_text(encoding="utf-8") == index(), "Lab index is stale")
print(f"11 authored routes ({len(pilots)} in the pilot format: labs {pilots}): objectives, setup, file trees, "
      "120-minute timetables, 10-point rubrics, public keys and local links PASS")
