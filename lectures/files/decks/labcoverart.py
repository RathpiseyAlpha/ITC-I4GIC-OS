"""Cover illustrations for the lab guides: one 640x600 scene per lab, keyed by the deck folder ("lab-01").

Same engine and look as the week covers (`oscoverart.py`, `coverlib.py` in the shared library). The lab guides
are built in a scratch mirror (.claude/skills/os-lab-guide-deck/build_guide.py), which copies this file next to
`oslib.py`. No text is drawn.
"""
from coverlib import (RED, Art, Iso, NAVY, WHITE, S1, S2, S3, SKY, BLUE, AMBER, AMBER2, GREEN, light, mix,
                      window, beam, arrow, chip, cyl, padlock)

TERM = "#0b1830"
RED_ = RED


def terminal(a, x, y, w, h, rows):
    """A dark terminal window. rows: (indent, length, colour) bars, each led by a green prompt mark."""
    window(a, x, y, w, h)
    a.add(f'<path d="M{x},{y + 34} H{x + w} V{y + h - 14} Q{x + w},{y + h} {x + w - 14},{y + h} H{x + 14} Q{x},{y + h} {x},{y + h - 14} Z" '
          f'fill="{a.lg([(0, "#16315a"), (1, TERM)])}"/>')
    for i, (indent, length, c) in enumerate(rows):
        ry = y + 62 + i * 34
        a.add(f'<path d="M{x + 24},{ry - 8} l11,8 l-11,8" fill="none" stroke="{GREEN}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
              f'<rect x="{x + 48 + indent}" y="{ry - 5}" width="{length}" height="10" rx="5" fill="{c}"/>')


def folder(a, x, y, w, h, c):
    """A folder seen from the front: a tab on top of a body with a lit top edge."""
    a.add(f'<rect x="{x + 5}" y="{y + 10}" width="{w}" height="{h}" rx="10" fill="#050d1f" opacity=".35" filter="{a.blur(7)}"/>',
          f'<path d="M{x},{y + 10} Q{x},{y} {x + 10},{y} H{x + w * .38} L{x + w * .46},{y + 12} H{x + w - 10} Q{x + w},{y + 12} {x + w},{y + 22} V{y + h - 10} '
          f'Q{x + w},{y + h} {x + w - 10},{y + h} H{x + 10} Q{x},{y + h} {x},{y + h - 10} Z" fill="{a.lg([(0, light(c, .5)), (1, c)])}"/>',
          f'<rect x="{x + 8}" y="{y + 24}" width="{w - 16}" height="4" rx="2" fill="#fff" opacity=".55"/>')


def sheet(a, x, y, w, h, c):
    """A file: a white page with a folded corner and a coloured stripe."""
    a.add(f'<rect x="{x + 4}" y="{y + 8}" width="{w}" height="{h}" rx="6" fill="#050d1f" opacity=".3" filter="{a.blur(6)}"/>',
          f'<path d="M{x},{y + 6} Q{x},{y} {x + 6},{y} H{x + w - 16} L{x + w},{y + 16} V{y + h - 6} Q{x + w},{y + h} {x + w - 6},{y + h} H{x + 6} '
          f'Q{x},{y + h} {x},{y + h - 6} Z" fill="{a.lg([(0, WHITE), (1, S1)])}"/>',
          f'<path d="M{x + w - 16},{y} V{y + 16} H{x + w} Z" fill="{S2}"/>',
          f'<rect x="{x + 10}" y="{y + 26}" width="{w - 20}" height="6" rx="3" fill="{c}"/>'
          f'<rect x="{x + 10}" y="{y + 40}" width="{(w - 20) * .6:.0f}" height="6" rx="3" fill="{S3}" opacity=".6"/>')


