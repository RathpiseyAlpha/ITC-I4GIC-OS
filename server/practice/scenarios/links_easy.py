"""Wildcards and links, Easy: Two kinds of link (Lab 3)."""
import kit

META = {"id": "links-easy", "track": "links", "level": "easy", "title": "Two kinds of link",
        "learn": "A hard link is another name for the same inode; a symbolic link holds a path."}
META["skills"] = ['links']   # the roadmap's skills this scenario trains (a clear acquires them)


def values(pick):
    return {"name": kit.WORDS[pick("name", len(kit.WORDS))], "port": 8000 + pick("port", 900)}


def fixture(v):
    return {"files": {"config/%s.conf" % v["name"]: "# %s service\nport = %d\n" % (v["name"], v["port"])}}


def brief(v):
    c = "config/%s.conf" % v["name"]
    return [
        {"p": "The service reads `%s`. Two programs want to find it under other names." % c},
        {"ol": ["Make `app.conf`, a **hard link** to `%s`." % c,
                "Make `latest.conf`, a **symbolic link** to `%s`." % c,
                "Write the inode number of `%s` in `inode.txt` (just the number)." % c]},
    ]


def hints(v):
    c = "config/%s.conf" % v["name"]
    return [
        "`ln` makes hard links and `ln -s` symbolic links. The target comes first, then the new name.",
        "`ls -li` shows the inode number in the first column, and the link count after the mode.",
        "`ln %s app.conf`, `ln -s %s latest.conf`, then `ls -i %s`, and write the number in `inode.txt`." % (c, c, c),
    ]


def collect(v, hidden):
    return {"tree": True}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    c = "config/%s.conf" % v["name"]
    conf = t.get(c)
    out = [kit.ck("config", "%s is still there" % c, conf and conf["t"] == "f", "%s is missing" % c)]
    app = t.get("app.conf")
    hard = bool(conf and app and app["t"] == "f" and app["i"] == conf["i"])
    why = "there is no app.conf" if not app else ("app.conf is a symbolic link; a hard link has no arrow in ls -l" if app["t"] == "l"
                                                 else "app.conf is a copy with its own inode, not a hard link")
    out.append(kit.ck("hard", "app.conf is a hard link to %s" % c, hard, why))
    lat = t.get("latest.conf")
    sym = bool(lat and lat["t"] == "l" and t.resolve("latest.conf") == c)
    why = "there is no latest.conf" if not lat else ("latest.conf is not a symbolic link" if lat["t"] != "l"
                                                    else "latest.conf points to %r, which is not %s" % (lat.get("x"), c))
    out.append(kit.ck("symbolic", "latest.conf is a symbolic link to %s" % c, sym, why))
    got = (t.text("inode.txt") or "").strip()
    out.append(kit.ck("inode", "inode.txt holds the inode number", conf and got == str(conf["i"]),
                      "there is no inode.txt" if t.text("inode.txt") is None else "%r is not the inode number of %s" % (got[:20], c)))
    return out


def steps(v, remix=False):
    c = "config/%s.conf" % v["name"]
    return kit.guided([
        ("A hard link is a second name for the same file: both names share one inode, so a change through one shows through the other. "
         "`ln TARGET NAME` makes it, and the target comes first.",
         "Make `app.conf`, a hard link to `%s`." % c, ["config", "hard"]),
        ("A symbolic link is a small file that holds a path. `ln -s TARGET NAME` makes it, and `ls -l` shows it with an arrow.",
         "Make `latest.conf`, a symbolic link to `%s`." % c, ["symbolic"]),
        ("`ls -i FILE` prints the inode number of a file: the number a hard link shares.",
         "Write the inode number of `%s` in `inode.txt` (just the number)." % c, ["inode"]),
    ], remix)
