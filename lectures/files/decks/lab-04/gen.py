"""Lab 4 command-practice guide. Run gen.py to rebuild the slide project."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import h3, card, col, flow, init, lst, mono, para, row, tbl, term  # noqa: E402

WEEK = "Lab 4"
TITLE = "Operating Systems — Lab 4"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-28T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 4)
S = d.S
CW, HALF = labkit.CW, labkit.HALF


def example(t, lines, *, size=28, width=None):
    return col(h3(t, "Example"), term(t, lines, size=size, width=width), gap=16, flex=None)

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-04", "Redirection and Pipelines",
                  "Lab 4 guide: send output and errors to different places, connect commands, and build a report you can trust.", size=96)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Use redirection and pipelines, and tell stdout, stderr and the exit status apart.",
                    "Select records, extract fields and count matches in a CSV file.",
                    "Test exact matching, changed inputs and missing files."], ordered=True, size=36, flex=3),
            card(t, "Lab 4", "First the concepts, with examples. Then the lab on the server, where you work directly at the terminal. Watching and signalling processes are optional extensions, so they come at the end.", label="THIS LAB", flex=2),
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
                       [mono("2&gt;&amp;1"), "Make stderr go where stdout goes now", mono("cat example-events.csv missing-demo.txt &gt; all.txt 2&gt;&amp;1")],
                       [mono("&amp;&gt;"), "Bash shorthand: stdout and stderr into one file", mono("cat example-events.csv missing-demo.txt &amp;&gt; all.txt")],
                       [mono("&lt;"), "Read stdin from a file", mono("sort &lt; unsorted.txt")],
                       [mono("/dev/null"), "Throw the output away", mono("ls /fake &gt; /dev/null 2&gt;&amp;1")]],
                      [3, 8, 8]),
        note="A single &gt; replaces the file. Use &gt;&gt; to add to it. In a pipeline, |&amp; sends both streams to the next command.",
        label=BG)

d.slide("redir-demo", "Two streams, two files",
        lambda t: row(example(t, ["printf 'normal output\\n' > evidence/stdout-demo.txt",
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
        lambda t: row(col(h3(t, "Example 1: stderr follows stdout to the file"),
                          term(t, ["printf 'ready,4\\n' > example-events.csv",
                                   "cat example-events.csv missing-demo.txt > both.txt 2>&1",
                                   "cat both.txt",
                                   ("out", "ready,4"),
                                   ("out", "cat: missing-demo.txt: No such file or directory")], size=24),
                          para(t, "First stdout goes to the file. Then 2&gt;&amp;1 points stderr at that same place.", size=30),
                          gap=20, flex=None),
                      col(h3(t, "Example 2: stderr stays on the screen"),
                          term(t, ["cat example-events.csv missing-demo.txt 2>&1 > only-out.txt",
                                   ("out", "cat: missing-demo.txt: No such file or directory"),
                                   "cat only-out.txt",
                                   ("out", "ready,4")], size=24),
                          para(t, "Here stderr is pointed at stdout while stdout is still the screen. Only then does stdout move to the file.", size=30),
                          gap=20, flex=None),
                      gap=40, align="flex-start"),
        note="Run Example 1 before Example 2. Read redirections from left to right.",
        label=BG)

d.slide("pipes", "A pipe joins two commands",
        lambda t: row(lst(t, ["The pipe | connects the stdout of one command to the stdin of the next.",
                              "The commands run at the same time. Data flows through as it is produced.",
                              "Only stdout goes through the pipe. stderr still goes to the terminal.",
                              "The exit status of a pipeline is, by default, the status of the last command."], size=34, flex=3),
                      example(t, ["printf 'ok,3\\nfail,2\\n'",
                               ("out", "ok,3"), ("out", "fail,2"),
                               "printf 'ok,3\\nfail,2\\n' | grep '^ok,'",
                               ("out", "ok,3"),
                               "printf 'ok,3\\nfail,2\\n' | grep '^ok,' | cut -d, -f2",
                               ("out", "3")], size=24),
                      gap=48, align="center"),
        note="Read it stage by stage: all rows, then only the ok rows, then only field 2 of those rows.",
        label=BG)

def guide_step(slug, title, commands, notes):
    if commands:
        d.slide(slug, title,
                lambda t: row(example(t, commands, size=24), lst(t, notes, size=30, flex=1),
                              gap=48, align="center"))
    else:
        d.slide(slug, title, lambda t: lst(t, notes, size=36))



d.opener("examples-open", "EXAMPLE", "Try it on a sample CSV",
         "Use these sample files to see each command's input and output before opening your personal lab.")

guide_step(
    "example-write", "Write, append and read",
    [
        "mkdir -p ~/lab4-examples",
        "cd ~/lab4-examples",
        "printf 'status,count\\nready,4\\n' > events.csv",
        "printf 'done,2\\nready-late,9\\nready,7\\n' >> events.csv",
        "cat events.csv",
        ("out", "status,count"),
        ("out", "ready,4"),
        ("out", "done,2"),
        ("out", "ready-late,9"),
        ("out", "ready,7"),
    ],
    [
        "mkdir -p creates the practice folder. cd enters it.",
        "printf writes text. The escape sequence creates a new line.",
        "Use > to replace the file and >> to append. cat displays the whole file.",
    ],
)

guide_step(
    "example-filter", "Select records, extract fields and count lines",
    [
        "grep '^ready,' events.csv",
        ("out", "ready,4"),
        ("out", "ready,7"),
        "grep '^ready,' events.csv | cut -d, -f2",
        ("out", "4"),
        ("out", "7"),
        "grep '^ready,' events.csv | wc -l",
        ("out", "2"),
    ],
    [
        "grep selects lines. The caret anchors the first field and the comma excludes ready-late.",
        "cut -d, -f2 takes the second comma-separated field.",
        "wc -l counts two records. The quantities are 4 and 7.",
    ],
)

guide_step(
    "example-save", "Display, save and compare",
    [
        "grep '^ready,' events.csv | tee selected.txt",
        ("out", "ready,4"),
        ("out", "ready,7"),
        "printf 'done,2\\n' | tee -a selected.txt",
        ("out", "done,2"),
        "cp -- selected.txt copy.txt",
        "diff -u selected.txt copy.txt",
    ],
    [
        "tee displays the selected rows and saves them. tee -a also keeps the existing lines.",
        "cp makes a copy. diff -u prints nothing when the files match.",
    ],
)

guide_step(
    "example-errors", "Save diagnostics and inspect the exit status",
    [
        "cat missing.csv > normal.txt 2> errors.txt",
        "echo $?",
        ("out", "1"),
        "cat errors.txt",
        ("out", "cat: missing.csv: No such file or directory"),
        "cat events.csv missing.csv > combined.txt 2>&1",
        "cat missing.csv | wc -l",
        ("out", "cat: missing.csv: No such file or directory"),
        ("out", "0"),
        "echo $?",
        ("out", "0"),
    ],
    [
        "The first cat leaves normal.txt empty and writes its diagnostic to errors.txt.",
        "The combined file receives both streams. In the pipeline, wc succeeds on empty input.",
    ],
)

guide_step(
    "example-oslab", "Check your Lab 4 workspace",
    [
        "oslab doctor",
        "oslab prelab lab4",
        "oslab start lab4",
        "oslab values lab4",
        ("out", "status = ready"),
        ("out", "other  = done"),
        "oslab hint lab4 1",
        "oslab check lab4",
    ],
    [
        "doctor checks setup. prelab opens the short review.",
        "start prepares your folder. values prints your own status words.",
        "hint gives a pointer. check reports the saved evidence milestones.",
    ],
)

d.opener('lab-open', 'LAB 4', 'Read the help-desk event log', 'Select records, extract their quantities, and save normal output and diagnostics.')

guide_step(
    'overview', 'Lab 4: Redirection and Pipelines',
    [],
    [
        'Work directly in the terminal. No Bash script is required.',
        'Goal: select records, extract fields, count lines, and distinguish normal output from errors.',
        '120 minutes • individual account • personal status words',
    ],
)

guide_step(
    'command-streams', 'Read the exit status',
    [],
    [
        'Run echo $? immediately after the command you want to check.',
        'Status 0 indicates success. For grep, 1 means no match and 2 means an error.',
        'A pipeline normally reports the status of its last command.',
    ],
)

guide_step(
    'start', 'Setup: 0–10 minutes',
    [
        'export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
        'oslab start lab4',
        'cd "$OSLAB_WORKSPACE/lab4"',
        'mkdir -p evidence',
        'oslab values lab4',
        'cat data/events.csv',
    ],
    [
        'Replace STATUS and OTHER with your own words.',
        'Never reset to fix one command.',
        "For status ready, type grep '^ready,' to exclude ready-late.",
    ],
)

d.opener('g-open', 'GUIDED', 'Streams, append and tee', 'Run each line in the terminal and inspect what it produces.')

guide_step(
    'guided-append', 'Guided: 10–25 minutes',
    [
        "printf 'first observation\\n' > evidence/practice.txt",
        "printf 'second observation\\n' >> evidence/practice.txt",
        'cat evidence/practice.txt',
    ],
    [
        'Which operator preserves the first line?',
    ],
)

guide_step(
    'guided-tee', 'Display and save',
    [
        "printf 'shown and saved\\n' | tee evidence/tee-demo.txt",
        "printf 'one more line\\n' | tee -a evidence/tee-demo.txt",
    ],
    [
        'tee writes to the screen and a file.',
        'tee -a preserves earlier file contents.',
    ],
)

guide_step(
    'guided-errors', 'Separate output from errors',
    [
        'cat data/not-present.csv > evidence/demo-out.txt 2> evidence/demo-error.txt',
        'echo $?',
        'cat evidence/demo-out.txt',
        'cat evidence/demo-error.txt',
    ],
    [
        'Inspect both files. Expected: empty stdout, diagnostic on stderr.',
        'Read exit status immediately; the next command changes it.',
    ],
)

guide_step(
    'guided-both', 'Save both streams in one file',
    [
        'cat data/events.csv data/not-present.csv > evidence/both.txt 2>&1',
        'cat evidence/both.txt',
    ],
    [
        'First send stdout to the file. Then 2>&amp;1 sends stderr to the same destination.',
        'Inspect the file for both CSV records and a diagnostic.',
    ],
)


guide_step(
    'predict', 'Prediction: 25–35 minutes',
    [
        'oslab predict lab4',
    ],
    [
        'Read your personal CSV first. Make your prediction alone with AI tools closed.',
        'Predict the first selected quantity, the matching-record count and the error stream.',
    ],
)

d.opener('c1-open', 'CORE 1', 'Select, extract and count', 'Minutes 35 to 55. Inspect each stage before moving on.')

guide_step(
    'core-select', 'Core 1: select, extract, count, minutes 35–55',
    [
        "grep '^STATUS,' data/events.csv | tee evidence/selected.txt",
        "grep '^STATUS,' data/events.csv | cut -d, -f2 | tee evidence/fields.txt",
        "grep '^STATUS,' data/events.csv | wc -l > evidence/normal.txt",
    ],
    [
        'The comma excludes STATUS-late.',
        'Expected count: 3. Quantities are not added.',
    ],
)

guide_step(
    'core-compare', 'Compare and record',
    [
        'cat evidence/normal.txt',
        'diff -u data/expected.txt evidence/normal.txt',
        'nano evidence/commands.txt',
        'oslab check lab4',
    ],
    [
        'No diff output means the counts agree.',
        'Save the three commands you used, one per line. The helper checks your saved results.',
    ],
)

d.opener('c2-open', 'CORE 2', 'Test changed and missing inputs', 'Minutes 55 to 70. Keep the original CSV for comparison.')

guide_step(
    'core-inputs', 'Core 2: changed inputs, minutes 55–70',
    [
        "printf 'status,count\\nOTHER,2\\n' > data/no-match.csv",
        'cp -- data/events.csv data/changed.csv',
        "printf 'STATUS,7\\nSTATUS-late,99\\n' >> data/changed.csv",
        "grep '^STATUS,' data/no-match.csv | wc -l > evidence/edge.txt",
        "grep '^STATUS,' data/changed.csv | wc -l >> evidence/edge.txt",
    ],
    [
        'Expected: 0 then 4. The quantity 7 adds one record.',
    ],
)

guide_step(
    'core-errors', 'Core 2: missing input',
    [
        'cat data/missing.csv > evidence/stdout.txt 2> evidence/stderr.txt',
        'echo $? > evidence/status.txt',
        'oslab check lab4',
    ],
    [
        'Expected: empty stdout, diagnostic naming missing.csv, nonzero status.',
        'Four Core milestones check saved observations, not command authorship.',
        'Add your actual test commands to evidence/commands.txt.',
    ],
)

guide_step(
    'plus', 'Demonstration and optional work, minutes 70–85',
    [
        'cat data/missing.csv | wc -l',
        'echo $?',
    ],
    [
        'The last stage may succeed even when the input command fails.',
        "Plus: inspect grep's no-match status (1).",
        'Challenge: put stderr into the pipe and use tee to display/save both streams.',
    ],
)

d.opener('cp-open', 'LIVE CHECKPOINT', 'Select from fresh records', 'Wait for release. Work alone with AI tools closed.')

guide_step(
    'cp-steps', 'Checkpoint: 85–100 minutes',
    [
        'oslab checkpoint lab4',
        'oslab check lab4',
    ],
    [
        'Wait for release; close AI tools.',
        'Answer questions about fresh records. Create the input with the supplied command.',
        'Write your own exact-selection pipeline.',
        'Save evidence/checkpoint-selected.txt and checkpoint.txt (record count).',
        'Look for five passing milestones.',
    ],
)

d.opener('end-open', 'DEBRIEF AND SUBMIT', 'Explain what each stage did', 'Use your saved observations to explain the results.')

guide_step(
    'debrief', 'Debrief: 100–110 minutes',
    [
        'oslab debrief lab4',
    ],
    [
        'Why does wc -l count records here?',
        'What does cut extract?',
        'Why is the comma important in grep?',
        'How did you prove a diagnostic used stderr?',
        'Why can a pipeline report status 0 after an input error?',
    ],
)

guide_step(
    'submission', 'Submit and grading: 110–120 minutes',
    [],
    [
        'Fill in README.md from the report template and include checkpoint.txt and the required evidence files.',
        'Keep commands.txt and the empty stdout.txt. Commit and push with the Lab 1 Git workflow.',
        'Core results: 2 • commands/tests: 2 • prediction/debrief: 2 • checkpoint: 3 • submission: 1',
        'Scripts belong in Lab 7. Advanced extensions require later prerequisites.',
    ],
)

d.opener("ext-open", "BEYOND THE CORE", "Processes, jobs and signals", "For later study after the prerequisites in the extensions handout.")

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
                      example(t, ["sleep 30 & pid=$!",
                               'ps -o pid,ppid,stat,comm -p "$pid"',
                               'kill -STOP "$pid"',
                               'kill -CONT "$pid"',
                               'kill -TERM "$pid"',
                               'wait "$pid"; echo "status=$?"'], size=24, width=HALF),
                      gap=32, align="center"),
        note="$! is the PID of the last background job. A stopped process shows state T. A wait status above 128 means a signal ended it.",
        label=EXT)

d.slide("jobcontrol", "Job control",
        lambda t: row(example(t, ["sleep 60 &",
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
         ("Count records", "Use wc -l to count selected rows and cut to inspect their fields."),
         ("Test the edges", "Try inputs with no matches, an extra matching row and a missing file.")],
        "chapter 3, Processes", ("Lab 5: threads, kernel workers and signals", "Look at threads inside a process, the kernel's own workers, and how a signal reaches a process."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: the three streams, redirection operators, and pipes.", "start": "bg-open"},
    "examples": {"description": "Worked terminal examples with sample files and output.", "start": "examples-open"},
    "s3": {"description": "How the lab works: the scenario, setup and personal values.", "start": "lab-open"},
    "s4": {"description": "Guided: redirection and pipelines, then the prediction.", "start": "g-open"},
    "s5": {"description": "Core 1 and Core 2: select, extract and count, then test changed inputs.", "start": "c1-open"},
    "s6": {"description": "The live checkpoint: why, the steps with oslab, and what it asks.", "start": "cp-open"},
    "s7": {"description": "Debrief, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: processes, jobs and signals, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