# ---- lab 1: exploring operating system basics ---------------------------------------------------------------
def scene_lab01():
    a = Art()
    a.glow(320, 300, 250, "#bcd5ff", .3)
    terminal(a, 70, 50, 500, 250, [(0, 150, SKY), (30, 230, S1), (0, 110, AMBER), (30, 190, S1), (0, 70, S3)])
    for x, c in ((130, SKY), (290, AMBER), (450, GREEN)):                   # three running processes
        beam(a, x + 30, 310, 320, 400, SKY, 3, "2 10")
        a.add(f'<rect x="{x - 10}" y="300" width="80" height="50" rx="10" fill="{a.lg([(0, light(c, .5)), (1, c)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2.4"/>'
              f'<rect x="{x + 6}" y="316" width="48" height="6" rx="3" fill="#fff" opacity=".75"/><rect x="{x + 6}" y="330" width="30" height="6" rx="3" fill="#fff" opacity=".5"/>')
    iso = Iso(a, 320, 440, 1.1)
    a.shadow(320, 560, 230, 20)
    chip(iso, -45, -45, 0, 90, "#173366", AMBER, 5)
    iso.box(-165, -20, 0, 80, 30, 16, "#2f6fe0")                            # memory stick
    iso.on_top(-165, -20, 16, "".join(f'<rect x="{6 + i * 18}" y="5" width="12" height="20" rx="2" fill="#0b1830"/>' for i in range(4)))
    iso.box(85, -20, 0, 80, 30, 16, "#1e8a5a")                              # a second stick, for symmetry
    iso.on_top(85, -20, 16, "".join(f'<rect x="{6 + i * 18}" y="5" width="12" height="20" rx="2" fill="#0b1830"/>' for i in range(4)))
    return a.svg("Illustration of a terminal window above three running processes that share one processor chip")


# ---- lab 2: Linux navigation and file management ------------------------------------------------------------
def scene_lab02():
    a = Art()
    a.glow(320, 290, 250, "#bcd5ff", .3)
    for x1, y1, x2, y2 in ((320, 118, 150, 232), (320, 118, 320, 232), (320, 118, 490, 232),
                           (150, 292, 90, 388), (150, 292, 210, 388), (490, 292, 430, 388), (490, 292, 550, 388)):
        beam(a, x1, y1, x2, y2, SKY, 3, "2 10")
    folder(a, 250, 40, 140, 100, AMBER)                                     # the root folder
    for x, c in ((80, SKY), (250, GREEN), (420, "#9d7bff")):                # its three folders
        folder(a, x, 230, 140, 100, c)
    for x, c in ((40, SKY), (160, GREEN), (380, "#9d7bff"), (500, AMBER)):  # files inside them
        sheet(a, x, 380, 100, 90, c)
    a.add(f'<rect x="90" y="500" width="460" height="56" rx="28" fill="{a.lg([(0, "#16315a"), (1, TERM)])}" stroke="{SKY}" stroke-width="2.4"/>'
          f'<path d="M122,518 l14,10 l-14,10" fill="none" stroke="{GREEN}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
          f'<rect x="156" y="524" width="150" height="9" rx="4.5" fill="{S1}"/><rect x="320" y="524" width="70" height="9" rx="4.5" fill="{AMBER}"/>'
          f'<rect x="404" y="524" width="100" height="9" rx="4.5" fill="{S3}"/>')
    return a.svg("Illustration of a folder tree with files and a command line below it")


# ---- lab 3: wildcards and links -----------------------------------------------------------------------------
def scene_lab03():
    a = Art()
    a.glow(320, 300, 250, "#bcd5ff", .3)
    cyl(a, 320, 470, 110, 34, 74, "#c3cee4")                                # the data on the disk: one inode
    a.add(f'<rect x="250" y="470" width="140" height="8" rx="4" fill="{NAVY}" opacity=".35"/><circle cx="360" cy="500" r="5" fill="{GREEN}"/>')
    for x, c, y in ((60, SKY, 80), (255, GREEN, 60), (450, AMBER, 80)):     # three names
        sheet(a, x, y, 130, 120, c)
    beam(a, 125, 205, 270, 400, SKY, 3)                                     # a name and a hard link share the data
    beam(a, 320, 185, 320, 400, GREEN, 3)
    a.add(f'<path d="M515,205 C560,300 520,320 400,215" fill="none" stroke="{AMBER}" stroke-width="5" stroke-dasharray="12 10" stroke-linecap="round"/>'
          f'<polygon points="388,205 414,208 402,228" fill="{AMBER}"/>')    # a symbolic link points at a name
    return a.svg("Illustration of two file names that point at the same data on a disk and a third name that only points at another name")


