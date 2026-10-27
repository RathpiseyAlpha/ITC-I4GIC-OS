"""Building blocks shared by the lab guides from Lab 3 on: the Ubuntu look, terminal windows, folder trees and tables.

Copied from the Lab 2 guide's gen.py (see its docstring and Lab 1's for the instructor's decisions of 2026-10-08).
`build_guide.py` copies this file next to oslib.py. A guide's gen.py calls `init(HERE, lab_number)` first.
"""
import json
import os
import re
import sys

import oslib  # noqa: E402  (it puts the shared library on the path)
import decklib  # noqa: E402
from oslib import (h2, para, statement, em, lst, row, col, grid, card, rule, table,  # noqa: E402,F401
                   box, arrow, flow, layers, lanes, OSDeck, setup)

decklib.PAGE_BADGE = True  # the page number is a round badge at the bottom right, as in the ICT decks (oslib turns it off for the week decks)

# ---- this guide's own look ------------------------------------------------
UBUNTU = "font-family:'Ubuntu', 'Segoe UI', Arial, sans-serif"
MONO = "font-family:'Ubuntu Mono', 'Courier New', monospace"
decklib.SERIF = decklib.SANS = oslib.SERIF = UBUNTU
decklib.FACES = {
    "newsreader": {"family": "Newsreader", "href": "https://fonts.googleapis.com/css2?family=Newsreader:ital,wght@0,400..600;1,400..500&display=swap"},
    "dm-sans": {"family": "DM Sans", "href": "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400..700&display=swap"},
    "ubuntu": {"family": "Ubuntu", "href": "https://fonts.googleapis.com/css2?family=Ubuntu:ital,wght@0,300;0,400;0,500;0,700;1,400&display=swap"},
    "ubuntu-mono": {"family": "Ubuntu Mono", "href": "https://fonts.googleapis.com/css2?family=Ubuntu+Mono:ital,wght@0,400;0,700;1,400&display=swap"},
}

def h3(t, text):
    return f'<h3 style="font-size:32px;font-weight:500;color:{t["accent"]}">{text}</h3>'


def mono(text):
    return f'<span style="{MONO}">{text}</span>'


def tbl(t, headers, rows, weights, width=None):
    """A table whose column widths are given as weights and scaled to the content width."""
    width = width or CW
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


def term(t, lines, title=None, size=32, width=None, user="student", host="server"):
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
    return window(title or LAB_TITLE, "".join(rows), width)


def tree(t, root, kids, cmd=None, title=None, size=28, width=None, summary=True, lh=1.4, blank=True):
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
    return window(title or LAB_TITLE, body, width)




CW = 1904        # content width: the canvas minus the two 128px side paddings; set again by init()
HALF = (CW - 32) // 2
LAB_TITLE = "student@server: ~/oslab-work"


def init(here, lab):
    """Read this deck's canvas size and picture sizes, load its assets and return the OSDeck for "Lab N"."""
    global CW, HALF, LAB_TITLE
    with open(os.path.join(here, "size.json"), encoding="utf-8") as f:
        CW = json.load(f)["width"] - 256
    HALF = (CW - 32) // 2
    LAB_TITLE = "student@server: ~/oslab-work/lab%d" % lab
    setup(here)
    with open(os.path.join(here, "dims.json"), encoding="utf-8") as f:
        decklib.DIM.update({k: tuple(v) for k, v in json.load(f).items()})
    return OSDeck("Lab %d" % lab)


# ---- the slides every lab of the standard format shares ------------------------------------------------------
# Labs 3 to 7 and 9 to 11 follow one instruction template: setup, guided example, prediction, tasks, tests, an
# individual checkpoint, correction, cleanup and submission, grading. Each function adds one such slide, so a
# lab's gen.py holds only what is its own. Slide ids are fixed; call the functions in the order of the lab.

def scenario(d, n, who, text, extra, start_tree, cmd="tree -a"):
    d.slide("scenario", "The scenario",
            lambda t: row(col(card(t, who, text, label="SCENARIO", pad=40, title_size=36),
                              para(t, extra, size=30), gap=28),
                          tree(t, "lab%d" % n, start_tree, cmd=cmd, title="student@server: ~/oslab-work/lab%d" % n, size=30),
                          gap=56, align="center"))


