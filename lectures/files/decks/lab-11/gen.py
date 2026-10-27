"""Lab 11 guide, Linux Disk Management Utilities (bonus). Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

A guide for the lab session, built like the Lab 3 to Lab 10 guides with the shared look and the shared standard
slides in labkit.py. The whole lab is optional bonus work. The concepts section is new: capacity, length and
allocation are three different sizes, sparse files and holes, what a regular image file is, and what
formatting adds. The lab part follows labs/lab11/lab11-instruction.md. Mounting through FUSE, checking and
growing an image, a small diagnostic utility and storage thresholds are optional extensions in that
instruction, so they come last (images.json is empty).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, listing, flow, init)  # noqa: E402,F401

WEEK = "Lab 11"
TITLE = "Operating Systems — Lab 11"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-28T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 11)
S = d.S
CW, HALF = labkit.CW, labkit.HALF

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-11", "Disk Management Utilities",
                  "Lab 11 guide (bonus): measure capacity, length and allocation, and build and inspect a disk image safely.", size=96)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Read filesystem capacity and per-file allocation, without mixing up df, du and apparent size.",
                    "Create a bounded sparse regular image, and explain the difference between length and allocation.",
                    "Format and inspect only an image you own, or read a supplied metadata trace and state its limits."], ordered=True, size=34, flex=3),
            card(t, "Lab 11, bonus", "The whole lab is optional bonus work. Skipping it carries no penalty. First the concepts, then the lab. Mounting and resizing are extensions, so they come last.", label="THIS LAB", flex=2),
            gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "A file is 8 MB long. Does it use 8 MB of the disk?",
         "What if most of it was never written? Which command would tell you, and which would only tell you the length?")

# ---- concepts first ---------------------------------------------------------
d.opener("bg-open", "CONCEPTS FIRST", "Three sizes of a file", "Three ideas: the capacity of a filesystem, the length of a file, and the space really allocated to it.")

d.slide("three", "Capacity, length and allocation",
        lambda t: tbl(t, ["Size", "Tool", "Answers"],
                      [["Capacity and free space", mono("df -hT"), "How big is the whole filesystem, and how much is free?"],
                       ["Apparent length", mono("ls -l, stat %s"), "How many bytes does the file claim to have?"],
                       ["Allocated space", mono("du -h, stat %b x %B"), "How many disk blocks does the file really occupy?"]],
                      [5, 5, 9]),
        note="The three can differ. df covers a whole mounted filesystem, not one file. A sparse file can be long and small at the same time.",
        label=BG)

d.slide("sparse", "A sparse file has holes",
        lambda t: row(term(t, ["truncate -s 8M images/demo-sparse.img",
                               "dd if=/dev/zero of=images/demo-written.img bs=1M count=8 status=none",
                               "ls -lh images/demo-*.img",
                               "du -h images/demo-*.img"], size=24),
                      col(para(t, "truncate -s 8M sets the length to 8 MiB without writing the bytes. The unwritten part is a hole: reads give zeros, and no block is used.", size=30),
                          para(t, "dd copies bytes. Here it writes 8 MiB of real zeros, so every block is allocated.", size=30),
                          para(t, "Both files have the same length. du shows the difference.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=BG)

d.slide("stat", "Reading stat",
        lambda t: row(term(t, ["stat -c '%n length=%s blocks=%b block-unit=%B' images/demo-*.img",
                               ("out", "images/demo-sparse.img length=8388608 blocks=0 block-unit=512"),
                               ("out", "images/demo-written.img length=8388608 blocks=16384 block-unit=512")], size=24),
                      col(para(t, "%s is the length in bytes. %b is the number of blocks, and %B is the size of one counted block.", size=30),
                          para(t, "Allocated bytes = %b times %B. Here: 16384 times 512 is 8 MiB for the written file, and nothing for the sparse one.", size=30),
                          para(t, "The exact figures depend on the host filesystem, and compression or deduplication can change them.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=BG)

d.slide("image", "A disk image is a regular file",
        lambda t: row(card(t, "A file that acts as a disk", "A disk image is an ordinary file whose bytes are laid out like a disk. A tool can format it like a disk.", label="IMAGE", pad=40, title_size=36),
                      card(t, "Check before you format", "Make sure it is a regular file, not a link, and that it is inside your own workspace. Never point a tool at a /dev/ device.", label="SAFETY", pad=40, title_size=36),
                      card(t, "Formatting adds metadata", "mkfs writes structures that describe the filesystem. The length stays the same, but some blocks are now allocated.", label="FORMAT", pad=40, title_size=36),
                      gap=32, align="stretch"),
        label=BG)

# ---- the lab ----------------------------------------------------------------
d.opener("lab-open", "LAB 11 (BONUS)", "Measure before you resize", "QuantumTech's build server is short of storage. Rehearse safe measurements on your own image files.")

START_TREE = [("images", [("README.txt", None)]), ("evidence", [])]

labkit.scenario(d, 11, "QuantumTech's build server", "The server is running low on storage. Rehearse safe capacity measurements on regular image files you own, and tell apparent length from allocated blocks before anyone thinks about mounting or resizing.",
                "This whole lab is bonus work. Skipping it carries no penalty.", START_TREE)
labkit.timetable(d, [["0 to 10", "Introduction, objectives and setup"],
                     ["10 to 25", "Levels 0 and 1, guided: inventory and usage"],
                     ["25 to 35", "Written prediction"],
                     ["35 to 50", "Level 2: create and inspect an image"]],
                 [["50 to 70", "Level 3: format and inspect metadata"],
                  ["70 to 85", "Tests and feedback"],
                  ["85 to 100", "Individual changed-case checkpoint"],
                  ["100 to 120", "Correction, cleanup and submission"]])
labkit.rules(d, safety="Never use a /dev/ device, a partition or a mount point. Only regular files in your workspace.")
labkit.setup_slides(d, 11, START_TREE,
                    ["images/README.txt is a reminder about regular image files.",
                     "The images you make go in images/. They are large, so they are not submission files.",
                     "The helper also writes a hidden file, .oslab-managed.json. Leave it as it is."])

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Inventory and usage", "Levels 0 and 1, with the instructor: fifteen minutes.")

d.slide("g-df", "Step 1: capacity, read only",
        lambda t: row(term(t, ['df -hT "$PWD"',
                               "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT"], size=26),
                      col(para(t, "df reports the filesystem that holds the current folder: its size, its type and how much is free.", size=30),
                          para(t, "lsblk lists the devices you can see. In WSL or a container the view can differ.", size=30),
                          card(t, "Only look", "These are read-only observations. They are not permission to format any device in the list.", label="CAREFUL", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-two", "Step 2: two files of equal length",
        lambda t: row(term(t, ["truncate -s 8M images/demo-sparse.img",
                               "dd if=/dev/zero of=images/demo-written.img bs=1M count=8 status=none",
                               "ls -lh images/demo-*.img",
                               "du -h images/demo-*.img",
                               "stat -c '%n length=%s blocks=%b block-unit=%B' images/demo-*.img"], size=24),
                      col(para(t, "/dev/zero is only a source of zero bytes. Both output paths are regular files you own.", size=30),
                          para(t, "Both lengths are 8 MiB. The sparse file normally uses fewer blocks.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-compute", "Step 3: compute the allocation",
        lambda t: row(card(t, "Compute", "Allocated bytes = %b times %B. Compare the result with the length %s for each file.", label="TRY", pad=40, title_size=36),
                      card(t, "Observe", "Does df show the allocation of one file? Does du have to equal ls -l for a sparse file?", label="THINK", pad=40, title_size=36),
                      gap=32, align="stretch"))

labkit.predict(d, "A 32 MiB file is created with truncate without writing all its bytes. Predict its apparent size, and whether its allocated space must also be 32 MiB. Explain what the holes represent.")

# ---- levels 2 and 3 ---------------------------------------------------------------
d.opener("l2-open", "LEVEL 2", "Create and inspect an image", "Fifteen minutes, from minute 35 to 50.")

d.slide("l2-make", "Step 1: a bounded image, and proof it is regular",
        lambda t: row(term(t, ["truncate -s 32M images/scratch.img",
                               "test -f images/scratch.img && test ! -L images/scratch.img",
                               "readlink -f images/scratch.img",
                               "stat -c '%F %n length=%s blocks=%b block-unit=%B' images/scratch.img",
                               "du -h images/scratch.img"], size=24),
                      col(para(t, "test -f is true for a regular file. test ! -L is true when it is not a symbolic link. readlink -f prints the real path.", size=30),
                          para(t, "Confirm all three before any command that formats. Never use a /dev/ path, a partition or a mount point instead.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("l2-save", "Step 2: save the sizes",
        lambda t: row(term(t, ["{",
                               "  stat -c '%n length=%s blocks=%b block-unit=%B' images/*.img",
                               "  du -h images/*.img",
                               '  df -hT "$PWD"',
                               "} > evidence/sizes.txt"], size=24),
                      col(para(t, "Record the length and the allocation of every image, with the filesystem capacity.", size=30),
                          card(t, "Explain", "Compare the new image with the two guided files. Why is the length of a file not the space reserved for it?", label="THINK", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.opener("l3-open", "LEVEL 3", "Format and inspect metadata", "Twenty minutes, from minute 50 to 70.")

d.slide("l3-tools", "Step 1 and 2: check the tools, then format only the image",
        lambda t: row(term(t, ["command -v mkfs.ext4",
                               "command -v dumpe2fs",
                               "if test -f images/scratch.img && test ! -L images/scratch.img; then",
                               "    mkfs.ext4 -F images/scratch.img",
                               "fi",
                               "dumpe2fs -h images/scratch.img > evidence/filesystem.txt 2>&1"], size=24),
                      col(para(t, "Use this only if both tools exist. mkfs.ext4 replaces the contents of the image, so do it once, on a new image you own.", size=30),
                          para(t, "-F lets mkfs work on a regular file. It is not a safety check. The fixed path and the test before it are the safety.", size=30),
                          para(t, "dumpe2fs -h prints the header of the filesystem. Then run stat and du again on the image and compare.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("l3-read", "Step 3: read the header",
        lambda t: row(lst(t, ["Find the filesystem UUID, the block count, the free blocks and the block size.",
                              "Estimate the filesystem size: block count times block size.",
                              "Explain why not every block is free for your data: some hold metadata or are reserved."], ordered=True, size=32, flex=3),
                      card(t, "Complete when", "Your measurements tell capacity, length and allocation apart. The image stays bounded and regular. Your metadata claims match a real header or a supplied trace that you label as such.", label="DONE", pad=32, title_size=32, flex=2),
                      gap=48, align="stretch"))

d.slide("l3-trace", "Step 4: no tools? Use a labelled trace",
        lambda t: row(term(t, ["cat > evidence/filesystem.txt <<'TRACE'",
                               "Illustrative ext4 header excerpt; not measured on this machine.",
                               "Filesystem UUID: 11111111-2222-3333-4444-555555555555",
                               "Block count: 32768",
                               "Free blocks: 25830",
                               "Block size: 1024",
                               "TRACE"], size=24),
                      col(para(t, "Save the excerpt as it is, with its label. In your report write: metadata interpretation only; formatting not executed.", size=30),
                          para(t, "The numbers describe a 32 MiB filesystem with some space used or reserved. They say nothing about your real image or free space.", size=30),
                          gap=22),
                      gap=48, align="center"))

# ---- tests ---------------------------------------------------------------------
d.opener("test-open", "TESTS AND FEEDBACK", "Three comparisons", "Fifteen minutes, from minute 70 to 85.")

d.slide("tests-table", "The three comparisons, and their limits",
        lambda t: tbl(t, ["Case", "Evidence", "Claim and limit"],
                      [["Sparse and fully written, 8 MiB", "Length and blocks of each", "Allocation depends on the content and the host filesystem"],
                       ["Fresh and formatted, 32 MiB", "Size before and after, and the header", "Formatting adds metadata. It does not show that FUSE works"],
                       ["Capacity", "df for the filesystem that holds the image", "It covers the whole filesystem, not only the image"]],
                      [5, 6, 8]),
        note="Add the allocation of the formatted image to evidence/sizes.txt. If you used a trace, label it as supplied evidence, not a local test. FUSE is not needed here, because this core never mounts.")

d.slide("tests-trouble", "If something does not work",
        lambda t: row(rule(t, "A large image and reset", "oslab reset refuses an archive over 2 MB. Save your evidence and remove your own unmounted image files first, or keep the workspace.", title_size=36),
                      rule(t, "No tools", "Without mkfs.ext4 or dumpe2fs, the sparse-file work and the checkpoint still work. Use the labelled trace.", title_size=36),
                      rule(t, "Stay safe", "Only regular files in your workspace. See man du and man mkfs.ext4.", title_size=36)))

# ---- checkpoint, correction, submission -------------------------------------------
labkit.checkpoint(d, "Two files have the same apparent length. One was made sparsely with truncate, the other was fully written with zero bytes. Predict how their allocated blocks may differ, and name a command and field that checks it. Why is df not enough to say which file uses the space?")
labkit.correction(d, "(a) Why can a 32 MiB image occupy fewer allocated bytes? (b) Why does formatting change allocation? (c) What did you observe here, and what needs real FUSE or server validation?")
labkit.submission(d, 11, ['cp -- evidence/sizes.txt evidence/filesystem.txt "$SUBMISSION_REPO/lab11/evidence/"'],
                  [("README.md", None), ("evidence", [("sizes.txt", None), ("filesystem.txt", None)])],
                  note="Keep the large image files in your workspace. They are not submission files. filesystem.txt is a real header or a trace you labelled.")
labkit.grading(d, [["Bounded regular-image measurements and metadata interpretation, correct", "3"],
                   ["Sparse and written, fresh and formatted comparisons, with the limits stated", "2"],
                   ["df, du and length explained, and the filesystem metadata; original prediction and correction", "2"],
                   ["Individual checkpoint: result or diagnosis, and mechanism", "2"],
                   ["Concise, attributable evidence and the required artifacts", "1"]],
               note="This lab is bonus work, so its points are extra. Other valid commands and names earn credit. If you use AI, note one useful suggestion and how you verified it.")
labkit.mistakes(d, [["A /dev/ path instead of your image", "A real device could be damaged", "Only a regular file in your workspace"],
                    ["Reading length as space used", "A sparse file looks bigger than it is", "Compare %s with %b times %B"],
                    ["Formatting a file you still need", "Its contents are gone", "Format only a new image, once"],
                    ["Calling a trace a measurement", "A claim your evidence cannot back", "Label supplied traces as such"]])

# ---- beyond the core --------------------------------------------------------------
d.opener("ext-open", "BEYOND THE CORE", "Mounting, checking and growing", "Optional extensions. They need FUSE or a prepared machine, and never run on the shared server's real devices.")

d.slide("ext-mount", "Mount an image, then check and grow it",
        lambda t: row(card(t, "Mount without root", "A FUSE tool can show the files inside an image under a folder you own. Unmount it as soon as you have looked.", label="FUSE", pad=32, title_size=32),
                      card(t, "Check", "e2fsck -n reads the filesystem and reports problems without changing anything.", label="CHECK", pad=32, title_size=32),
                      card(t, "Grow", "truncate makes the file longer, then resize2fs grows the filesystem to fit. Each step changes what df reports.", label="GROW", pad=32, title_size=32),
                      gap=32, align="stretch"),
        label=EXT)

d.slide("ext-util", "A small diagnostic utility",
        lambda t: row(card(t, "A script of your own", "Print df, the largest folders with du, and a warning when usage passes a threshold you choose.", label="UTILITY", pad=32, title_size=32),
                      card(t, "Read thresholds with care", "80 percent means different things on a 10 GB disk and a 10 TB disk. Think about what remains, and how fast it fills.", label="THRESHOLDS", pad=32, title_size=32),
                      card(t, "Always clean up", "Unmount, and remove your own image files, before you finish.", label="CLEANUP", pad=32, title_size=32),
                      gap=32, align="stretch"),
        label=EXT)

d.close([("Three sizes", "Capacity is for a filesystem, length is for a file, and allocation is the space really used."),
         ("Sparse files", "Holes read as zeros and use no blocks, so length and allocation can differ a lot."),
         ("Only your own regular files", "Never aim a format command at a device. Check the path first."),
         ("Say what you measured", "A header you read is evidence. A supplied trace is only an illustration.")],
        "chapter 14, File-System Implementation", ("The end of the labs", "Look back at your reports, and bring the questions you could not answer yourself."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: capacity, length and allocation, sparse files, stat, and disk images.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the rules, setup and the starting tree.", "start": "lab-open"},
    "s4": {"description": "Guided: inventory and usage, then the prediction.", "start": "g-open"},
    "s5": {"description": "Levels 2 and 3: create and inspect an image, format it, then the tests.", "start": "l2-open"},
    "s6": {"description": "The individual checkpoint: why, and the practice question.", "start": "cp-open"},
    "s7": {"description": "Correction, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: mounting, checking, growing and a utility, then takeaways.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