# ---- lab 4: redirection, pipelines and data analysis --------------------------------------------------------
def stage(a, x, y, c):
    """One stage of a pipeline: a rounded block with a lit top and two short lines of text-like bars."""
    a.add(f'<rect x="{x + 5}" y="{y + 10}" width="130" height="110" rx="16" fill="#050d1f" opacity=".35" filter="{a.blur(8)}"/>',
          f'<rect x="{x}" y="{y}" width="130" height="110" rx="16" fill="{a.lg([(0, light(c, .5)), (1, c)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2.4"/>'
          f'<rect x="{x + 20}" y="{y + 30}" width="90" height="10" rx="5" fill="#fff" opacity=".8"/><rect x="{x + 20}" y="{y + 54}" width="60" height="10" rx="5" fill="#fff" opacity=".55"/>'
          f'<rect x="{x + 20}" y="{y + 78}" width="76" height="10" rx="5" fill="#fff" opacity=".4"/>')


def scene_lab04():
    a = Art()
    a.glow(320, 290, 250, "#bcd5ff", .3)
    sheet(a, 20, 120, 100, 130, SKY)                                        # the input file
    for x, c in ((170, GREEN), (330, "#9d7bff"), (490, AMBER)):             # three stages joined by pipes
        stage(a, x, 130, c)
    for x1, x2 in ((125, 168), (303, 328), (463, 488)):
        arrow(a, x1, 185, x2, 185, WHITE, 6, 16)
    a.add(f'<rect x="150" y="330" width="440" height="64" rx="32" fill="{a.lg([(0, "#16315a"), (1, TERM)])}" stroke="{SKY}" stroke-width="2.4"/>'
          f'<path d="M184,350 l14,12 l-14,12" fill="none" stroke="{GREEN}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
          f'<rect x="218" y="357" width="140" height="10" rx="5" fill="{S1}"/><rect x="372" y="357" width="80" height="10" rx="5" fill="{AMBER}"/>'
          f'<rect x="466" y="357" width="90" height="10" rx="5" fill="{S3}"/>')
    arrow(a, 555, 255, 555, 325, AMBER, 6, 20)                              # the result
    arrow(a, 395, 255, 395, 440, RED_, 6, 20)                               # a diagnostic, kept apart
    a.add(f'<rect x="300" y="450" width="190" height="64" rx="14" fill="{a.lg([(0, light(RED_, .45)), (1, RED_)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2.4"/>'
          f'<rect x="324" y="472" width="120" height="9" rx="4.5" fill="#fff" opacity=".8"/><rect x="324" y="490" width="80" height="9" rx="4.5" fill="#fff" opacity=".5"/>')
    return a.svg("Illustration of an input file passing through three connected pipeline stages to a result, with an error message kept on a separate path")


# ---- lab 5: threads and joining -----------------------------------------------------------------------------
def scene_lab05():
    a = Art()
    a.glow(320, 300, 250, "#bcd5ff", .3)
    window(a, 190, 40, 260, 130, SKY)                                       # main
    a.add(f'<rect x="215" y="100" width="150" height="10" rx="5" fill="{BLUE}" opacity=".7"/><rect x="215" y="124" width="200" height="8" rx="4" fill="{S3}" opacity=".5"/>')
    for x, c, y in ((50, GREEN, 260), (250, AMBER, 300), (450, "#9d7bff", 260)):   # three workers
        a.add(f'<path d="M{320},{172} C{320},{225} {x + 70},{200} {x + 70},{y}" fill="none" stroke="{WHITE}" stroke-width="4" stroke-dasharray="2 10" stroke-linecap="round"/>')
        a.add(f'<rect x="{x + 5}" y="{y + 10}" width="140" height="90" rx="16" fill="#050d1f" opacity=".35" filter="{a.blur(8)}"/>'
              f'<rect x="{x}" y="{y}" width="140" height="90" rx="16" fill="{a.lg([(0, light(c, .5)), (1, c)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2.4"/>'
              f'<rect x="{x + 22}" y="{y + 26}" width="96" height="10" rx="5" fill="#fff" opacity=".8"/><rect x="{x + 22}" y="{y + 50}" width="62" height="10" rx="5" fill="#fff" opacity=".5"/>')
    a.add(f'<path d="M{50 + 70},{352} C{120},{440} 270,{440} 320,{455}" fill="none" stroke="{SKY}" stroke-width="4" stroke-linecap="round"/>'
          f'<path d="M{250 + 70},{392} V455" fill="none" stroke="{SKY}" stroke-width="4" stroke-linecap="round"/>'
          f'<path d="M{450 + 70},{352} C{520},{440} 370,{440} 320,{455}" fill="none" stroke="{SKY}" stroke-width="4" stroke-linecap="round"/>')
    a.add(f'<rect x="210" y="450" width="220" height="68" rx="34" fill="{a.lg([(0, light(AMBER, .5)), (1, AMBER2)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2.4"/>'
          f'<rect x="250" y="478" width="140" height="12" rx="6" fill="#fff" opacity=".8"/>')                    # join: all arrows meet
    return a.svg("Illustration of a main program starting three workers that all meet again at a join before the result is used")


