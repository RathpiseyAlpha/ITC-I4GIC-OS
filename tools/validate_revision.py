"""Check the authored lab routes, linked teaching resources and rubric/timing gates."""
import re
from pathlib import Path
from build_lab_revision import index

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [(0, 10), (10, 25), (25, 35), (35, 70), (70, 85), (85, 100), (100, 110), (110, 120)]


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
        path = (file.parent / target.split("#")[0]).resolve()
        require(path.exists(), f"Missing link: {file.relative_to(ROOT)} -> {target}")


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
    for label in ("## Lab Objectives", "## Lab Setup", "## Prediction", "Guided", "Example", "## Individual Changed-case Checkpoint", "## Cleanup and Final Submission", "## Grading Criteria"):
        require(label in text, f"Missing {label}: {student}")
    require(re.search(r"^## .*Tests.*\(70–85\)", text, re.M), f"Missing test/feedback section: {student}")
    objectives = text.split("## Lab Objectives", 1)[1].split("**Extension objectives:**", 1)[0]
    require(len(re.findall(r"^\d+\. ", objectives, re.M)) == 3, f"Expected three core objectives: {student}")
    require(f'cd "$OSLAB_WORKSPACE/lab{number}"' in text, f"Missing explicit workspace cd: {student}")
    require(len(re.findall(r"^\s*```text$", text, re.M)) >= 2, f"Missing starting/submission trees: {student}")
    require("120 minutes" in text, f"Missing duration: {student}")
    require("3 Hours" not in text and "2026-06" not in text, f"Stale duration/date: {student}")
    for file in (student, instructor):
        value = file.read_text(encoding="utf-8")
        spans = [(int(a), int(b)) for a, b in re.findall(r"^\| (\d+)–(\d+) \|", value, re.M)]
        require(spans == EXPECTED and sum(b-a for a,b in spans) == 120, f"Bad timetable: {file}")
        points = [int(x) for x in re.findall(r"^\| [^\n|]+ \| ([1-3]) \|$", value, re.M)]
        require(points == [3, 2, 2, 2, 1] and sum(points) == 10, f"Bad rubric: {file}: {points}")
    plan = instructor.read_text(encoding="utf-8")
    require("Public repository notice" in plan and "private" in plan and "Key:" in plan, f"Missing public-key/private-variant notice: {instructor}")

for file in (ROOT / "labs/SETUP.md", ROOT / "labs/INDEX.md", ROOT / "README.md", ROOT / "labs/REPORT-TEMPLATE.md"):
    links(file)
require((ROOT / "labs/INDEX.md").read_text(encoding="utf-8") == index(), "Lab index is stale")
print("11 authored routes: objectives, setup, file trees, exact 120-minute timetables, 10-point rubrics, public keys and local links PASS")
