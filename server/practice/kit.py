"""Helpers for writing practice scenarios (server/practice/scenarios/*.py and private/*.py).

A scenario never touches the student's files itself. Its `fixture(v)` returns the starting files, `collect(v, hidden)`
says what the student-side collector should bring back (the workspace tree, the student's processes, runs of the
student's script on given inputs), and `checks(data, v, hidden, info)` judges that data. `checks` runs as root in the
runner, on plain data: it reads no file and runs nothing.
"""
import posixpath
import random

WORDS = ("maple", "river", "cloud", "stone", "tiger", "lemon", "ocean", "panda",
         "candle", "garden", "pencil", "rocket", "forest", "silver", "bridge", "market",
         "comet", "harbor", "violet", "falcon", "meadow", "copper", "glacier", "orchid")


def ck(cid, label, ok, why=""):
    """One check: label says what is checked (always shown); why says what is wrong without giving the answer."""
    return {"id": cid, "label": label, "ok": bool(ok), "why": "" if ok else why}


def guided(rows, remix=False):
    """The steps of a guided scenario, for a function `steps(v, remix=False)` in the scenario file: rows of
    (lesson line, task, [ids of the checks that decide the step]). Every id must be one the scenario's checks always report.
    A remix has no lesson lines: the student has read them, so the second time is a test."""
    return [{"learn": "" if remix else learn, "task": task, "checks": list(checks)} for learn, task, checks in rows]


def distinct(pick, label, items, n):
    """n different items, in a personal order."""
    pool = list(items)
    out = []
    for i in range(n):
        out.append(pool.pop(pick("%s%d" % (label, i), len(pool))))
    return out


def rng(pick, label="seed"):
    return random.Random(pick(label, 2 ** 31))


def lines(text):
    """The non-empty lines of a text, without trailing spaces or carriage returns."""
    return [ln.rstrip() for ln in (text or "").splitlines() if ln.strip()]


def norm(path):
    """A path as a student may write it (./a/b, a//b/, a/b/) in the plain form a/b."""
    p = (path or "").strip()
    while p.startswith("./"):
        p = p[2:]
    p = posixpath.normpath(p) if p else p
    return "" if p == "." else p


class Tree:
    """The workspace snapshot from the collector: one entry per path, relative to the workspace.

    entry: p (path), t (f file, d folder, l symbolic link, o other), m (mode bits), s (size), mt (mtime), i (inode),
    n (link count), x (a link's target), c (a small file's text, or None when unreadable or too big).
    """

    def __init__(self, entries, root=""):
        self.root = root or ""
        self.by = {e["p"]: e for e in entries or []}

    @classmethod
    def of(cls, data, name=None):
        if name is None:
            return cls(data.get("tree") or [], data.get("root", ""))
        t = (data.get("trees") or {}).get(name) or {}
        return cls(t.get("entries") or [], t.get("root", ""))

    def get(self, p):
        return self.by.get(norm(p))

    def kind(self, p):
        e = self.get(p)
        return e["t"] if e else None

    def is_file(self, p):
        return self.kind(p) == "f"

    def is_dir(self, p):
        return self.kind(p) == "d"

    def is_link(self, p):
        return self.kind(p) == "l"

    def text(self, p):
        e = self.get(p)
        return e.get("c") if e and e["t"] == "f" else None

    def files(self, under=""):
        under = norm(under)
        pre = under + "/" if under else ""
        return sorted(p for p, e in self.by.items() if e["t"] == "f" and p.startswith(pre))

    def entries(self, under="", kinds="fdlo"):
        under = norm(under)
        pre = under + "/" if under else ""
        return sorted(p for p, e in self.by.items() if e["t"] in kinds and p.startswith(pre))

    def children(self, folder):
        folder = norm(folder)
        pre = folder + "/" if folder else ""
        return sorted(p for p in self.by if p.startswith(pre) and "/" not in p[len(pre):])

    def target_rel(self, link_path):
        """Where a symbolic link points, as a workspace path, one step only (None when it points outside)."""
        e = self.get(link_path)
        if not e or e["t"] != "l":
            return None
        x = e.get("x") or ""
        if x.startswith("/"):
            if not self.root or not (x == self.root or x.startswith(self.root.rstrip("/") + "/")):
                return None
            rel = x[len(self.root.rstrip("/")) + 1:]
        else:
            rel = posixpath.join(posixpath.dirname(norm(link_path)), x)
        rel = posixpath.normpath(rel)
        if rel.startswith("..") or rel == ".":
            return None
        return rel

    def resolve(self, p, depth=0):
        """Follow symbolic links inside the workspace; the final path, or None if it leaves or is broken."""
        p = norm(p)
        if depth > 12:
            return None
        e = self.get(p)
        if e is None:
            # a folder on the way may be a link
            parts = p.split("/")
            for i in range(1, len(parts)):
                head = "/".join(parts[:i])
                if self.is_link(head):
                    t = self.resolve(head, depth + 1)
                    return self.resolve(posixpath.join(t, *parts[i:]), depth + 1) if t is not None else None
            return None
        if e["t"] == "l":
            t = self.target_rel(p)
            return self.resolve(t, depth + 1) if t is not None else None
        return p


def procs_matching(procs, *needles):
    """The student's processes whose command line contains every needle."""
    out = []
    for pr in procs or []:
        line = " ".join(pr.get("args") or []) or pr.get("comm", "")
        if all(n in line for n in needles):
            out.append(pr)
    return out


def zombies(procs):
    return [pr for pr in procs or [] if pr.get("state") == "Z"]
