"""Static checks for the first-revision teaching set."""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
expected = [(0, 10), (10, 25), (25, 35), (35, 70), (70, 85), (85, 100), (100, 110), (110, 120)]
for number in range(1, 12):
    lab = root / "labs" / f"lab{number}"
    student = lab / f"lab{number}-instruction.md"
    report = lab / "README.md"
    instructor = root / "teaching" / "instructor" / f"lab{number}" / "plan.md"
    for file in (student, report, instructor):
        assert file.is_file(), file
    text = student.read_text(encoding="utf-8")
    assert "120 minutes" in text
    assert "Independent changed-case checkpoint" in text or "Individual changed-case checkpoint" in text
    assert "3 Hours" not in text and "2026-06" not in text
    spans = [(int(a), int(b)) for a, b in re.findall(r"^\| (\d+)–(\d+) \|", text, re.M)]
    assert spans == expected, (student, spans)
    assert sum(b-a for a,b in spans) == 120
    assert "| Concise, attributable evidence | 1 |" in instructor.read_text(encoding="utf-8")
    for file in (student, report):
        for target in re.findall(r"\]\(([^)]+)\)", file.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#")):
                continue
            path = (file.parent / target.split("#")[0]).resolve()
            assert path.exists(), (file, target)
print("11 routes, exact 120-minute totals, instructor rubrics, and local links PASS")
