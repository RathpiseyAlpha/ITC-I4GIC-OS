"""Lab 4 guide, Linux I/O Redirection, Pipelines and Process Management. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

Revised 2026-11-05 to the pilot-format instruction: personal values (STATUS and OTHER), Core 1 and Core 2, Plus and
Challenge, a live checkpoint, oslab predict and oslab debrief. Modelled on the Lab 8 guide.

A guide for the lab session, built like the Lab 3 guide with the shared look and the shared standard slides in
labkit.py. It starts with the concepts the core needs: the three standard streams, redirection operators,
pipes, and the filters grep, cut, awk, sort and uniq. The lab part follows labs/lab4/lab4-instruction.md.
Process monitoring, job control, signals, orphans and zombies are optional extensions in that instruction;
the earlier guide taught them, so they stay as a short background section at the end, redrawn here
(images.json is empty).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, flow, init)  # noqa: E402,F401

WEEK = "Lab 4"
TITLE = "Operating Systems — Lab 4"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-28T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 4)
S = d.S
CW, HALF = labkit.CW, labkit.HALF

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-04", "Redirection, Pipelines and Processes",
                  "Lab 4 guide: send output and errors to different places, connect commands, and build a report you can trust.", size=96)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Use redirection and pipelines, and tell stdout, stderr and the exit status apart.",
                    "Filter and aggregate a CSV file, checking each stage of the pipeline.",
                    "Find out why a selection or a total is wrong, using normal and changed inputs."], ordered=True, size=36, flex=3),
            card(t, "Lab 4", "First the concepts, with examples. Then the lab on the server, where you write the script yourself. Watching and signalling processes are optional extensions, so they come at the end.", label="THIS LAB", flex=2),
            gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "A command prints an error and a result. Where does each go?",
         "Both appear on your screen. Are they the same thing? How would you save only one of them?")

# ---- concepts first ---------------------------------------------------------
d.opener("bg-open", "CONCEPTS FIRST", "Streams, pipes and filters", "Three ideas: every program has three streams, a pipe joins two programs, and small filters do one job each.")

d.slide("streams", "Every command has three streams",
        lambda t: row(tbl(t, ["Stream", "Number", "Default", "Used for"],
                          [["stdin", "0", "The keyboard", "Input"],
                           ["stdout", "1", "The terminal", "Normal output"],
                           ["stderr", "2", "The terminal", "Error messages and diagnostics"]],
                          [3, 3, 4, 7], width=CW),
                      gap=32),
        note="Both output streams appear on the screen, so they look the same. They are different streams, and you can send them to different places.",
        label=BG)

d.slide("operators", "The redirection operators",
        lambda t: tbl(t, ["Operator", "Meaning", "Example"],
                      [[mono("&gt;"), "Send stdout to a file, replacing it", mono("ls &gt; files.txt")],
                       [mono("&gt;&gt;"), "Append stdout to a file", mono("echo done &gt;&gt; log.txt")],
                       [mono("2&gt;"), "Send stderr to a file", mono("ls /fake 2&gt; errors.txt")],
                       [mono("2&gt;&amp;1"), "Make stderr go where stdout goes now", mono("cmd &gt; all.txt 2&gt;&amp;1")],
                       [mono("&amp;&gt;"), "Bash shorthand: stdout and stderr into one file", mono("cmd &amp;&gt; all.txt")],
                       [mono("&lt;"), "Read stdin from a file", mono("sort &lt; unsorted.txt")],
                       [mono("/dev/null"), "Throw the output away", mono("cmd &gt; /dev/null 2&gt;&amp;1")]],
                      [3, 8, 8]),
        note="A single &gt; replaces the file. Use &gt;&gt; to add to it. In a pipeline, |&amp; sends both streams to the next command.",
        label=BG)

d.slide("redir-demo", "Two streams, two files",
        lambda t: row(term(t, ["printf 'normal output\\n' > evidence/stdout-demo.txt",
                               "cat missing-demo.txt 2> evidence/stderr-demo.txt",
                               "cat evidence/stdout-demo.txt",
                               ("out", "normal output"),
                               "cat evidence/stderr-demo.txt",
                               ("out", "cat: missing-demo.txt: No such file or directory")], size=26),
                      col(para(t, "printf writes the text. &gt; sends it into the first file. The second command fails on purpose, and 2&gt; catches only its error message.", size=32),
                          para(t, "Nothing about the error appeared on the screen the first time. It went into the file.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("order", "The order of redirections matters",
        lambda t: row(col(h3(t, "stderr follows stdout to the file"),
                          term(t, ["bash -c 'echo normal; echo problem >&2' > both.txt 2>&1",
                                   "cat both.txt",
                                   ("out", "normal"),
                                   ("out", "problem")], size=24),
                          para(t, "First stdout goes to the file. Then 2&gt;&amp;1 points stderr at that same place.", size=30),
                          gap=20, flex=None),
                      col(h3(t, "stderr stays on the screen"),
                          term(t, ["bash -c 'echo normal; echo problem >&2' 2>&1 > only-out.txt",
                                   ("out", "problem"),
                                   "cat only-out.txt",
                                   ("out", "normal")], size=24),
                          para(t, "Here stderr is pointed at stdout while stdout is still the screen. Only then does stdout move to the file.", size=30),
                          gap=20, flex=None),
                      gap=40, align="flex-start"),
        note="Read redirections from left to right.",
        label=BG)

d.slide("pipes", "A pipe joins two commands",
        lambda t: row(lst(t, ["The pipe | connects the stdout of one command to the stdin of the next.",
                              "The commands run at the same time. Data flows through as it is produced.",
                              "Only stdout goes through the pipe. stderr still goes to the terminal.",
                              "The exit status of a pipeline is, by default, the status of the last command."], size=34, flex=3),
                      term(t, ["printf 'ok,3\\nfail,2\\n'",
                               ("out", "ok,3"), ("out", "fail,2"),
                               "printf 'ok,3\\nfail,2\\n' | grep '^ok,'",
                               ("out", "ok,3"),
                               "printf 'ok,3\\nfail,2\\n' | grep '^ok,' | cut -d, -f2",
                               ("out", "3")], size=24),
                      gap=48, align="center"),
        note="Read it stage by stage: all rows, then only the ok rows, then only field 2 of those rows.",
        label=BG)

d.slide("filters", "Small filters, one job each",
        lambda t: tbl(t, ["Command", "What it does", "Example"],
                      [[mono("grep"), "Keeps the lines that match a pattern", mono("grep '^ok,' events.csv")],
                       [mono("cut"), "Takes fields from each line", mono("cut -d, -f2")],
                       [mono("awk"), "Fields, conditions and arithmetic", mono("awk '{ total += $1 } END { print total+0 }'")],
                       [mono("sort, uniq -c"), "Sort lines, then count equal neighbours", mono("sort data | uniq -c")],
                       [mono("wc -l"), "Counts lines", mono("wc -l file.txt")],
                       [mono("head, tail"), "The first or last lines", mono("head -n 1")],
                       [mono("tee"), "Saves a copy and passes the data on", mono("ls | tee files.txt | wc -l")]],
                      [3, 7, 9]),
        note="uniq compares neighbours only, so sort first. tee lets you look inside a pipeline.",
        label=BG)

d.slide("grep-cut", "grep, cut and awk",
        lambda t: row(col(h3(t, "grep: keep matching lines"),
                          lst(t, ["grep -v: lines that do not match.", "grep -c: only the count of matching lines.",
                                  "grep -i: ignore upper and lower case.", "grep -E: extended patterns."], size=30),
                          gap=20, flex=None),
                      col(h3(t, "cut: simple fields"),
                          lst(t, ["-d sets the delimiter, -f picks the fields.", "cut -d: -f1 /etc/passwd lists account names.",
                                  "It cannot do arithmetic or conditions."], size=30),
                          gap=20, flex=None),
                      col(h3(t, "awk: fields with logic"),
                          lst(t, ["$1 is the first field, $2 the second.", "END runs once, after the last line.",
                                  "awk -F: '$3 &gt;= 1000' /etc/passwd keeps ordinary accounts."], size=30),
                          gap=20, flex=None),
                      gap=40, align="flex-start"),
        note="Use cut for simple delimited fields. Use awk when you need a condition or a sum.",
        label=BG)

d.slide("rows-counts", "Rows are not counts",
        lambda t: row(term(t, ["printf 'ok,3\\nfail,2\\nok,5\\n' | grep '^ok,' | wc -l",
                               ("out", "2"),
                               "printf 'ok,3\\nfail,2\\nok,5\\n' | grep '^ok,' | cut -d, -f2 | awk '{ t += $1 } END { print t+0 }'",
                               ("out", "8")], size=24),
                      col(para(t, "wc -l counts the selected rows: two lines start with ok.", size=32),
                          para(t, "The report needs the sum of the second field of those rows: 3 plus 5.", size=32),
                          card(t, "Know which quantity you want", "Counting rows and adding numbers answer different questions. Check each stage before you trust the last one.", label="REMEMBER", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("freq", "The frequency pipeline",
        lambda t: row(term(t, ["printf 'b\\na\\nb\\nc\\nb\\n' | sort | uniq -c | sort -rn",
                               ("out", "      3 b"), ("out", "      1 c"), ("out", "      1 a")], size=26),
                      col(para(t, "Extract a column, then sort | uniq -c | sort -rn. It counts how often each value occurs and puts the most frequent first.", size=32),
                          para(t, "The first sort puts equal lines next to each other, uniq -c counts them, and sort -rn orders the counts from high to low.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

# ---- the lab ----------------------------------------------------------------
d.opener("lab-open", "LAB 4", "A report you can trust", "TechCorp receives small CSV event logs. Count the successes, and keep results apart from diagnostics.")

START_TREE = [("data", [("events.csv", None), ("expected.txt", None)]), ("evidence", [])]

labkit.scenario(d, 4, "Event logs at TechCorp", "Produce a trustworthy success-count report from a small CSV event log, and tell normal output apart from error messages.",
                "Your status word and your numbers are your own. This guide shows example values.", START_TREE)
labkit.timetable(d, [["0 to 10", "Setup"],
                     ["10 to 25", "Guided: redirection and pipelines"],
                     ["25 to 35", "Prediction"],
                     ["35 to 55", "Core 1: write report.sh"],
                     ["55 to 70", "Core 2: test your report"]],
                 [["70 to 85", "Instructor demonstration, Plus and Challenge"],
                  ["85 to 100", "Live checkpoint"],
                  ["100 to 110", "Debrief"],
                  ["110 to 120", "Submit"]])

d.slide("helper", "Six helper commands, and why you use them",
        lambda t: tbl(t, ["Command", "What it does"],
                      [[mono("oslab values lab4"), "Shows your status word and the other word. Use them everywhere in this lab"],
                       [mono("oslab predict lab4"), "Saves your prediction once, before the experiment"],
                       [mono("oslab hint lab4 1"), "A hint, levels 1 to 3. Hints cost no points"],
                       [mono("oslab check lab4"), "Runs your report.sh on test files and shows your milestones"],
                       [mono("oslab checkpoint lab4"), "Opens when the instructor says so, near the end"],
                       [mono("oslab debrief lab4"), "After the lab: you give the right answers to your prediction questions"]],
                      [5, 11]),
        note="Before the lab, run oslab doctor and oslab prelab lab4. It takes about ten minutes.")

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Core, Plus, Challenge", "Core is for everyone. Plus and Challenge are for students who finish early. Full marks need only Core and the checkpoint.", title_size=36),
                      rule(t, "AI tools", "Allowed in Core, Plus and Challenge, so test what they tell you. Not allowed in the prediction and the checkpoint.", title_size=36),
                      rule(t, "You write report.sh", "In Core 1 nobody gives you the full script. You build it from the pieces you already know.", title_size=36)),
        note="A wrong prediction costs nothing. It is marked for being made and corrected, not for being right.")

d.slide("start", "Setup: start the lab",
        lambda t: row(term(t, ['export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                               "oslab start lab4",
                               'cd "$OSLAB_WORKSPACE/lab4"',
                               "mkdir -p evidence",
                               "oslab values lab4"], title="student@server: ~", size=26),
                      col(lst(t, ["The first line sets OSLAB_WORKSPACE to ~/oslab-work, unless it is already set. Type it as it is.",
                                  "oslab start lab4 makes the lab folder.",
                                  "cd takes you into it, and mkdir -p makes the evidence folder.",
                                  "oslab values lab4 prints your own words."], size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("values", "Your values: two words that are only yours",
        lambda t: row(col(h3(t, "The last command prints them"),
                          term(t, ["oslab values lab4",
                                   ("out", "Your personal values for lab4 (your-account):"),
                                   ("out", "  status   = ready"),
                                   ("out", "  other    = done")], title="example: your values will be different", size=28),
                          gap=20, flex=None),
                      col(h3(t, "What to do with them"),
                          lst(t, ["Write both words down. Your own words are different from the example.",
                                  "Use them everywhere in this lab.",
                                  "The numbers inside events.csv are also only yours."], size=30),
                          gap=20, flex=None),
                      gap=48, align="flex-start"))

d.slide("capital", "The capital words are placeholders",
        lambda t: tbl(t, ["The instruction says", "With the example values, you type"],
                      [[mono("grep '^STATUS,' data/events.csv"), mono("grep '^ready,' data/events.csv")],
                       [mono("printf 'OTHER,5\\n'"), mono("printf 'done,5\\n'")],
                       ["the label " + mono("STATUS total: NUMBER"), "the label " + mono("ready total: NUMBER")]],
                      [1, 1]),
        note="The instruction cannot know your values, so it writes STATUS and OTHER in capitals where your word belongs. Never type the capital words. Type your own value in their place.")

d.slide("start-tree", "Your folder",
        lambda t: row(tree(t, "lab4", START_TREE, cmd="tree -a -L 3", title="student@server: ~/oslab-work/lab4", size=30),
                      col(para(t, "data/events.csv has a header and six records. Its numbers are only yours.", size=32),
                          para(t, "data/expected.txt is the report you must produce.", size=32),
                          para(t, "oslab check lab4 now shows TRY on every line, because there is no report.sh yet. The hidden .oslab-managed.json is the helper's. Leave it.", size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Redirection, then pipelines", "Ten to twenty-five minutes, with the instructor.")

d.slide("g-redir", "Step 1: normal output and an error, apart",
        lambda t: row(term(t, ["printf 'normal output\\n' > evidence/stdout-demo.txt",
                               "cat missing-demo.txt 2> evidence/stderr-demo.txt",
                               "cat evidence/stdout-demo.txt",
                               "cat evidence/stderr-demo.txt"], size=26),
                      col(para(t, "The second command fails on purpose. &gt; sent stream 1 to the first file. 2&gt; sent stream 2 to the second file.", size=32),
                          card(t, "Observe", "Which file holds the error text? What did the terminal show while the second command ran?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-both", "Step 2: both streams into one file, and the status",
        lambda t: row(term(t, ["bash -c 'printf \"out\\n\"; printf \"err\\n\" >&2' > evidence/both.txt 2>&1",
                               "cat evidence/both.txt",
                               "cat missing-demo.txt 2> /dev/null",
                               'echo "status: $?"'], size=24),
                      col(para(t, "bash -c runs the quoted text as a small program. The second printf writes to stderr: &gt;&amp;2. 2&gt;&amp;1 sends stderr where stdout goes.", size=30),
                          para(t, "/dev/null throws away what you send to it. The status is not 0, because cat failed.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-pipe", "Step 3: a pipeline, one stage at a time",
        lambda t: row(term(t, ["printf 'ready,3\\ndone,2\\n' | grep '^ready,'",
                               ("out", "ready,3"),
                               "printf 'ready,3\\ndone,2\\n' | grep '^ready,' | cut -d, -f2",
                               ("out", "3")], title="example values: use your own words", size=24),
                      col(para(t, "In the instruction these lines say STATUS and OTHER. Type your own words. The example uses ready and done.", size=30),
                          para(t, "Run each line and read the result before you add the next stage. cut -d, -f2 cuts each line at the commas and keeps the second field.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-data", "Step 4: look at your data",
        lambda t: row(term(t, ["cat data/events.csv", "cat data/expected.txt"], size=28),
                      col(para(t, "The lab uses a simple two-field CSV without quoted commas.", size=32),
                          card(t, "Observe", "Which rows have your status? Is there a row whose name only starts like your status? What does wc -l count: records or a sum?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- prediction ---------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Before you write the report. Ten minutes.")

d.slide("predict", "The prediction",
        lambda t: row(col(term(t, ["oslab predict lab4"]),
                          para(t, "It asks three questions and one sentence about your own events.csv. Answer alone, without AI.", size=32),
                          gap=24, flex=3),
                      col(card(t, "The rules", "The first answer is the one that counts. A wrong guess costs nothing. You compare it with the real result later, in the debrief.", label="PREDICTION", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"),
        note="Use the pipeline from Step 3 in your head, on your own events.csv.")

# ---- core 1 ---------------------------------------------------------------------
d.opener("c1-open", "CORE 1", "Write report.sh", "Twenty minutes, from minute 35 to 55. Make a script that prints one line you can trust.")

d.slide("c1-spec", "What report.sh must do",
        lambda t: row(col(h3(t, "report.sh must"),
                          lst(t, ["Take one argument: the path of a CSV file.",
                                  "Select every record whose first field is exactly your status. A look-alike such as STATUS-late must not count.",
                                  "Add up field 2 of those records.",
                                  "Print the result once: STATUS total: NUMBER, for example ready total: 8. Print STATUS total: 0 when no record matches.",
                                  "If the input file does not exist: a message on stderr, nothing on stdout, and a status other than 0."], size=30),
                          gap=20, flex=3),
                      col(card(t, "You write it", "Nobody gives you the script. Decide where the selection, the field extraction and the sum belong.", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("c1-look", "Step 1: look at an incomplete pipeline",
        lambda t: row(term(t, ["grep '^ready,' data/events.csv",
                               "grep '^ready,' data/events.csv | cut -d, -f2",
                               "grep '^ready,' data/events.csv | cut -d, -f2 | head -n 1"], title="example value: use your own word", size=24),
                      col(para(t, "Type your own status word where the example says ready. Run the three lines, then compare with your prediction.", size=30),
                          card(t, "Observe", "Which stage first loses information? What does head -n 1 keep, and what does it throw away?", label="TRY", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("c1-tools", "Step 2: two tools you may need",
        lambda t: row(col(h3(t, "awk adds numbers"),
                          term(t, ["printf '2\\n4\\n' | awk '{ total += $1 } END { print total+0 }'",
                                   ("out", "6")], size=24),
                          para(t, "+0 makes an empty sum print 0. This demonstration does not solve the lab.", size=30),
                          gap=20, flex=None),
                      col(h3(t, "An error on stderr, and a stop"),
                          term(t, ['if [ ! -f "$1" ]; then',
                                   '    echo "report.sh: no such file: $1" >&2',
                                   "    exit 1",
                                   "fi"], size=24),
                          para(t, "&gt;&amp;2 sends the message to stderr. exit 1 stops with a failing status.", size=30),
                          gap=20, flex=None),
                      gap=40, align="flex-start"))

d.slide("c1-write", "Step 3: your decision",
        lambda t: row(card(t, "Write report.sh in the lab4 folder", "Open it with nano report.sh. A staged pipeline and a single awk program are both fine.", label="YOUR TURN", pad=40, title_size=36, flex=1),
                      col(h3(t, "If you are stuck"),
                          lst(t, ["oslab hint lab4 1, then 2, then 3.", "Print each stage of your pipeline.", "AI is allowed here. Test every suggestion on these small files."], ordered=True, size=32),
                          gap=20, flex=1),
                      gap=48, align="stretch"))

d.slide("c1-run", "Step 4: run it and compare",
        lambda t: row(term(t, ["bash report.sh data/events.csv > evidence/normal.txt",
                               "diff -u data/expected.txt evidence/normal.txt"], size=26),
                      col(para(t, "No output from diff means the files are the same. oslab check lab4 also runs your script.", size=32),
                          card(t, "Think", "A matching report is useful evidence. Why does matching one file not prove that the script is right for every CSV?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- core 2 ---------------------------------------------------------------------
d.opener("c2-open", "CORE 2", "Test your report", "Fifteen minutes, from minute 55 to 70. One matching file does not prove the script.")

d.slide("c2-make", "Step 1: make two changed inputs",
        lambda t: row(term(t, ["printf 'status,count\\ndone,2\\n' > data/no-match.csv",
                               "cp -- data/events.csv data/changed.csv",
                               "printf 'ready,7\\n' >> data/changed.csv"], title="example values: use your own words", size=24),
                      col(para(t, "no-match.csv has no row with your status. changed.csv is a copy of the original with one more record, worth 7.", size=30),
                          para(t, "The original file is not changed. &gt;&gt; adds a line at the end.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-run", "Step 2: run it on every input, and save everything",
        lambda t: row(term(t, ["{",
                               "  bash report.sh data/no-match.csv",
                               "  bash report.sh data/changed.csv",
                               "  bash report.sh data/missing.csv",
                               "  printf 'missing-input status=%s\\n' \"$?\"",
                               "} > evidence/edge.txt 2>&1",
                               "cat evidence/edge.txt"], size=24),
                      col(para(t, "Expect your status total 0, then your normal total plus 7, then your error message, then a status that is not 0.", size=30),
                          para(t, "$? is the exit status of the last command. 2&gt;&amp;1 puts the error message in the file too.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-table", "What each test contradicts",
        lambda t: tbl(t, ["Case", "Expected", "A wrong script that it exposes"],
                      [["Your events.csv", "The total in expected.txt", "Counting rows, or counting a look-alike"],
                       ["No match", "STATUS total: 0", "Printing nothing, or an error, when nothing matches"],
                       ["Extra records", "Your normal total plus 7", "Keeping only the first match"],
                       ["Missing input", "A message on stderr, and a status that is not 0", "Ignoring input errors"]],
                      [4, 5, 9]),
        note="grep returns 1 when nothing matches, which is not a read error. State one kind of CSV your script cannot read, for example a quoted comma.")

d.slide("c2-check", "Step 3: check your work",
        lambda t: row(term(t, ["oslab check lab4"], size=28),
                      col(para(t, "The four Core milestones must show PASS: your own events.csv, no match, extra records and a missing input.", size=32),
                          card(t, "Write down for your report", "What does each test contradict? Which test would catch counting rows, using only the first match, counting a look-alike, and ignoring a missing input?", label="REPORT", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- demonstration, plus and challenge ----------------------------------------------------
d.slide("plus", "Plus: how many records has each status?",
        lambda t: row(term(t, ["cut -d, -f1 data/events.csv | sort | uniq -c"], size=26),
                      col(para(t, "sort puts equal lines next to each other, and uniq -c counts each group.", size=32),
                          card(t, "Answer in evidence/plus.txt", "Why does the header line status appear in the result?", label="PLUS", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"),
        note="First watch the instructor show a pipeline in which one stage fails and the pipe still succeeds. Plus and Challenge are not needed for full marks.")

d.slide("challenge", "Challenge: the same sum without awk",
        lambda t: row(term(t, ["echo $(( $(grep '^ready,' data/events.csv | cut -d, -f2 | paste -sd+ -) ))"], title="example value: use your own word", size=24),
                      col(para(t, "paste -sd+ - joins the lines with a plus sign, and $(( )) calculates it.", size=32),
                          card(t, "Answer in evidence/plus.txt", "What does this print for your own data? What happens when no row matches, and why?", label="CHALLENGE", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- live checkpoint ------------------------------------------------------------------------
d.opener("cp-open", "LIVE CHECKPOINT", "Show what you can do alone", "Fifteen minutes near the end of the lab. Worth 3 of the 10 points.")

d.slide("cp-why", "Why is there a checkpoint?",
        lambda t: grid(card(t, "It shows what you can do alone", "For most of the lab you may use hints and AI tools. The checkpoint is the one moment without them.", icon_name="CheckCircle", pad=28, title_size=32),
                       card(t, "The records are new", "The questions use new records, made for you at that moment. An answer copied from a neighbour does not fit.", icon_name="Key", pad=28, title_size=32),
                       card(t, "The instructor sees who needs help", "Your answers arrive at once, so a common mistake can be explained before the next lab.", icon_name="Users", pad=28, title_size=32),
                       card(t, "It is fair", "Everyone gets the same kind of task, with their own numbers.", icon_name="ThumbsUp", pad=28, title_size=32),
                       cols=2),
        gap=36)

d.slide("cp-steps", "What happens, step by step",
        lambda t: flow(t, [("1. The instructor opens it", "Close your AI tools"), ("2. oslab checkpoint lab4", "Answer the four questions"),
                           ("3. The small task", "Make the new CSV, run report.sh"), ("4. oslab check lab4", "A fifth milestone must pass")], 400, hot=1),
        lambda t: row(rule(t, "Before it opens", "The command says that the checkpoint is not open yet. Wait for the instructor.", title_size=36),
                      rule(t, "While you work", "Use your terminal and what you learned in this lab. No AI tools, and no help from a neighbour.", title_size=36),
                      rule(t, "When you finish", "oslab check lab4 shows whether the fifth milestone, checkpoint, passes. You can fix report.sh and check again.", title_size=36)),
        gap=56)

d.slide("cp-marks", "What the checkpoint asks",
        lambda t: tbl(t, ["Part", "What you do"],
                      [["Four questions", "They use new records that were made for you at this moment. Answer them in the terminal."],
                       ["The small task", "Create the new CSV file the command prints, run your own report.sh on it, and save the output in checkpoint.txt."],
                       ["The check", "Run oslab check lab4. The fifth milestone, checkpoint, must show PASS."]],
                      [4, 13]),
        note="The same report.sh must work on the new file. This is why Core 2 tested more than one input.")

# ---- debrief and submit ---------------------------------------------------------------------
d.opener("end-open", "DEBRIEF AND SUBMIT", "Look back, then hand in", "Ten minutes of debrief, ten to submit.")

d.slide("debrief", "Debrief: look at your prediction again",
        lambda t: row(term(t, ['cat "$OSLAB_WORKSPACE/.records/lab4-predict.json"',
                               "oslab debrief lab4"], size=24, title="student@server: ~/oslab-work/lab4"),
                      col(para(t, "oslab saved your prediction in a hidden folder, .records. It stays as it was, so the comparison shows which answers you confirmed and which you corrected.", size=30),
                          card(t, "Class discussion", "Why is the number from wc -l a different quantity from the total?", label="DISCUSS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

labkit.submission(d, 4, ['cp -- report.sh "$SUBMISSION_REPO/lab4/"',
                         'cp -- evidence/normal.txt evidence/edge.txt "$SUBMISSION_REPO/lab4/evidence/"'],
                  [("README.md", None), ("report.sh", None), ("evidence", [("normal.txt", None), ("edge.txt", None)])],
                  note="If you did Plus or Challenge, copy evidence/plus.txt the same way. The course website checks that these exact names are there.")

d.slide("submit-git", "Submit 3: commit and push",
        lambda t: row(term(t, ["cd ~/os-gic-YOUR_ID",
                               "git pull",
                               "git add os-lab-YOUR_ID/lab4",
                               'git commit -m "Lab 4"',
                               "git push"], title="student@server: ~", size=26),
                      col(para(t, "git pull comes first, in case you pushed from your own computer since.", size=32),
                          para(t, "Replace YOUR_ID with your own ID, as before.", size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.grading(d, [["Report: oslab check lab4 passes the four Core milestones (your own events.csv, no match, extra records, missing input)", "2"],
                   ["Tests: normal.txt and edge.txt show the results, and the README says what each test contradicts", "2"],
                   ["Prediction saved in time, and corrected with oslab debrief lab4", "2"],
                   ["Live checkpoint: the four answers and your report.sh working on the new file", "3"],
                   ["Complete submission: the required files in your repository, on time", "1"]],
               note="Every row is marked from your oslab records and the files in your repository, so run oslab check lab4 until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.")

labkit.mistakes(d, [["Typing STATUS instead of your own word", "No matching rows, so a total of 0", "Use the word from oslab values lab4"],
                    ["A pattern without the comma", "A look-alike such as STATUS-late is counted", "Match the whole first field: ^STATUS,"],
                    ["wc -l after the filter", "The number of rows, not the total", "Add field 2 with awk"],
                    ["Error text on stdout", "A message inside the report line", "Send it to stderr with &gt;&amp;2"],
                    ["No exit 1 after the message", "A missing file looks like a success", "Finish with a status other than 0"]])

# ---- beyond the core (kept from the earlier guide) --------------------------------
d.opener("ext-open", "BEYOND THE CORE", "Processes, jobs and signals", "Optional extensions. They use only your own, bounded processes.")

d.slide("ps-tools", "Looking at processes",
        lambda t: tbl(t, ["Command", "What it shows", "Output"],
                      [[mono("ps aux"), "A snapshot of all processes", "Can be redirected"],
                       [mono("ps --forest"), "The process tree", "Can be redirected"],
                       [mono("ps -o pid,ppid,stat,comm -p PID"), "One process, with its parent and state", "Can be redirected"],
                       [mono("top, htop"), "A live view, updated all the time", "Interactive: take a screenshot"]],
                      [7, 7, 6]),
        note="Start exactly one process of your own and keep its PID. Do not kill processes by name.",
        label=EXT)

d.slide("jobs", "Jobs and signals",
        lambda t: row(tbl(t, ["Signal", "Number", "Effect", "Can be caught?"],
                          [["SIGTERM", "15", "Asks the process to end", "Yes"],
                           ["SIGKILL", "9", "Ends it at once", "No"],
                           ["SIGSTOP", "19", "Pauses it", "No"],
                           ["SIGCONT", "18", "Resumes it", "Yes"],
                           ["SIGINT", "2", "Ctrl+C from the keyboard", "Yes"]],
                          [3, 2, 5, 3], width=HALF),
                      term(t, ["sleep 30 & pid=$!",
                               'ps -o pid,ppid,stat,comm -p "$pid"',
                               'kill -STOP "$pid"',
                               'kill -CONT "$pid"',
                               'kill -TERM "$pid"',
                               'wait "$pid"; echo "status=$?"'], size=24, width=HALF),
                      gap=32, align="center"),
        note="$! is the PID of the last background job. A stopped process shows state T. A wait status above 128 means a signal ended it.",
        label=EXT)

d.slide("jobcontrol", "Job control",
        lambda t: row(term(t, ["sleep 60 &",
                               "jobs -l",
                               "fg %1",
                               "# press Ctrl+Z to pause it",
                               "bg %1",
                               "nohup sleep 60 &"], size=26),
                      col(para(t, "A trailing &amp; runs a command in the background. jobs -l lists your jobs with their PIDs.", size=30),
                          para(t, "fg %1 brings job 1 to the front. Ctrl+Z pauses the front job, and bg %1 lets it run in the background.", size=30),
                          para(t, "nohup keeps a command running after the terminal closes. Use these only on your own, short commands.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=EXT)

d.slide("orphan", "Orphans and zombies",
        lambda t: tbl(t, ["", "Orphan", "Zombie"],
                      [["Who ends first?", "The parent", "The child"],
                       ["Is the child still running?", "Yes", "No, it has exited"],
                       ["State in ps", "S or R, normal", "Z, shown as defunct"],
                       ["Who cleans it up?", "The system gives it a new parent, often PID 1", "Its parent must call wait"],
                       ["Can you kill it?", "Yes, it is a normal process", "No, it is already dead: fix the parent"]],
                      [5, 7, 8]),
        note="Run these demonstrations for a few seconds, in a disposable environment, and leave nothing running.",
        label=EXT)

d.close([("Three streams", "stdin, stdout and stderr are separate. Redirect each on purpose."),
         ("Pipes", "A pipe carries only stdout. Build a pipeline one stage at a time."),
         ("Rows are not counts", "Check which quantity each stage produces before you trust the total."),
         ("Test the edges", "No match, a changed count and a missing input show what the script really does.")],
        "chapter 3, Processes", ("Lab 5: threads, kernel workers and signals", "Look at threads inside a process, the kernel's own workers, and how a signal reaches a process."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: the three streams, redirection operators, pipes and the filters grep, cut and awk.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the rules, setup and the starting tree.", "start": "lab-open"},
    "s4": {"description": "Guided: redirection and pipelines, then the prediction.", "start": "g-open"},
    "s5": {"description": "Core 1 and Core 2: write report.sh and test it, then Plus and Challenge.", "start": "c1-open"},
    "s6": {"description": "The live checkpoint: why, the steps with oslab, and what it asks.", "start": "cp-open"},
    "s7": {"description": "Debrief, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: processes, jobs and signals, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