def timetable(d, left, right):
    d.slide("time", "Inside the 120 minutes",
            lambda t: row(tbl(t, ["Minutes", "What happens"], left, [1, 3], width=HALF),
                          tbl(t, ["Minutes", "What happens"], right, [1, 3], width=HALF), gap=32), gap=36)


DEFAULT_TIME = ([["0 to 10", "Introduction, objectives and setup"],
                 ["10 to 25", "Guided example: commands and observations"],
                 ["25 to 35", "Written prediction"],
                 ["35 to 70", "Individual investigation"]],
                [["70 to 85", "Normal and edge tests, feedback"],
                 ["85 to 100", "Individual changed-case checkpoint"],
                 ["100 to 110", "Correction and explanation"],
                 ["110 to 120", "Cleanup and submission"]])


def rules(d, safety="Privileged and boot work is never done on the shared server."):
    d.slide("rules", "How you work",
            lambda t: row(rule(t, "Your own account", "Log in with your own account. Use only your own files and processes. " + safety, title_size=36),
                          rule(t, "AI tools", "Optional in the investigation and the tests. Not allowed in the prediction and the individual checkpoint.", title_size=36),
                          rule(t, "Evidence", "Keep what you observe in the evidence folder. Short, attributable evidence earns more than long output.", title_size=36)),
            note="Initial prediction accuracy is lightly weighted. A reasoned attempt and an evidence-based correction earn credit.")


def setup_slides(d, n, tree_kids, notes):
    """The two setup slides. tree_kids is the starting tree; notes are two or three lines about its files."""
    d.slide("start", "Setup: start the lab",
            lambda t: row(term(t, ["whoami", "command -v oslab", "oslab doctor",
                                   'export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                                   "oslab start lab%d" % n, 'cd "$OSLAB_WORKSPACE/lab%d"' % n, "pwd",
                                   "mkdir -p evidence", "find . -maxdepth 3 -type f"], title="student@server: ~", size=26),
                          col(lst(t, ["whoami shows your account. command -v oslab and oslab doctor check the helper.",
                                      "If the helper is missing, follow the local setup guide in the course repository.",
                                      "oslab start lab%d makes the lab folder. It keeps your work if you start again, and it does not change your current folder, so cd into it yourself." % n,
                                      "If you are resuming, look at the existing files before you run a command that writes to them."], size=30),
                              gap=20),
                          gap=48, align="center"))
    d.slide("start-tree", "Compare with the starting tree",
            lambda t: row(tree(t, "lab%d" % n, tree_kids, cmd="tree -a -L 3", title="student@server: ~/oslab-work/lab%d" % n, size=30),
                          col(*[para(t, x, size=32) for x in notes], gap=24),
                          gap=48, align="center"))


def predict(d, question, rules_text="Alone, and without AI. On paper or in the course worksheet, before you run the command. You may compare with a neighbour for five minutes, but keep your own answer."):
    d.opener("predict-open", "PREDICT", "Guess first, then try", "Before you run the experiment. Ten minutes.")
    d.slide("predict", "The prediction",
            lambda t: row(col(card(t, "Write this down first", question, label="PREDICTION", pad=40, title_size=36), gap=24, flex=3),
                          col(card(t, "The rules", rules_text, label="HOW", pad=32, title_size=32), gap=24, flex=2),
                          gap=48, align="stretch"),
            note="A wrong prediction costs nothing. It is marked for being made and for the evidence-based correction afterwards.")


def checkpoint(d, question, title="Practice question"):
    d.opener("cp-open", "INDIVIDUAL CHECKPOINT", "Show what you can do alone", "Fifteen minutes, from minute 85 to 100. No AI, no neighbours.")
    d.slide("cp-why", "Why there is a checkpoint",
            lambda t: row(rule(t, "It checks you, not the tools", "Everything before it may use AI and help. The checkpoint shows what you understood without them.", title_size=36),
                          rule(t, "A short question on paper", "You answer one question on paper or on the course worksheet. Your earlier work does not need to be finished.", title_size=36),
                          rule(t, "Practice question", "The question on the next slide is public practice. A graded session may use a fresh private variant.", title_size=36)))
    d.slide("cp-question", "The question",
            lambda t: row(col(card(t, title, question, label="CHECKPOINT", pad=40, title_size=36), gap=24, flex=3),
                          col(h3(t, "What to give"),
                              lst(t, ["The result or diagnosis.", "The mechanism.", "One observation that could check it."], ordered=True, size=32),
                              gap=20, flex=2),
                          gap=48, align="stretch"),
            note="The instructor collects your answer before discussing the public key.")