# ---- lab 6: users, groups and permissions -------------------------------------------------------------------
def scene_lab06():
    a = Art()
    a.glow(320, 290, 250, "#bcd5ff", .3)
    folder(a, 60, 70, 210, 150, AMBER)                                      # a private folder with a padlock
    padlock(a, 165, 175, 1.3, AMBER)
    folder(a, 370, 70, 210, 150, GREEN)                                     # a shared folder, readable
    sheet(a, 440, 140, 70, 80, SKY)
    for x, bits, label in ((60, "rw-", 0), (250, "r--", 1), (440, "---", 2)):      # owner, group and others
        a.add(f'<rect x="{x}" y="320" width="140" height="150" rx="16" fill="{a.lg([(0, WHITE), (1, S1)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2.4"/>')
        for i, ch in enumerate(bits):
            on = ch != "-"
            c = (GREEN if i == 0 else AMBER if i == 1 else SKY) if on else S2
            a.add(f'<rect x="{x + 14 + i * 40}" y="{352}" width="32" height="78" rx="9" fill="{a.lg([(0, light(c, .5)), (1, c)]) if on else "none"}" '
                  f'stroke="{c}" stroke-width="2.6"{"" if on else " stroke-dasharray=\"6 5\""}/>')
    a.add(f'<rect x="60" y="490" width="140" height="10" rx="5" fill="{GREEN}"/><rect x="250" y="490" width="140" height="10" rx="5" fill="{AMBER}"/>'
          f'<rect x="440" y="490" width="140" height="10" rx="5" fill="{SKY}"/>')
    return a.svg("Illustration of a locked private folder, a readable shared folder and three groups of permission bits for owner, group and others")


# ---- lab 7: Bash scripting ----------------------------------------------------------------------------------
def scene_lab07():
    a = Art()
    a.glow(320, 290, 250, "#bcd5ff", .3)
    terminal(a, 70, 40, 500, 260, [(0, 60, AMBER), (0, 220, S1), (30, 180, SKY), (30, 120, S1), (0, 90, GREEN)])
    a.add(f'<path d="M96,140 l14,0" stroke="{AMBER}" stroke-width="4" stroke-linecap="round"/>')
    for x, w, c, quote in ((90, 170, SKY, True), (290, 110, GREEN, False), (420, 120, AMBER, True)):     # arguments, two kept whole
        y = 360
        a.add(f'<rect x="{x}" y="{y}" width="{w}" height="60" rx="30" fill="{a.lg([(0, light(c, .5)), (1, c)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2.4"/>'
              f'<rect x="{x + 24}" y="{y + 25}" width="{w - 48}" height="10" rx="5" fill="#fff" opacity=".8"/>')
        if quote:
            a.add(f'<path d="M{x - 12},{y + 8} v44 M{x + w + 12},{y + 8} v44" stroke="{WHITE}" stroke-width="5" stroke-linecap="round"/>')
        beam(a, x + w / 2, 300, x + w / 2, 358, SKY, 3, "2 10")
    a.add(f'<rect x="150" y="470" width="340" height="60" rx="30" fill="{a.lg([(0, "#16315a"), (1, TERM)])}" stroke="{SKY}" stroke-width="2.4"/>'
          f'<path d="M184,488 l14,12 l-14,12" fill="none" stroke="{GREEN}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
          f'<rect x="218" y="494" width="110" height="10" rx="5" fill="{S1}"/><rect x="342" y="494" width="100" height="10" rx="5" fill="{AMBER}"/>')
    arrow(a, 320, 425, 320, 466, WHITE, 5, 16)
    return a.svg("Illustration of a script in a terminal receiving three arguments, two of them kept whole inside quotes, and running as a command")


