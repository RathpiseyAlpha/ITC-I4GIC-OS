"""Lab 7 guide, Bash Scripting, Permissions and Server Automation. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

Revised 2026-11-05 to the pilot-format instruction: two personal file names (FILE1 and FILE2), Core 1 and Core 2,
Plus and Challenge, a live checkpoint, oslab predict and oslab debrief. Modelled on the Lab 8 guide.

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
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, listing, flow, init)  # noqa: E402,F401

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

START_TREE = [("count_words.sh", None), ("input", [("-silver.txt", None), ("bridge candle.txt", None)]), ("evidence", [])]

labkit.scenario(d, 7, "A command for your own files", "Build a personal TechCorp command that inspects files in your own server neighbourhood. It must keep argument boundaries intact before any cross-user automation is considered.",
                "Your two file names and your word counts are your own. This guide shows example values.", START_TREE)
labkit.timetable(d, [["0 to 10", "Setup"],
                     ["10 to 25", "Guided: script basics"],
                     ["25 to 35", "Prediction"],
                     ["35 to 55", "Core 1: build count_words.sh"],
                     ["55 to 70", "Core 2: test it"]],
                 [["70 to 85", "Instructor demonstration, Plus and Challenge"],
                  ["85 to 100", "Live checkpoint"],
                  ["100 to 110", "Debrief"],
                  ["110 to 120", "Submit"]])

d.slide("helper", "Six helper commands, and why you use them",
        lambda t: tbl(t, ["Command", "What it does"],
                      [[mono("oslab values lab7"), "Shows your two file names. They are already in your input/ folder"],
                       [mono("oslab predict lab7"), "Saves your prediction once, before the experiment"],
                       [mono("oslab hint lab7 1"), "A hint, levels 1 to 3. Hints cost no points"],
                       [mono("oslab check lab7"), "Runs your count_words.sh on test files and shows your milestones"],
                       [mono("oslab checkpoint lab7"), "Opens when the instructor says so, near the end"],
                       [mono("oslab debrief lab7"), "After the lab: you give the right answers to your prediction questions"]],
                      [5, 11]),
        note="Before the lab, run oslab doctor and oslab prelab lab7. It takes about ten minutes.")

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Core, Plus, Challenge", "Core is for everyone. Plus and Challenge are for students who finish early. Full marks need only Core and the checkpoint.", title_size=36),
                      rule(t, "AI tools", "Allowed in Core, Plus and Challenge, so test every suggestion with your own file names. Not allowed in the prediction and the checkpoint.", title_size=36),
                      rule(t, "You write the script", "In Core 1 you receive an empty skeleton. You write the script, and you decide how to keep the exit status.", title_size=36)),
        note="Do not use eval, and do not run scripts you did not write. A wrong prediction costs nothing.")

d.slide("start", "Setup: start the lab",
        lambda t: row(term(t, ['export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                               "oslab start lab7",
                               'cd "$OSLAB_WORKSPACE/lab7"',
                               "mkdir -p evidence",
                               "oslab values lab7"], title="student@server: ~", size=26),
                      col(lst(t, ["The first line sets OSLAB_WORKSPACE to ~/oslab-work, unless it is already set. Type it as it is.",
                                  "oslab start lab7 makes the lab folder.",
                                  "cd takes you into it, and mkdir -p makes the evidence folder.",
                                  "oslab values lab7 prints your own file names."], size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("values", "Your values: two file names that are only yours",
        lambda t: row(col(h3(t, "The last command prints them"),
                          term(t, ["oslab values lab7",
                                   ("out", "Your personal values for lab7 (your-account):"),
                                   ("out", "  file1    = bridge candle.txt"),
                                   ("out", "  file2    = -silver.txt")], title="example: your values will be different", size=26),
                          gap=20, flex=None),
                      col(h3(t, "What to notice"),
                          lst(t, ["file1 has spaces in its name. file2 starts with a dash.",
                                  "Your own names are different. Write them down.",
                                  "Both files are already in your input/ folder."], size=30),
                          gap=20, flex=None),
                      gap=48, align="flex-start"))

d.slide("capital", "The capital words are placeholders",
        lambda t: tbl(t, ["The instruction says", "With the example values, you type"],
                      [[mono("bash show_args.sh 'FILE1' 'FILE2'"), mono("bash show_args.sh 'bridge candle.txt' '-silver.txt'")],
                       [mono("wc -w -- 'input/FILE1'"), mono("wc -w -- 'input/bridge candle.txt'")]],
                      [1, 1]),
        note="The instruction cannot know your names, so it writes FILE1 and FILE2 where your values belong. Never type the capital words. Type your own name in their place, between single quotes when it has a space.")

d.slide("start-tree", "Your folder",
        lambda t: row(tree(t, "lab7", START_TREE, cmd="tree -a -L 3", title="student@server: ~/oslab-work/lab7", size=30),
                      col(para(t, "count_words.sh is an editable starter skeleton.", size=32),
                          para(t, "input/ holds your two files: one with spaces in its name, one with a leading dash. Each holds a few words.", size=32),
                          para(t, "oslab check lab7 shows TRY on every line at the start. The hidden .oslab-managed.json is the helper's. Leave it.", size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Script basics", "Ten to twenty-five minutes, with the instructor. See how a script receives its arguments, and why quotes matter.")

d.slide("g-heredoc", "Step 1: write the argument viewer",
        lambda t: row(term(t, ["cat > show_args.sh <<'SH'",
                               "#!/usr/bin/env bash",
                               "printf 'argument count=%s\\n' \"$#\"",
                               "for argument in \"$@\"; do",
                               "    printf '<%s>\\n' \"$argument\"",
                               "done",
                               "SH",
                               "bash show_args.sh 'bridge candle.txt' '-silver.txt'"], title="example names: use your own", size=24),
                      col(para(t, "cat &gt; file &lt;&lt;'SH' writes everything up to the line SH into the file. This is a here-document.", size=30),
                          para(t, "The quotes around SH stop your own shell from changing $# and $@ while you type.", size=30),
                          para(t, "Expected: a count of 2, then each argument in angle brackets. \"$@\" keeps the spaces inside an argument.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-direct", "Step 2: run it directly",
        lambda t: row(term(t, ["chmod u+x show_args.sh",
                               "./show_args.sh 'bridge candle.txt' '-silver.txt'"], title="example names: use your own", size=26),
                      col(para(t, "The first line, #!/usr/bin/env bash, is the shebang. It chooses the interpreter for a direct run.", size=30),
                          para(t, "./ says in the current folder. The folder does not need to be in PATH.", size=30),
                          card(t, "Compare", "Is the output the same as with bash show_args.sh? Why does ./ need the execute bit when bash does not?", label="TRY", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-noquote", "Step 3: what the missing quotes do",
        lambda t: row(term(t, ["bash show_args.sh bridge candle.txt",
                               ("out", "argument count=2"),
                               ("out", "<bridge>"),
                               ("out", "<candle.txt>")], title="example name, typed without quotes", size=26),
                      col(para(t, "Type your own file1 name without quotes. The shell splits it at every space before the script starts.", size=30),
                          card(t, "Think", "How many arguments does the script receive? Why?", label="TRY", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-wc", "Step 4: safe operands for wc",
        lambda t: row(term(t, ["wc -w -- 'input/bridge candle.txt'",
                               "cd input",
                               "wc -w -- '-silver.txt'",
                               "cd .."], title="example names: use your own", size=26),
                      col(para(t, "-- ends the list of options for wc, so a name that starts with a dash is read as a file.", size=30),
                          card(t, "Observe", "Inside input/, what would wc -w -silver.txt do without the --? Try it once. The error is intended.", label="TRY", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- prediction ---------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Before you write the script. Ten minutes.")

d.slide("predict", "The prediction",
        lambda t: row(col(term(t, ["oslab predict lab7"]),
                          para(t, "It asks three questions and one sentence, with your own file names. Answer alone, without AI.", size=32),
                          gap=24, flex=3),
                      col(card(t, "The rules", "The first answer is the one that counts. A wrong guess costs nothing. You compare it with the real result in the debrief.", label="PREDICTION", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

# ---- core 1 ---------------------------------------------------------------------
d.opener("c1-open", "CORE 1", "Build count_words.sh", "Twenty minutes, from minute 35 to 55. A reusable command that counts the words of the files it is given.")

d.slide("c1-spec", "What count_words.sh must do",
        lambda t: row(col(h3(t, "Requirements"),
                          lst(t, ["No arguments: print a usage message on stderr and end with a status other than 0.",
                                  "For each regular file: print one line with the file's name and its word count. The wording of the label is yours.",
                                  "For a missing or non-regular file: a message on stderr, continue with the next arguments, and a final status other than 0.",
                                  "Keep each argument in one piece, and pass file names to wc after --. Do not use eval."], size=30),
                          gap=20, flex=3),
                      col(card(t, "You write it", "Build it from the argument loop of the guided part. Different, reasonable output labels are accepted.", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("c1-look", "Step 1: look before you edit",
        lambda t: row(term(t, ["cat count_words.sh",
                               "cat 'input/bridge candle.txt' 'input/-silver.txt'"], title="example names: use your own", size=26),
                      col(para(t, "Read the skeleton and your two input files first.", size=32),
                          para(t, "Both file names are in quotes when they contain a space.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("c1-grow", "Steps 2 and 3: grow it, and keep the status",
        lambda t: row(col(term(t, ["nano count_words.sh",
                                   "bash count_words.sh 'input/bridge candle.txt'",
                                   "bash count_words.sh 'input/bridge candle.txt' 'input/-silver.txt'"], title="example names: use your own", size=24),
                          para(t, "Open the script with nano and write it. Start with one valid file, then two, and test each step before you add the error handling.", size=30),
                          gap=22, flex=3),
                      col(card(t, "Keep the status", "Keep the status in a variable that starts at 0. Change it when an input fails, and finish with exit \"$status\". Why is the variable better than relying on the last command?", label="THINK", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("c1-exec", "Step 4: make it executable",
        lambda t: row(term(t, ["chmod u+x count_words.sh",
                               "./count_words.sh 'input/bridge candle.txt'",
                               "bash count_words.sh 'input/bridge candle.txt'"], title="example name: use your own", size=24),
                      col(para(t, "Run it directly, then through bash, and compare the behaviour.", size=30),
                          card(t, "Hints", "oslab hint lab7 1, then 2, then 3. AI is allowed here: test every suggestion with your own file names.", label="STUCK?", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- core 2 ---------------------------------------------------------------------
d.opener("c2-open", "CORE 2", "Test it", "Fifteen minutes, from minute 55 to 70. Show that the command keeps names intact and reports failures.")

d.slide("c2-normal", "Steps 1 and 2: a normal run, and a failure",
        lambda t: row(term(t, ["bash count_words.sh 'input/bridge candle.txt' 'input/-silver.txt' | tee evidence/normal.txt",
                               ("blank",),
                               "{",
                               "  bash count_words.sh missing.txt 'input/bridge candle.txt'",
                               "  printf 'status=%s\\n' \"$?\"",
                               "} > evidence/edge.txt 2>&1",
                               "cat evidence/edge.txt"], title="example names: use your own", size=24),
                      col(para(t, "Save the normal run with both files in evidence/normal.txt.", size=30),
                          para(t, "Then run it with a missing file first and a valid file second. The valid file must still be counted, and the status must not be 0.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-dash", "Step 3: a real leading dash",
        lambda t: row(term(t, ["cd input",
                               "bash ../count_words.sh '-silver.txt' | tee ../evidence/dash.txt",
                               "cd .."], title="example name: use your own", size=26),
                      col(para(t, "Inside input/, the name really starts with a dash, so the script must put -- before it.", size=32),
                          para(t, "The result goes into evidence/dash.txt.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("c2-table", "What each test shows",
        lambda t: tbl(t, ["Case", "Expected", "A weak script that it exposes"],
                      [["Two valid files", "A count for each, names intact", "A loop over unquoted $@"],
                       ["Missing, then valid", "A message, a result, status above 0", "A script that stops at the first error, or hides it"],
                       ["Leading dash, from inside input/", "A count for the file", "A script with no -- before the operands"],
                       ["Last command decides the status", "Status above 0 although the last file was fine", "A status taken from the last command"]],
                      [5, 6, 8]),
        note="Direct execution can fail with Permission denied: check the execute bit, or use bash script.")

d.slide("c2-check", "Steps 4 and 5: check, then explain",
        lambda t: row(term(t, ["oslab check lab7"], size=28),
                      col(para(t, "The four Core milestones must show PASS: a direct run, two files, a leading dash, and errors with the status.", size=30),
                          card(t, "Write down for your report", "What does each test contradict? A loop over unquoted $@, a missing --, and a status taken from the last command each fail one of the tests. Which one?", label="REPORT", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- demonstration, plus and challenge ----------------------------------------------------
d.slide("plus", "Plus: give it a folder",
        lambda t: row(term(t, ["mkdir -p input/folder",
                               "bash count_words.sh input/folder"], size=26),
                      col(para(t, "Give your script a folder instead of a file.", size=32),
                          card(t, "Answer in evidence/plus.txt", "What does it print, and what is the final status? Does your test [[ -f \"$file\" ]] treat a folder like a missing file?", label="PLUS", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"),
        note="First watch the instructor run a script on a file name with a space, with and without quotes. Plus and Challenge are not needed for full marks.")

d.slide("challenge", "Challenge: * or ./*",
        lambda t: row(term(t, ["cd input",
                               "bash ../show_args.sh *",
                               "bash ../show_args.sh ./*",
                               "cd .."], size=26),
                      col(para(t, "The shell replaces * by the file names before the script starts.", size=32),
                          card(t, "Answer in evidence/plus.txt", "Which form is safer when a name starts with a dash, and why?", label="CHALLENGE", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- live checkpoint ------------------------------------------------------------------------
d.opener("cp-open", "LIVE CHECKPOINT", "Show what you can do alone", "Fifteen minutes near the end of the lab. Worth 3 of the 10 points.")

d.slide("cp-why", "Why is there a checkpoint?",
        lambda t: grid(card(t, "It shows what you can do alone", "For most of the lab you may use hints and AI tools. The checkpoint is the one moment without them.", icon_name="CheckCircle", pad=28, title_size=32),
                       card(t, "The file name is new", "The questions use a new, awkward file name, made for you at that moment. An answer copied from a neighbour does not fit.", icon_name="Key", pad=28, title_size=32),
                       card(t, "The instructor sees who needs help", "Your answers arrive at once, so a common mistake can be explained before the next lab.", icon_name="Users", pad=28, title_size=32),
                       card(t, "It is fair", "Everyone gets the same kind of task, with their own file name.", icon_name="ThumbsUp", pad=28, title_size=32),
                       cols=2),
        gap=36)

d.slide("cp-steps", "What happens, step by step",
        lambda t: flow(t, [("1. The instructor opens it", "Close your AI tools"), ("2. oslab checkpoint lab7", "Answer the four questions"),
                           ("3. The file task", "Create the new file, run your script"), ("4. oslab check lab7", "A fifth milestone must pass")], 400, hot=1),
        lambda t: row(rule(t, "Before it opens", "The command says that the checkpoint is not open yet. Wait for the instructor.", title_size=36),
                      rule(t, "While you work", "Use your terminal and what you learned in this lab. No AI tools, and no help from a neighbour.", title_size=36),
                      rule(t, "When you finish", "oslab check lab7 shows whether the fifth milestone, checkpoint, passes. You can fix your script and check again.", title_size=36)),
        gap=56)

d.slide("cp-marks", "What the checkpoint asks",
        lambda t: tbl(t, ["Part", "What you do"],
                      [["Four questions", "They use a new, awkward file name made for you at this moment. Answer them in the terminal."],
                       ["The file task", "Create the new file the command prints, run your own count_words.sh on it, and save the output in checkpoint.txt."],
                       ["The check", "Run oslab check lab7. The fifth milestone, checkpoint, must show PASS."]],
                      [4, 13]),
        note="The same script must handle the new name. This is why Core 2 tested spaces and a leading dash.")

# ---- debrief and submit ---------------------------------------------------------------------
d.opener("end-open", "DEBRIEF AND SUBMIT", "Look back, then hand in", "Ten minutes of debrief, ten to submit.")

d.slide("debrief", "Debrief: look at your prediction again",
        lambda t: row(term(t, ['cat "$OSLAB_WORKSPACE/.records/lab7-predict.json"',
                               "oslab debrief lab7"], size=24, title="student@server: ~/oslab-work/lab7"),
                      col(para(t, "oslab saved your prediction in a hidden folder, .records. It stays as it was, so the comparison shows which answers you confirmed and which you corrected.", size=30),
                          card(t, "Class discussion", "Your script worked on the files you tested. Which file name could still break it?", label="DISCUSS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

labkit.submission(d, 7, ['cp -- count_words.sh "$SUBMISSION_REPO/lab7/"',
                         'cp -- evidence/normal.txt evidence/edge.txt "$SUBMISSION_REPO/lab7/evidence/"'],
                  [("README.md", None), ("count_words.sh", None), ("evidence", [("normal.txt", None), ("edge.txt", None)])],
                  note="If you did Plus or Challenge, copy evidence/plus.txt the same way. The course website checks that these exact names are there.")

d.slide("submit-git", "Submit 3: commit and push",
        lambda t: row(term(t, ["cd ~/os-gic-YOUR_ID",
                               "git pull",
                               "git add os-lab-YOUR_ID/lab7",
                               'git commit -m "Lab 7"',
                               "git push"], title="student@server: ~", size=26),
                      col(para(t, "git pull comes first, in case you pushed from your own computer since.", size=32),
                          para(t, "Replace YOUR_ID with your own ID, as before.", size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.grading(d, [["Script: oslab check lab7 passes the four Core milestones (direct run, two files, leading dash, errors and status)", "2"],
                   ["Tests: normal.txt and edge.txt show the runs, and the README says what each test contradicts", "2"],
                   ["Prediction saved in time, and corrected with oslab debrief lab7", "2"],
                   ["Live checkpoint: the answers and your script counting the new file", "3"],
                   ["Complete submission: the required files in your repository, on time", "1"]],
               note="Every row is marked from your oslab records and the files in your repository, so run oslab check lab7 until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.")

labkit.mistakes(d, [["for a in $@ without quotes", "A name with a space split into two words", "Write \"$@\""],
                    ["No -- before operands", "wc: invalid option", "Put -- before the file names"],
                    ["Exit 0 after a failed input", "A script that always looks successful", "Keep a status variable, exit with it"],
                    ["Running ./script without chmod", "Permission denied", "chmod u+x, or use bash script"],
                    ["Typing FILE1, or a spaced name without quotes", "No such file, or two arguments", "Use your own name, in single quotes"]])

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
    "s5": {"description": "Core 1 and Core 2: build count_words.sh and test it, then Plus and Challenge.", "start": "c1-open"},
    "s6": {"description": "The live checkpoint: why, the steps with oslab, and what it asks.", "start": "cp-open"},
    "s7": {"description": "Debrief, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: PATH, login messages and the outbox, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
