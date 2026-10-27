"""Lab 7 guide, Bash Scripting, Permissions and Server Automation. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

A guide for the lab session, built like the Lab 3 to Lab 6 guides with the shared look and the shared standard
slides in labkit.py. The concepts section is new (the lab folder has only an old PDF, not a guide): what a
script is, the shebang and execute permission, arguments and "$@", quoting and word splitting, `--` and
leading-dash names, and exit status. The lab part follows labs/lab7/lab7-instruction.md. The personal PATH,
login-message previews, the owned outbox and the cross-user mailbox are optional extensions in that
instruction, so they come last (images.json is empty).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, listing, init)  # noqa: E402,F401

WEEK = "Lab 7"
TITLE = "Operating Systems — Lab 7"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-28T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 7)
S = d.S
CW, HALF = labkit.CW, labkit.HALF

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-07", "Bash Scripting and Safe Arguments",
                  "Lab 7 guide: turn commands into a script, keep every argument whole, and report failure with an exit status.", size=96)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Create and run a Bash script with arguments you understand and the right execute permission.",
                    "Handle spaces, names that start with a dash, and missing input without unwanted word splitting.",
                    "Test a reusable command, and explain its exit status and its safe handling of file names."], ordered=True, size=34, flex=3),
            card(t, "Lab 7", "First the concepts, with examples. Then the lab on the server. A personal PATH, login messages and the outbox are optional extensions, so they come last.", label="THIS LAB", flex=2),
            gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "A file is called one file.txt. How many arguments is that?",
         "To you it is one name. To the shell, with a space inside it, how many words is it?")

# ---- concepts first ---------------------------------------------------------
d.opener("bg-open", "CONCEPTS FIRST", "Scripts, arguments and quoting", "Four ideas: a script is a saved command, arguments need quotes, option parsing needs --, and every command ends with a status.")

d.slide("script", "A script is a saved list of commands",
        lambda t: row(listing(t, ["#!/usr/bin/env bash", 'printf \'argument count=%s\\n\' "$#"', 'for argument in "$@"; do',
                                  "    printf '<%s>\\n' \"$argument\"", "done"], title="show_args.sh", size=24),
                      col(para(t, "The first line, the shebang, names the interpreter that should run the file.", size=32),
                          para(t, "$# is the number of arguments. $@ is the list of arguments. for repeats the body once for each of them.", size=32),
                          para(t, "printf with angle brackets shows exactly where each argument starts and ends.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("run-modes", "Two ways to run it",
        lambda t: row(term(t, ["bash show_args.sh 'one file.txt' '-dash.txt'",
                               ("out", "argument count=2"), ("out", "<one file.txt>"), ("out", "<-dash.txt>"),
                               ("blank",),
                               "chmod u+x show_args.sh",
                               "./show_args.sh 'one file.txt' '-dash.txt'"], size=24),
                      col(para(t, "bash script runs the file with Bash, whether or not it is executable.", size=32),
                          para(t, "./script runs it directly. That needs the execute bit and the shebang. ./ names the file in the current folder, which is not on PATH.", size=32),
                          para(t, "chmod u+x gives the owner the execute bit.", size=32),
                          gap=24),
                      gap=48, align="center"),
        note="If a direct run says Permission denied, the file may lack the execute bit, or the folder may be mounted noexec. bash script is the allowed fallback.",
        label=BG)

d.slide("quote-at", 'Quotes keep an argument whole: "$@"',
        lambda t: row(col(h3(t, 'Quoted: "$@"'),
                          term(t, ["for a in \"$@\"; do printf '<%s>\\n' \"$a\"; done",
                                   ("out", "<one file.txt>")], size=24),
                          para(t, "Each argument stays one item, spaces inside it and all.", size=30),
                          gap=20, flex=None),
                      col(h3(t, "Unquoted: $@"),
                          term(t, ["for a in $@; do printf '<%s>\\n' \"$a\"; done",
                                   ("out", "<one"), ("out", "<file.txt>")], size=24),
                          para(t, "The shell splits on spaces. One name becomes two words, and the script looks for files that do not exist.", size=30),
                          gap=20, flex=None),
                      gap=40, align="flex-start"),
        note="Quote every expansion that holds a file name: \"$path\", \"$@\", \"$file\".",
        label=BG)

d.slide("dashdash", "A name that starts with a dash",
        lambda t: row(term(t, ["wc -w -dash.txt",
                               ("out", "wc: invalid option -- 'd'"),
                               "wc -w -- -dash.txt",
                               ("out", "1 -dash.txt"),
                               "wc -w ./-dash.txt",
                               ("out", "1 ./-dash.txt")], size=26),
                      col(para(t, "A word that starts with - looks like an option, so wc tries to read it as one.", size=32),
                          para(t, "-- tells a command that the options have ended. Everything after it is a file name.", size=32),
                          para(t, "Quoting alone does not help: the quotes are removed by the shell before wc sees the word. Writing ./-dash.txt also works.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("status", "Every command ends with an exit status",
        lambda t: row(tbl(t, ["Status", "Meaning"],
                          [["0", "Success"],
                           ["1 and above", "Some kind of failure"],
                           ["2", "By habit, a wrong use of the command"]],
                          [3, 9], width=HALF),
                      term(t, ["test -f input/one\\ file.txt; echo $?",
                               ("out", "0"),
                               "test -f missing.txt; echo $?",
                               ("out", "1")], size=24, width=HALF),
                      gap=32, align="center"),
        note="$? holds the status of the last command. A script ends with the status you give to exit, or with the status of its last command.",
        label=BG)

# ---- the lab ----------------------------------------------------------------
d.opener("lab-open", "LAB 7", "Your own file command", "Build a personal TechCorp command that inspects files. It must keep every argument whole.")

START_TREE = [("count_words.sh", None), ("input", [("-dash.txt", None), ("one file.txt", None)]), ("evidence", [])]

labkit.scenario(d, 7, "A command for your own files", "Build a personal TechCorp command that inspects files in your own server neighbourhood. It must keep argument boundaries intact before any cross-user automation is considered.",
                "The core stays in your own folders. Cross-user work needs a narrow folder the instructor prepared.", START_TREE)
labkit.timetable(d, [["0 to 10", "Introduction, objectives and setup"],
                     ["10 to 25", "Task 1, guided: script basics"],
                     ["25 to 35", "Written prediction"],
                     ["35 to 70", "Task 2: your personal file command"]],
                 [["70 to 85", "Normal, edge and leading-dash tests"],
                  ["85 to 100", "Individual changed-case checkpoint"],
                  ["100 to 110", "Correction and explanation"],
                  ["110 to 120", "Cleanup and submission"]])
labkit.rules(d, safety="Do not use eval, and do not run scripts you did not write.")
labkit.setup_slides(d, 7, START_TREE,
                    ["count_words.sh is an editable starter skeleton.",
                     "input/ holds two files: one file.txt has two words, and -dash.txt has one.",
                     "The helper also writes a hidden file, .oslab-managed.json. Leave it as it is."])

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Script basics", "Task 1, with the instructor: fifteen minutes.")

d.slide("g-heredoc", "Step 1: write the argument viewer",
        lambda t: row(term(t, ["cat > show_args.sh <<'SH'",
                               "#!/usr/bin/env bash",
                               "printf 'argument count=%s\\n' \"$#\"",
                               "for argument in \"$@\"; do",
                               "    printf '<%s>\\n' \"$argument\"",
                               "done",
                               "SH",
                               "bash show_args.sh 'one file.txt' '-dash.txt'"], size=24),
                      col(para(t, "cat &gt; file &lt;&lt;'SH' writes everything up to the line SH into the file. This is a here-document.", size=30),
                          para(t, "The quotes around SH stop your own shell from expanding $# and $@ while you type. They are left for the script.", size=30),
                          para(t, "Expected: a count of 2, then two arguments in angle brackets.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-direct", "Step 2: run it directly",
        lambda t: row(term(t, ["chmod u+x show_args.sh",
                               "./show_args.sh 'one file.txt' '-dash.txt'"], size=28),
                      col(para(t, "The shebang picks the interpreter for a direct run. ./ finds the script in this folder, which is not on PATH.", size=32),
                          card(t, "Compare", "Is the output the same as with bash show_args.sh? Why does ./ need the execute bit when bash does not?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-wc", "Step 3: safe operands for wc",
        lambda t: row(term(t, ["wc -w -- 'input/one file.txt'",
                               "wc -w -- 'input/-dash.txt'"], size=28),
                      col(para(t, "Expected counts: 2 and 1. -- ends option parsing for wc.", size=32),
                          para(t, "input/-dash.txt does not start with a dash, so it is not mistaken for an option. The checkpoint tests -dash.txt from inside input/, where it would be.", size=32),
                          card(t, "Observe", "Why is a file name with a space one argument? What might for argument in $@ do differently?", label="THINK", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.predict(d, "A script receives 'one file.txt' as one argument, but loops over an unquoted $@. What pieces might the loop see? Why might a file named -dash.txt cause a different kind of problem?")

# ---- task 2 -----------------------------------------------------------------
d.opener("t2-open", "TASK 2", "Build your personal file command", "Thirty-five minutes, from minute 35 to 70. Work alone.")

d.slide("t2-look", "Step 1: look before you edit",
        lambda t: row(term(t, ["cat count_words.sh",
                               "cat 'input/one file.txt' 'input/-dash.txt'"], size=28),
                      col(para(t, "Read the skeleton and the two input files first.", size=32),
                          para(t, "Both file names are in quotes, because one of them contains a space.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t2-spec", "Step 2: what count_words.sh must do",
        lambda t: row(col(h3(t, "Requirements"),
                          lst(t, ["No arguments: print a usage message to stderr, and exit with a non-zero status.",
                                  "For each regular file: print its word count and its original path on one labelled line.",
                                  "For a missing or non-regular input: print a useful message to stderr, carry on with the other arguments, and return non-zero overall.",
                                  "Keep argument boundaries, and pass file names safely. Do not use eval."], size=30),
                          gap=20, flex=3),
                      col(card(t, "You write it", "Build it from the guided argument loop. Different, reasonable output labels are accepted.", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("t2-grow", "Step 3 and 4: grow it in small steps",
        lambda t: row(term(t, ["bash count_words.sh 'input/one file.txt'",
                               "bash count_words.sh 'input/one file.txt' 'input/-dash.txt'"], size=24),
                      col(para(t, "Start with one valid file, then two. Check each before you add error handling.", size=32),
                          para(t, "To keep going after a failed input but still report it: set a variable to 0 at the start, change it when an input fails, and exit with it at the end.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t2-exec", "Step 5: make it executable",
        lambda t: row(term(t, ["chmod u+x count_words.sh",
                               "./count_words.sh 'input/one file.txt'",
                               "bash count_words.sh 'input/one file.txt'"], size=26),
                      col(para(t, "Run it both ways and compare the behaviour.", size=32),
                          card(t, "Complete when", "Both normal counts are right, the names stay intact, missing inputs are explained, and the final status tells whether any input failed.", label="DONE", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t2-hints", "Hints, one at a time",
        lambda t: row(card(t, "If you are stuck", "Use show_args.sh to see how a name was split. That shows the problem at once.", label="DEBUG", pad=40, title_size=36, flex=1),
                      col(h3(t, "Three hints"),
                          lst(t, ["Quote each expanded path.", "Display the arguments with the viewer when a name splits.",
                                  "Test with [[ -f \"$path\" ]], and put -- before file name operands."], ordered=True, size=32),
                          gap=20, flex=1),
                      gap=48, align="stretch"))

# ---- tests ---------------------------------------------------------------------
d.opener("test-open", "TESTS AND FEEDBACK", "Normal, missing, leading dash, empty", "Fifteen minutes, from minute 70 to 85.")

d.slide("tests-normal", "Test 1 and 2: a normal run, and a failure",
        lambda t: row(term(t, ["bash count_words.sh 'input/one file.txt' 'input/-dash.txt' | tee evidence/normal.txt",
                               ("blank",),
                               "{",
                               "  bash count_words.sh missing.txt 'input/one file.txt'",
                               "  printf 'status=%s\\n' \"$?\"",
                               "} > evidence/edge.txt 2>&1",
                               "cat evidence/edge.txt"], size=24),
                      col(para(t, "Save the normal run in evidence/normal.txt.", size=32),
                          para(t, "Expect: a message for the first input, a result for the second, and a non-zero status overall. Save it as evidence/edge.txt.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("tests-dash", "Test 3 and 4: a real leading dash, no input, an empty file",
        lambda t: row(term(t, ["cd input",
                               "bash ../count_words.sh '-dash.txt' 'one file.txt'",
                               "cd .."], size=26),
                      col(para(t, "Inside input/, the name -dash.txt really starts with a dash, so the script must put -- before it.", size=32),
                          para(t, "Also test no arguments, and an empty regular file of your own. An empty file has zero words. That is different from a missing file.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("tests-table", "What each test shows",
        lambda t: tbl(t, ["Case", "Expected", "A weak script that it exposes"],
                      [["Two valid files", "Counts 2 and 1, names intact", "A loop over unquoted $@"],
                       ["Missing, then valid", "A message, a result, status above 0", "A script that stops at the first error, or hides it"],
                       ["-dash.txt in input/", "A count of 1", "A script with no -- before the operands"],
                       ["No arguments", "Usage on stderr, status above 0", "A script that silently succeeds"],
                       ["An empty file", "A count of 0, status 0", "A script that treats empty as missing"]],
                      [4, 6, 8]),
        note="Direct execution can fail with Permission denied: check the execute bit, or use bash script. See man wc and the Bash manual.")

# ---- checkpoint, correction, submission -------------------------------------------
labkit.checkpoint(d, "The current folder holds a file literally named -dash.txt. Explain why wc -w -dash.txt may be misread, and give a safe command. Then explain why quoting alone does not end option parsing.")
labkit.correction(d, "(a) What does \"$@\" preserve? (b) Which problem does -- solve? (c) How does your script report one failed input while it processes the next?")
labkit.submission(d, 7, ['cp -- count_words.sh "$SUBMISSION_REPO/lab7/"',
                         'cp -- evidence/normal.txt evidence/edge.txt "$SUBMISSION_REPO/lab7/evidence/"'],
                  [("README.md", None), ("count_words.sh", None), ("evidence", [("normal.txt", None), ("edge.txt", None)])])
labkit.grading(d, [["Safe arguments, correct counts and a status for any failed input", "3"],
                   ["Tests with a space, a leading dash, a missing file and an empty file", "2"],
                   ["Quoting, option boundaries, execution mode and status explained; original prediction and correction", "2"],
                   ["Individual checkpoint: result or diagnosis, and mechanism", "2"],
                   ["Concise, attributable evidence and the required artifacts", "1"]])
labkit.mistakes(d, [["for a in $@ without quotes", "one file.txt split into two words", "Write \"$@\""],
                    ["No -- before operands", "wc: invalid option", "Put -- before the file names"],
                    ["Exit 0 after a failed input", "A script that always looks successful", "Keep a status variable, exit with it"],
                    ["Running ./script without chmod", "Permission denied", "chmod u+x, or use bash script"]])

# ---- beyond the core --------------------------------------------------------------
d.opener("ext-open", "BEYOND THE CORE", "PATH, login messages and the outbox", "Optional extensions. Cross-user work needs a narrow folder the instructor prepared.")

d.slide("ext-path", "Your own commands on PATH",
        lambda t: row(term(t, ["mkdir -p ~/bin",
                               "cp count_words.sh ~/bin/count_words",
                               'export PATH="$HOME/bin:$PATH"',
                               "command -v count_words",
                               ("out", "/home/student/bin/count_words")], size=24),
                      col(para(t, "PATH is the list of folders the shell searches for a command name. Add your own folder in front, and the script runs without ./.", size=30),
                          para(t, "export PATH=... lasts for this shell only. Put it in ~/.bashrc to keep it, and read that file again with source ~/.bashrc.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=EXT)

d.slide("ext-login", "Login messages, outbox and the mailbox idea",
        lambda t: row(card(t, "A message when you log in", "A line in ~/.bash_profile or ~/.bashrc can print a notice. Preview it with a plain command before you rely on it.", label="LOGIN", pad=32, title_size=32),
                      card(t, "An owned outbox", "A folder you own where a script leaves messages. Only you write to it, so permissions stay simple.", label="OUTBOX", pad=32, title_size=32),
                      card(t, "A cross-user mailbox", "Needs a narrow shared folder the instructor prepared, with write permission only for the people who need it. Never open your own home.", label="MAILBOX", pad=32, title_size=32),
                      gap=32, align="stretch"),
        note="A program that runs with its owner's rights (setuid) is a concept for a prepared virtual machine. It is not part of this lab.",
        label=EXT)

d.close([("A script is saved commands", "A shebang names the interpreter, and chmod u+x lets you run the file directly."),
         ("Quote what you expand", "\"$@\" keeps each argument whole. Unquoted, a space splits it into two words."),
         ("-- ends the options", "Use it before file names, so a leading dash cannot be read as an option."),
         ("The status is the message", "Exit non-zero when any input failed, even if you carried on with the rest.")],
        "chapter 2, Operating-System Structures (the command interpreter), and the Bash manual", ("Lab 8: secure scripts, races and file locking", "Two scripts touch one file at once. See what goes wrong, and fix it with a lock."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: a script, running modes, quoting arguments, the leading dash and exit status.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the rules, setup and the starting tree.", "start": "lab-open"},
    "s4": {"description": "Guided: script basics, then the prediction.", "start": "g-open"},
    "s5": {"description": "Task 2: your personal file command, then the tests.", "start": "t2-open"},
    "s6": {"description": "The individual checkpoint: why, and the practice question.", "start": "cp-open"},
    "s7": {"description": "Correction, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: PATH, login messages and the outbox, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
