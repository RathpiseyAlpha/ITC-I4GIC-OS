"""Lab 2 guide, Linux Navigation and File Management. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

A guide for the lab session, built like the Lab 1 guide (see its gen.py for the instructor's decisions
of 2026-10-08: Ubuntu fonts, a wider canvas, dark terminal windows, folder trees drawn like `tree`).

It starts with the concepts, as the instruction's Concepts First section does: the folder tree from /,
the home directory, absolute and relative paths, . and .., names with spaces and the file and folder
commands. These topics come from the earlier Lab 2 guide (Linux Essentials: Navigation); its pictures
are redrawn here as folder trees and terminal windows, so this guide uses no pictures (images.json is empty).

The lab part follows labs/lab2/lab2-instruction.md: Setup, Guided, Prediction, Core 1 to 3, Plus and
Challenge, the live checkpoint, Debrief and Submit.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import oslib  # noqa: E402  (it puts the shared library on the path)
import decklib  # noqa: E402
from oslib import (h2, para, statement, em, lst, row, col, grid, card, rule, table,  # noqa: E402,F401
                   box, arrow, flow, layers, lanes, OSDeck, setup)

# ---- this guide's own look ------------------------------------------------
UBUNTU = "font-family:'Ubuntu', 'Segoe UI', Arial, sans-serif"
MONO = "font-family:'Ubuntu Mono', 'Courier New', monospace"
decklib.SERIF = decklib.SANS = oslib.SERIF = UBUNTU
decklib.FACES = {
    "ubuntu": {"family": "Ubuntu", "href": "https://fonts.googleapis.com/css2?family=Ubuntu:ital,wght@0,300;0,400;0,500;0,700;1,400&display=swap"},
    "ubuntu-mono": {"family": "Ubuntu Mono", "href": "https://fonts.googleapis.com/css2?family=Ubuntu+Mono:ital,wght@0,400;0,700;1,400&display=swap"},
}

with open(os.path.join(HERE, "size.json"), encoding="utf-8") as f:
    SLIDE_W = json.load(f)["width"]
CW = SLIDE_W - 256  # content width: the canvas minus the two 128px side paddings

WEEK = "Lab 2"
TITLE = "Operating Systems — Lab 2"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-21T09:00:00Z"
BG = "Concepts first"

setup(HERE)
with open(os.path.join(HERE, "dims.json"), encoding="utf-8") as f:
    decklib.DIM.update({k: tuple(v) for k, v in json.load(f).items()})
d = OSDeck(WEEK)
S = d.S


def h3(t, text):
    return f'<h3 style="font-size:32px;font-weight:500;color:{t["accent"]}">{text}</h3>'


def mono(text):
    return f'<span style="{MONO}">{text}</span>'


def tbl(t, headers, rows, weights, width=CW):
    """A table whose column widths are given as weights and scaled to the content width."""
    total = sum(weights)
    widths = [int(width * w / total) for w in weights]
    widths[-1] += width - sum(widths)
    return table(t, headers, rows, widths, width=width)


# ---- terminal windows -------------------------------------------------------
TBG, TBAR, TEDGE = "#10131a", "#222733", "#313849"
TC = dict(out="#c9d1dc", plain="#f2f4f8", cmd="#50fa7b", sudo="#ff6b6b", opt="#7be1f6", string="#f1fa8c",
          op="#ff79c6", path="#82aaff", comment="#8793a8", ph="#ffb86c", user="#50fa7b", dir="#82aaff", line="#8d97aa")
PLACEHOLDERS = ("YOUR_ID", "YOUR_ACCOUNT", "YOUR RELATIVE PATH")
PH = re.compile("(" + "|".join(sorted(map(re.escape, PLACEHOLDERS), key=len, reverse=True)) + ")")
CHAIN = ("|", "||", "&&", ";")
REDIRECT = re.compile(r"^(\d?>>?|<|\d?>&\d|&)$")


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def span(text, color, bold=False, italic=False, back=None):
    style = f"color:{color}"
    if bold:
        style += ";font-weight:700"
    if italic:
        style += ";font-style:italic"
    if back:
        style += f";background:{back}"
    return f'<span style="{style}">{text}</span>'


def token(text, color, bold=False):
    """One word of a command. A placeholder the student must replace is shown in orange."""
    out = []
    for i, part in enumerate(PH.split(text)):
        if part:
            out.append(span(esc(part), TC["ph"] if i % 2 else color, bold or bool(i % 2)))
    return "".join(out)


def command(line):
    """Colour one bash command line: the command, its options, strings, paths and redirections."""
    code, comment = line, ""
    m = re.search(r"\s+#\s.*$", line)
    if m:
        code, comment = line[:m.start()], line[m.start():]
    out, first = [], True
    for tok in re.findall(r"\"[^\"]*\"|'[^']*'|\s+|\S+", code):
        if tok.isspace():
            out.append("&#160;" * len(tok))
        elif tok in CHAIN:
            out.append(span(esc(tok), TC["op"], True))
            first = True
        elif REDIRECT.match(tok):
            out.append(span(esc(tok), TC["op"], True))
        elif tok == "sudo":
            out.append(span(tok, TC["sudo"], True))
        elif first:
            out.append(token(tok, TC["cmd"], True))
            first = False
        elif tok.startswith("-") and len(tok) > 1:
            out.append(token(tok, TC["opt"]))
        elif tok[0] in "\"'":
            out.append(token(tok, TC["string"]))
        elif "/" in tok or tok.startswith("~") or tok.startswith(".."):
            out.append(token(tok, TC["path"]))
        else:
            out.append(token(tok, TC["plain"]))
    if comment:
        out.append(span(esc(comment).replace(" ", "&#160;"), TC["comment"], italic=True))
    return "".join(out)


def prompt(path=None, user="student", host="server"):
    """`$` alone, or the full `user@host:path$` when a path is given."""
    if path is None:
        return span("$", TC["plain"], True) + "&#160;"
    return (span(f"{user}@{host}", TC["user"], True) + span(":", TC["plain"]) + span(esc(path), TC["dir"], True)
            + span("$", TC["plain"]) + "&#160;")


def tline(html, size):
    return f'<p style="{MONO};font-size:{size}px;line-height:1.45;white-space:nowrap;color:{TC["plain"]}">{html}</p>'


def window(title, body, width=None):
    """A terminal window: a title bar with three dots, then the dark body."""
    w = f"width:{width}px;" if width else ""
    dots = "".join(f'<div style="width:18px;height:18px;border-radius:9px;background:{c}"></div>' for c in ("#ff5f56", "#ffbd2e", "#27c93f"))
    return (f'<div style="{w}display:flex;flex-direction:column;border:1px solid {TEDGE};border-radius:20px">'
            f'<div style="background:{TBAR};border-radius:19px 19px 0 0;padding:14px 24px;display:flex;gap:12px;align-items:center">{dots}'
            f'<p style="{UBUNTU};font-size:24px;color:{TC["comment"]};padding-left:12px;white-space:nowrap">{esc(title)}</p></div>'
            f'<div style="background:{TBG};border-radius:0 0 19px 19px;padding:28px 36px;display:flex;flex-direction:column;gap:2px">{body}</div></div>')


def term(t, lines, title="student@server: ~/oslab-work/lab2", size=32, width=None, user="student", host="server"):
    """Lines are commands, or tuples: ("out", text) printed output, ("in", text) something the student types
    at a question, ("cmd", text, path) a command after the full prompt, ("blank",)."""
    rows = []
    for ln in lines:
        if isinstance(ln, str):
            rows.append(tline(prompt() + command(ln), size))
        elif ln[0] == "cmd":
            rows.append(tline(prompt(ln[2], user, host) + command(ln[1]), size))
        elif ln[0] == "out":
            rows.append(tline(span(esc(ln[1]).replace(" ", "&#160;"), TC["out"]), size))
        elif ln[0] == "in":
            rows.append(tline(span("&gt;&#160;", TC["out"]) + span(esc(ln[1]).replace(" ", "&#160;"), TC["string"], True), size))
        else:
            rows.append(tline("&#160;", size))
    return window(title, "".join(rows), width)


def tree(t, root, kids, cmd=None, title="student@server: ~/oslab-work/lab2", size=28, width=None, summary=True, lh=1.4, blank=True):
    """A folder tree drawn like the output of `tree`: names in rows, branch lines as one vector path.
    kids is a list of (name, children); children is None for a file and a list for a folder."""
    H = round(size * lh)
    adv = size / 2          # the width of one character of the monospaced font
    cell, arm = round(4 * adv), round(3 * adv)
    rows, segs, count = [(-1, root, True)], [], {"d": 0, "f": 0}

    def walk(nodes, depth):
        nodes = sorted(nodes, key=lambda n: re.sub(r"[^a-z0-9]", "", n[0].lower()))  # as `tree` sorts them
        x = round(depth * cell + adv / 2)
        top, mid = len(rows) * H, 0
        for name, sub in nodes:
            mid = len(rows) * H + H // 2
            rows.append((depth, name, sub is not None))
            count["d" if sub is not None else "f"] += 1
            segs.append(f"M{x} {mid}H{x + arm}")
            if sub:
                walk(sub, depth + 1)
        segs.append(f"M{x} {top}V{mid}")

    walk(kids, 0)
    names = []
    for depth, name, is_dir in rows:
        text = token(name, TC["dir"], True) if is_dir else token(name, TC["plain"])
        names.append(f'<p style="{MONO};font-size:{size}px;line-height:{H}px;height:{H}px;white-space:nowrap;'
                     f'padding-left:{(depth + 1) * cell}px">{text}</p>')
    w, h = (max(r[0] for r in rows) + 2) * cell, len(rows) * H
    art = (f'<svg aria-label="Branch lines of the folder tree" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
           f'style="position:absolute;left:0;top:0;width:{w}px;height:{h}px">'
           f'<path d="{"".join(segs)}" stroke="{TC["line"]}" stroke-width="2" fill="none"/></svg>')
    body = tline(prompt() + command(cmd), size) if cmd else ""
    body += f'<div style="position:relative;display:flex;flex-direction:column">{art}{"".join(names)}</div>'
    if summary:
        nd, nf = count["d"], count["f"]
        text = f'{nd} director{"y" if nd == 1 else "ies"}, {nf} file{"" if nf == 1 else "s"}'
        body += (tline("&#160;", size) if blank else "") + tline(span(text, TC["out"]), size)
    return window(title, body, width)


HALF = (CW - 32) // 2

# ---- opening --------------------------------------------------------------
d.cover("Linux Navigation and File Management",
        "Lab 2 guide: concepts first, then move and copy files with your own paths.",
        size=96)

d.slide("objectives", "Learning objectives", lambda t: row(
    lst(t, ["Move around with absolute and relative paths, and explain . and ..",
            "Build a folder tree, then move and copy files without changing their contents.",
            "Find the cause of a path error and prove that a copy is identical."], ordered=True, size=36, flex=3),
    card(t, "Lab 2", "First the concepts, with examples. Then the lab on the server: Core for everyone, Plus and Challenge if you finish early, and a live checkpoint.", label="THIS LAB", flex=2),
    gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "How do you tell a friend exactly where a file is?",
         "From the top of the disk, or from where your friend is now? Linux has a name for each: an absolute path and a relative path.")

# ---- concepts first (kept and redrawn from the earlier Lab 2 guide) ----------
d.opener("bg-open", "CONCEPTS FIRST", "Files, folders and paths", "The ideas this lab uses, each with an example.")

d.slide("files", "Everything is a file",
        lambda t: row(lst(t, ["Files store data: text, pictures, programs.",
                              "A directory is a special file that holds other files. Windows and macOS call it a folder. The two words mean the same thing.",
                              "Directories inside directories make a tree.",
                              "Many Linux servers have no desktop, so you manage files from the command line."], size=34, flex=3),
                      card(t, "Why learn it here?", "Every later lab works in folders on the server. If you can say where a file is, you can reach it from anywhere.", label="FOR THE WHOLE COURSE", pad=40, title_size=36, flex=2),
                      gap=48, align="stretch"),
        label=BG)

d.slide("one-tree", "One tree, not one per drive",
        lambda t: row(col(h3(t, "Windows: one tree for each drive"),
                          tree(t, "This PC", [("C:", [("Program Files", []), ("Users", []), ("Windows", [])]),
                                              ("D:", [("Data", [])]), ("E: (USB stick)", [("Photos", [])])],
                               title="Windows", summary=False, size=30),
                          gap=20, flex=None),
                      col(h3(t, "Linux: one tree that starts at /"),
                          tree(t, "/", [("bin", []), ("etc", []), ("home", [("student", [])]),
                                        ("media", [("usb", [])]), ("tmp", []), ("usr", [])],
                               title="Linux", summary=False, size=30),
                          gap=20, flex=None),
                      gap=64, align="flex-start"),
        note="The top of the Linux tree is the root, written /. A USB stick appears as a folder in the same tree, for example under /media.",
        label=BG)

FS_LEVEL1 = ("bin", "boot", "dev", "etc", "home", "lib", "media", "tmp", "usr")


def fs_svg(accent, ink, fill, edge, line, back=None, width=1800):
    """The Linux folder tree drawn top-down: the root / at the top, its folders in a row below, and the path
    /home/student/oslab-work/lab2 marked in the accent colour. Used on a slide and saved for the instruction."""
    bh, top = 60, 18                      # box height; room above the first row for the folder tabs
    nodes = {"root": ("/", 900, 0, True)}
    for i, name in enumerate(FS_LEVEL1):
        nodes[name] = (name, 100 + i * 200, 140, name == "home")
    nodes.update({"other": ("another-student", 760, 280, False), "student": ("student", 1040, 280, True),
                  "docs": ("Documents", 820, 420, False), "down": ("Downloads", 1060, 420, False),
                  "work": ("oslab-work", 1300, 420, True), "lab2": ("lab2", 1300, 560, True)})
    family = {"root": FS_LEVEL1, "home": ("other", "student"), "student": ("docs", "down", "work"), "work": ("lab2",)}

    def bottom(key):
        return nodes[key][2] + top + bh

    plain, hot = [], []
    for parent, kids in family.items():
        px, py = nodes[parent][1], bottom(parent)
        mid = nodes[kids[0]][2] + top - 40
        xs = [nodes[k][1] for k in kids]
        plain.append(f"M{px} {py}V{mid}M{min(xs + [px])} {mid}H{max(xs + [px])}")
        for k in kids:
            plain.append(f"M{nodes[k][1]} {mid}V{nodes[k][2] + top}")
            if nodes[k][3]:
                hot.append(f"M{px} {py}V{mid}H{nodes[k][1]}V{nodes[k][2] + top}")

    parts = []
    if back:
        parts.append(f'<rect x="0" y="0" width="{width}" height="{top + 560 + bh + 4}" fill="{back}"/>')
    parts.append(f'<path d="{"".join(plain)}" stroke="{line}" stroke-width="3" fill="none"/>')
    parts.append(f'<path d="{"".join(hot)}" stroke="{accent}" stroke-width="6" fill="none"/>')
    for label, cx, y, on in nodes.values():
        w = max(150, len(label) * 15 + 44)
        x, y = cx - w // 2, y + top
        box, text = (accent, "#ffffff") if on else (fill, ink)
        parts.append(f'<rect x="{x + 12}" y="{y - 12}" width="48" height="20" rx="5" fill="{box}" stroke="{accent if on else edge}" stroke-width="2"/>'
                     f'<rect x="{x}" y="{y}" width="{w}" height="{bh}" rx="10" fill="{box}" stroke="{accent if on else edge}" stroke-width="2"/>'
                     f'<text x="{cx}" y="{y + 40}" text-anchor="middle" font-family="Ubuntu Mono, DejaVu Sans Mono, Consolas, monospace" '
                     f'font-size="{34 if label == "/" else 28}" font-weight="{700 if on else 400}" fill="{text}">{label}</text>')
    h = top + 560 + bh + 4
    return (f'<svg xmlns="http://www.w3.org/2000/svg" aria-label="The Linux folder tree with the root / at the top. Below it: '
            f'{", ".join(FS_LEVEL1)}. Below home: another-student and student. Below student: Documents, Downloads and oslab-work. '
            f'Below oslab-work: lab2. The path from / to lab2 is marked." viewBox="0 0 {width} {h}" width="{width}" height="{h}" '
            f'style="width:{width}px;height:{h}px">{"".join(parts)}</svg>')


if os.environ.get("GUIDE_REPO"):
    # The same picture for the instruction, on a white card so it reads on light and dark GitHub pages.
    _fig = os.path.join(os.environ["GUIDE_REPO"], "labs", "lab2", "figures")
    os.makedirs(_fig, exist_ok=True)
    with open(os.path.join(_fig, "linux-tree.svg"), "w", encoding="utf-8") as _f:
        _f.write(fs_svg("#1f5fbf", "#1b2a41", "#eef3fb", "#9db4d6", "#8d97aa", back="#ffffff") + "\n")

FS_ROOT = ("bin", "boot", "cdrom", "dev", "etc", "home", "lib", "lib64", "lost+found", "media", "mnt", "opt",
           "proc", "root", "run", "sbin", "snap", "srv", "sys", "tmp", "usr", "var")
FS_LINKS = ("bin", "lib", "lib64", "sbin")  # links into /usr on Ubuntu


def fit(label, box):
    """Squeeze a long label into its box, because a browser without Ubuntu Mono uses a wider font."""
    return f' textLength="{box - 16}" lengthAdjust="spacingAndGlyphs"' if len(label) * 15 > box - 16 else ""


def fs_root_svg(accent, ink, fill, edge, line, back=None, width=1800):
    """Every folder in / of the course server (Ubuntu 26.04), drawn top-down with the root at the top:
    twelve in the first row and ten in the second. Links into /usr have a dashed border."""
    slot, bw, bh, top = 150, 136, 56, 18
    rows = (FS_ROOT[:12], FS_ROOT[12:])
    row_y, bus_y = (150, 320), (110, 280)
    trunk = width // 2                      # passes through the gap between the sixth and seventh box
    parts, lines = [], [f"M{trunk} {top + 64}V{bus_y[1] + top}"]
    boxes = []
    for r, names in enumerate(rows):
        first = (width - len(names) * slot) // 2
        xs = [first + i * slot + slot // 2 for i in range(len(names))]
        y = row_y[r] + top
        lines.append(f"M{xs[0]} {bus_y[r] + top}H{xs[-1]}")
        for name, cx in zip(names, xs):
            lines.append(f"M{cx} {bus_y[r] + top}V{y}")
            boxes.append((name, cx, y))
    if back:
        parts.append(f'<rect x="0" y="0" width="{width}" height="{row_y[1] + top + bh + 70}" fill="{back}"/>')
    parts.append(f'<path d="{"".join(lines)}" stroke="{line}" stroke-width="3" fill="none"/>')
    font = 'font-family="Ubuntu Mono, DejaVu Sans Mono, Consolas, monospace"'
    parts.append(f'<rect x="{trunk - 60}" y="{top}" width="120" height="64" rx="10" fill="{accent}" stroke="{accent}" stroke-width="2"/>'
                 f'<text x="{trunk}" y="{top + 45}" text-anchor="middle" {font} font-size="38" font-weight="700" fill="#ffffff">/</text>')
    for name, cx, y in boxes:
        dash = ' stroke-dasharray="8 6"' if name in FS_LINKS else ""
        x = cx - bw // 2
        parts.append(f'<rect x="{x + 10}" y="{y - 11}" width="44" height="18" rx="5" fill="{fill}" stroke="{edge}" stroke-width="2"{dash}/>'
                     f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="10" fill="{fill}" stroke="{edge}" stroke-width="2"{dash}/>'
                     f'<text x="{cx}" y="{y + 37}" text-anchor="middle" {font} font-size="{20 if back and fit(name, bw) else 24}" fill="{ink}"{fit(name, bw)}>{name}</text>')
    ly = row_y[1] + top + bh + 48
    parts.append(f'<rect x="{trunk - 330}" y="{ly - 26}" width="60" height="34" rx="8" fill="{fill}" stroke="{edge}" stroke-width="2" stroke-dasharray="8 6"/>'
                 f'<text x="{trunk - 255}" y="{ly}" {font} font-size="24" fill="{ink}">a link: bin, lib, lib64 and sbin lead into /usr</text>')
    h = row_y[1] + top + bh + 70
    return (f'<svg xmlns="http://www.w3.org/2000/svg" aria-label="Every folder in the root directory of the course server, with / at the top: '
            f'{", ".join(FS_ROOT)}. bin, lib, lib64 and sbin are links into /usr." viewBox="0 0 {width} {h}" width="{width}" height="{h}" '
            f'style="width:{width}px;height:{h}px">{"".join(parts)}</svg>')


FS_ROOT_ROWS = [
    ("/bin", "Link to /usr/bin: the programs everybody uses, such as ls, cp and mv"),
    ("/boot", "The kernel and the files that start the system"),
    ("/cdrom", "Where an installation disc appears. Left over from installing Ubuntu"),
    ("/dev", "Devices shown as files: disks, terminals, /dev/null"),
    ("/etc", "Settings of the system (configuration files), for example /etc/passwd"),
    ("/home", "One home folder for each user"),
    ("/lib, /lib64", "Links to /usr/lib and /usr/lib64: libraries that programs need"),
    ("/lost+found", "Pieces of files rescued by a disk check. Only root can open it"),
    ("/media", "USB sticks and DVDs appear here when they are plugged in"),
    ("/mnt", "A place where the administrator attaches a disk for a while"),
    ("/opt", "Optional software installed outside the package manager"),
    ("/proc", "Not on the disk: the kernel shows running processes here, for example /proc/cpuinfo"),
    ("/root", "The home of the administrator account, root. It is not the root /"),
    ("/run", "Information about the system since it started. Kept in memory"),
    ("/sbin", "Link to /usr/sbin: programs for the administrator"),
    ("/snap", "Software installed as snap packages (Ubuntu)"),
    ("/srv", "Data that this server offers, for example a website"),
    ("/sys", "Not on the disk: the kernel shows devices and its settings here"),
    ("/tmp", "Temporary files. Every user may write here. Emptied at restart"),
    ("/usr", "Installed software: programs in /usr/bin, libraries in /usr/lib, documents in /usr/share"),
    ("/var", "Data that changes: logs in /var/log, mail, caches"),
    ("swap.img", "A file, not a folder: disk space used as extra memory (swap)"),
]

if os.environ.get("GUIDE_REPO"):
    with open(os.path.join(os.environ["GUIDE_REPO"], "labs", "lab2", "figures", "linux-root.svg"), "w", encoding="utf-8") as _f:
        _f.write(fs_root_svg("#1f5fbf", "#1b2a41", "#eef3fb", "#9db4d6", "#8d97aa", back="#ffffff") + "\n")

d.slide("fs-root", "Every folder in /, with the root at the top",
        lambda t: fs_root_svg(t["accent"], "#1b2a41", "#ffffff", "#9db4d6", "#8d97aa"),
        note="This is ls / on the course server. Ubuntu made all of them when it was installed; the next three slides say what each one is for.",
        label=BG, gap=24)

for _part, _rows in (("1 of 3", FS_ROOT_ROWS[:8]), ("2 of 3", FS_ROOT_ROWS[8:15]), ("3 of 3", FS_ROOT_ROWS[15:])):
    d.slide(f"fs-what-{_part[0]}", f"What each folder is for ({_part})",
            lambda t, rows=_rows: tbl(t, ["In /", "What it is for"], [[mono(a), b] for a, b in rows], [2, 9]),
            label=BG, gap=24)

d.slide("main", "The folders you meet in this course",
        lambda t: tbl(t, ["Folder", "What it holds"],
                      [[mono("/"), "The root: everything is below it"],
                       [mono("/bin"), "Programs everybody can run: ls, cp, mv and the others"],
                       [mono("/etc"), "Settings of the system (configuration files)"],
                       [mono("/home"), "One home folder for each user"],
                       [mono("/tmp"), "Temporary files, deleted at restart"],
                       [mono("/usr"), "Installed software"],
                       [mono("/media"), "Disks and USB sticks"]],
                      [1, 4]),
        note="ls / shows the real list. It is longer; these are the ones you need now.",
        label=BG)

d.slide("fs-picture", "The tree, with the root at the top",
        lambda t: fs_svg(t["accent"], t["ink"] if "ink" in t else "#1b2a41", "#ffffff", "#9db4d6", "#8d97aa"),
        note="Follow the blue line down from the root: it is the path /home/student/oslab-work/lab2, your lab folder.",
        label=BG, gap=24)

HOME_TREE = [("bin", []), ("etc", []),
             ("home", [("another-student", []),
                       ("student", [("Documents", []), ("Downloads", []), ("oslab-work", [("lab2", [])])])]),
             ("tmp", [])]

d.slide("home", "Your home directory",
        lambda t: row(tree(t, "/", HOME_TREE, title="student@server: /", summary=False, size=30),
                      col(para(t, "Every account has its own home: /home/ followed by the account name. When you log in, you start there.", size=32, tone="ink"),
                          tbl(t, ["You write", "It means"],
                              [[mono("/home/student"), "The full name of the home of student"],
                               [mono("~"), "Your own home, whoever you are"],
                               [mono("$HOME"), "The same, as a shell variable"]],
                              [2, 5], width=1040),
                          para(t, "You may create files only in your home and in /tmp. Your lab folder is ~/oslab-work/lab2.", size=30),
                          gap=28),
                      gap=56, align="center"),
        label=BG)

d.slide("tilde", "The prompt shows where you are",
        lambda t: row(term(t, [("cmd", "pwd", "~"), ("out", "/home/student"),
                               ("cmd", "cd /etc", "~"),
                               ("cmd", "pwd", "/etc"), ("out", "/etc"),
                               ("cmd", "cd", "/etc"),
                               ("cmd", "pwd", "~"), ("out", "/home/student")],
                           title="student@server: ~"),
                      col(para(t, "The prompt shows ~ while you are at home, and the real folder when you are somewhere else.", size=34, tone="ink"),
                          para(t, "pwd prints the full name of the folder you are in.", size=32),
                          para(t, "cd with nothing after it takes you home from anywhere.", size=32),
                          gap=24),
                      gap=56, align="center"),
        label=BG)

d.slide("path", "What is a path?",
        lambda t: flow(t, [("/", "the root"), ("home", "the folder of all homes"), ("student", "the home of student"),
                           ("Documents", "a folder in that home")], 400, hot=3),
        lambda t: row(rule(t, "The path", "/home/student/Documents: the folders you walk through, from the left.", title_size=36),
                      rule(t, "The / sign", "At the start it is the root. Between two names it separates one folder from the next.", title_size=36),
                      rule(t, "A file at the end", "/home/student/Documents/cv.txt is the file cv.txt in the folder Documents.", title_size=36)),
        label=BG, gap=64)

d.slide("absolute", "Absolute paths start at the root",
        lambda t: row(term(t, [("cmd", "cd /home/student/Documents", "/etc"),
                               ("cmd", "pwd", "~/Documents"), ("out", "/home/student/Documents")],
                           title="student@server: /etc"),
                      col(para(t, "An absolute path starts with /.", size=36, tone="ink"),
                          para(t, "It starts at the root, so it means the same place from anywhere: here the command works from /etc, and it would work the same from any other folder.", size=32),
                          gap=24),
                      gap=56, align="center"),
        label=BG)

d.slide("relative", "Relative paths start where you are",
        lambda t: row(term(t, [("cmd", "cd Documents", "~"),
                               ("cmd", "pwd", "~/Documents"), ("out", "/home/student/Documents"),
                               ("blank",),
                               ("cmd", "cd Documents", "/etc"),
                               ("out", "bash: cd: Documents: No such file or directory")],
                           title="student@server: ~"),
                      col(para(t, "A relative path does not start with /.", size=36, tone="ink"),
                          para(t, "It starts from the folder you are in now, which pwd shows. From your home, Documents is there. From /etc, it is not.", size=32),
                          gap=24),
                      gap=56, align="center"),
        label=BG)

EXAMPLE_TREE = [("Documents", [("School", [("Art", [("poster.txt", None)]), ("Math", [("homework.txt", None)])])]),
                ("Downloads", [("photo.jpg", None)])]

d.slide("example", "An example tree",
        lambda t: row(tree(t, "/home/student", EXAMPLE_TREE, cmd="tree", title="student@server: ~", size=30),
                      col(para(t, "The next slides use this tree in the home of student.", size=34, tone="ink"),
                          para(t, "It is not the lab's tree. In the lab you use the same ideas on your own folders.", size=32),
                          gap=24),
                      gap=64, align="center"),
        label=BG)

d.slide("table", "The same files, from different folders",
        lambda t: tbl(t, ["You are in (pwd)", "You want", "Absolute path", "Relative path"],
                      [[mono("/home/student"), mono("poster.txt"), mono("/home/student/Documents/School/Art/poster.txt"), mono("Documents/School/Art/poster.txt")],
                       [mono("/home/student/Documents/School"), mono("poster.txt"), mono("/home/student/Documents/School/Art/poster.txt"), mono("Art/poster.txt")],
                       [mono("/home/student/Documents/School/Math"), mono("poster.txt"), mono("/home/student/Documents/School/Art/poster.txt"), mono("../Art/poster.txt")],
                       [mono("/home/student/Documents/School/Art"), mono("photo.jpg"), mono("/home/student/Downloads/photo.jpg"), mono("../../../Downloads/photo.jpg")]],
                      [9, 4, 11, 8]),
        note="The absolute path is the same in every row. The relative path changes, because it starts from where you are.",
        label=BG)

d.slide("dotdot", "Two dots: one level up",
        lambda t: row(tree(t, "/home/student", EXAMPLE_TREE, title="student@server: ~", summary=False, size=28),
                      col(term(t, [("cmd", "cd ..", "~/Documents/School/Art"),
                                   ("cmd", "pwd", "~/Documents/School"), ("out", "/home/student/Documents/School"),
                                   ("cmd", "cd ../../Downloads", "~/Documents/School"),
                                   ("cmd", "pwd", "~/Downloads"), ("out", "/home/student/Downloads")],
                               title="you start in Art", size=28),
                          para(t, "Each .. goes up one folder from where you are now. From School, ../.. is /home/student.", size=30),
                          gap=24, flex=None),
                      gap=48, align="center"),
        note=".. does not mean your home or the lab folder. It always counts from the folder you are in.",
        label=BG)

d.slide("special", "Four special names",
        lambda t: tbl(t, ["Name", "Means", "Example"],
                      [[mono("."), "The folder you are in now", mono("cp /tmp/a.txt .") + "  copies a.txt here"],
                       [mono(".."), "The folder one level above", mono("cd ..") + "  goes up one level"],
                       [mono("../.."), "Two levels above", mono("cd ../..") + "  goes up two levels"],
                       [mono("~"), "Your home", mono("cd ~/oslab-work")]],
                      [2, 5, 6]),
        note="ls -a shows . and .. as the first two lines of every folder.",
        label=BG)

d.slide("spaces", "Names with spaces",
        lambda t: row(term(t, ["cat my notes.txt",
                               ("out", "cat: my: No such file or directory"),
                               ("out", "cat: notes.txt: No such file or directory"),
                               "cat 'my notes.txt'",
                               ("out", "hello")], title="student@server: ~"),
                      col(para(t, "The shell splits a command into words at every space. Without quotes, cat receives two names.", size=32, tone="ink"),
                          para(t, "With quotes, the name is one word again.", size=32),
                          para(t, "Double quotes still replace a variable: &quot;$file1&quot; is your file name. Single quotes keep the text exactly as typed.", size=30),
                          gap=24),
                      gap=56, align="center"),
        note="In this lab you also see -- before file names, as in cp -- &quot;$file1&quot; reports/. It means: no more options after this point.",
        label=BG)

d.slide("commands", "File and folder commands",
        lambda t: row(tbl(t, ["Command", "Meaning"],
                          [[mono("pwd"), "Prints the folder you are in"],
                           [mono("ls"), "Lists a folder"],
                           [mono("cd"), "Changes folder"],
                           [mono("mkdir -p"), "Makes a chain of folders"],
                           [mono("touch"), "Makes an empty file"],
                           [mono("cat"), "Shows what is in a file"],
                           [mono("find -type f"), "Lists the files below a folder"]],
                          [2, 5], width=HALF),
                      tbl(t, ["Command", "Meaning"],
                          [[mono("cp"), "Copies a file. The original stays"],
                           [mono("cp -r"), "Copies a folder with all inside"],
                           [mono("mv"), "Moves or renames a file"],
                           [mono("rm"), "Deletes a file. No recycle bin"],
                           [mono("rmdir"), "Deletes an empty folder"],
                           [mono("cmp"), "Compares two files byte by byte"],
                           [mono("nano"), "A text editor in the terminal"]],
                          [2, 5], width=HALF),
                      gap=32),
        note="When the destination of cp or mv is a folder, the file keeps its name inside it. When it is a new name, the file gets that name.",
        label=BG, gap=36)

d.slide("listing", "Listing options",
        lambda t: row(tbl(t, ["You type", "It shows"],
                          [[mono("ls -l"), "Long list: permissions, size, date"],
                           [mono("ls -a"), "Also hidden names, which start with ."],
                           [mono("ls -R"), "Every folder below, too (recursive)"],
                           [mono("ls -lt"), "Newest first"],
                           [mono("ls -lS"), "Largest first"],
                           [mono("ls -lh"), "Sizes like 4.0K"],
                           [mono("ls -ltr"), "-r reverses the order: oldest first"]],
                          [2, 5], width=HALF),
                      term(t, ["ls -R Documents",
                               ("out", "Documents:"), ("out", "School"), ("blank",),
                               ("out", "Documents/School:"), ("out", "Art  Math"), ("blank",),
                               ("out", "Documents/School/Art:"), ("out", "poster.txt"), ("blank",),
                               ("out", "Documents/School/Math:"), ("out", "homework.txt")],
                           title="student@server: ~", size=28, width=HALF),
                      gap=32, align="flex-start"),
        label=BG, gap=36)

d.slide("demo", "Try them together",
        lambda t: row(term(t, [("cmd", "mkdir -p demo/School/Art demo/School/Math", "~"),
                               ("cmd", "cd demo/School", "~"),
                               ("cmd", "echo 'draft' > Art/poster.txt", "~/demo/School"),
                               ("cmd", "cp Art/poster.txt Math/", "~/demo/School"),
                               ("cmd", "mv Math/poster.txt Math/copy.txt", "~/demo/School"),
                               ("cmd", "cmp Art/poster.txt Math/copy.txt", "~/demo/School"),
                               ("cmd", "cd ../..", "~/demo/School")],
                           title="student@server: ~", size=26),
                      col(tree(t, "School", [("Art", [("poster.txt", None)]), ("Math", [("copy.txt", None)])],
                               cmd="tree demo/School", title="the result", size=28),
                          para(t, "cmp printed nothing, so the copy is identical.", size=30),
                          gap=20, flex=None),
                      gap=40, align="center"),
        note="Delete the practice folder with rm -r demo. rm -r deletes a folder and everything in it, with no undo: run pwd first.",
        label=BG)

d.slide("output", "Sending output somewhere else",
        lambda t: tbl(t, ["You type", "What happens"],
                      [[mono("ls &gt; list.txt"), "Saves the output in the file, replacing what was there (Lab 1)"],
                       [mono("ls &gt;&gt; list.txt"), "Adds the output to the end of the file (Lab 1)"],
                       [mono("ls | sort"), "The pipe passes the output to the next command; sort puts the lines in order"],
                       [mono("ls | tee list.txt"), "tee shows the output on the screen and also saves it in the file"]],
                      [2, 7]),
        lambda t: row(term(t, ["find demo -type f | sort | tee files.txt",
                               ("out", "demo/School/Art/poster.txt"),
                               ("out", "demo/School/Math/copy.txt")], title="student@server: ~", size=28),
                      para(t, "Read it from left to right: find lists the files, sort puts them in order, tee shows the list and saves it. You use exactly this in Core 3.", size=30),
                      gap=48, align="center"),
        label=BG, gap=36)

d.slide("nano", "Writing a file with nano",
        lambda t: row(col(term(t, ["nano evidence/paths.txt"], size=30),
                          para(t, "nano is a simple text editor in the terminal. You use it in Core 2 to keep the commands that worked.", size=32),
                          gap=24, flex=None),
                      tbl(t, ["Press", "To"],
                          [["Type or paste", "Write your text"],
                           [mono("Ctrl+O") + ", then " + mono("Enter"), "Save the file"],
                           [mono("Ctrl+X"), "Leave nano"]],
                          [2, 3], width=820),
                      gap=56, align="center"),
        note="The keys are listed at the bottom of the nano screen. The sign ^ means Ctrl.",
        label=BG)

# ---- how the lab works ------------------------------------------------------
d.opener("lab-open", "LAB 2", "Navigation and file management", "Two reports arrived in TechCorp's incoming folder. Put them in the right places, unchanged.")

START_TREE = [("incoming", [("audit notes.txt", None), ("budget 2026.txt", None)]),
              ("reports", [("README.txt", None)]), ("evidence", [])]

d.slide("scenario", "The scenario",
        lambda t: row(col(card(t, "Your job at TechCorp", "Put the two reports in the right places in the company's folders, keep their contents unchanged, and be able to reach them from any department.",
                               label="SCENARIO", pad=40, title_size=36),
                          para(t, "Your two file names are only yours. This guide shows example names.", size=30),
                          gap=28),
                      tree(t, "lab2", START_TREE, cmd="tree", title="student@server: ~/oslab-work/lab2", size=30),
                      gap=56, align="center"))

HALF = (CW - 32) // 2
d.slide("time", "Inside the 120 minutes",
        lambda t: row(tbl(t, ["Minutes", "What happens"],
                          [["0 to 5", "Setup"],
                           ["5 to 20", "Concepts, then guided: where am I?"],
                           ["20 to 30", "Prediction, then class discussion"],
                           ["30 to 40", "Core 1: build the company folders"],
                           ["40 to 65", "Core 2: move and copy with your own paths"]],
                          [1, 3], width=HALF),
                      tbl(t, ["Minutes", "What happens"],
                          [["65 to 75", "Core 3: prove it"],
                           ["75 to 90", "Plus and Challenge, or finish Core"],
                           ["90 to 105", "Live checkpoint"],
                           ["105 to 115", "Debrief"],
                           ["115 to 120", "Submit"]],
                          [1, 3], width=HALF),
                      gap=32),
        gap=36)

d.slide("helper", "Six helper commands, and why you use them",
        lambda t: tbl(t, ["Command", "What it does", "Why"],
                      [[mono("oslab values lab2"), "Shows your file names and folders", "Your work is different from your neighbour's"],
                       [mono("oslab predict lab2"), "Saves your prediction once", "Guessing first makes you think. The first answer is kept"],
                       [mono("oslab hint lab2 1"), "A hint, levels 1 to 3", "You get unstuck without waiting, at no cost"],
                       [mono("oslab check lab2"), "Looks at your folders, shows milestones", "You see at once what is still missing"],
                       [mono("oslab checkpoint lab2"), "A short test near the end", "It shows what you can do alone"],
                       [mono("oslab debrief lab2"), "After the lab: the right answers to your prediction", "It shows what you corrected, and it is marked"]],
                      [5, 6, 8]))

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Core, Plus, Challenge", "Core is for everyone. Plus and Challenge are for students who finish early. Full marks need only Core and the checkpoint.", title_size=36),
                      rule(t, "AI tools", "Allowed in Core, Plus and Challenge, so test what they tell you. Not allowed in the prediction and the checkpoint.", title_size=36),
                      rule(t, "Core 2", "Nobody gives you the commands there. You write every path yourself. Hints cost no points.", title_size=36)),
        note="A wrong prediction costs nothing. It is marked for being made and corrected, not for being right.")

d.slide("start", "Setup: start the lab",
        lambda t: row(term(t, ['export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                               "oslab start lab2",
                               'cd "$OSLAB_WORKSPACE/lab2"',
                               "mkdir -p evidence",
                               "oslab values lab2"], title="student@server: ~", size=28),
                      col(lst(t, ["The first line sets the variable OSLAB_WORKSPACE to ~/oslab-work, unless it is already set. export lets oslab see it. Type it as it is.",
                                  "oslab start lab2 makes the lab folder with your two reports.",
                                  "cd takes you into it.",
                                  "oslab values lab2 prints your own names. The next slide shows what to do with them."], size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("values", "Your values, kept in variables",
        lambda t: row(col(h3(t, "1. The command prints your values"),
                          term(t, ["oslab values lab2",
                                   ("out", "Your personal values for lab2 (your-account):"),
                                   ("out", "  file1    = budget 2026.txt"),
                                   ("out", "  file2    = audit notes.txt"),
                                   ("out", "  owner    = Finance"),
                                   ("out", "  reader   = HR"),
                                   ("out", "  third    = Support")], title="example: your values will be different", size=28),
                          gap=20, flex=None),
                      col(h3(t, "2. Type them into shell variables"),
                          term(t, ["file1='budget 2026.txt'",
                                   "file2='audit notes.txt'",
                                   "owner=Finance",
                                   "reader=HR",
                                   "third=Support"], title="type your own values", size=28),
                          para(t, "Write name=value with no spaces around =. Keep the quotes: your file names have a space. In a new terminal, set them again.", size=28),
                          gap=20, flex=None),
                      gap=48, align="flex-start"))

d.slide("placeholders", "Variables and placeholders",
        lambda t: tbl(t, ["The instruction says", "With the example values, you type", "Or, with the variable"],
                      [[mono("ls -l &quot;incoming/$file1&quot;"), mono("ls -l 'incoming/budget 2026.txt'"), mono("ls -l &quot;incoming/$file1&quot;")],
                       [mono("TechCorp/&lt;owner&gt;/"), mono("TechCorp/Finance/"), mono("&quot;TechCorp/$owner/&quot;")],
                       [mono("TechCorp/&lt;reader&gt;/"), mono("TechCorp/HR/"), mono("&quot;TechCorp/$reader/&quot;")]],
                      [1, 1, 1]),
        lambda t: row(rule(t, "&quot;$file1&quot;", "The shell replaces it with your first file name, and the double quotes keep it one word.", title_size=36),
                      rule(t, "&lt;owner&gt;", "A placeholder: never type the angle brackets. Type your own value, or the variable in double quotes.", title_size=36)),
        gap=48)

# ---- guided -----------------------------------------------------------------
d.opener("g-open", "GUIDED", "Where am I?", "Type along with the instructor.")

d.slide("g-look", "Steps 1 and 2: look, then practise",
        lambda t: row(term(t, ["pwd", "ls", "ls -la",
                               ("blank",),
                               "mkdir -p practice/notes",
                               "echo 'orientation' > 'practice/welcome note.txt'",
                               "cd practice",
                               "pwd",
                               "cp -- 'welcome note.txt' notes/",
                               "cat 'notes/welcome note.txt'",
                               "cd ..",
                               "pwd"], size=28),
                      col(para(t, "pwd prints an absolute path: it starts with /.", size=32),
                          para(t, "In ls -la, the first two lines are . and .., this folder and the one above.", size=32),
                          para(t, "echo with &gt; writes the text into a new file. -- after cp means: no more options. cd .. goes to the parent.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-two", "Steps 3 and 4: two paths, and the quotes",
        lambda t: row(col(h3(t, "3. One file, two paths"),
                          term(t, ["cat 'practice/welcome note.txt'",
                                   'cat "$OSLAB_WORKSPACE/lab2/practice/welcome note.txt"'], size=26),
                          para(t, "Which of the two stops working if you cd somewhere else?", size=30),
                          gap=20, flex=None),
                      col(h3(t, "4. Why the quotes matter"),
                          term(t, ['ls -l "incoming/$file1"',
                                   "ls -l incoming/$file1"], size=26),
                          para(t, "The second command fails. Read its error: which names did ls receive?", size=30),
                          gap=20, flex=None),
                      gap=40, align="flex-start"),
        note="Without the double quotes, the shell splits the name at its space, so ls looks for two files that do not exist.")

# ---- prediction -------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Five questions, before you move any report.")

d.slide("predict", "Five questions, before the experiment",
        lambda t: row(lst(t, ["You are in incoming/. Type the relative path of the reports directory.",
                              "You change to the lab folder. Does that path still point to reports?",
                              "After mv 'incoming/&lt;file1&gt;' reports/, how many files with that name are in the lab folder tree?",
                              "Then after cp 'reports/&lt;file1&gt;' TechCorp/&lt;owner&gt;/, how many are there?",
                              "One sentence: why did you answer like this?"], ordered=True, size=32, flex=3),
                      col(term(t, ["oslab predict lab2"]),
                          card(t, "The rules", "Alone, and without AI. The first answer is the one that counts. A wrong guess costs nothing.", label="PREDICTION", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"),
        note="The class then looks at the spread of answers together, without names.")

# ---- core -------------------------------------------------------------------
d.opener("c1-open", "CORE 1", "Build the company folders", "Ten minutes. Then you read the two reports.")

COMPANY = [("Finance", [("archive", [])]), ("HR", []), ("Support", [])]

d.slide("c1", "Make the departments, read the reports",
        lambda t: row(term(t, ['cd "$OSLAB_WORKSPACE/lab2"',
                               'mkdir -p "TechCorp/$owner/archive" "TechCorp/$reader" "TechCorp/$third"',
                               "find TechCorp -type d",
                               'cat "incoming/$file1" "incoming/$file2"'], size=26),
                      col(tree(t, "TechCorp", COMPANY, cmd="tree TechCorp", title="with the example values", size=28),
                          para(t, "find -type d lists only folders. cat with two names shows one file, then the other: write down what they contain.", size=28),
                          gap=20, flex=None),
                      gap=40, align="center"))

d.opener("c2-open", "CORE 2", "Move and copy with your own paths", "Nobody gives you the commands here. You write every path yourself.")

d.slide("c2-steps", "Six steps",
        lambda t: row(lst(t, ["Go into incoming/. Move your first file to reports/ with a relative destination.",
                              "Go back to the lab folder. Move your second file to reports/ with absolute paths for both source and destination.",
                              "Copy both reports from reports/ into TechCorp/&lt;owner&gt;/. The originals stay in reports/.",
                              "Copy your first report into TechCorp/&lt;owner&gt;/archive/ as first-original.txt.",
                              "Go into TechCorp/&lt;reader&gt;/. Read the first report in the owner department: once relative, once absolute.",
                              "Your decision: for step 3, relative or absolute? Write which, and when the other would be better."], ordered=True, size=29, flex=3),
                      col(card(t, "Before every mv or cp", "Run pwd. Then draw where you are and where the file must go.", label="HABIT", pad=32, title_size=32),
                          card(t, "evidence/paths.txt", "Write every command that worked into it, with nano evidence/paths.txt from the lab folder.", label="RECORD", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=40, align="stretch"),
        note="Absolute paths here start with &quot;$OSLAB_WORKSPACE/lab2/...&quot;. Stuck for five minutes? oslab hint lab2 1, then 2, then 3.")

GOAL_TREE = [("TechCorp", [("Finance", [("archive", [("first-original.txt", None)]), ("audit notes.txt", None), ("budget 2026.txt", None)]),
                           ("HR", []), ("Support", [])]),
             ("evidence", [("paths.txt", None)]),
             ("incoming", []),
             ("reports", [("audit notes.txt", None), ("budget 2026.txt", None), ("README.txt", None)])]

d.slide("c2-goal", "Where the files must end up",
        lambda t: row(tree(t, "lab2", GOAL_TREE, cmd="tree", title="student@server: ~/oslab-work/lab2", size=24, lh=1.2, summary=False),
                      col(para(t, "After Core 2 your folder has this shape, with your own names.", size=32, tone="ink"),
                          para(t, "incoming/ is empty: mv took the files out of it. Your practice/ folder from the guided part is there too.", size=30),
                          para(t, "Each report is now in reports/ and in TechCorp/&lt;owner&gt;/: cp left the original in place.", size=30),
                          gap=24),
                      gap=56, align="center"),
        gap=28)

d.opener("c3-open", "CORE 3", "Prove it", "A name in ls does not prove that the contents are the same.")

d.slide("c3-cmp", "Step 1: prove that the copies are identical",
        lambda t: row(col(term(t, ['cd "$OSLAB_WORKSPACE/lab2"',
                                   'cmp -- "reports/$file1" "TechCorp/$owner/$file1"',
                                   'cmp -- "reports/$file2" "TechCorp/$owner/$file2"'], size=28),
                          term(t, ["cmp -- a.txt b.txt",
                                   ("out", "a.txt b.txt differ: byte 1, line 1")], title="only if a copy is wrong", size=28),
                          gap=24, flex=None),
                      col(rule(t, "You should see nothing", "cmp prints nothing when two files are identical. Silence means success.", title_size=36),
                          rule(t, "If cmp says differ", "That copy is not the same. Copy it again from reports/ (Core 2, step 3) and compare again.", title_size=36),
                          gap=32),
                      gap=48, align="center"),
        note="A name in ls does not prove the contents are the same. cmp compares the bytes.")

d.slide("c3-error", "Step 2: make one path error on purpose",
        lambda t: row(col(term(t, [("cmd", 'cd "TechCorp/$reader"', "~/oslab-work/lab2"),
                                   ("cmd", "pwd", "~/oslab-work/lab2/TechCorp/HR"),
                                   ("out", "/home/student/oslab-work/lab2/TechCorp/HR"),
                                   ("cmd", 'cat "reports/$file1"', "~/oslab-work/lab2/TechCorp/HR"),
                                   ("out", "cat: 'reports/budget 2026.txt': No such file or directory")],
                               title="example: your names will be different", size=26),
                          para(t, "You use the path that works from the lab folder, but you are in your reader department. The file exists, yet cat cannot find it.", size=30),
                          gap=24, flex=None),
                      col(h3(t, "Then write it down"),
                          term(t, ["nano ../../evidence/paths.txt"], title="from your reader department", size=28),
                          para(t, "Find the path that does work from here, and test it with cat. Then add two lines at the end:", size=28),
                          window("evidence/paths.txt", tline(span("Error: cat: 'reports/budget 2026.txt': No such", TC["plain"]), 24)
                                 + tline(span("&#160;" * 7 + "file or directory", TC["plain"]), 24)
                                 + tline(span("Fix: the relative path that worked", TC["ph"], True), 24)),
                          gap=20, flex=None),
                      gap=40, align="center"),
        note="After Fix: write only the path, without cat. oslab check tests both lines.")

d.slide("c3-check", "Step 3: save the list, then check",
        lambda t: row(term(t, ['cd "$OSLAB_WORKSPACE/lab2"',
                               "find incoming reports TechCorp -type f | sort | tee evidence/tree.txt",
                               "oslab check lab2"], size=26),
                      para(t, "find lists the files, sort orders them, tee shows the list and saves it in tree.txt. incoming lists nothing: mv emptied it.", size=28),
                      gap=40, align="center"),
        lambda t: col(term(t, [("out", "PASS: both files were moved into reports/ with their contents"),
                               ("out", "PASS: TechCorp/Finance/ holds identical copies"),
                               ("out", "PASS: archive/first-original.txt is a copy of your first file"),
                               ("out", "PASS: evidence/paths.txt records a relative and an absolute path"),
                               ("out", "PASS: evidence/paths.txt has your Error: line and a Fix: path that works from your reader department"),
                               ("out", "milestones: 5/5")], title="what oslab check lab2 should show after the list", size=24),
                      gap=16),
        note="A TRY line names what is still missing: fix that part and check again. Core is complete at 5/5.",
        gap=24)

d.slide("early", "If you finish early",
        lambda t: row(card(t, "Plus: find the lost file", "Make the mess folders. From mess/c, without cd, move lost file.txt here as found.txt in one command. From mess/a/b, copy it to your third department with a relative path. How many .. did you need?",
                           label="evidence/plus.txt", icon_name="Search", pad=40, title_size=36),
                      card(t, "Challenge: one command with *", "* stands for any characters, so *.txt is every name ending in .txt. Copy them all into your third department with one command. Why does it fail with quotes around *.txt? Does it copy reports/.hidden.txt?",
                           label="evidence/challenge.txt", icon_name="Lightbulb", pad=40, title_size=36),
                      gap=24, align="stretch"),
        note="Neither is needed for full marks. They are noted in your feedback.")

# ---- checkpoint -------------------------------------------------------------
d.opener("cp-open", "LIVE CHECKPOINT", "Show what you can do alone", "Fifteen minutes near the end of the lab. Worth 3 of the 10 points.")

d.slide("cp-why", "Why is there a checkpoint?",
        lambda t: grid(card(t, "It shows what you can do alone", "For most of the lab you may use hints and AI tools. The checkpoint is the one moment without them. It tells you, and the instructor, which paths you can really write.", icon_name="CheckCircle", pad=28, title_size=32),
                       card(t, "Your folders are new", "The starting folder and the target are made for you when the instructor opens it. An answer copied from a neighbour does not fit.", icon_name="Key", pad=28, title_size=32),
                       card(t, "The instructor sees who needs help", "Your answers arrive at once. The instructor can explain a common mistake before the next lab builds on paths.", icon_name="Users", pad=28, title_size=32),
                       card(t, "It is fair", "Everyone gets the same kind of task. You can take it even if Core is not finished.", icon_name="ThumbsUp", pad=28, title_size=32),
                       cols=2),
        gap=36)

d.slide("cp-steps", "What happens, step by step",
        lambda t: flow(t, [("1. The instructor opens it", "Close your AI tools"), ("2. oslab checkpoint lab2", "Answer four questions"),
                           ("3. Read the file for real", "From the new folder, save the output"), ("4. oslab check lab2", "A sixth milestone must pass")], 400, hot=1),
        lambda t: row(rule(t, "Before it opens", "The command only says that the checkpoint is not open yet. Wait for the instructor.", title_size=36),
                      rule(t, "While you work", "Use your terminal and what you learned in this lab. No AI tools, and no help from a neighbour.", title_size=36),
                      rule(t, "When you finish", "oslab check lab2 tells you whether checkpoint.txt is right. You can fix it and check again.", title_size=36)),
        gap=56)

d.slide("cp-run", "What you see when you run it",
        lambda t: term(t, ["oslab checkpoint lab2",
                           ("out", "Checkpoint: your own work. Close AI tools; do not ask a neighbour."),
                           ("out", "Your current directory is `TechCorp/HR/drafts` (inside your lab2 folder; create it if it does not exist)."),
                           ("out", "You must read the file `TechCorp/Finance/archive/first-original.txt` without changing directory."),
                           ("out", "Type a relative path from that directory to the file. Do not type quotes."),
                           ("in", "your answer"),
                           ("out", "How many `..` does the shortest such path need?"),
                           ("in", "your answer"),
                           ("out", "From the lab folder you type  cat reports/audit notes.txt  with no quotes. How many arguments does `cat` receive?"),
                           ("in", "your answer"),
                           ("out", "Which folder is `..` from that directory? Type its path from the lab folder, for example reports."),
                           ("out", "Type . if it is the lab folder itself."),
                           ("in", "your answer")],
                       title="example: your folders will be different", size=24),
        note="Type each answer after the &gt; and press Enter. Your answers are saved once: the first answer counts.",
        gap=24)

d.slide("cp-task", "Then read the file for real",
        lambda t: row(term(t, [("out", "Now do it for real from that directory and save the output:"),
                               ("out", "  cat 'YOUR RELATIVE PATH' | tee \"$OSLAB_WORKSPACE/lab2/evidence/checkpoint.txt\""),
                               ("out", "Then run: oslab check lab2")],
                           title="the end of the checkpoint", size=26),
                      col(h3(t, "You already know how"),
                          para(t, "Make the starting folder with mkdir -p if it does not exist, go into it with cd, and use your own relative path.", size=30),
                          para(t, "tee shows the content and saves it in checkpoint.txt.", size=30),
                          gap=24),
                      gap=40, align="center"))

d.slide("cp-marks", "How the checkpoint is marked",
        lambda t: tbl(t, ["Part", "Points", "Who marks it, and how"],
                      [["The path, the number of .., the number of arguments", "1", "The computer. All right is 1 point. At least half right is half a point."],
                       ["Which folder .. is from your start folder", "1", "The computer. Each .. goes up one folder from the current one."],
                       ["evidence/checkpoint.txt holds the content of the target file", "1", "The computer. oslab check lab2 compares it."]],
                      [6, 2, 11]),
        lambda t: row(rule(t, "Can I answer again?", "No. Your answers are saved once. You can still fix checkpoint.txt and run oslab check lab2 again.", title_size=36),
                      rule(t, "Any path that works", "Any relative path that reaches the target is accepted, not only the shortest one.", title_size=36)),
        gap=48)

# ---- debrief and submit -----------------------------------------------------
d.opener("end-open", "DEBRIEF AND SUBMIT", "Look back, then hand in", "Ten minutes of debrief, five to submit.")

d.slide("debrief", "Debrief: your prediction again",
        lambda t: row(term(t, ['cat "$OSLAB_WORKSPACE/.records/lab2-predict.json"', "oslab debrief lab2"], size=28),
                      col(para(t, "Your prediction is in the hidden folder .records, as JSON: a text format of names and values.", size=30),
                          para(t, "oslab debrief lab2 asks each prediction question again. Type the right answer: the same one where you were right, the correct one where you were wrong. It is marked, and you may run it again.", size=32, tone="ink"),
                          para(t, "Then the class discusses: why can a correct file name still give No such file or directory?", size=30),
                          gap=24),
                      gap=48, align="center"))

SUBMIT_TREE = [("README.md", None), ("evidence", [("paths.txt", None), ("tree.txt", None), ("checkpoint.txt", None)])]

d.slide("submit", "Submit",
        lambda t: row(col(term(t, ['SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"',
                                   'mkdir -p "$SUBMISSION_REPO/lab2/evidence"',
                                   'cp -- evidence/paths.txt evidence/tree.txt "$SUBMISSION_REPO/lab2/evidence/"',
                                   'cp -- evidence/checkpoint.txt "$SUBMISSION_REPO/lab2/evidence/"'], size=24),
                          para(t, "Copy plus.txt or challenge.txt the same way if you did them. Fill in the report template as lab2/README.md, then commit and push. The website checks these exact names.", size=28),
                          gap=24, flex=None),
                      tree(t, "lab2", SUBMIT_TREE, cmd="tree", title="your repository", size=28),
                      gap=40, align="center"))

d.slide("push", "Commit and push",
        lambda t: row(term(t, ["cd ~/os-gic-YOUR_ID",
                               "git pull",
                               "git add os-lab-YOUR_ID/lab2",
                               'git commit -m "Lab 2"',
                               "git push"], title="student@server: ~", size=30),
                      col(para(t, "As in Lab 1. git pull comes first, in case you pushed from your own computer since.", size=32, tone="ink"),
                          para(t, "git add takes your lab2 folder, git commit records it with a message, git push sends it to GitHub.", size=30),
                          gap=24),
                      gap=56, align="center"))

d.slide("grading", "How Lab 2 is graded",
        lambda t: tbl(t, ["Evidence", "Points"],
                      [["Correct folders and files: oslab check lab2 passes Core milestones 1 to 4", "2"],
                       ["Tests: your path error and its working fix in paths.txt (milestone 5)", "2"],
                       ["Prediction saved in time, and corrected with oslab debrief lab2", "2"],
                       ["Live checkpoint: the three answers, the .. question and the saved output", "3"],
                       ["Complete submission: the required files in your repository, on time", "1"]],
                      [14, 2]),
        note="Every row is marked from your oslab records and your repository files, so run oslab check lab2 until it shows what you expect. Plus and Challenge are not needed for full marks.")

d.slide("mistakes", "Common mistakes",
        lambda t: tbl(t, ["Mistake", "What happens", "Fix"],
                      [["Losing the quotes in file1='...'", "The variable holds only the first word", "Type it again with the quotes"],
                       ["$file1 without double quotes", "The command receives two names", "Write &quot;$file1&quot;"],
                       ["A relative path from the wrong folder", "No such file or directory", "Run pwd, then draw the path"],
                       ["Thinking .. means the lab folder", "The path goes to the wrong place", "Each .. is one level up from here"],
                       ["Proving a copy with ls", "Same name, unknown content", "Use cmp"],
                       ["Typing &lt;owner&gt; literally", "A folder with brackets, or an error", "Use your own value or &quot;$owner&quot;"],
                       ["A Fix path written from the lab folder", "Milestone 5 says TRY", "Write it from your reader department"]],
                      [6, 6, 6]),
        gap=36)

t = d.alt()
d.add("takeaways", t, [h2("Key takeaways"), grid(
    card(t, "One tree from /", "Every file is somewhere below the root. Your home is /home/your-account, or ~.", number="01", pad=32, title_size=32),
    card(t, "Absolute or relative", "Absolute starts at /. Relative starts where you are, so check with pwd.", number="02", pad=32, title_size=32),
    card(t, "Dots", ". is here. Each .. is one level up from here.", number="03", pad=32, title_size=32),
    card(t, "Copy, move, prove", "cp keeps the original, mv does not. cmp proves two files are identical.", number="04", pad=32, title_size=32),
    cols=2)], top=True, gap=40)

t = d.alt()
d.add("next", t, [
    h2("Next lab"),
    row(card(t, "Lab 3: wildcards and links", "Select files with a wildcard, then create hard and symbolic links and see what happens when their target changes.",
             label="COMING UP", icon_name="PaperPlane", pad=48, flex=3),
        card(t, "Reference", "The Lab 2 instruction and its Concepts First section, the report template in the course repository, and man cp, man mv and man find.",
             label="SOURCE", icon_name="Book", pad=48, flex=2),
        gap=24, align="stretch"),
])

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: the folder tree from /, the home directory, absolute and relative paths, . and .., names with spaces, and the file and folder commands.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the helper commands, the rules, setup and your values.", "start": "lab-open"},
    "s4": {"description": "Guided: where am I?", "start": "g-open"},
    "s5": {"description": "The prediction.", "start": "predict-open"},
    "s6": {"description": "Core 1 to 3, then Plus and Challenge.", "start": "c1-open"},
    "s7": {"description": "The live checkpoint: why it exists, what happens and how it is marked.", "start": "cp-open"},
    "s8": {"description": "Debrief, submission, grading, common mistakes, takeaways and the next lab.", "start": "end-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
