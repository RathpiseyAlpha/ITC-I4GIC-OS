"""Cover illustrations for the lab guides: one 640x600 scene per lab, keyed by the deck folder ("lab-01").

Same engine and look as the week covers (`oscoverart.py`, `coverlib.py` in the shared library). The lab guides
are built in a scratch mirror (.claude/skills/os-lab-guide-deck/build_guide.py), which copies this file next to
`oslib.py`. No text is drawn.
"""
from coverlib import (Art, Iso, NAVY, WHITE, S1, S2, S3, SKY, BLUE, AMBER, AMBER2, GREEN, light, mix,
                      window, beam, arrow, chip)

TERM = "#0b1830"


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


SCENES = {"lab-01": scene_lab01, "lab-02": scene_lab02}


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