# ---- lab 8: race conditions and file locking ----------------------------------------------------------------
def scene_lab08():
    a = Art()
    a.glow(320, 290, 250, "#bcd5ff", .3)
    for x, c in ((40, SKY), (400, AMBER)):                                  # two buyers
        window(a, x, 60, 200, 140, c)
        a.add(f'<rect x="{x + 22}" y="{110}" width="110" height="10" rx="5" fill="{BLUE}" opacity=".7"/><rect x="{x + 22}" y="{134}" width="150" height="8" rx="4" fill="{S3}" opacity=".5"/>'
              f'<rect x="{x + 22}" y="{154}" width="80" height="8" rx="4" fill="{S3}" opacity=".4"/>')
    sheet(a, 250, 330, 140, 150, GREEN)                                     # the shared stock file
    a.add(f'<rect x="268" y="400" width="104" height="34" rx="8" fill="{NAVY}" opacity=".12"/>')
    for x1, x2 in ((140, 262), (500, 378)):                                  # both want to write at once
        arrow(a, x1, 210, x2, 318, RED, 6, 20)
    padlock(a, 320, 285, 1.1, AMBER)                                        # the lock that makes them take turns
    return a.svg("Illustration of two buyers both writing to one shared stock file, with a padlock that makes them take turns")


# ---- lab 9: deadlock ----------------------------------------------------------------------------------------
def scene_lab09():
    a = Art()
    a.glow(320, 300, 250, "#bcd5ff", .3)
    nodes = ((320, 90, "p", SKY), (520, 300, "r", AMBER), (320, 510, "p", GREEN), (120, 300, "r", "#9d7bff"))   # A, Beta, B, Alpha
    for (x1, y1, *_), (x2, y2, *_) in zip(nodes, nodes[1:] + nodes[:1]):                                       # a closed wait cycle
        dx, dy = x2 - x1, y2 - y1
        n = (dx * dx + dy * dy) ** .5
        arrow(a, x1 + dx / n * 70, y1 + dy / n * 70, x2 - dx / n * 70, y2 - dy / n * 70, RED, 7, 24)
    for x, y, kind, c in nodes:
        if kind == "p":
            a.add(f'<circle cx="{x + 5}" cy="{y + 10}" r="58" fill="#050d1f" opacity=".35" filter="{a.blur(8)}"/>'
                  f'<circle cx="{x}" cy="{y}" r="58" fill="{a.lg([(0, light(c, .5)), (1, c)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2.6"/>'
                  f'<rect x="{x - 28}" y="{y - 6}" width="56" height="10" rx="5" fill="#fff" opacity=".8"/>')
        else:
            a.add(f'<rect x="{x - 50 + 5}" y="{y - 50 + 10}" width="100" height="100" rx="18" fill="#050d1f" opacity=".35" filter="{a.blur(8)}"/>'
                  f'<rect x="{x - 50}" y="{y - 50}" width="100" height="100" rx="18" fill="{a.lg([(0, light(c, .5)), (1, c)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2.6"/>')
            padlock(a, x, y + 4, .8, c)
    return a.svg("Illustration of two workers and two locked resources joined by arrows in a closed circle, a circular wait")


# ---- lab 10: backups, archives and cron ---------------------------------------------------------------------
def scene_lab10():
    a = Art()
    a.glow(320, 300, 250, "#bcd5ff", .3)
    a.add(f'<circle cx="160" cy="180" r="100" fill="#050d1f" opacity=".35" filter="{a.blur(10)}" transform="translate(6,12)"/>'
          f'<circle cx="160" cy="180" r="100" fill="{a.lg([(0, WHITE), (1, S1)])}" stroke="#fff" stroke-width="3"/>'
          f'<circle cx="160" cy="180" r="84" fill="none" stroke="{S2}" stroke-width="2.4" stroke-dasharray="3 14" stroke-linecap="round"/>'
          f'<line x1="160" y1="180" x2="160" y2="116" stroke="{NAVY}" stroke-width="8" stroke-linecap="round"/>'
          f'<line x1="160" y1="180" x2="206" y2="206" stroke="{BLUE}" stroke-width="8" stroke-linecap="round"/>'
          f'<circle cx="160" cy="180" r="11" fill="{AMBER}"/>')
    beam(a, 270, 180, 360, 180, SKY, 3, "2 10")
    for i, c in enumerate((GREEN, GREEN, GREEN)):                           # three kept archives, newest on top
        y = 300 - i * 62
        a.add(f'<rect x="{385 + 6}" y="{y + 10}" width="190" height="52" rx="12" fill="#050d1f" opacity=".35" filter="{a.blur(7)}"/>'
              f'<rect x="385" y="{y}" width="190" height="52" rx="12" fill="{a.lg([(0, light(c, .5)), (1, c)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2.4"/>'
              f'<rect x="405" y="{y + 20}" width="110" height="10" rx="5" fill="#fff" opacity=".8"/><circle cx="548" cy="{y + 26}" r="9" fill="#fff" opacity=".8"/>')
    a.add(f'<rect x="385" y="388" width="190" height="52" rx="12" fill="none" stroke="{S2}" stroke-width="2.4" stroke-dasharray="8 7" opacity=".8"/>'
          f'<path d="M420,414 h110" stroke="{S2}" stroke-width="4" stroke-linecap="round" opacity=".8"/>')    # the oldest is dropped
    cyl(a, 160, 450, 90, 28, 60, "#c3cee4")
    arrow(a, 160, 380, 160, 418, WHITE, 6, 18)
    return a.svg("Illustration of a clock that triggers a backup, three archives kept and the oldest one dropped, with the data on a disk")


