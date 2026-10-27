"""Lab 4 guide, Linux I/O Redirection, Pipelines and Process Management. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

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
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, init)  # noqa: E402,F401

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
            card(t, "Lab 4", "First the concepts, with examples. Then the lab on the server. Watching and signalling processes are optional extensions, so they come at the end.", label="THIS LAB", flex=2),
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

labkit.scenario(d, 4, "Event logs at TechCorp", "Produce a trustworthy success-count report from a small CSV event log, and distinguish command output from diagnostics.",
                "The core uses text files only. Process-management examples are optional and use your own processes.", START_TREE)
labkit.timetable(d, [["0 to 10", "Introduction, objectives and setup"],
                     ["10 to 18", "Task 1, guided: redirection"],
                     ["18 to 25", "Task 2, guided: pipelines and filters"],
                     ["25 to 35", "Written prediction"]],
                 [["35 to 70", "Task 3: build the report"],
                  ["70 to 85", "Normal and edge tests, feedback"],
                  ["85 to 100", "Individual changed-case checkpoint"],
                  ["100 to 120", "Correction, cleanup and submission"]])
labkit.rules(d)
labkit.setup_slides(d, 4, [("data", [("events.csv", None), ("expected.txt", None)]), ("evidence", [])],
                    ["data/events.csv has a header and three records.",
                     "data/expected.txt holds the report the lab asks for: ok total: 8.",
                     "The helper also writes a hidden file, .oslab-managed.json. Leave it as it is."])

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Redirection, then pipelines", "Tasks 1 and 2, with the instructor: ten to twenty-five minutes.")

d.slide("g-redir", "Task 1: normal output and an error, apart",
        lambda t: row(term(t, ["printf 'normal output\\n' > evidence/stdout-demo.txt",
                               "cat missing-demo.txt 2> evidence/stderr-demo.txt",
                               "cat evidence/stdout-demo.txt",
                               "cat evidence/stderr-demo.txt"], size=26),
                      col(para(t, "The missing-file command fails on purpose. &gt; redirects descriptor 1 (stdout), 2&gt; redirects descriptor 2 (stderr), and &gt;&gt; appends.", size=32),
                          card(t, "Observe", "Which file holds the error text? What did the terminal show while the second command ran?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-both", "Task 1: both streams into one file",
        lambda t: row(term(t, ["bash -c 'printf \"out\\n\"; printf \"err\\n\" >&2' > evidence/both.txt 2>&1",
                               "cat evidence/both.txt"], size=24),
                      col(para(t, "bash -c runs the quoted text as a small program. The second printf writes to stderr: &gt;&amp;2.", size=32),
                          para(t, "2&gt;&amp;1 makes stderr refer to stdout's current destination, the file. Reversing the two redirections can change where stderr goes.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-pipe", "Task 2: a pipeline, one stage at a time",
        lambda t: row(term(t, ["printf 'ok,3\\nfail,2\\n'",
                               "printf 'ok,3\\nfail,2\\n' | grep '^ok,'",
                               "printf 'ok,3\\nfail,2\\n' | grep '^ok,' | cut -d, -f2"], size=24),
                      col(para(t, "Add one stage at a time, and look at the output before you add the next. The last stage should print 3.", size=32),
                          para(t, "| forwards stdout to the next command. stderr is not included by default.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-data", "Task 2: look at the real input",
        lambda t: row(term(t, ["cat data/events.csv", "cat data/expected.txt"], size=28),
                      col(para(t, "The lab uses simple two-field CSV without quoted commas.", size=32),
                          card(t, "Observe", "Does wc -l count successful events or selected rows? Which stage would add numbers instead of counting records?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.predict(d, "What will grep '^ok,' data/events.csv | cut -d, -f2 | head -n 1 print? Will that equal the required successful total? Explain what information it discards.")

# ---- task 3 -----------------------------------------------------------------
d.opener("t3-open", "TASK 3", "Build the report", "Thirty-five minutes, from minute 35 to 70. Work alone.")

d.slide("t3-one", "Step 1: run the incomplete pipeline you predicted",
        lambda t: row(term(t, ["grep '^ok,' data/events.csv",
                               "grep '^ok,' data/events.csv | cut -d, -f2",
                               "grep '^ok,' data/events.csv | cut -d, -f2 | head -n 1"], size=24),
                      col(para(t, "Compare each stage with the original data.", size=32),
                          card(t, "Observe", "Which stage first loses information? What does head -n 1 keep, and what does it throw away?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t3-two", "Step 2: write your own report.sh",
        lambda t: row(col(h3(t, "What report.sh must do"),
                          lst(t, ["Take one CSV path as its argument.",
                                  "Select every record whose first field is exactly ok.",
                                  "Sum field 2 of those records.",
                                  "Print ok total: NUMBER once.",
                                  "Reject a missing input, and print zero when no row matches."], size=32),
                          gap=20, flex=3),
                      col(card(t, "You write it", "Nobody gives you the script. Decide where selection, field extraction and summing belong. A staged pipeline or one carefully limited awk program both work.", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("t3-awk", "Step 3: awk as a calculator",
        lambda t: row(term(t, ["printf '2\\n4\\n' | awk '{ total += $1 } END { print total+0 }'",
                               ("out", "6")], size=26),
                      col(para(t, "total += $1 adds the first field of each line. END runs once, after the last line. total+0 prints 0, not an empty line, when nothing arrived.", size=32),
                          para(t, "This demonstration teaches summing without giving you the whole solution.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t3-run", "Step 4: run it and compare",
        lambda t: row(term(t, ["bash report.sh data/events.csv > evidence/normal.txt",
                               "diff -u data/expected.txt evidence/normal.txt"], size=26),
                      col(para(t, "diff prints nothing when the two files are identical.", size=32),
                          card(t, "Think", "A matching report is useful evidence. Why does matching one file not prove that the script is right for every CSV?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t3-hints", "Hints, one at a time",
        lambda t: row(card(t, "Complete when", "report.sh prints ok total: 8 for the supplied file, and you can say what each stage of it does.", label="DONE", pad=40, title_size=36, flex=1),
                      col(h3(t, "If you are stuck"),
                          lst(t, ["Tell rows apart from counts.", "Print each stage of the pipeline.",
                                  "Sum only the selected numeric field, and format the label at the end."], ordered=True, size=32),
                          para(t, "AI is allowed here. Test what it suggests on these small files.", size=30),
                          gap=20, flex=1),
                      gap=48, align="stretch"))

# ---- tests ---------------------------------------------------------------------
d.opener("test-open", "TESTS AND FEEDBACK", "Change the input, run it again", "Fifteen minutes, from minute 70 to 85.")

d.slide("tests-make", "Make two changed inputs",
        lambda t: row(term(t, ["printf 'status,count\\nfail,2\\n' > data/no-ok.csv",
                               "cp -- data/events.csv data/changed.csv",
                               "printf 'ok,7\\n' >> data/changed.csv"], size=24),
                      col(para(t, "no-ok.csv has no ok row. changed.csv is a copy of the original with one more record, ok,7.", size=32),
                          para(t, "The original fixture is not altered. &gt;&gt; adds a line at the end.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("tests-run", "Run the report on every input",
        lambda t: row(term(t, ["{",
                               "  bash report.sh data/no-ok.csv",
                               "  bash report.sh data/changed.csv",
                               "  bash report.sh data/missing.csv",
                               "  printf 'missing-input status=%s\\n' \"$?\"",
                               "} > evidence/edge.txt 2>&1",
                               "cat evidence/edge.txt"], size=24),
                      col(para(t, "Expect ok total: 0 and ok total: 15. The missing file must fail.", size=32),
                          para(t, "$? is the exit status of the last command. 2&gt;&amp;1 puts the error message in the file too.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("tests-table", "What each test contradicts",
        lambda t: tbl(t, ["Case", "Expected", "A wrong script that it exposes"],
                      [["Normal", "ok total: 8", "Counting rows instead of adding numbers"],
                       ["No ok row", "ok total: 0", "Printing nothing, or an error, when nothing matches"],
                       ["Changed count", "ok total: 15", "Keeping only the first match"],
                       ["Missing input", "An error and a non-zero status", "Ignoring input errors"]],
                      [4, 5, 9]),
        note="The exercise does not cover quoted fields in CSV. State that limit in your explanation. grep returns 1 when nothing matches, which is not the same as a read error.")

# ---- checkpoint, correction, submission -------------------------------------------
labkit.checkpoint(d, "The original fixture gains ok,7 and fail,20. Predict the report total. A student uses wc -l after filtering. Identify why their answer would measure a different quantity.")
labkit.correction(d, "(a) Why is the row count different from the summed event count? (b) Which stream carries a missing-file error? (c) Which inputs are outside your parser assumptions?")
labkit.submission(d, 4, ['cp -- report.sh "$SUBMISSION_REPO/lab4/"',
                         'cp -- evidence/normal.txt evidence/edge.txt "$SUBMISSION_REPO/lab4/evidence/"'],
                  [("README.md", None), ("report.sh", None), ("evidence", [("normal.txt", None), ("edge.txt", None)])],
                  note="Copy the script, the two evidence files and two selected test records, not every terminal output. The core starts no background job.")
labkit.grading(d, [["Correct report selection and aggregation, and clear stdout and stderr handling", "3"],
                   ["No-match, changed-count and missing-input diagnosis", "2"],
                   ["Each pipeline stage explained, and the claim each test supports; original prediction and correction", "2"],
                   ["Individual checkpoint: result or diagnosis, and mechanism", "2"],
                   ["Concise, attributable evidence and the required artifacts", "1"]])
labkit.mistakes(d, [["wc -l after the filter", "The number of rows, not the total", "Add field 2 with awk"],
                    ["Only the first match kept", "A total that is too small", "Do not use head -n 1 to sum"],
                    ["Error text mixed into the report", "A message inside ok total lines", "Keep stderr apart from stdout"],
                    ["Trusting the pipeline's success", "A zero status while a stage failed", "Inspect the intermediate values"]])

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
    "s5": {"description": "Task 3: build the report, then the tests.", "start": "t3-open"},
    "s6": {"description": "The individual checkpoint: why, and the practice question.", "start": "cp-open"},
    "s7": {"description": "Correction, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: processes, jobs and signals, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
