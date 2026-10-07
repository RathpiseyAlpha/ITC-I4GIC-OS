"""Maintain the lab index only; authored teaching prose is never regenerated."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def index():
    rows = []
    for n in range(1, 12):
        folder = ROOT / "labs" / f"lab{n}"
        title = (folder / f"lab{n}-instruction.md").read_text(encoding="utf-8").splitlines()[0].lstrip("# ")
        rows.append(
            f"| {n}{' (bonus)' if n == 11 else ''} | {title} | "
            f"[Instruction](lab{n}/lab{n}-instruction.md) · "
            f"[Report](lab{n}/README.md) · [Extensions](lab{n}/extensions.md) | "
            f"[Public plan](../teaching/instructor/lab{n}/plan.md) |"
        )
    return "\n".join([
        "# Lab index", "",
        "Start with [environment setup](SETUP.md). Every route has a 120-minute individual core, objectives, guided commands, starting/submission trees and a topic rubric. Labs 1, 2 and 8 use the pilot format (personal values, Core / Plus / Challenge, live checkpoint). Lab 11 is optional bonus work.", "",
        "| Lab | Original topic title | Student files | Instructor preparation |",
        "|---|---|---|---|", *rows, "",
        "Instructor answers here are public; use fresh private variants for graded checkpoints. The Markdown instructions define the required route; older visual guides are background references.", "",
        "This index is maintained by `python tools/build_lab_revision.py`. That command updates only this file. Instructions, reports, extensions and instructor plans are authored directly; `--check` verifies the index without writing.", "",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = ROOT / "labs" / "INDEX.md"
    expected = index()
    if args.check:
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            raise SystemExit("Lab index is stale; run python tools/build_lab_revision.py")
        print("Lab index PASS")
    else:
        path.write_text(expected, encoding="utf-8")
        print("Updated labs/INDEX.md only")


if __name__ == "__main__":
    main()
