"""Lab 3 guide, Wildcards, Hard Links and Symbolic Links. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

Revised 2026-11-06 to the pilot format, like Labs 1 and 2: personal values (a name, a tag and two version numbers),
Core 1 to 3, Plus and Challenge, a live checkpoint on a chain of links, oslab debrief, and the 2/2/2/3/1 rubric.

A guide for the lab session, built like the Lab 1 and Lab 2 guides with the shared look in labkit.py
(Ubuntu fonts, a wider canvas, dark terminal windows, folder trees drawn like `tree`).

It starts with the concepts the core needs: wildcards and quoting, inodes, hard and symbolic links and
how a relative link target is resolved. The lab part follows labs/lab3/lab3-instruction.md: Setup, the
guided example, the prediction, Core 1 to 3, Plus and Challenge, the live checkpoint, debrief and submission.
GRUB and shared libraries are optional extensions in that instruction; the earlier guide taught them,
so they stay as a short background section at the end, redrawn here (images.json is empty).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, flow, init)  # noqa: E402,F401

WEEK = "Lab 3"
TITLE = "Operating Systems — Lab 3"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-27T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 3)
S = d.S
CW, HALF = labkit.CW, labkit.HALF

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-03", "Wildcards, Hard Links and Symbolic Links",
                  "Lab 3 guide: select files with patterns, then see what a rename does to a hard link and to a symbolic link.", size=88)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Explain which filenames a Bash wildcard selects, and what quoting changes.",
                    "Use inode numbers to tell a hard link from a separate copy.",
                    "Explain and repair a symbolic link after its target is renamed."], ordered=True, size=36, flex=3),
            card(t, "Lab 3", "First the concepts, with examples. Then the lab on the server. GRUB and shared libraries are optional extensions, so they come at the end.", label="THIS LAB", flex=2),
            gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "You rename a report. What breaks?",
         "A shortcut on the desktop, a second name for the same file, a note that says where the file is. Which of them still work?")

# ---- concepts first ---------------------------------------------------------
d.opener("bg-open", "CONCEPTS FIRST", "Wildcards and links", "Two ideas: the shell turns patterns into names, and one file can have more than one name.")

d.slide("wild-what", "A wildcard is a pattern, and the shell expands it",
        lambda t: row(lst(t, ["A wildcard is a character that stands for other characters, such as * for any characters.",
                              "The shell, not the command, expands the pattern into a list of matching names, then runs the command with that list.",
                              "If nothing matches, Bash keeps the pattern as typed. The command then looks for a file with that exact name.",
                              "Wildcards select file names. They are not the same as regular expressions."], size=34, flex=3),
                      card(t, "Why learn it here?", "One pattern replaces a long list of names. The same pattern, used carelessly with rm, removes more than you meant.", label="BEFORE THE LAB", pad=40, title_size=36, flex=2),
                      gap=48, align="stretch"),
        label=BG)

d.slide("wild-table", "The wildcard patterns",
        lambda t: tbl(t, ["Pattern", "Meaning", "Example", "Matches"],
                      [[mono("*"), "Zero or more characters", mono("*.txt"), "every .txt file"],
                       [mono("?"), "Exactly one character", mono("file?.txt"), "file1.txt, fileA.txt"],
                       [mono("[abc]"), "One character from the set", mono("file[123].txt"), "file1.txt, file2.txt, file3.txt"],
                       [mono("[a-z]"), "One character in the range", mono("[A-Z]*.txt"), "names that start with a capital"],
                       [mono("[!abc]"), "One character not in the set", mono("file[!0-9].txt"), "fileA.txt, not file1.txt"],
                       [mono("{a,b}"), "Brace expansion: generates words", mono("file.{txt,log}"), "the words file.txt and file.log"]],
                      [2, 5, 5, 6]),
        note="Square brackets match one character that exists. Braces only write words, before any file is looked at.",
        label=BG)

d.slide("wild-action", "Patterns at work",
        lambda t: row(term(t, ["ls *.txt",
                               "ls report0[1-3].txt",
                               "ls log_[!j]*.log",
                               "touch memo_{mon,tue,wed}.txt",
                               "cp *.csv archive/",
                               "ls *.tmp",
                               "rm *.tmp"], size=30),
                      col(para(t, "The first three list files. touch with braces creates three files in one command.", size=32),
                          para(t, "cp copies every .csv file into archive/.", size=32),
                          card(t, "Preview before you delete", "Run ls *.tmp first. If the list is what you expect, then run rm *.tmp.", label="CAUTION", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("wild-expand", "See what the shell really passes",
        lambda t: row(term(t, ["mkdir -p practice",
                               "printf 'one\\n' > practice/report1.txt",
                               "printf 'two\\n' > practice/report2.txt",
                               "printf 'log\\n' > practice/report.log",
                               ("blank",),
                               "printf '<%s>\\n' practice/*.txt",
                               ("out", "<practice/report1.txt>"),
                               ("out", "<practice/report2.txt>"),
                               "printf '<%s>\\n' 'practice/*.txt'",
                               ("out", "<practice/*.txt>")], size=28),
                      col(para(t, "printf prints each word it receives between angle brackets, one per line.", size=32),
                          para(t, "Without quotes, the shell sends two words: the two .txt files. With single quotes around the whole pattern, it sends one word with a literal *.", size=32),
                          para(t, "Use this trick to check a pattern before you give it to cp, mv or rm.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("wild-brace", "Brackets and braces are not the same",
        lambda t: row(col(h3(t, "Square brackets look at files"),
                          term(t, ["ls practice/report[12].txt",
                                   ("out", "practice/report1.txt  practice/report2.txt"),
                                   "ls practice/report[13].txt",
                                   ("out", "ls: cannot access 'practice/report3.txt': No such file")], size=26),
                          para(t, "Only names that exist can match. Bash keeps a pattern with no match, so the error names the pattern.", size=30),
                          gap=20, flex=None),
                      col(h3(t, "Braces only write words"),
                          term(t, ["echo practice/report{1,3}.txt",
                                   ("out", "practice/report1.txt practice/report3.txt")], size=26),
                          para(t, "The file report3.txt does not exist, and echo does not care. Brace expansion happens first, and no file is looked at.", size=30),
                          gap=20, flex=None),
                      gap=40, align="flex-start"),
        label=BG)

SVG_SANS = "Ubuntu, Segoe UI, Arial, sans-serif"
SVG_MONO = "Ubuntu Mono, DejaVu Sans Mono, Consolas, monospace"


def _arrow(x1, y1, x2, y2, color, dash=False, head=True):
    """A straight arrow drawn as a line and a triangle, so every renderer shows the same head."""
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - 16 * math.cos(a), y2 - 16 * math.sin(a)
    tri = (f'<polygon points="{x2},{y2} {bx + 8 * math.sin(a):.1f},{by - 8 * math.cos(a):.1f} '
           f'{bx - 8 * math.sin(a):.1f},{by + 8 * math.cos(a):.1f}" fill="{color}"/>') if head else ""
    d = ' stroke-dasharray="10 7"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{bx if head else x2:.1f}" y2="{by if head else y2:.1f}" stroke="{color}" stroke-width="4"{d}/>{tri}'


def _text(x, y, s, size=24, fill="#1b2a41", mono=False, bold=False, anchor="start"):
    fam = SVG_MONO if mono else SVG_SANS
    weight = ' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{fam}" font-size="{size}"{weight} fill="{fill}">{s}</text>'


def _svg(width, height, label, parts, back):
    bg = f'<rect x="0" y="0" width="{width}" height="{height}" fill="{back}"/>' if back else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" aria-label="{label}" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" style="width:{width}px;height:{height}px">{bg}{"".join(parts)}</svg>')


def inode_svg(accent, ink, fill, edge, line, back=None):
    """What an inode looks like: a directory entry (name and inode number), the inode record, and the data blocks."""
    amber = "#c77d00"
    p = [_text(270, 44, "The directory", 28, ink, bold=True, anchor="middle"),
         _text(910, 44, "The inode", 28, ink, bold=True, anchor="middle"),
         _text(1550, 44, "Data blocks on the disk", 28, ink, bold=True, anchor="middle")]
    # directory table: one row per name
    p.append(f'<rect x="20" y="80" width="500" height="171" rx="12" fill="{fill}" stroke="{edge}" stroke-width="2"/>')
    p.append(f'<line x1="300" y1="80" x2="300" y2="251" stroke="{edge}" stroke-width="2"/>'
             f'<line x1="20" y1="137" x2="520" y2="137" stroke="{edge}" stroke-width="2"/>'
             f'<line x1="20" y1="194" x2="520" y2="194" stroke="{edge}" stroke-width="2"/>')
    p.append(_text(40, 118, "name", 24, ink, bold=True) + _text(320, 118, "inode number", 24, ink, bold=True))
    p.append(f'<rect x="24" y="141" width="492" height="49" rx="8" fill="{accent}" fill-opacity=".14" stroke="{accent}" stroke-width="3"/>')
    p.append(_text(40, 175, "report1.txt", 24, ink, mono=True) + _text(320, 175, "12345", 24, ink, mono=True, bold=True))
    p.append(_text(40, 232, "report2.txt", 24, ink, mono=True) + _text(320, 232, "12346", 24, ink, mono=True))
    # the inode record
    x0, w = 640, 540
    p.append(f'<rect x="{x0}" y="70" width="{w}" height="380" rx="14" fill="{fill}" stroke="{accent}" stroke-width="3"/>')
    p.append(f'<path d="M{x0} 130V84a14 14 0 0 1 14-14H{x0 + w - 14}a14 14 0 0 1 14 14V130Z" fill="{accent}"/>')
    p.append(_text(x0 + w // 2, 112, "inode 12345", 30, "#ffffff", bold=True, anchor="middle"))
    rows = [("mode", "-rw-r--r--"), ("owner", "student"), ("size", "4 bytes"), ("times", "3 timestamps"),
            ("link count", "1"), ("data", "block 8841")]
    for i, (k, v) in enumerate(rows):
        y = 130 + i * 53
        if i:
            p.append(f'<line x1="{x0 + 16}" y1="{y}" x2="{x0 + w - 16}" y2="{y}" stroke="{edge}" stroke-width="1.5"/>')
        p.append(_text(x0 + 28, y + 36, k, 24, ink) + _text(x0 + 250, y + 36, v, 24, ink, mono=True, bold=(k == "data")))
    # data blocks
    for i, (num, txt) in enumerate((("block 8841", "hello"), ("block 8842", "(unused)"))):
        y = 180 + i * 96
        dash = "" if i == 0 else ' stroke-dasharray="8 6"'
        p.append(f'<rect x="1340" y="{y}" width="420" height="72" rx="10" fill="{fill if i == 0 else "none"}" stroke="{accent if i == 0 else edge}" stroke-width="3"{dash}/>')
        p.append(_text(1364, y + 45, num, 24, ink) + _text(1736, y + 45, txt, 24, ink, mono=True, anchor="end"))
    # arrows
    p.append(_arrow(516, 165, 636, 165, accent))
    p.append(_arrow(1176, 120 + 53 * 5 + 24, 1336, 216, accent))
    p.append(_text(900, 500, "The directory maps a name to an inode number. The inode describes the file and says where its data is.",
                   26, ink, anchor="middle"))
    p.append(_text(900, 540, "The name is not stored in the inode.", 26, amber, bold=True, anchor="middle"))
    return _svg(1800, 570, "What an inode looks like. The directory has a row for each file name with an inode number, for example report1.txt with 12345. "
                "Inode 12345 holds the mode, owner, size, timestamps, link count and the block where the data is. "
                "The data block holds the bytes of the file. The file name is not stored in the inode.", p, back)


def links_svg(accent, ink, fill, edge, line, back=None):
    """Hard link and symbolic link side by side: two names for one inode, and a small file that stores a path."""
    amber = "#c77d00"
    red = "#c0392b"
    p = []

    def box(x, y, w, h, label, sub=None, mono=True, hot=False, dashed=False):
        st = accent if hot else edge
        dash = ' stroke-dasharray="8 6"' if dashed else ""
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{st}" stroke-width="3"{dash}/>')
        if sub:
            p.append(_text(x + w // 2, y + 34, label, 24, ink, mono=mono, bold=True, anchor="middle"))
            p.append(_text(x + w // 2, y + 68, sub, 24, ink, mono=mono, anchor="middle"))
        else:
            p.append(_text(x + w // 2, y + h // 2 + 8, label, 24, ink, mono=mono, anchor="middle"))

    # left panel: hard link
    p.append(_text(450, 44, "Hard link", 32, accent, bold=True, anchor="middle"))
    p.append(_text(450, 84, "ln report1.txt hard-demo.txt", 24, ink, mono=True, anchor="middle"))
    box(30, 150, 240, 70, "report1.txt")
    box(30, 330, 240, 70, "hard-demo.txt")
    box(350, 230, 310, 110, "inode 12345", "link count 2", hot=True)
    box(740, 245, 140, 80, "hello")
    p.append(_arrow(270, 185, 346, 262, accent) + _arrow(270, 365, 346, 308, accent) + _arrow(660, 285, 736, 285, accent))
    p.append(_text(450, 470, "Two names for one inode.", 26, ink, bold=True, anchor="middle"))
    p.append(_text(450, 508, "Remove one name and the data stays.", 26, ink, anchor="middle"))
    # right panel: symbolic link
    ox = 920
    p.append(_text(ox + 450, 44, "Symbolic link", 32, accent, bold=True, anchor="middle"))
    p.append(_text(ox + 450, 84, "ln -s report1.txt soft-demo.txt", 24, ink, mono=True, anchor="middle"))
    box(ox + 30, 150, 240, 70, "soft-demo.txt")
    box(ox + 350, 140, 310, 110, "inode 99001", "stores report1.txt", dashed=True)
    box(ox + 30, 330, 240, 70, "report1.txt")
    box(ox + 350, 320, 310, 110, "inode 12345", "link count 1", hot=True)
    box(ox + 740, 335, 140, 80, "hello")
    p.append(_arrow(ox + 270, 185, ox + 346, 185, accent) + _arrow(ox + 270, 365, ox + 346, 375, accent) + _arrow(ox + 660, 375, ox + 736, 375, accent))
    p.append(f'<path d="M{ox + 505} 250V290H{ox + 150}V326" stroke="{amber}" stroke-width="4" stroke-dasharray="10 7" fill="none"/>'
             f'<polygon points="{ox + 150},328 {ox + 142},{312} {ox + 158},{312}" fill="{amber}"/>')
    p.append(_text(ox + 170, 282, "looks up that name", 24, amber, bold=True))
    p.append(_text(ox + 450, 470, "Its own inode, storing a path.", 26, ink, bold=True, anchor="middle"))
    p.append(_text(ox + 450, 508, "Rename the target and the path breaks.", 26, ink, anchor="middle"))
    p.append(f'<line x1="900" y1="120" x2="900" y2="520" stroke="{line}" stroke-width="2" stroke-dasharray="4 8"/>')
    return _svg(1800, 540, "Hard link and symbolic link. A hard link: report1.txt and hard-demo.txt are two names for inode 12345, which has link count 2 and holds the data. "
                "A symbolic link: soft-demo.txt has its own inode, 99001, which stores the path report1.txt. That path is looked up as a name, "
                "which leads to inode 12345 and the data.", p, back)


if os.environ.get("GUIDE_REPO"):
    for _name, _fn in (("inode.svg", inode_svg), ("hard-soft-links.svg", links_svg)):
        os.makedirs(os.path.join(os.environ["GUIDE_REPO"], "labs", "lab3", "figures"), exist_ok=True)
        with open(os.path.join(os.environ["GUIDE_REPO"], "labs", "lab3", "figures", _name), "w", encoding="utf-8") as _f:
            _f.write(_fn("#1f5fbf", "#1b2a41", "#eef3fb", "#9db4d6", "#8d97aa", back="#ffffff") + "\n")

d.slide("inode", "A name is not the file",
        lambda t: row(lst(t, ["The data of a file lives on the disk. An inode is the record that describes it: size, owner, permissions and where the data is.",
                              "Every inode has a number. A file name is only an entry in a directory that points to an inode number.",
                              "Two entries can point to the same inode. They are two names for one file: hard links.",
                              "The data is freed only when the last name is gone."], size=32, flex=3),
                      term(t, ["ls -li",
                               ("out", "12345 -rw-r--r-- 2 student student 4 report1.txt"),
                               ("out", "12345 -rw-r--r-- 2 student student 4 hard-demo.txt"),
                               ("out", "99001 lrwxrwxrwx 1 student student 11 soft-demo.txt -> report1.txt")],
                           size=24, title="inode number, permissions, link count, ..."),
                      gap=48, align="center"),
        note="The 2 in the third column is the link count: two names point to inode 12345. The symbolic link has its own inode, 99001.",
        label=BG)

d.slide("inode-look", "What an inode looks like",
        lambda t: inode_svg(t["accent"], "#1b2a41", "#ffffff", "#9db4d6", "#8d97aa"),
        note="Read it from left to right: the name leads to an inode number, the inode leads to the data. ls -li shows that number.",
        label=BG, gap=24)

d.slide("hard-soft", "Hard link and symbolic link",
        lambda t: tbl(t, ["", "Hard link", "Symbolic link"],
                      [["Command", mono("ln target link"), mono("ln -s target link")],
                       ["What it is", "Another name for the same inode", "A small file that stores a path"],
                       ["Inode", "The same as the original", "Its own inode"],
                       ["Original is removed", "Data survives under the other name", "The link breaks: it is dangling"],
                       ["Across filesystems", "No", "Yes"],
                       ["Folders", "Not normally", "Yes"],
                       ["Seen in ls -l", "No arrow", "An arrow to the stored target"]],
                      [3, 6, 6]),
        note="Inspect with ls -li (inode numbers), stat (link count) and readlink (the stored path).",
        label=BG)

d.slide("links-drawn", "The two kinds of link, drawn",
        lambda t: links_svg(t["accent"], "#1b2a41", "#ffffff", "#9db4d6", "#8d97aa"),
        note="A hard link is a second name for the inode. A symbolic link is a separate small file that holds a name to look up.",
        label=BG, gap=24)

d.slide("rel-target", "A relative target is read from the link's folder",
        lambda t: row(term(t, ["cd ~/oslab-work/lab3",
                               "ls -l links",
                               ("out", "lrwxrwxrwx 1 student student 9 maple-soft.txt -> maple.txt"),
                               ("blank",),
                               "cat links/maple-soft.txt",
                               ("out", "version 417"),
                               "cd links && cat maple-soft.txt",
                               ("out", "version 417")], size=26),
                      col(para(t, "The stored target maple.txt has no / at the front, so it is relative.", size=32),
                          para(t, "It is resolved from the folder that holds the link (links/), not from the folder where you are standing.", size=32),
                          para(t, "That is why the same link works from two places. Write the target as if you were standing next to the link.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("link-name", "A symbolic link repeats a name",
        lambda t: row(term(t, ["mv maple.txt maple-old.txt",
                               "cat maple-soft.txt",
                               ("out", "cat: maple-soft.txt: No such file or directory"),
                               "printf 'version 463\\n' > maple.txt",
                               "cat maple-soft.txt",
                               ("out", "version 463"),
                               "cat maple-hard.txt",
                               ("out", "version 417")], size=24, title="example values, in links/"),
                      col(para(t, "The link stores only the text maple.txt. After the rename no file has that name, so the link is dangling.", size=30),
                          para(t, "A new file with the old name makes it work again, but it now reads the new file. A hard link never does this: it follows the inode.", size=30),
                          gap=24),
                      gap=48, align="center"),
        note="This is the surprise of Core 2. The hard link made before the rename still prints the original version.",
        label=BG)

d.slide("experiment", "The key experiment",
        lambda t: row(term(t, ["echo 'config data' > original.txt",
                               "ln original.txt hardlink.txt",
                               "ln -s original.txt symlink.txt",
                               "ls -li",
                               "rm original.txt",
                               "cat hardlink.txt",
                               ("out", "config data"),
                               "cat symlink.txt",
                               ("out", "cat: symlink.txt: No such file or directory")], size=26),
                      col(para(t, "echo with &gt; writes the text into a new file. rm removes only the name original.txt.", size=32),
                          para(t, "The data still has one name, hardlink.txt, so it survives.", size=32),
                          para(t, "symlink.txt still says original.txt, and no such name exists. The link is dangling.", size=32),
                          gap=24),
                      gap=48, align="center"),
        note="In practice: ls -la /usr/bin/python* shows programs that are managed with symbolic links.",
        label=BG)

# ---- the lab ----------------------------------------------------------------
d.opener("lab-open", "LAB 3", "Wildcards and links", "A report is renamed. Which references still work, which break, and what does a new file with the old name do?")

START_TREE = [("links", [("maple.txt", None)]),
              ("notes", [(".maple.txt", None), ("maple.log", None), ("maple1.txt", None), ("maple12.txt", None), ("maple2.txt", None)]),
              ("evidence", [])]

SCENE_TREE = [("links", [("maple.txt", None)]),
              ("notes", [("maple1.txt", None), ("maple2.txt", None), ("maple12.txt", None), ("...", None)]),
              ("evidence", [])]

labkit.scenario(d, 3, "A report with many references", "Rename a report, see which references break, repair the symbolic link, and meet a new file that takes the old name.",
                "Your names and your version numbers are your own. This guide shows example values.", SCENE_TREE)
labkit.timetable(d, [["0 to 5", "Setup"],
                     ["5 to 20", "Guided: names, inodes and links"],
                     ["20 to 30", "Prediction, then class discussion"],
                     ["30 to 40", "Core 1: wildcards on your own files"],
                     ["40 to 60", "Core 2: rename, break, and reuse the old name"]],
                 [["60 to 75", "Core 3: repair and prove it"],
                  ["75 to 90", "Plus and Challenge (or finish Core)"],
                  ["90 to 105", "Live checkpoint"],
                  ["105 to 115", "Debrief"],
                  ["115 to 120", "Submit"]])

d.slide("helper", "Six helper commands, and why you use them",
        lambda t: tbl(t, ["Command", "What it does"],
                      [[mono("oslab values lab3"), "Shows your report name, the word for the renamed file and your two version numbers. Use them everywhere"],
                       [mono("oslab predict lab3"), "Saves your prediction once, before the experiment"],
                       [mono("oslab hint lab3 1"), "A hint, levels 1 to 3. Hints cost no points"],
                       [mono("oslab check lab3"), "Looks at your files and shows your milestones"],
                       [mono("oslab checkpoint lab3"), "Opens when the instructor says so, near the end"],
                       [mono("oslab debrief lab3"), "After the lab: you give the right answers to your prediction questions"]],
                      [5, 11]),
        note="Before the lab, run oslab doctor and oslab prelab lab3. Read Concepts First as well. It takes about twenty minutes.")

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Core, Plus, Challenge", "Core is for everyone. Plus and Challenge are for students who finish early. Full marks need only Core and the checkpoint.", title_size=36),
                      rule(t, "AI tools", "Allowed in Core, Plus and Challenge, so test what they tell you. Not allowed in the prediction and the checkpoint.", title_size=36),
                      rule(t, "You write the repair", "In Core 3 nobody gives you the repair commands. You decide the target and write both commands.", title_size=36)),
        note="A wrong prediction costs nothing. It is marked for being made and corrected, not for being right. No step needs sudo.")

d.slide("start", "Setup: start the lab",
        lambda t: row(term(t, ['export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                               "oslab start lab3",
                               'cd "$OSLAB_WORKSPACE/lab3"',
                               "mkdir -p evidence",
                               "oslab values lab3"], title="student@server: ~", size=26),
                      col(lst(t, ["The first line sets OSLAB_WORKSPACE to ~/oslab-work, unless it is already set. Type it as it is.",
                                  "oslab start lab3 makes the lab folder. It keeps your work if you run it again.",
                                  "cd takes you into it, and mkdir -p makes the evidence folder.",
                                  "oslab values lab3 prints your own names and numbers."], size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("values", "Your values: a name, a tag and two numbers",
        lambda t: row(col(h3(t, "The last command prints them"),
                          term(t, ["oslab values lab3",
                                   ("out", "Your personal values for lab3 (your-account):"),
                                   ("out", "  name     = maple"),
                                   ("out", "  tag      = old"),
                                   ("out", "  v1       = 417"),
                                   ("out", "  v2       = 463")], title="example: your values will be different", size=26),
                          gap=20, flex=None),
                      col(h3(t, "What they are"),
                          lst(t, ["name is your report, for example maple.txt.",
                                  "tag is the word you add when you rename it: maple-old.txt.",
                                  "v1 is the version number inside your report. v2 is the number in the new file.",
                                  "Your values are different from the example, and from your neighbour's."], size=30),
                          gap=20, flex=None),
                      gap=48, align="flex-start"))

d.slide("vars", "Type your values into shell variables",
        lambda t: row(term(t, ["name=maple", "tag=old", "v1=417", "v2=463"], title="example values: use your own", size=30),
                      col(lst(t, ["A variable is a name that holds a value. Write name=value with no spaces around the =.",
                                  "After this, the shell replaces \"$name\" with your report name, \"$tag\" with your word, and so on.",
                                  "Always write the variable in double quotes.",
                                  "If you open a new terminal, run cd and set the variables again."], size=30),
                          gap=20),
                      gap=48, align="center"),
        note="Everything in the lab uses these four variables. Do not copy the example values. Use the ones oslab values lab3 printed.")

d.slide("capital", "Angle brackets stand for your own values",
        lambda t: tbl(t, ["The instruction says", "With the example values, you type", "Or, with the variables"],
                      [[mono('ln "$name.txt" "$name-hard.txt"'), mono("ln maple.txt maple-hard.txt"), "the same line"],
                       [mono("&lt;name&gt;-&lt;tag&gt;.txt"), mono("maple-old.txt"), mono('"$name-$tag.txt"')],
                       [mono("version &lt;v2&gt;"), mono("version 463"), mono("printf 'version %s\\n' \"$v2\"")]],
                      [5, 5, 6]),
        note="Never type the angle brackets. Type your own value, or the variable in double quotes. The - in \"$name-hard.txt\" ends the variable name, so the shell reads $name and then the text -hard.txt.")

d.slide("start-tree", "Your folder",
        lambda t: row(tree(t, "lab3", START_TREE, cmd="tree -a -L 3", title="student@server: ~/oslab-work/lab3", size=28),
                      col(para(t, "links/ holds your report, with your name. It contains version 417 in the example.", size=32),
                          para(t, "notes/ holds five files with your name: two with one digit, one with two digits, a log and a hidden file.", size=32),
                          para(t, "oslab check lab3 shows TRY on every line now. The hidden .oslab-managed.json is the helper's. Leave it.", size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Names, inodes and links", "Five to twenty minutes, with the instructor. A separate practice folder, so your own files stay untouched.")

d.slide("g-files", "Step 1: three clearly different names",
        lambda t: row(term(t, ["mkdir -p practice",
                               "printf 'one\\n' > practice/report1.txt",
                               "printf 'two\\n' > practice/report2.txt",
                               "printf 'log\\n' > practice/report.log",
                               "ls practice",
                               ("out", "report1.txt  report2.txt  report.log")], size=28),
                      col(para(t, "This part uses fixed names in practice/. Your own names come back in Core 1.", size=32),
                          para(t, "printf with &gt; writes one line into a new file. The names differ on purpose: two .txt files and one .log file.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-expand", "Step 1: how the shell expands a pattern",
        lambda t: row(term(t, ["printf '<%s>\\n' practice/*.txt",
                               ("out", "<practice/report1.txt>"),
                               ("out", "<practice/report2.txt>"),
                               "printf '<%s>\\n' practice/report?.txt",
                               ("out", "<practice/report1.txt>"),
                               ("out", "<practice/report2.txt>"),
                               "printf '<%s>\\n' 'practice/*.txt'",
                               ("out", "<practice/*.txt>")], size=26),
                      col(para(t, "Bash expands * and ? before printf runs. printf prints each name it receives between &lt; and &gt;.", size=30),
                          para(t, "The quoted pattern is not expanded, so printf receives the literal text.", size=30),
                          card(t, "Observe", "Why is report.log never in the list?", label="TRY", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-links", "Step 2: your first two links",
        lambda t: row(term(t, ["ln practice/report1.txt practice/hard-demo.txt",
                               "ln -s report1.txt practice/soft-demo.txt",
                               "ls -li practice/report1.txt practice/hard-demo.txt practice/soft-demo.txt",
                               "readlink practice/soft-demo.txt"], size=24),
                      col(para(t, "report1.txt and hard-demo.txt show the same inode number and the link count 2: one file, two names. The symbolic link has its own number.", size=30),
                          para(t, "readlink prints the text the link stores.", size=30),
                          card(t, "Think", "soft-demo.txt is inside practice/ and stores only report1.txt. Which path would be wrong, and what would Linux look for?", label="TRY", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- prediction ---------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Before you rename anything. Ten minutes.")

d.slide("predict", "The prediction",
        lambda t: row(col(term(t, ["oslab predict lab3"]),
                          para(t, "It asks three questions and one sentence, with your own names and numbers. Answer alone, without AI.", size=32),
                          gap=24, flex=3),
                      col(card(t, "The sequence", "You rename your report. Then a new file takes the old name. What do the two links print?", label="PREDICTION", pad=32, title_size=32),
                          card(t, "The rules", "The first answer counts. A wrong guess costs nothing.", label="HOW", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"),
        note="Use what you know from Concepts First: what does each kind of link store?")

# ---- core 1 ---------------------------------------------------------------------
d.opener("c1-open", "CORE 1", "Wildcards on your own files", "Ten minutes, from minute 30 to 40.")

d.slide("c1-look", "Step 1: look at your notes folder",
        lambda t: row(term(t, ['cd "$OSLAB_WORKSPACE/lab3"',
                               "ls -a notes",
                               ("out", ".  ..  .maple.txt  maple1.txt  maple12.txt  maple2.txt  maple.log")], title="example values: your names are different", size=24),
                      col(para(t, "ls -a also shows hidden names: the ones that start with a dot.", size=32),
                          card(t, "Think", "Which of these files will the pattern notes/*.txt select? Which will it skip, and why?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("c1-write", "Step 2: three patterns, and the middle one is yours",
        lambda t: row(term(t, ["{",
                               "  printf '<%s>\\n' notes/*.txt",
                               "  # write the middle command here",
                               "  printf '<%s>\\n' 'notes/*.txt'",
                               "} | tee evidence/wildcards.txt"], size=26),
                      col(card(t, "You write the middle command", "It must print only your two files with a one-digit number, maple1.txt and maple2.txt, and not maple12.txt. Write the variable in double quotes and the ? outside them.", label="YOUR TURN", pad=32, title_size=32),
                          para(t, "{ and } group the three commands, so one tee saves all their output.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c1-see", "What you should see",
        lambda t: tbl(t, ["Command", "Prints, with the example values"],
                      [[mono("notes/*.txt"), "maple1.txt, maple12.txt and maple2.txt. Not the hidden file, and not maple.log"],
                       [mono("your middle command"), "maple1.txt and maple2.txt only"],
                       [mono("'notes/*.txt'"), "The literal text: &lt;notes/*.txt&gt;"]],
                      [5, 11]),
        note="The most common mistake is a * where the ? belongs: then maple12.txt is in the list too. oslab hint lab3 1 helps.")

# ---- core 2 ---------------------------------------------------------------------
d.opener("c2-open", "CORE 2", "Rename, break, and reuse the old name", "Twenty minutes, from minute 40 to 60. Keep your own names: oslab check looks for them.")

d.slide("c2-one", "Step 1: make the references, and save the starting state",
        lambda t: row(term(t, ['cd "$OSLAB_WORKSPACE/lab3/links"',
                               'cat "$name.txt"',
                               'ln "$name.txt" "$name-hard.txt"',
                               'ln -s "$name.txt" "$name-soft.txt"',
                               "{",
                               "  printf '\\n=== BEFORE RENAME ===\\n'",
                               '  ls -li "$name.txt" "$name-hard.txt" "$name-soft.txt"',
                               "  printf 'hard: '; cat \"$name-hard.txt\"",
                               "  printf 'soft: '; cat \"$name-soft.txt\"",
                               "  printf 'stored target: '; readlink \"$name-soft.txt\"",
                               "} | tee ../evidence/links.txt"], size=24, title="student@server: ~/oslab-work/lab3/links"),
                      col(para(t, "The two links are made before the rename. tee starts evidence/links.txt, and the labelled line marks the state.", size=30),
                          para(t, "You should see version 417 three times, and the same inode number for your report and the hard link.", size=30),
                          card(t, "If ln says File exists", "Look at the existing entry first. Do not overwrite work blindly.", label="CAREFUL", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-two", "Step 2: rename the report, then look",
        lambda t: row(term(t, ['mv -- "$name.txt" "$name-$tag.txt"',
                               "{",
                               "  printf '\\n=== AFTER RENAME, BEFORE REPAIR ===\\n'",
                               '  ls -li "$name-$tag.txt" "$name-hard.txt" "$name-soft.txt"',
                               "  printf 'hard: '; cat \"$name-hard.txt\"",
                               "  printf 'stored target: '; readlink \"$name-soft.txt\"",
                               "  printf 'soft: '; cat \"$name-soft.txt\"",
                               "} 2>&1 | tee -a ../evidence/links.txt"], size=24, title="student@server: ~/oslab-work/lab3/links"),
                      col(para(t, "mv -- renames the entry; the file keeps its inode. tee -a adds to the file. 2&gt;&amp;1 puts the error message into the evidence.", size=30),
                          card(t, "The error is expected", "cat of the symbolic link fails with No such file or directory. The link exists, but the name it stores belongs to no file now: it is dangling.", label="THINK", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-three", "Step 3: a new file takes the old name",
        lambda t: row(term(t, ['printf \'version %s\\n\' "$v2" > "$name.txt"',
                               "{",
                               "  printf '\\n=== NEW FILE USING THE OLD NAME ===\\n'",
                               '  ls -li "$name.txt" "$name-$tag.txt" "$name-hard.txt" "$name-soft.txt"',
                               "  printf '%s: ' \"$name.txt\"; cat \"$name.txt\"",
                               "  printf 'hard: '; cat \"$name-hard.txt\"",
                               "  printf 'soft: '; cat \"$name-soft.txt\"",
                               "} 2>&1 | tee ../evidence/replacement.txt"], size=24, title="student@server: ~/oslab-work/lab3/links"),
                      col(para(t, "Somebody else makes a new report with your old file name. It holds version 463 in the example.", size=30),
                          card(t, "Look closely", "The symbolic link works again, but it prints the NEW number. The hard link still prints your original number: it follows the inode, not the name.", label="SURPRISE", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-see", "What each name prints in each state",
        lambda t: tbl(t, ["State", "Hard link", "Symbolic link"],
                      [["Before the rename", "version 417", "version 417"],
                       ["After the rename", "version 417", "cat fails: dangling"],
                       ["After the new file", "version 417", "version 463, the wrong file"]],
                      [5, 5, 6]),
        note="Example values. Write in your report which of the two was a surprise. The hard link and the renamed report keep one inode all the time.")

# ---- core 3 ---------------------------------------------------------------------
d.opener("c3-open", "CORE 3", "Repair and prove it", "Fifteen minutes, from minute 60 to 75.")

d.slide("c3-repair", "Step 1: repair only the symbolic link",
        lambda t: row(col(h3(t, "What to do"),
                          lst(t, ["Make maple-soft.txt read your original report again, which is now maple-old.txt.",
                                  "Use a relative target. Ask: from which folder is the stored target read?",
                                  "Do not touch the hard link. Do not rename the report back.",
                                  "Check: cat \"$name-soft.txt\" must print version 417."], ordered=True, size=30),
                          gap=20, flex=3),
                      col(card(t, "Your decision, your commands", "Delete the link with rm --, then make it again with ln -s TARGET LINK. Nobody gives you TARGET.", label="YOUR TURN", pad=32, title_size=32),
                          term(t, ["rm -- LINK", "ln -s TARGET LINK", 'cat "$name-soft.txt"'], size=26),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("c3-save", "Step 2: save the repaired state, and your decision",
        lambda t: row(term(t, ["{",
                               "  printf '\\n=== AFTER REPAIR ===\\n'",
                               '  ls -li "$name-$tag.txt" "$name-hard.txt" "$name-soft.txt"',
                               "  printf 'stored target: '; readlink \"$name-soft.txt\"",
                               "  printf 'hard: '; cat \"$name-hard.txt\"",
                               "  printf 'soft: '; cat \"$name-soft.txt\"",
                               "} | tee -a ../evidence/links.txt",
                               "nano ../evidence/links.txt"], size=24, title="student@server: ~/oslab-work/lab3/links"),
                      col(para(t, "In nano, add one line at the end. It starts with Decision: and says why you stored a relative target.", size=30),
                          para(t, "Say also what would break if the link stored an absolute path and you moved the whole folder. Save with Ctrl+O and Enter, leave with Ctrl+X.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c3-check", "Step 3: check your milestones",
        lambda t: col(term(t, ['cd "$OSLAB_WORKSPACE/lab3"',
                               "oslab check lab3",
                               ("out", "PASS: wildcards: evidence/wildcards.txt holds your three expansions"),
                               ("out", "PASS: hard link: maple-hard.txt and maple-old.txt are the same file (version 417)"),
                               ("out", "PASS: symbolic link: maple-soft.txt stores a relative target that reaches maple-old.txt"),
                               ("out", "PASS: new file: maple.txt holds version 463 and is separate from the version 417 file"),
                               ("out", "PASS: evidence/links.txt records the failure after the rename and the repaired link"),
                               ("out", "milestones: 5/5")], title="example values", size=24),
                      para(t, "A TRY line names what is missing, and the why: lines say what oslab found instead. Fix it and check again.", size=30),
                      gap=24),
        note="Core is complete when oslab check lab3 shows milestones: 5/5. Hints: oslab hint lab3 1, 2, 3.")

# ---- plus and challenge ---------------------------------------------------------------------------------------
d.slide("plus", "Plus: one more pattern",
        lambda t: row(term(t, ['cd "$OSLAB_WORKSPACE/lab3"',
                               "printf '<%s>\\n' notes/\"$name\"[12].txt",
                               "printf '<%s>\\n' notes/\"$name\"[!1]*"], size=24),
                      col(para(t, "[12] matches one character, 1 or 2. [!1] matches one character that is not 1.", size=30),
                          para(t, "Write down which names you expect before you run them. Then save one sentence in evidence/plus.txt: where did your guess differ?", size=30),
                          card(t, "Hint", "The second pattern needs one character that is not 1, then anything.", label="PLUS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"),
        note="Plus and Challenge are not needed for full marks. They are noted in your feedback.")

d.slide("challenge", "Challenge: how many names does a file have?",
        lambda t: row(term(t, ["mkdir -p extra",
                               "cd extra",
                               "printf 'keep me\\n' > one.txt",
                               "ln one.txt two.txt",
                               "ln one.txt three.txt",
                               "ls -l one.txt two.txt three.txt"], size=24),
                      col(para(t, "The number after the permissions is the link count. Then rm -- one.txt, look again, and cat two.txt.", size=30),
                          card(t, "Answer in evidence/challenge.txt", "What link count do the remaining names show after each rm? Is the data gone after you delete one.txt? When would it be gone?", label="CHALLENGE", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- live checkpoint ------------------------------------------------------------------------
d.opener("cp-open", "LIVE CHECKPOINT", "Show what you can do alone", "Fifteen minutes near the end of the lab. Worth 3 of the 10 points.")

d.slide("cp-why", "Why is there a checkpoint?",
        lambda t: grid(card(t, "It shows what you can do alone", "For most of the lab you may use hints and AI tools. The checkpoint is the one moment without them.", icon_name="CheckCircle", pad=28, title_size=32),
                       card(t, "The names are new", "The questions use a new folder and new file names, made for you at that moment. An answer copied from a neighbour does not fit.", icon_name="Key", pad=28, title_size=32),
                       card(t, "The instructor sees who needs help", "Your answers arrive at once, so a common mistake can be explained before the next lab.", icon_name="Users", pad=28, title_size=32),
                       card(t, "It is fair", "Everyone gets the same kind of task, with their own names.", icon_name="ThumbsUp", pad=28, title_size=32),
                       cols=2),
        gap=36)

d.slide("cp-steps", "What happens, step by step",
        lambda t: flow(t, [("1. The instructor opens it", "Close your AI tools"), ("2. oslab checkpoint lab3", "Answer the five questions"),
                           ("3. Build and repair", "A chain of two links; you repair it"), ("4. oslab check lab3", "A sixth milestone must pass")], 400, hot=1),
        lambda t: row(rule(t, "Before it opens", "The command says that the checkpoint is not open yet. Wait for the instructor.", title_size=36),
                      rule(t, "While you work", "Use your terminal and what you learned in this lab. No AI tools, and no help from a neighbour.", title_size=36),
                      rule(t, "When you finish", "oslab check lab3 shows whether the sixth milestone, checkpoint, passes. You can fix the repair and check again.", title_size=36)),
        gap=56)

d.slide("cp-marks", "What the checkpoint asks",
        lambda t: tbl(t, ["Part", "What you do"],
                      [["Five questions", "They use a new folder, new names and a chain of two symbolic links. Four are marked; the last is one sentence that your instructor reads."],
                       ["The case", "Build the case with the commands that oslab prints, repair first.txt yourself, and save the output in evidence/checkpoint.txt."],
                       ["The check", "Run oslab check lab3. The sixth milestone, checkpoint, must show PASS."]],
                      [4, 13]),
        note="The same idea as Core 3: a link stores a name, and a rename breaks it. Here a second link points at the first.")

# ---- debrief and submit ---------------------------------------------------------------------
d.opener("end-open", "DEBRIEF AND SUBMIT", "Look back, then hand in", "Ten minutes of debrief, five to submit.")

d.slide("debrief", "Debrief: look at your prediction again",
        lambda t: row(term(t, ['cat "$OSLAB_WORKSPACE/.records/lab3-predict.json"',
                               "oslab debrief lab3"], size=24, title="student@server: ~/oslab-work/lab3"),
                      col(para(t, "oslab saved your prediction in a hidden folder, .records. It stays as it was, so the comparison shows which answers you confirmed and which you corrected.", size=30),
                          card(t, "Class discussion", "Why can a symbolic link work and still read the wrong file?", label="DISCUSS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

labkit.submission(d, 3, ['cp -- evidence/wildcards.txt evidence/links.txt "$SUBMISSION_REPO/lab3/evidence/"',
                         'cp -- evidence/replacement.txt "$SUBMISSION_REPO/lab3/evidence/"',
                         'cp -- evidence/checkpoint.txt "$SUBMISSION_REPO/lab3/evidence/"'],
                  [("README.md", None), ("evidence", [("checkpoint.txt", None), ("links.txt", None), ("replacement.txt", None), ("wildcards.txt", None)])],
                  note="If you did Plus or Challenge, copy evidence/plus.txt or evidence/challenge.txt the same way. The course website checks that README.md, wildcards.txt, links.txt and replacement.txt are there, with these exact names.")

d.slide("submit-git", "Submit 3: commit and push",
        lambda t: row(term(t, ["cd ~/os-gic-YOUR_ID",
                               "git pull",
                               "git add os-lab-YOUR_ID/lab3",
                               'git commit -m "Lab 3"',
                               "git push"], title="student@server: ~", size=26),
                      col(para(t, "git pull comes first, in case you pushed from your own computer since.", size=32),
                          para(t, "Replace YOUR_ID with your own ID, as before.", size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.grading(d, [["Correct files: oslab check lab3 passes Core milestones 1 to 4", "2"],
                   ["Tests: the failure after the rename and the repaired link in links.txt (milestone 5)", "2"],
                   ["Prediction saved in time, and corrected with oslab debrief lab3", "2"],
                   ["Live checkpoint: the four answers, the repaired chain and the saved output, and your sentence", "3"],
                   ["Complete submission: the required files in your repository, on time", "1"]],
               note="Every row is marked from your oslab records and the files in your repository, so run oslab check lab3 until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.")

labkit.mistakes(d, [["A space around the = in name=maple", "An error, or an empty variable", "Write it with no spaces"],
                    ["Quotes around the whole pattern", "The literal pattern is printed", "Quote only the variable: \"$name\"?.txt"],
                    ["The hard link made after the rename", "It names the new file, so the experiment proves nothing", "Make both links before mv"],
                    ["The repair uses the old name", "The link reads the new file, version 463", "Point it at the renamed report, maple-old.txt"],
                    ["An absolute target in the repair", "oslab check says it must be relative", "Write the target as if you stood next to the link"],
                    ["Predicting after the rename", "No prediction saved in time", "Run oslab predict lab3 before Core 1"]])

# ---- beyond the core (kept from the earlier guide) --------------------------------
d.opener("ext-open", "BEYOND THE CORE", "GRUB and shared libraries", "Optional extensions. They need a disposable virtual machine or a compiler, and they are not part of the two-hour core.")

d.slide("boot", "From power-on to login",
        lambda t: row(tbl(t, ["Stage", "What it does"],
                          [["BIOS or UEFI", "Self-test, then finds the boot device"],
                           ["GRUB", "Shows a menu and loads the kernel"],
                           ["Kernel", "Starts the hardware, mounts the root filesystem, runs the first process (PID 1)"],
                           ["init or systemd", "Starts the system services in order"],
                           ["Login", "User space is ready"]],
                          [4, 11], width=CW),
                      gap=32),
        label=EXT)

d.slide("grub-files", "GRUB files and key settings",
        lambda t: row(tbl(t, ["File", "Purpose", "Edit?"],
                          [[mono("/boot/grub/grub.cfg"), "The generated menu", "Never"],
                           [mono("/etc/default/grub"), "Timeout, kernel parameters", "Yes"],
                           [mono("/etc/grub.d/"), "Scripts, custom entries", "Yes"],
                           [mono("/boot/vmlinuz-*"), "The compressed kernel", "No"]],
                          [6, 7, 2], width=HALF),
                      tbl(t, ["Setting", "Meaning", "Example"],
                          [[mono("GRUB_DEFAULT"), "Entry to boot", "0"],
                           [mono("GRUB_TIMEOUT"), "Seconds at the menu", "10"],
                           [mono("GRUB_CMDLINE_LINUX_DEFAULT"), "Kernel parameters", "quiet splash"],
                           [mono("GRUB_BACKGROUND"), "A menu background image", "/boot/grub/bg.png"]],
                          [8, 5, 4], width=HALF),
                      gap=32),
        note="After you edit /etc/default/grub, run sudo update-grub. Custom entries go in /etc/grub.d/40_custom. Do this only in a disposable virtual machine, never on the shared server.",
        label=EXT)

d.slide("grub-recover", "GRUB recovery",
        lambda t: row(tbl(t, ["Mode", "How you enter", "Use"],
                          [["Recovery mode", "GRUB menu, Advanced options, recovery", "A root shell, fsck, limited services"],
                           ["GRUB command line", "Press c at the menu", "Boot by hand when the menu is broken"],
                           ["Live USB", "Boot from an external image", "Full rescue when GRUB is gone"]],
                          [4, 6, 6], width=HALF),
                      term(t, ["set root=(hd0,msdos1)",
                               "linux /boot/vmlinuz-VERSION root=/dev/sda1",
                               "initrd /boot/initrd.img-VERSION",
                               "boot"], title="grub>", size=24, width=HALF),
                      gap=32, align="center"),
        note="Take a snapshot of the virtual machine before you break anything on purpose.",
        label=EXT)

d.slide("libs", "Static and dynamic linking",
        lambda t: tbl(t, ["", "Static", "Dynamic"],
                      [["When linked", "At compile time", "When the program starts"],
                       ["Library code", "Copied into the executable", "Loaded from .so files"],
                       ["Executable size", "Larger", "Smaller"],
                       ["Memory", "Each program has its own copy", "Programs share one copy"],
                       ["Updates", "Recompile every program", "Replace the .so, and all programs benefit"],
                       ["File extension", ".a (archive)", ".so (shared object)"]],
                      [4, 6, 7]),
        label=EXT)

d.slide("linker", "How a program finds its libraries",
        lambda t: flow(t, [("1. The kernel loads the program", "an ELF file"), ("2. The dynamic linker starts", "ld-linux.so"),
                           ("3. It finds each .so", "LD_LIBRARY_PATH, /etc/ld.so.cache, then /lib and /usr/lib"),
                           ("4. It maps them in", "into the process, and the program runs")], 400, hot=2),
        label=EXT)

d.slide("libs-cmds", "Looking at shared libraries, and building one",
        lambda t: row(term(t, ["ldd /bin/ls",
                               "ldconfig -p | grep libc",
                               "gcc -fPIC -c mylib.c -o mylib.o",
                               "gcc -shared -o libmylib.so mylib.o",
                               "gcc main.c -L. -lmylib -o myprogram",
                               "LD_LIBRARY_PATH=. ./myprogram"], size=24),
                      col(para(t, "ldd lists the libraries a program needs. ldconfig -p searches the library cache.", size=30),
                          para(t, "-fPIC makes position-independent code, so the library can load at any address. -shared makes the .so file.", size=30),
                          para(t, "For a user-local library, set LD_LIBRARY_PATH instead of installing into system folders.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=EXT)

d.slide("libs-more", "More ways to look at a library",
        lambda t: row(term(t, ["file /lib/x86_64-linux-gnu/libc.so.6",
                               "readelf -h /bin/ls",
                               "grep '[.]so' /proc/$$/maps",
                               "sudo ldconfig"], size=26),
                      col(para(t, "file tells you the kind of file: an ELF shared object.", size=30),
                          para(t, "readelf -h prints the ELF header of a program. /proc/$$/maps lists what the current shell has loaded.", size=30),
                          para(t, "After you install a new .so in a system folder, sudo ldconfig refreshes the cache. Not on the shared server.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=EXT)

d.close([("Wildcards", "The shell expands a pattern into names before the command runs. Quote a pattern to keep it literal."),
         ("Name and inode", "A file name is an entry that points to an inode. Hard links are more names for one inode."),
         ("Symbolic links", "A symbolic link stores a path. A relative target is read from the link's folder."),
         ("Evidence", "Rename, look, repair, replace. Each step has a record you can check.")],
        "chapters 13 and 14, File-System Interface and File-System Implementation", ("Lab 4: I/O redirection, pipelines and processes", "Send output to files, connect commands with pipes, and see and stop processes."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: wildcards, quoting, inodes, hard and symbolic links, relative targets and reused names.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the helper, setup, your values and the starting tree.", "start": "lab-open"},
    "s4": {"description": "Guided: names, inodes and links, then the prediction.", "start": "g-open"},
    "s5": {"description": "Core 1 to 3: wildcards, rename and reuse, repair and prove it, then Plus and Challenge.", "start": "c1-open"},
    "s6": {"description": "The live checkpoint: why, the steps with oslab, and what it asks.", "start": "cp-open"},
    "s7": {"description": "Debrief, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: GRUB and shared libraries, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
