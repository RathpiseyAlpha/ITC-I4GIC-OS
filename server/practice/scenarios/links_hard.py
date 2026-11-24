"""Wildcards and links, Hard: Release switch (Lab 3)."""
import kit

META = {"id": "links-hard", "track": "links", "level": "hard", "title": "Release switch",
        "learn": "ln -sfn swaps a link to a folder in one step; without -n, ln goes into the old folder."}
META["skills"] = ['links']   # the roadmap's skills this scenario trains (a clear acquires them)


def values(pick):
    order = kit.distinct(pick, "rel", ("2026.1", "2026.2", "2026.3", "2026.4"), 4)
    return {"releases": sorted(order), "from": order[0], "to": order[1], "app": kit.WORDS[pick("app", len(kit.WORDS))]}


def fixture(v):
    files = {}
    for r in v["releases"]:
        files["releases/%s/index.html" % r] = "<h1>%s %s</h1>\n" % (v["app"], r)
        files["releases/%s/VERSION" % r] = r + "\n"
    files["current"] = {"l": "releases/%s" % v["from"]}
    return {"files": files}


def brief(v):
    return [
        {"p": "The web server shows whatever `current` points to. Today it is release %s; release **%s** must go live."
              % (v["from"], v["to"])},
        {"ol": ["Write in `switch.log` what `current` points to now (the output of `readlink current`).",
                "Switch `current` to `releases/%s`, with one command. Keep it a relative link." % v["to"],
                "Add a second line to `switch.log`: what `current` points to after the switch.",
                "Leave the releases themselves unchanged."]},
    ]


def hints(v):
    return [
        "`readlink current >> switch.log` adds the target to the file. Run it before and after.",
        "`ln -sf releases/%s current` does not replace a link to a folder: `ln` follows `current` into the old "
        "release and makes the new link there. `-n` treats `current` as the link itself." % v["to"],
        "`readlink current > switch.log`, `ln -sfn releases/%s current`, `readlink current >> switch.log`." % v["to"],
    ]


def collect(v, hidden):
    return {"tree": True, "texts": ["switch.log", "releases"]}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    cur = t.get("current")
    target = "releases/" + v["to"]
    ok = bool(cur and cur["t"] == "l" and t.resolve("current") == target)
    why = "current is gone" if not cur else ("current is not a symbolic link any more" if cur["t"] != "l"
                                             else "current points to %r" % cur.get("x"))
    out = [kit.ck("switched", "current leads to release %s" % v["to"], ok, why)]
    out.append(kit.ck("relative", "current is a relative link", ok and not str(cur.get("x", "")).startswith("/"),
                      "current is an absolute link; give a relative target" if ok else "switch current first"))
    strays = [p for p in t.entries("releases", "l")]
    out.append(kit.ck("no-stray", "no link was made inside a release", not strays,
                      "found the link %s: without -n, ln followed current into the old release" % strays[0] if strays else ""))
    changed = [r for r in v["releases"] if t.text("releases/%s/VERSION" % r) != r + "\n"]
    out.append(kit.ck("releases", "the releases are unchanged", not changed, "release %s changed" % changed[0] if changed else ""))
    got = [kit.norm(x) for x in kit.lines(t.text("switch.log"))]
    out.append(kit.ck("log", "switch.log has the target before, then after", got == ["releases/" + v["from"], target],
                      "there is no switch.log" if t.text("switch.log") is None else
                      ("switch.log should have 2 lines, it has %d" % len(got) if len(got) != 2 else "those are not the targets before and after")))
    return out
