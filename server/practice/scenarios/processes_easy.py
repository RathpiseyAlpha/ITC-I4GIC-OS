"""Files and processes, Easy: Unpack the delivery (Lab 1)."""
import kit

META = {"id": "processes-easy", "track": "processes", "level": "easy", "title": "Unpack the delivery",
        "learn": "mkdir -p makes several folders at once; mv moves several files into a folder."}
META["skills"] = ['mkdir', 'move']   # the roadmap's skills this scenario trains (a clear acquires them)
DEPTS = ("kitchen", "bakery", "cellar", "office", "garage", "studio", "library", "garden")
ITEMS = ("apron", "knife", "flour", "sugar", "candle", "ladder", "stapler", "paint", "brush", "notebook", "hammer", "basket")


def values(pick):
    depts = kit.distinct(pick, "dept", DEPTS, 3)
    items = kit.distinct(pick, "item", ITEMS, 6)
    return {"shop": kit.WORDS[pick("shop", len(kit.WORDS))], "depts": depts, "items": items,
            "where": {it: depts[i % 3] for i, it in enumerate(items)}}


def content(v, it):
    return "item: %s\nfor: %s\nshop: %s\n" % (it, v["where"][it], v["shop"])


def fixture(v):
    files = {"inbox/%s.txt" % it: content(v, it) for it in v["items"]}
    rows = ["# delivery for the %s shop: a department, then its files" % v["shop"]]
    for d in v["depts"]:
        rows.append("%s: %s" % (d, " ".join("%s.txt" % it for it in v["items"] if v["where"][it] == d)))
    files["delivery.txt"] = "\n".join(rows) + "\n"
    return {"dirs": ["inbox"], "files": files}


def brief(v):
    return [
        {"p": "A delivery for the **%s** shop arrived in `inbox/`. The list `delivery.txt` says which department "
              "each file belongs to." % v["shop"]},
        {"ol": ["Make a folder `store/` with one folder inside it for each department in `delivery.txt`.",
                "Move every file from `inbox/` into its department's folder in `store/`. Keep the files as they are.",
                "Leave `inbox/` empty, but keep the folder."]},
    ]


def hints(v):
    d = v["depts"]
    first = [it for it in v["items"] if v["where"][it] == d[0]]
    return [
        "Read the list first with `cat delivery.txt`. One `mkdir -p` can make several folders at once.",
        "`mv` takes several files, then the folder last: `mv inbox/a.txt inbox/b.txt store/x/`.",
        "`mkdir -p store/%s store/%s store/%s`, then `mv %s store/%s/`, and the same for the other departments."
        % (d[0], d[1], d[2], " ".join("inbox/%s.txt" % i for i in first), d[0]),
    ]


def collect(v, hidden):
    return {"tree": True}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    missing = [d for d in v["depts"] if not t.is_dir("store/" + d)]
    why = ("missing: %s" % ", ".join("store/" + d for d in missing)) if t.is_dir("store") else "there is no folder store/ yet"
    out = [kit.ck("folders", "store/ has a folder for each department", not missing, why)]
    wrong = ["%s.txt" % it for it in v["items"] if t.text("store/%s/%s.txt" % (v["where"][it], it)) != content(v, it)]
    out.append(kit.ck("files", "every file is in its department's folder, unchanged", not wrong,
                      "%d file(s) are not where delivery.txt says, or were changed: %s" % (len(wrong), ", ".join(wrong[:3]))))
    left = t.children("inbox")
    out.append(kit.ck("inbox", "inbox/ is empty and still there", t.is_dir("inbox") and not left,
                      ("inbox/ still holds %d file(s); moving a file, not copying it, takes it out of inbox/" % len(left))
                      if left else "inbox/ is gone; keep the folder"))
    return out


def steps(v, remix=False):
    return kit.guided([
        ("`cat delivery.txt` shows which department each file belongs to. `mkdir -p a b c` makes several folders at once.",
         "Make `store/` with one folder inside it for each department named in `delivery.txt`.", ["folders"]),
        ("`mv` takes several files and the folder last. Moving takes a file out of its old folder, which is what empties `inbox/`.",
         "Move every file from `inbox/` into its department's folder in `store/`, unchanged, and keep the empty `inbox/` folder.",
         ["files", "inbox"]),
    ], remix)