def correction(d, questions):
    d.opener("end-open", "CORRECTION AND SUBMISSION", "Look back, then hand in", "Ten minutes of correction, ten to clean up and submit.")
    d.slide("explain", "Correct your prediction",
            lambda t: row(lst(t, ["Keep your original prediction in view. Under it, write confirmed or corrected.",
                                  "Cite the test that shows it.",
                                  "Explain the OS mechanism in three to five sentences."], ordered=True, size=34, flex=3),
                          card(t, "Three questions", questions, label="ANSWER", pad=40, title_size=36, flex=2),
                          gap=48, align="stretch"))


def submission(d, n, copy_cmds, final_tree, note=None):
    d.slide("submit-one", "Submit 1: your repository and the copy",
            lambda t: row(term(t, ['SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"',
                                   'mkdir -p "$SUBMISSION_REPO/lab%d/evidence"' % n,
                                   'cd "$OSLAB_WORKSPACE/lab%d"' % n] + copy_cmds, title="student@server: ~", size=24),
                          col(para(t, "Replace YOUR_ID with your own ID. The orange text is the part you change. Use the absolute path of your existing course repository, never a neighbour's.", size=30),
                              para(t, "Example: with the ID 0123, the first line becomes SUBMISSION_REPO=\"$HOME/os-gic-0123/os-lab-0123\", and echo \"$SUBMISSION_REPO\" prints /home/student/os-gic-0123/os-lab-0123.", size=28),
                              para(t, note or "Copy the listed artifacts and two selected test records, not every terminal output.", size=30),
                              gap=22),
                          gap=48, align="center"))
    d.slide("submit-two", "Submit 2: the final tree and Git",
            lambda t: row(tree(t, "lab%d" % n, final_tree, cmd="tree", title="student@server: ~/os-gic-YOUR_ID/os-lab-YOUR_ID", size=30),
                          col(lst(t, ["Write README.md from the lab's template, in your own words.",
                                      "The prediction must have been written before you ran anything. Copying it into the README only records it.",
                                      "git status --short, then add only your lab files, then commit and push.",
                                      "No passwords, personal shell files, generated binaries or disk images."], ordered=True, size=30),
                              gap=20),
                          gap=48, align="center"))


def grading(d, rows, note="Other valid commands and names earn credit. A naming difference costs points only when it breaks the result. If you use AI, note one useful suggestion and how you verified it."):
    d.slide("grading", "How it is marked: 10 points",
            lambda t: tbl(t, ["Evidence for the lab objectives", "Points"], rows, [10, 1]), note=note)


def mistakes(d, rows):
    d.slide("mistakes", "Common mistakes",
            lambda t: tbl(t, ["Mistake", "What you see", "Fix"], rows, [6, 5, 6]), gap=36)


def listing(t, lines, title="threads/one_worker.c", size=24, width=None, hot=(), lh=1.2):
    """Source code in a dark window. Lines in `hot` (zero-based) get an orange left bar, and comments are dimmed."""
    rows = []
    for i, ln in enumerate(lines):
        raw = esc(ln).replace(" ", "&#160;") or "&#160;"
        m = re.search(r"(/\*.*\*/|//.*)$", raw)
        if m:
            raw = raw[:m.start()] + span(m.group(1), TC["comment"], italic=True)
        raw = re.sub(r"(#include|#define)", lambda x: span(x.group(1), TC["op"], True), raw, count=1) if ln.lstrip().startswith("#") else raw
        bar = f"border-left:6px solid {TC['ph']};padding-left:10px;" if i in hot else "border-left:6px solid transparent;padding-left:10px;"
        rows.append(f'<p style="{MONO};font-size:{size}px;line-height:{lh};white-space:nowrap;color:{TC["plain"]};{bar}">{raw}</p>')
    return window(title, "".join(rows), width)
