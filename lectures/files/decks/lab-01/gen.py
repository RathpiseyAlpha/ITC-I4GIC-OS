"""Lab 1 guide, Exploring Operating System Basics. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

This is a guide for the lab session, not a lecture, so it is not one of the week decks, and it
differs from them on purpose (instructor's decisions, 2026-10-08):

- Ubuntu and Ubuntu Mono fonts, not Newsreader and DM Sans.
- A wider canvas (size.json), so the guide fills a laptop browser window.
- Linux commands are shown in dark terminal windows with bash-style colours.
- Folder trees are drawn like the output of `tree`, with branch lines.
- It keeps the Linux background of the earlier Lab 1 guide (why Linux matters, distributions,
  the kernel and its creator, package management, Linux families, shells and the prompt), with
  that guide's own pictures (images.json).

The lab part follows labs/lab1/lab1-instruction.md: Part A in class, Part B as homework.
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

WEEK = "Lab 1"
TITLE = "Operating Systems — Lab 1"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-08T09:00:00Z"
BG = "Linux in brief"
PART_B = "Lab 1 · Part B"

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
PLACEHOLDERS = ("FILE1", "FILE2", "COUNT", "YOUR_USERNAME", "YOUR_ID", "SERVER_USER", "SERVER_ADDRESS", "xxx")
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


def term(t, lines, title="student@server: ~/oslab-work/lab1", size=32, width=None, user="student", host="server"):
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


def tree(t, root, kids, cmd=None, title="student@server: ~/oslab-work/lab1", size=28, width=None, summary=True, lh=1.4, blank=True):
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


# ---- opening --------------------------------------------------------------
d.cover("Exploring Operating System Basics",
        "Lab 1 guide: Linux in brief, then find out which system you are on, practise the basic commands, and see programs and processes at work.",
        size=96)

d.slide("objectives", "Learning objectives", lambda t: row(
    lst(t, ["Identify basic operating system and kernel information.",
            "Use essential Linux file and directory commands.",
            "Install, remove, and purge software using the APT package manager.",
            "Understand the difference between a program and a running process.",
            "Observe multitasking in a running operating system.",
            "Detect whether an operating system is running on a virtualized environment."], ordered=True, size=36, flex=3),
    card(t, "Lab 1", "First, Linux in brief. Then Part A in class, on the course server, and Part B as homework, on your own Ubuntu.", label="THIS LAB", flex=2),
    gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "You log in to a server you have never seen. What do you check first?",
         "Which system it is, what is in your folder, and what is running. This lab shows you how to find out.")

# ---- Linux in brief (kept from the earlier Lab 1 guide) ---------------------
d.opener("bg-open", "LINUX IN BRIEF", "What is Linux, and why learn it?",
         "Where it comes from, how a distribution is built, and how you talk to it.")

d.text_pic("everywhere", "Linux is everywhere",
           [lambda t: lst(t, ["Servers and cloud platforms",
                              "Android phones and tablets, which use the Linux kernel",
                              "Routers, smart TVs and cars",
                              "Supercomputers",
                              "Developers' laptops and desktops"], size=36),
            lambda t: para(t, "As an engineer you will meet Linux again and again. That is why this course works on it.", size=32)],
           "everywhere", "The words Linux is everywhere, surrounded by icons of devices and services that run Linux",
           maxw=820, maxh=560, label=BG)

d.text_pic("origin", "Where Linux comes from",
           [lambda t: lst(t, ["Linus Torvalds developed the first version, 0.01, in 1991.",
                              "Linux was first distributed as source code only.",
                              "Later it came as a pair of downloadable floppy-disk images.",
                              "One image was bootable and held the Linux kernel.",
                              "The other held a set of GNU utilities and tools for setting up a file system."], size=34)],
           "linus", "Portrait of Linus Torvalds", caption="Linus Torvalds, 1969 to present",
           maxw=640, maxh=520, label=BG)

d.text_pic("kernel", "The Linux kernel",
           [lambda t: lst(t, ["The kernel is the core of the operating system.",
                              "It manages the processor, the memory and the devices.",
                              "Programs ask it for services through system calls.",
                              "Linux is the kernel. A distribution adds the programs around it."], size=34)],
           "kernel", "Diagram of the Linux kernel between the hardware it runs on and the software that uses it",
           maxw=980, maxh=551, label=BG)

d.slide("distro", "A Linux distribution, or distro",
        lambda t: row(col(para(t, "An operating system made from a software collection, based on the Linux kernel and, often, a package management system.", size=34, tone="ink"),
                          h3(t, "A typical distribution comprises"),
                          lst(t, ["A Linux kernel", "GNU tools",
                                  "Others: libraries, additional software, documentation, a window system, a window manager and a desktop environment"], size=32),
                          gap=24),
                      layers(t, [[("Desktop and applications", "window system, window manager, desktop environment", False)],
                                 [("GNU tools and libraries", None, False)],
                                 [("Linux kernel", "what Linus Torvalds started", True)],
                                 [("Hardware", None, False)]], width=780),
                      gap=64, align="center"),
        note="About 500 to 600 distributions are in active development (the figure given in the earlier Lab 1 guide).",
        label=BG)

d.pic("distro-pic", "Layers of a Linux distribution", "layers",
      "Table of the layers of a Linux distribution: user applications, system components and the C library in user mode, the Linux kernel in kernel mode, and the hardware",
      note="Programs in user mode sit on the kernel, and the kernel sits on the hardware.", maxw=1500, maxh=520, label=BG)

d.pic("timeline", "A timeline of distributions", "timeline",
      "Timeline chart in which each line is a Linux distribution, many of them branching from older ones",
      note="Each line is one distribution. Most of them branch from an older one.", maxw=1700, maxh=520, label=BG)

d.slide("families", "Linux families",
        lambda t: tbl(t, ["Family", "Examples", "Package files", "Tools"],
                      [["Debian", "Debian, Ubuntu, Linux Mint, Raspberry Pi OS", mono(".deb"), mono("dpkg, apt")],
                       ["Red Hat", "Red Hat Enterprise Linux, Fedora, CentOS", mono(".rpm"), mono("rpm, yum, dnf")],
                       ["SUSE", "SUSE Linux Enterprise, openSUSE", mono(".rpm"), mono("rpm, zypper")],
                       ["Slackware", "Slackware", mono(".tgz"), mono("pkgtools")]],
                      [3, 8, 3, 4]),
        note="This lab uses Ubuntu, so you use the tools of the Debian family: dpkg and apt.",
        label=BG)

d.pic("families-pic", "The families over time", "families",
      "Timeline from 1991 showing the Debian, Slackware, SUSE and Red Hat families and the distributions that came from each",
      note="Debian, Slackware, SUSE and Red Hat each started a family of distributions.", maxw=1700, maxh=520, label=BG)

d.slide("packages", "Package management",
        lambda t: row(card(t, "Packages", "A distribution is normally split into packages. Each package holds one application or service.", number="01", pad=36, title_size=36),
                      card(t, "What a package holds", "The software, and metadata: its full name, a description of its purpose, a version number, a checksum, and the list of dependencies it needs to run.", number="02", pad=36, title_size=36),
                      card(t, "The package manager", "A collection of tools that automates installing, upgrading, configuring and removing programs, in a consistent way.", number="03", pad=36, title_size=36),
                      gap=24, align="stretch"),
        note="A dependency is another package that this one needs.",
        label=BG)

d.slide("dpkg", "DPKG",
        lambda t: row(col(para(t, "DPKG is the package manager of Debian-based systems.", size=34, tone="ink"),
                          para(t, "It can install, remove and build packages. Unlike other package managers, it cannot download and install packages or their dependencies by itself.", size=32),
                          para(t, "Details: man dpkg", size=32),
                          gap=24),
                      term(t, ["dpkg -l                 # list all installed packages",
                               "dpkg -l | grep xxx      # check if xxx is installed",
                               "sudo dpkg -i xxx.deb    # install xxx.deb",
                               "sudo dpkg -r xxx        # uninstall xxx"], title="student@ubuntu: ~"),
                      gap=56, align="center"),
        label=BG)

d.slide("apt", "APT",
        lambda t: row(col(para(t, "The apt command works with Ubuntu's Advanced Packaging Tool.", size=34, tone="ink"),
                          para(t, "It installs new packages, upgrades the ones you have, updates the package list, and can even upgrade the whole system.", size=32),
                          para(t, "Details: apt help. Lab 1 uses apt-get, the older command with the same actions.", size=32),
                          gap=24),
                      term(t, ["sudo apt install xxx    # install xxx",
                               "sudo apt remove xxx     # remove xxx",
                               "sudo apt update         # update the local package index",
                               "sudo apt upgrade        # update packages and system"], title="student@ubuntu: ~"),
                      gap=56, align="center"),
        label=BG)

d.text_pic("why-cli", "Why is knowing the command line important?",
           [lambda t: statement(t, f"{em(t, 'Flexibility and mobility.')}", size=56),
            lambda t: lst(t, ["When you understand the foundation of Linux, you can work on any Linux distribution.",
                              "That may be one company with a mixed environment.",
                              "Or a new company that uses a different distribution.",
                              "Many servers have no graphical desktop at all."], size=32)],
           "cli", "World map with terminal windows of several Linux distributions, under the question why is knowing the command line important",
           maxw=760, maxh=540, label=BG)

d.slide("shell", "What is a shell?",
        lambda t: flow(t, [("You", "type a command"), ("The terminal", "takes what you typed and passes it on"),
                           ("The shell", "the command-line interpreter, here bash"), ("The operating system", "carries out the action")], 400, hot=2),
        lambda t: row(rule(t, "The terminal", "Once you have entered a command, the terminal accepts what you typed and passes it to a shell.", title_size=36),
                      rule(t, "The shell", "The shell is the command-line interpreter. It translates the commands you enter into actions to be performed by the operating system.", title_size=36)),
        label=BG, gap=64)


def prompt_card(t, label, part):
    """The prompt sysadmin@localhost:~$ with one part marked, as in the earlier guide."""
    def mark(text, on):
        return span(text, "#10131a" if on else TC["plain"], True, back="#f1fa8c" if on else None)
    line = (mark("sysadmin", part == "user") + span("@", TC["plain"], True) + mark("localhost", part == "host")
            + span(":", TC["plain"], True) + mark("~", part == "dir") + span("$", TC["plain"], True))
    return col(h3(t, label), window("terminal", tline(line, 40)), gap=20)


d.slide("prompt", "The prompt",
        lambda t: para(t, "When a terminal starts, the shell shows a prompt. Its structure varies between distributions, but it typically tells you about the user and the system.", size=32),
        lambda t: row(prompt_card(t, "User name", "user"), prompt_card(t, "System name", "host"), prompt_card(t, "Current directory", "dir"), gap=32),
        note="The $ at the end means you are a normal user, and the shell is waiting for your command.",
        label=BG)

d.slide("tilde", "The ~ symbol is your home directory",
        lambda t: row(term(t, [("cmd", "pwd", "~"), ("out", "/home/sysadmin"),
                               ("cmd", "cd /etc", "~"),
                               ("cmd", "pwd", "/etc"), ("out", "/etc"),
                               ("cmd", "cd ~", "/etc"),
                               ("cmd", "pwd", "~"), ("out", "/home/sysadmin")],
                           title="sysadmin@localhost: ~", user="sysadmin", host="localhost"),
                      col(para(t, "The ~ symbol is shorthand for the user's home directory.", size=36, tone="ink"),
                          para(t, "Watch the prompt: it shows ~ while you are at home, and the real path when you are somewhere else.", size=32),
                          para(t, "cd ~ brings you home from anywhere.", size=32),
                          gap=24),
                      gap=56, align="center"),
        label=BG)

# ---- how the lab works ------------------------------------------------------
d.opener("lab-open", "LAB 1", "Exploring operating system basics", "Two parts: in class on the server, then homework on your own Ubuntu.")

d.slide("how", "Two parts, one lab",
        lambda t: row(card(t, "Part A: in class", "120 minutes on the course server. Five tasks, a prediction and a live checkpoint. Worth 7 of the 10 points.",
                           label="WITH THE INSTRUCTOR", icon_name="Clock", pad=40, title_size=40),
                      card(t, "Part B: homework", "About 60 minutes on your own Ubuntu and PC. Install and remove software, three screenshots, your report and a push to GitHub. Worth 3 points.",
                           label="DUE BEFORE THE NEXT CLASS", icon_name="Home", pad=40, title_size=40),
                      gap=24, align="stretch"),
        note="Both parts are graded together as Lab 1.")

d.slide("where", "Where each task runs",
        lambda t: tbl(t, ["Task", "What you do", "Where"],
                      [["1", "Find the kernel and the distribution", "Server, in class"],
                       ["2", "Practise file and folder commands", "Server, in class"],
                       ["3", "Install, remove and purge a package", "Your Ubuntu, homework"],
                       ["4", "Program or process?", "Server, in class"],
                       ["5", "Several programs at once", "Server, in class"],
                       ["6", "Is this a virtual machine?", "Server, in class"]],
                      [2, 11, 6]),
        note="You have no sudo on the server, so only Task 3 happens on your own machine.")

HALF = (CW - 32) // 2
d.slide("time", "Inside the 120 minutes",
        lambda t: row(tbl(t, ["Minutes", "What happens"],
                          [["0 to 10", "Setup"],
                           ["10 to 20", "Task 1: which system is this?"],
                           ["20 to 40", "Task 2: files and folders"],
                           ["40 to 50", "Prediction, then class discussion"],
                           ["50 to 65", "Tasks 4 and 5: programs, processes and multitasking"]],
                          [1, 3], width=HALF),
                      tbl(t, ["Minutes", "What happens"],
                          [["65 to 75", "Task 6: is this a virtual machine?"],
                           ["75 to 90", "Instructor demonstration, then Plus and Challenge"],
                           ["90 to 105", "Live checkpoint"],
                           ["105 to 120", "Debrief and homework briefing"]],
                          [1, 3], width=HALF),
                      gap=32),
        gap=36)

d.slide("helper", "Five helper commands, and why you use them",
        lambda t: tbl(t, ["Command", "What it does", "Why"],
                      [[mono("oslab values lab1"), "Shows your own names and number", "Your work is different from your neighbour's"],
                       [mono("oslab predict lab1"), "Saves your guess before you try", "Guessing first makes you think. The first answer is kept"],
                       [mono("oslab hint lab1 1"), "A hint, levels 1 to 3", "You get unstuck without waiting, at no cost"],
                       [mono("oslab check lab1"), "Checks your files", "You see at once what is still missing"],
                       [mono("oslab checkpoint lab1"), "A short test near the end", "It shows what you can do alone"]],
                      [5, 6, 8]))

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Individual work", "Your file names and number are different from your neighbour's. You hand in your own work.", title_size=36),
                      rule(t, "AI tools", "Allowed in the tasks, so test what they tell you. Not allowed for the prediction and the checkpoint.", title_size=36),
                      rule(t, "Hints", "Use oslab hint lab1, levels 1 to 3, before you ask. Hints cost no points.", title_size=36)),
        note="A wrong prediction costs nothing. It is marked for being made and corrected, not for being right.")

d.slide("start", "Start the lab",
        lambda t: row(term(t, ["oslab doctor             # before class",
                               "oslab prelab lab1        # before class",
                               "oslab start lab1",
                               "cd ~/oslab-work/lab1",
                               "oslab values lab1",
                               "oslab check lab1"], title="student@server: ~"),
                      col(lst(t, ["oslab start lab1 makes your lab folder.",
                                  "cd takes you into it. You work there for all of Part A.",
                                  "oslab values lab1 prints your personal values. The next slide explains them.",
                                  "oslab check lab1 prints one line for each part of the lab: TRY means not done yet, PASS means done."], size=32),
                          gap=20),
                      gap=56, align="center"),
        note="At the start every line of oslab check lab1 says TRY, because you have not done anything yet.")

d.slide("values", "Your personal values",
        lambda t: row(col(h3(t, "1. The command prints values that are only yours"),
                          term(t, ["oslab values lab1",
                                   ("out", "Your personal values for lab1 (your-account):"),
                                   ("out", "  count    = 3"),
                                   ("out", "  file1    = maple"),
                                   ("out", "  file2    = river")], title="example: your values will be different"),
                          gap=20, flex=None),
                      col(h3(t, "2. The guide writes capitals where your value belongs"),
                          tbl(t, ["The guide says", "With the example values, you type"],
                              [[mono("touch FILE1.txt FILE2.txt"), mono("touch maple.txt river.txt")],
                               [mono("echo &quot;This is file FILE1&quot;"), mono("echo &quot;This is file maple&quot;")],
                               ["Type this line " + mono("COUNT") + " times", "Type this line 3 times"]],
                              [1, 1], width=960),
                          gap=20, flex=None),
                      gap=48, align="flex-start"),
        note="FILE1, FILE2 and COUNT are placeholders, shown in orange in the terminal windows. Never type them. Type your own value in their place.")

# ---- task 1 -----------------------------------------------------------------
d.opener("t1-open", "TASK 1", "Which system is this?", "The kernel and the distribution are not the same thing.")

d.slide("t1-commands", "Ask the system about itself",
        lambda t: row(col(term(t, ["uname -a > task1_os_info.txt",
                                   "lsb_release -a >> task1_os_info.txt",
                                   "cat task1_os_info.txt"]),
                          para(t, "uname asks the kernel. lsb_release describes the distribution.", size=32),
                          gap=32),
                      layers(t, [[("Your programs", None, False)],
                                 [("Ubuntu: the distribution", "the kernel plus many other programs", False)],
                                 [("Linux: the kernel", "controls the hardware", True)],
                                 [("Hardware", None, False)]], width=760),
                      gap=64, align="center"),
        note="For your report: which number is the kernel version, and which is the Ubuntu version?")

# ---- task 2 -----------------------------------------------------------------
d.opener("t2-open", "TASK 2", "Files and folders", "Ten commands, and two file names that are only yours.")

d.slide("t2-commands", "The ten commands",
        lambda t: row(tbl(t, ["Command", "Meaning"],
                          [[mono("pwd"), "Shows the folder you are in"],
                           [mono("ls"), "Lists the files here"],
                           [mono("mkdir"), "Makes a folder"],
                           [mono("cd"), "Goes into a folder"],
                           [mono("touch"), "Makes an empty file"]],
                          [1, 3], width=HALF),
                      tbl(t, ["Command", "Meaning"],
                          [[mono("echo"), "Prints text"],
                           [mono("cat"), "Shows what is in a file"],
                           [mono("cp"), "Copies a file"],
                           [mono("mv"), "Moves or renames a file"],
                           [mono("rm"), "Deletes a file"]],
                          [1, 3], width=HALF),
                      gap=32),
        gap=36)

d.slide("t2-redirect-where", "Where does the output of a command go?",
        lambda t: col(h3(t, "Normally: to the screen"),
                      flow(t, [("ls", "a command"), ("its output", "the standard output"), ("the screen", "you read it, then it is gone")], 460),
                      h3(t, "With &gt; or &gt;&gt;: into a file"),
                      flow(t, [("ls &gt; list.txt", "the same command, redirected"), ("its output", "the standard output"), ("list.txt", "it is saved, and the screen shows nothing")], 460, hot=2),
                      gap=28),
        note="This is called output redirection. You use it in every task to keep a record of your results.",
        gap=40)

d.slide("t2-redirect-syntax", "The syntax of &gt; and &gt;&gt;",
        lambda t: tbl(t, ["You type", "What it means", "If the file is new", "If the file exists"],
                      [[mono("COMMAND &gt; FILE"), "Send the output into FILE", "FILE is created", "Its old content is replaced"],
                       [mono("COMMAND &gt;&gt; FILE"), "Add the output to the end of FILE", "FILE is created", "Its old content stays, and the new output comes after it"]],
                      [5, 6, 4, 7]),
        lambda t: row(rule(t, "One arrow replaces", "Think of &gt; as: start this file again.", title_size=36),
                      rule(t, "Two arrows add", "Think of &gt;&gt; as: write on the next line.", title_size=36),
                      rule(t, "The command does not change", "Only where its output goes changes. COMMAND can be any command.", title_size=36)),
        gap=56)

d.slide("t2-redirect-examples", "See the difference",
        lambda t: row(col(h3(t, "&gt;  replaces the file"),
                          term(t, ["echo one > a.txt", "echo two > a.txt", "cat a.txt", ("out", "two")], title="one arrow"),
                          gap=20),
                      col(h3(t, "&gt;&gt;  adds to the end"),
                          term(t, ["echo one > a.txt", "echo two >> a.txt", "cat a.txt", ("out", "one"), ("out", "two")], title="two arrows"),
                          gap=20),
                      gap=48, align="stretch"),
        note="In this lab the first line of a record file uses > and every later line uses >>.")

d.slide("t2-dotdot", "Two dots mean the folder above",
        lambda t: row(tree(t, "lab1", [("README.txt", None), ("task1_os_info.txt", None), ("task2_file_commands.txt", None), ("task2_files", [])],
                           cmd="tree lab1", title="student@server: ~/oslab-work", size=30, summary=False),
                      col(term(t, [("cmd", "pwd > ../task2_file_commands.txt", "~/oslab-work/lab1/task2_files")],
                               title="you are inside task2_files", size=28),
                          para(t, "From inside task2_files, .. is lab1. So ../task2_file_commands.txt is a file in lab1, not in task2_files.", size=32),
                          gap=28),
                      gap=48, align="center"),
        note="Check where you are with pwd before every command that writes a file.")

d.slide("t2-steps-a", "Make, write and record",
        lambda t: row(term(t, ["mkdir task2_files",
                               "cd task2_files",
                               "pwd > ../task2_file_commands.txt",
                               "ls >> ../task2_file_commands.txt",
                               "touch FILE1.txt FILE2.txt",
                               "ls >> ../task2_file_commands.txt",
                               'echo "This is file FILE1" > FILE1.txt',
                               'echo "This is file FILE2" > FILE2.txt',
                               "cat FILE1.txt FILE2.txt >> ../task2_file_commands.txt"]),
                      col(para(t, "Replace FILE1 and FILE2, shown in orange, with your own file1 and file2.", size=32),
                          para(t, "Every result goes into the record file. The first line uses &gt;, the rest use &gt;&gt;.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t2-steps-b", "Copy, rename and delete",
        lambda t: row(term(t, ["cp FILE1.txt FILE1_copy.txt",
                               "ls >> ../task2_file_commands.txt",
                               "mv FILE2.txt FILE2_renamed.txt",
                               "ls >> ../task2_file_commands.txt",
                               "rm FILE1_copy.txt",
                               "ls >> ../task2_file_commands.txt",
                               "cd ..",
                               "cat task2_file_commands.txt"], title="student@server: ~/oslab-work/lab1/task2_files"),
                      col(h3(t, "At the end you have"),
                          tree(t, "task2_files", [("FILE1.txt", None), ("FILE2_renamed.txt", None)], cmd="tree task2_files", size=30),
                          gap=20, flex=None),
                      gap=48, align="center"))

# ---- prediction -------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Write down what you expect before you run the next tasks.")

d.slide("predict", "Four questions, before you run anything",
        lambda t: row(lst(t, ["You start COUNT copies of sleep in the background. How many lines with sleep does ps show?",
                              "They have all finished. Is the program file sleep still on the disk?",
                              "Does apt-get remove delete the package's settings in /etc?",
                              "One sentence: what is the difference between a program and a process?"], ordered=True, size=34, flex=3),
                      col(term(t, ["oslab predict lab1"]),
                          card(t, "The rules", "Alone, and without AI. The first answer is the one that counts. A wrong guess costs nothing.", label="PREDICTION", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

# ---- tasks 4 to 6 -----------------------------------------------------------
d.opener("t4-open", "TASK 4", "Program or process?", "A program is a file. A process is a program that is running.")

d.slide("t4-figure", "A program stays. A process comes and goes.",
        lambda t: lanes(t, [("Program file", [("sleep: a file on the disk", 12, "used")]),
                            ("Process", [(None, 3, "free"), ("sleep 30 &amp;", 6, "hot"), (None, 3, "free")])], 132, height=110),
        note="which sleep finds the file before, during and after. ps shows a sleep line only while the process runs.")

d.slide("t4-commands", "Run it in the background",
        lambda t: row(col(term(t, ["which sleep",
                                   "sleep 30 &",
                                   "ps > task4_process_list.txt",
                                   "cat task4_process_list.txt"]),
                          term(t, ["ps", "which sleep"], title="thirty seconds later"),
                          gap=24, flex=None),
                      col(lst(t, ["The &amp; at the end runs the command in the background and gives you the prompt back.",
                                  "ps lists the processes of your terminal.",
                                  "Afterwards ps shows no sleep, but which sleep still finds the file."], size=32),
                          gap=24),
                      gap=56, align="center"),
        note="For your report: what did you see before, during and after?")

d.slide("t5-commands", "Task 5: several at once",
        lambda t: row(col(term(t, ["sleep 300 &               # type this line COUNT times",
                                   "ps > task5_multitasking.txt",
                                   "cat task5_multitasking.txt"]),
                          para(t, "The up-arrow key brings the last line back.", size=32),
                          gap=24, flex=None),
                      card(t, "Then take a screenshot", "Keep it as task5.png. Your terminal prompt and the ps result must both be visible.", label="FOR YOUR REPORT", icon_name="Search", pad=40, title_size=36),
                      gap=56, align="center"),
        note="ps now shows COUNT lines with sleep: several processes at the same time.")

d.slide("t5-share", "What multitasking really is",
        lambda t: lanes(t, [("One processor", [("A", 1, "used"), ("B", 1, "hot"), ("C", 1, "used"), ("A", 1, "hot"),
                                               ("B", 1, "used"), ("C", 1, "hot"), ("A", 1, "used"), ("B", 1, "hot")]),
                            ("Process A", [("run", 1, "hot"), (None, 2, "free"), ("run", 1, "hot"), (None, 2, "free"), ("run", 1, "hot"), (None, 1, "free")]),
                            ("Process B", [(None, 1, "free"), ("run", 1, "hot"), (None, 2, "free"), ("run", 1, "hot"), (None, 2, "free"), ("run", 1, "hot")]),
                            ("Process C", [(None, 2, "free"), ("run", 1, "hot"), (None, 2, "free"), ("run", 1, "hot"), (None, 2, "free")])], 190, height=92),
        note="The system switches between processes so fast that they seem to run together. A sleeping process uses no processor, so your instructor shows one that does.")

d.opener("t6-open", "TASK 6", "Is this a virtual machine?", "Ask the system which hardware it thinks it runs on.")

d.slide("t6-commands", "Four commands, one file",
        lambda t: term(t, ["systemd-detect-virt > task6_virtualization_check.txt",
                           'lscpu | grep -i "hypervisor vendor" >> task6_virtualization_check.txt',
                           "uname -r >> task6_virtualization_check.txt",
                           "hostname >> task6_virtualization_check.txt",
                           "cat task6_virtualization_check.txt"]),
        lambda t: flow(t, [("lscpu", "describes the processor"), ("|", "the pipe passes the output on"),
                           ("grep", "keeps the matching line"), ("the file", "one line is added")], 400, hot=1),
        gap=40)

d.slide("t6-result", "Reading the result",
        lambda t: tbl(t, ["First line", "What it means"],
                      [["kvm, vmware, or another name", "A virtual machine. The hypervisor vendor line names the program that runs it."],
                       ["wsl", "Linux running inside Windows. It is also a virtual environment."],
                       ["none", "Real hardware: no hypervisor was found."]],
                      [2, 5]),
        note="Take a screenshot as task6.png, then run oslab check lab1. All four milestones must show PASS.")

d.slide("early", "If you finish early",
        lambda t: row(card(t, "Plus", "Run top. The line that starts with Tasks counts every process on the server. Run nproc: it prints the number of processors. Compare both with your sleep lines.",
                           label="OPTIONAL", icon_name="Lightbulb", pad=40, title_size=40),
                      card(t, "Challenge", "ps -e lists every process of the server, and wc -l counts lines. How many are running? You started only a few. Who started the others?",
                           label="OPTIONAL", icon_name="Search", pad=40, title_size=40),
                      gap=24, align="stretch"),
        note="Neither is needed for full marks.")

# ---- checkpoint -------------------------------------------------------------
d.opener("cp-open", "LIVE CHECKPOINT", "Show what you can do alone", "Fifteen minutes near the end of the lab. Worth 3 of the 10 points.")

d.slide("cp-why", "Why is there a checkpoint?",
        lambda t: grid(card(t, "It shows what you can do alone", "For most of the lab you may use hints and AI tools. The checkpoint is the one moment without them. It tells you, and the instructor, which commands you really know.", icon_name="CheckCircle", pad=28, title_size=32),
                       card(t, "Your numbers are new", "The names and numbers change at the checkpoint. An answer copied from a neighbour, or from your own earlier output, does not fit.", icon_name="Key", pad=28, title_size=32),
                       card(t, "The instructor sees who needs help", "Your answers arrive at once. The instructor can explain a common mistake before the next lab builds on this one.", icon_name="Users", pad=28, title_size=32),
                       card(t, "It is fair", "Everyone gets the same kind of task. You can take it even if an earlier task is not finished.", icon_name="ThumbsUp", pad=28, title_size=32),
                       cols=2),
        gap=36)

d.slide("cp-steps", "What happens, step by step",
        lambda t: flow(t, [("1. The instructor opens it", "Close your AI tools"), ("2. oslab checkpoint lab1", "Answer five questions"),
                           ("3. A small file task", "Folder, file, copy, rename, list"), ("4. oslab check lab1", "The fifth milestone shows PASS")], 400, hot=1),
        lambda t: row(rule(t, "Before it opens", "The command only says: the checkpoint is not open yet. Wait for the instructor.", title_size=36),
                      rule(t, "While you work", "Use your terminal and what you learned in this lab. No AI tools, and no help from a neighbour.", title_size=36),
                      rule(t, "When you finish", "oslab check lab1 tells you whether the file task is right. You can fix it and check again.", title_size=36)),
        gap=56)

d.slide("cp-run", "What you see when you run it",
        lambda t: row(term(t, ["oslab checkpoint lab1",
                               ("out", "Checkpoint: your own work. Close AI tools; do not ask a neighbour."),
                               ("out", "Work alone, with AI tools closed. Use only commands from this lab."),
                               ("blank",),
                               ("out", "You start 3 copies of `sleep 300` in the background, then run `ps`."),
                               ("out", "How many lines with `sleep` does `ps` show?"),
                               ("in", "3"),
                               ("blank",),
                               ("out", "Type the kernel release of this server: the number that `uname -r` prints."),
                               ("in", "your answer")],
                           title="example: your numbers will be different", size=28),
                      col(h3(t, "The five questions"),
                          lst(t, ["How many sleep lines ps shows",
                                  "Whether the program file is still there afterwards",
                                  "The kernel release of the server",
                                  "How many files the file task leaves",
                                  "One sentence: program and process"], ordered=True, size=30),
                          para(t, "Type each answer after the &gt; and press Enter. Your answers are saved once: the first answer counts.", size=28),
                          gap=20),
                      gap=48, align="center"))

d.slide("cp-task", "Then the file task",
        lambda t: row(term(t, [("out", "Saved and sent to the instructor."),
                               ("blank",),
                               ("out", "Now do it for real, in your lab1 folder:"),
                               ("out", "  1. Make a folder named cp-forest and go into it."),
                               ("out", "  2. Create a file named maple.txt that contains the text: hello forest"),
                               ("out", "  3. Copy it to a file named maple-copy.txt."),
                               ("out", "  4. Rename maple.txt to maple-old.txt."),
                               ("out", "  5. Go back to the lab1 folder and save the list of files"),
                               ("out", "     of cp-forest in checkpoint.txt"),
                               ("out", "Then run: oslab check lab1")],
                           title="example: your names will be different", size=28),
                      col(h3(t, "You already know how"),
                          para(t, "These are the commands of Task 2: mkdir, cd, echo with &gt;, cp, mv and ls with &gt;.", size=32),
                          para(t, "The guide does not show the commands here. Writing them yourself is the test.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("cp-marks", "How the checkpoint is marked",
        lambda t: tbl(t, ["Part", "Points", "Who marks it, and how"],
                      [["Your answers to the questions", "1", "The computer. All right is 1 point. At least half right is half a point."],
                       ["The file task", "1", "The computer. oslab check lab1 looks at your folder and your files."],
                       ["Your one sentence", "1", "The instructor reads it."]],
                      [6, 2, 11]),
        lambda t: row(rule(t, "Can I answer again?", "No. Your answers are saved once. You can still fix the file task and run oslab check lab1 again.", title_size=36),
                      rule(t, "I did not finish Task 6", "Take the checkpoint anyway. It does not depend on your earlier files.", title_size=36)),
        gap=48)

# ---- part B -----------------------------------------------------------------
d.opener("b-open", "PART B · HOMEWORK", "Install, remove, purge", "On your own Ubuntu. Due before the next class. Worth 3 points.")

d.slide("b-flow", "How your work travels",
        lambda t: col(flow(t, [("1. The server", "your Part A files: git push"), ("GitHub", "your repository OS-GIC-YOUR_ID"),
                               ("2. Your own Ubuntu", "git clone")], 520, hot=0),
                      flow(t, [("3. Your own Ubuntu", "Task 3, screenshots, README: git push"), ("GitHub", "the same repository"),
                               ("4. The server", "git pull, then check with tree")], 520, hot=0),
                      gap=40),
        note="No Word or PDF reports: you use Markdown and Git. The server pushes first, your computer pushes second, and after that the server only pulls.",
        label=PART_B, gap=56)

d.slide("b-server", "Step 1: on the server, push your Part A files",
        lambda t: row(term(t, ["mkdir -p ~/os-gic-YOUR_ID/os-lab-YOUR_ID/lab1",
                               "cp ~/oslab-work/lab1/task*.txt ~/os-gic-YOUR_ID/os-lab-YOUR_ID/lab1/",
                               "cp -r ~/oslab-work/lab1/task2_files ~/os-gic-YOUR_ID/os-lab-YOUR_ID/lab1/",
                               "cd ~/os-gic-YOUR_ID",
                               "git init",
                               "git add .",
                               'git commit -m "Lab 1: Part A files"',
                               "git branch -M main",
                               "git remote add origin https://github.com/YOUR_USERNAME/OS-GIC-YOUR_ID.git",
                               "git push -u origin main"], title="student@server: ~", size=28),
                      col(lst(t, ["First create an empty repository named OS-GIC-YOUR_ID on GitHub.",
                                  "The first time, tell Git your name and email with git config.",
                                  "GitHub asks for a personal access token, not your password."], size=30),
                          gap=20),
                      gap=40, align="center"),
        note="Do this at the end of the class if there is time, so the instructor can help.",
        label=PART_B, gap=36)

d.slide("b-clone", "Step 2: on your own Ubuntu, clone",
        lambda t: row(term(t, ["git clone https://github.com/YOUR_USERNAME/OS-GIC-YOUR_ID.git os-gic-YOUR_ID",
                               "cd os-gic-YOUR_ID/os-lab-YOUR_ID/lab1",
                               "mkdir images",
                               "ls"], title="you@your-ubuntu: ~", size=30),
                      col(para(t, "ls shows the files you made on the server. They travelled through GitHub.", size=32),
                          para(t, "Stay in this lab1 folder for Task 3, so its result file is saved in the right place.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=PART_B)

d.slide("b-apt", "Task 3: what each command does",
        lambda t: tbl(t, ["Command", "What it does"],
                      [[mono("sudo apt-get update"), "Refreshes the list of available software. Installs nothing."],
                       [mono("sudo apt-get install mc"), "Downloads and installs the package."],
                       [mono("sudo apt-get remove mc"), "Uninstalls the program. Keeps its settings in /etc."],
                       [mono("sudo apt-get purge mc"), "Uninstalls the program and deletes its settings."]],
                      [2, 3]),
        note="mc is Midnight Commander. Its settings live in the folder /etc/mc.",
        label=PART_B)

d.slide("b-figure", "What happens to /etc/mc",
        lambda t: lanes(t, [("Step", [("start", 3, "used"), ("install", 3, "used"), ("remove", 3, "used"), ("purge", 3, "used")]),
                            ("Program", [("absent", 3, "free"), ("installed", 3, "hot"), ("gone", 3, "free"), ("gone", 3, "free")]),
                            ("Settings", [("absent", 3, "free"), ("present", 3, "hot"), ("still there", 3, "hot"), ("gone", 3, "free")])], 132, height=110),
        note="Remove keeps the settings. Only purge deletes them. Compare this with your prediction.",
        label=PART_B)

d.slide("b-commands", "Task 3: the three steps",
        lambda t: row(term(t, ["sudo apt-get update",
                               "sudo apt-get install mc -y",
                               "which mc > task3_apt.txt",
                               "ls -ld /etc/mc >> task3_apt.txt",
                               "sudo apt-get remove mc -y",
                               "ls -ld /etc/mc >> task3_apt.txt",
                               "sudo apt-get purge mc -y",
                               "ls -ld /etc/mc >> task3_apt.txt 2>&1",
                               "cat task3_apt.txt"], title="you@your-ubuntu: ~/os-gic-YOUR_ID/os-lab-YOUR_ID/lab1"),
                      col(para(t, "2&gt;&amp;1 also saves the error message when the folder is gone.", size=32),
                          para(t, "Then take a screenshot of the last ls -ld /etc/mc and keep it as task3.png.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=PART_B)

d.slide("b-shots", "Three screenshots, in the images folder",
        lambda t: row(card(t, "task3.png", "The ls -ld /etc/mc after the purge.", label="TASK 3", pad=40, title_size=40),
                      card(t, "task5.png", "The ps list with your sleep lines.", label="TASK 5", pad=40, title_size=40),
                      card(t, "task6.png", "The four commands of Task 6 and their result.", label="TASK 6", pad=40, title_size=40),
                      gap=24, align="stretch"),
        note="Every screenshot must show your terminal prompt, so it is clear whose work it is. Then fill in README.md from the report template.",
        label=PART_B)

d.slide("b-push", "Steps 3 and 4: push, then pull on the server",
        lambda t: row(col(h3(t, "Step 3: on your own Ubuntu"),
                          term(t, ["cd ../..",
                                   "git add .",
                                   'git commit -m "Lab 1: Task 3, screenshots and report"',
                                   "git push"], title="you@your-ubuntu: ~/os-gic-YOUR_ID/os-lab-YOUR_ID/lab1", size=28),
                          gap=20, flex=None),
                      col(h3(t, "Step 4: on the server"),
                          term(t, ["cd ~/os-gic-YOUR_ID",
                                   "git pull",
                                   "tree"], title="student@server: ~", size=28),
                          gap=20, flex=None),
                      gap=48, align="flex-start"),
        note="From now on, only pull on the server. Never edit your repository files there.",
        label=PART_B)

REPO_TREE = [("os-lab-YOUR_ID", [("lab1", [
    ("README.md", None),
    ("images", [("task3.png", None), ("task5.png", None), ("task6.png", None)]),
    ("task1_os_info.txt", None), ("task2_file_commands.txt", None),
    ("task2_files", [("FILE1.txt", None), ("FILE2_renamed.txt", None)]),
    ("task3_apt.txt", None), ("task4_process_list.txt", None), ("task5_multitasking.txt", None),
    ("task6_virtualization_check.txt", None)])])]

d.slide("b-tree", "What tree must show",
        lambda t: row(tree(t, "os-gic-YOUR_ID", REPO_TREE, cmd="tree", title="student@server: ~/os-gic-YOUR_ID", size=24, lh=1.17, blank=False),
                      col(h3(t, "Check it on the server"),
                          para(t, "After git pull, the tree must match this, with your own ID and your own file names.", size=32),
                          para(t, "Folders are shown in blue. The last line counts the folders and the files.", size=32),
                          para(t, "The course website checks these names to show your progress.", size=32),
                          gap=24),
                      gap=56, align="center"),
        label=PART_B, gap=28)

# ---- wrap up ----------------------------------------------------------------
d.slide("grading", "How Lab 1 is graded",
        lambda t: tbl(t, ["Evidence", "Points", "Where"],
                      [["Files: oslab check lab1 passes the four milestones", "2", "In class"],
                       ["Report: kernel and distribution, remove and purge, program and process, virtual machine", "2", "Homework"],
                       ["Prediction saved in time, and honestly corrected", "2", "In class"],
                       ["Live checkpoint: answers, the file task and one sentence", "3", "In class"],
                       ["The APT file, three screenshots and README, pushed and pulled on time", "1", "Homework"]],
                      [14, 2, 3]),
        note="Plus and Challenge are not needed for full marks.")

d.slide("mistakes", "Common mistakes",
        lambda t: tbl(t, ["Mistake", "What happens", "Fix"],
                      [["Typing FILE1 literally", "A file named FILE1.txt appears", "Use your own file1 from oslab values lab1"],
                       ["&gt; instead of &gt;&gt;", "The record keeps only the last line", "Use &gt;&gt; after the first line"],
                       ["Forgetting the &amp;", "The terminal waits and you cannot type", "Press Ctrl+C, run it again with &amp;"],
                       ["Running ps too late", "There is no sleep line", "Run ps right after you start sleep"],
                       ["Working in the wrong folder", "No such file or directory", "Check with pwd and ls"]],
                      [5, 6, 7]),
        gap=36)

t = d.alt()
d.add("takeaways", t, [h2("Key takeaways"), grid(
    card(t, "Kernel and distribution", "Linux is the kernel. Ubuntu is the kernel plus many other programs.", number="01", pad=32, title_size=32),
    card(t, "Program and process", "A program is a file. A process is a running copy of it.", number="02", pad=32, title_size=32),
    card(t, "Remove and purge", "Remove keeps the settings in /etc. Purge deletes them.", number="03", pad=32, title_size=32),
    card(t, "One arrow or two", "&gt; replaces a file. &gt;&gt; adds to its end.", number="04", pad=32, title_size=32),
    cols=2)], top=True, gap=40)

t = d.alt()
d.add("next", t, [
    h2("Next lab"),
    row(card(t, "Lab 2: navigation and files", "Absolute and relative paths, moving and copying files, and proving that a copy is identical.",
             label="COMING UP", icon_name="PaperPlane", pad=48, flex=3),
        card(t, "Reference", "The Lab 1 instruction and report template in the course repository, the Week 1 lecture notes, and man uname, man ls and man apt-get.",
             label="SOURCE", icon_name="Book", pad=48, flex=2),
        gap=24, align="stretch"),
])

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Linux in brief: why it matters, its origin, the kernel, distributions, families, package management, the shell and the prompt.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the two parts, the timetable, the helper commands and the rules.", "start": "lab-open"},
    "s4": {"description": "Task 1: the kernel and the distribution.", "start": "t1-open"},
    "s5": {"description": "Task 2: files and folders, and output redirection.", "start": "t2-open"},
    "s6": {"description": "The prediction.", "start": "predict-open"},
    "s7": {"description": "Tasks 4 to 6: programs and processes, multitasking and virtualization.", "start": "t4-open"},
    "s8": {"description": "The live checkpoint: why it exists, what happens and how it is marked.", "start": "cp-open"},
    "s9": {"description": "Part B, homework: installing and purging software, screenshots and the report.", "start": "b-open"},
    "s10": {"description": "Grading, common mistakes, takeaways and the next lab.", "start": "grading"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
