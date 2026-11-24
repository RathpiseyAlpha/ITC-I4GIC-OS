"""Paths and names, Medium: Messy share (Lab 2)."""
import kit

META = {"id": "paths-medium", "track": "paths", "level": "medium", "title": "Messy share",
        "learn": "Names with spaces and leading dashes; wildcards keep every name whole; -- ends the options."}
META["skills"] = ['wildcards', 'move', 'quoting']   # the roadmap's skills this scenario trains (a clear acquires them)
FOLDERS = {"txt": "text", "csv": "tables", "log": "logs", "jpg": "photos"}
FORMS = ("-draft %s.txt", "--%s.csv", "%s 01.jpg", "-%s log.log", "%s.txt", "notes %s.csv", "%s-final.jpg",
         "- %s.log", "%s plan.txt", "-%s.csv", "trip %s.jpg", "%s.log", "--old %s.txt", "%s 2026.csv", "-%s.jpg",
         "night %s.log")


def values(pick):
    words = kit.distinct(pick, "w", kit.WORDS, len(FORMS))
    names = [f % w for f, w in zip(FORMS, words)]
    return {"names": names, "ref": 1000 + pick("ref", 9000)}


def folder_of(name):
    return FOLDERS[name.rsplit(".", 1)[1]]


def content(v, name):
    return "%s / %d\n" % (name, v["ref"])


def fixture(v):
    return {"files": {"share/" + n: content(v, n) for n in v["names"]}}


def brief(v):
    return [
        {"p": "The shared folder `share/` is a mess: %d files, some with spaces in their names, some starting with "
              "a dash, which makes a command take them for options." % len(v["names"])},
        {"ol": ["Make the folders `share/text`, `share/tables`, `share/logs` and `share/photos`.",
                "Move every `.txt` file into `text`, every `.csv` into `tables`, every `.log` into `logs` and every "
                "`.jpg` into `photos`.",
                "Leave no file loose in `share/`."]},
    ]


def hints(v):
    dash = [n for n in v["names"] if n.startswith("-")][0]
    return [
        "`ls` may complain about a name like `%s`: it looks like an option. `ls -- *` or `ls ./*` lists them." % dash,
        "A wildcard keeps each name whole, spaces and all. `--` tells `mv` that what follows are names, not options.",
        "`cd share`, `mkdir text tables logs photos`, then `mv -- *.txt text/`, `mv -- *.csv tables/`, "
        "`mv -- *.log logs/` and `mv -- *.jpg photos/`.",
    ]


def collect(v, hidden):
    return {"tree": True}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    folders = [f for f in FOLDERS.values() if not t.is_dir("share/" + f)]
    out = [kit.ck("folders", "the four folders exist in share/", not folders,
                  "missing: share/%s" % folders[0] if folders else "")]
    wrong = [n for n in v["names"] if t.text("share/%s/%s" % (folder_of(n), n)) != content(v, n)]
    out.append(kit.ck("sorted", "every file is in the folder for its type, unchanged", not wrong,
                      "%d file(s) are not in place, for example %r" % (len(wrong), wrong[0]) if wrong else ""))
    loose = [p for p in t.children("share") if not t.is_dir(p)]
    out.append(kit.ck("loose", "no file is left loose in share/", not loose,
                      "still in share/: %r" % loose[0].split("/", 1)[1] if loose else ""))
    expected = {"share/%s/%s" % (folder_of(n), n) for n in v["names"]}
    strays = [p for p in t.files() if p.startswith("share/") and p not in expected]
    out.append(kit.ck("strays", "no stray files were made by mistake", not strays,
                      "%r was not in the share before; a name was split or taken for an option" % strays[0] if strays else ""))
    return out


def steps(v, remix=False):
    return kit.guided([
        ("`mkdir a b c d` makes several folders at once.",
         "Make the four folders `share/text`, `share/tables`, `share/logs` and `share/photos`.", ["folders"]),
        ("A wildcard keeps each name whole, spaces included. A name that starts with a dash looks like an option, so put `--` before the "
         "names: `mv -- *.txt text/`.",
         "Move every file into the folder for its type (`.txt`, `.csv`, `.log`, `.jpg`), and leave none loose in `share/`.",
         ["sorted", "loose", "strays"]),
    ], remix)
