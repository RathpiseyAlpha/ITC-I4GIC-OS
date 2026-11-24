"""Wildcards and links, Medium: Broken after a move (Lab 3)."""
import kit

META = {"id": "links-medium", "track": "links", "level": "medium", "title": "Broken after a move",
        "learn": "A relative link target is read from the link's own folder; ln -sfn replaces a link."}
META["skills"] = ['links']   # the roadmap's skills this scenario trains (a clear acquires them)


def values(pick):
    names = kit.distinct(pick, "n", kit.WORDS, 5)
    absolute = set(kit.distinct(pick, "abs", range(5), 2))
    return {"names": names, "abs": [names[i] for i in sorted(absolute)], "ref": 100 + pick("ref", 900)}


def fixture(v):
    files = {}
    for n in v["names"]:
        files["store/%s.txt" % n] = "%s report %d\n" % (n, v["ref"])
        files["links/%s" % n] = {"l": ("{ROOT}/old/%s.txt" % n) if n in v["abs"] else ("../old/%s.txt" % n)}
    return {"files": files}


def brief(v):
    return [
        {"p": "The reports moved from `old/` to `store/`, and the five links in `links/` broke. %d of them are "
              "relative and %d absolute." % (5 - len(v["abs"]), len(v["abs"]))},
        {"ol": ["Repair every link in `links/` so it points to its report in `store/`.",
                "Keep a relative link relative, and an absolute link absolute.",
                "Do not move the reports back."]},
    ]


def hints(v):
    rel = [n for n in v["names"] if n not in v["abs"]][0]
    return [
        "`ls -l links/` shows where each link points; `readlink links/%s` prints one target." % rel,
        "A relative target is read from the link's folder, `links/`. So the report is `../store/%s.txt` from there." % rel,
        "`ln -sfn ../store/%s.txt links/%s` repairs a relative one; for an absolute one, start the target with "
        "`$PWD/store/`." % (rel, rel),
    ]


def collect(v, hidden):
    return {"tree": True, "texts": []}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    broken, kind = [], []
    for n in v["names"]:
        p = "links/" + n
        e = t.get(p)
        if not e or e["t"] != "l" or t.resolve(p) != "store/%s.txt" % n:
            broken.append(n)
        elif (n in v["abs"]) != str(e.get("x", "")).startswith("/"):
            kind.append(n)
    out = [kit.ck("repaired", "every link in links/ leads to its report", not broken,
                  "%d link(s) still broken or missing, for example links/%s" % (len(broken), broken[0]) if broken else "")]
    out.append(kit.ck("kind", "relative links stay relative, absolute ones absolute", not kind and not broken,
                      ("links/%s changed kind" % kind[0]) if kind else "repair the links first"))
    moved = [n for n in v["names"] if not t.is_file("store/%s.txt" % n)]
    out.append(kit.ck("stay", "the reports stay in store/", not moved and not t.files("old"),
                      "a report left store/ (%s)" % (moved[0] if moved else "old/ has files again")))
    return out


def steps(v, remix=False):
    return kit.guided([
        ("`readlink links/NAME` prints where a link points. A relative target is read from the folder the link is in, so a link in `links/` "
         "reaches `store/` with `../store/`; an absolute one starts with `/`. `ln -sfn TARGET LINK` replaces a link.",
         "Repair the five links in `links/` so each leads to its report in `store/`. Keep relative links relative and absolute ones "
         "absolute, and leave the reports where they are.", ["repaired", "kind", "stay"]),
    ], remix)