# ---- lab 11: disk management utilities (bonus) --------------------------------------------------------------
def scene_lab11():
    a = Art()
    a.glow(320, 300, 250, "#bcd5ff", .3)
    a.add(f'<rect x="75" y="60" width="490" height="260" rx="24" fill="#050d1f" opacity=".3" filter="{a.blur(10)}" transform="translate(6,12)"/>'
          f'<rect x="70" y="50" width="500" height="260" rx="24" fill="{a.lg([(0, WHITE), (1, S1)])}" stroke="#fff" stroke-width="3"/>')
    n = 0
    for r in range(5):                                                      # a file's blocks: written ones are filled, holes are dashed
        for c in range(10):
            x, y = 96 + c * 46, 80 + r * 44
            filled = (r * 10 + c) % 7 in (0, 1, 3)
            if filled:
                col = (GREEN, AMBER, SKY)[(r + c) % 3]
                a.add(f'<rect x="{x}" y="{y}" width="38" height="34" rx="7" fill="{a.lg([(0, light(col, .5)), (1, col)])}" stroke="#fff" stroke-opacity=".8" stroke-width="1.6"/>')
            else:
                a.add(f'<rect x="{x}" y="{y}" width="38" height="34" rx="7" fill="none" stroke="{S2}" stroke-width="2" stroke-dasharray="5 4"/>')
    cyl(a, 170, 460, 100, 32, 70, "#c3cee4")
    a.add(f'<rect x="100" y="456" width="140" height="8" rx="4" fill="{NAVY}" opacity=".35"/><circle cx="262" cy="486" r="5" fill="{GREEN}"/>')
    a.add(f'<rect x="340" y="420" width="220" height="26" rx="13" fill="{a.lg([(0, WHITE), (1, S1)])}" stroke="{S2}" stroke-width="2"/>'
          f'<rect x="340" y="470" width="220" height="26" rx="13" fill="none" stroke="{S2}" stroke-width="2" stroke-dasharray="6 5"/>'
          f'<rect x="340" y="470" width="96" height="26" rx="13" fill="{a.lg([(0, light(AMBER, .5)), (1, AMBER)])}" stroke="#fff" stroke-opacity=".8" stroke-width="2"/>')
    return a.svg("Illustration of a sparse file whose written blocks are filled and whose holes are dashed, beside a full length bar and a shorter allocated bar")


SCENES = {"lab-01": scene_lab01, "lab-02": scene_lab02, "lab-03": scene_lab03, "lab-04": scene_lab04, "lab-05": scene_lab05, "lab-06": scene_lab06, "lab-07": scene_lab07, "lab-08": scene_lab08, "lab-09": scene_lab09, "lab-10": scene_lab10, "lab-11": scene_lab11}


def cover(deck, key, title, subtitle, size=96):
    """Set the cover of a lab guide in the lecture-slide style: DM Sans text and a Newsreader title, though the guide itself is in Ubuntu."""
    import decklib
    import oslib
    saved = oslib.SERIF
    oslib.SERIF = "font-family:'Newsreader', Georgia, serif"
    try:
        body = oslib.cover(deck.week, title, subtitle, decklib.ASSET["seal"], size, SCENES[key]())
    finally:
        oslib.SERIF = saved
    deck.S["cover"] = (oslib.D, None, body.replace('<p style="', '<p style="font-family:\'DM Sans\', Arial, sans-serif;'), {})
