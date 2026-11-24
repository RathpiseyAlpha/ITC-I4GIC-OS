"""Paths and names, Hard: Lost in the tree (Lab 2)."""
import kit

META = {"id": "paths-hard", "track": "paths", "level": "hard", "title": "Lost in the tree",
        "learn": "find tests the type, the name, the size and the age of every file in a tree at once."}
META["skills"] = ['find']   # the roadmap's skills this scenario trains (a clear acquires them)
EXTS = ("bak", "old", "tmp")
TOP = ("2024", "2025", "2026")
DEPTS = ("finance", "sales", "lab", "office")
SUBS = ("q1", "q2", "drafts", "misc")


def values(pick):
    return {"ext": EXTS[pick("ext", len(EXTS))], "kb": (10, 20, 30)[pick("kb", 3)], "days": (14, 30, 60)[pick("days", 3)],
            "seed": pick("seed", 2 ** 31)}


def plan(v):
    """Every file: path -> (size in bytes, age in days). The targets are the ones the student must list."""
    import random
    r = random.Random(v["seed"])
    ext, big, small = v["ext"], v["kb"] * 1024 * 2, v["kb"] * 1024 // 3
    old, recent = v["days"] * 2, max(1, v["days"] // 3)
    other = [e for e in EXTS if e != ext][0]
    files, targets = {}, []
    kinds = ["target"] * 7 + ["small"] * 5 + ["recent"] * 5 + ["otherext"] * 5 + ["suffix"] * 3 + ["plain"] * 20
    r.shuffle(kinds)
    for i, kind in enumerate(kinds):
        folder = "archive/%s/%s/%s" % (r.choice(TOP), r.choice(DEPTS), r.choice(SUBS))
        word = kit.WORDS[(i * 7 + r.randint(0, 3)) % len(kit.WORDS)]
        name = "%s-%02d.%s" % (word, i, ext)
        size, age = big, old
        if kind == "small":
            size = small
        elif kind == "recent":
            age = recent
        elif kind == "otherext":
            name = "%s-%02d.%s" % (word, i, other)
        elif kind == "suffix":
            name = "%s-%02d.%s.txt" % (word, i, ext)
        elif kind == "plain":
            name, size, age = "%s-%02d.txt" % (word, i), r.choice((small, big)), r.choice((old, recent))
        files["%s/%s" % (folder, name)] = (size, age)
        if kind == "target":
            targets.append("%s/%s" % (folder, name))
    return files, sorted(targets)


def fixture(v):
    files, _t = plan(v)
    out = {p: {"t": ("x" * 63 + "\n") * (size // 64), "age": age} for p, (size, age) in files.items()}
    out["archive/2026/office/old.%s/README.txt" % v["ext"]] = {"t": "a folder, not a file\n", "age": v["days"] * 2}
    return {"files": out}


def brief(v):
    return [
        {"p": "Somewhere in `archive/` are leftover `.%s` files. The ones worth looking at are big and old." % v["ext"]},
        {"ol": ["List every **file** under `archive/` whose name ends in `.%s`, that is larger than **%d KB**, and that "
                "was last changed more than **%d days** ago." % (v["ext"], v["kb"], v["days"]),
                "Write their paths, starting with `archive/`, one per line, in `found.txt`."]},
    ]


def hints(v):
    return [
        "`find` walks the whole tree and can test several things at once; all the tests must be true.",
        "The tests you need: `-type f`, `-name '*.%s'`, `-size +%dk` and `-mtime +%d`." % (v["ext"], v["kb"], v["days"]),
        "`find archive -type f -name '*.%s' -size +%dk -mtime +%d > found.txt`" % (v["ext"], v["kb"], v["days"]),
    ]


def collect(v, hidden):
    return {"tree": True, "texts": ["found.txt"]}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    _files, targets = plan(v)
    text = t.text("found.txt")
    got = [kit.norm(ln) for ln in kit.lines(text)]
    want = set(targets)
    extra = [p for p in got if p not in want]
    missing = sorted(want - set(got))
    out = [kit.ck("exists", "found.txt exists", text is not None, "there is no found.txt yet")]
    why = ("%s should not be in the list" % extra[0]) if extra else ""
    if extra and extra[0].endswith(".txt"):
        why += ": its name does not end in .%s" % v["ext"]
    elif extra and t.is_dir(extra[0]):
        why += ": it is a folder"
    out.append(kit.ck("nothing-extra", "every path in found.txt matches all three rules", text is not None and not extra,
                      why or "found.txt is empty"))
    out.append(kit.ck("all-found", "found.txt lists every matching file", text is not None and not missing,
                      "%d matching file(s) are missing from the list" % len(missing) if text is not None else "found.txt is empty"))
    out.append(kit.ck("once", "each path appears once", len(got) == len(set(got)), "a path is listed twice"))
    return out
