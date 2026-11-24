"""Redirection and pipelines, Hard: Top talkers (Lab 4)."""
import kit

META = {"id": "pipes-hard", "track": "pipes", "level": "hard", "title": "Top talkers",
        "learn": "awk adds up per key; sort -k2,2nr orders by a number; bad lines are filtered out first."}
META["skills"] = ['awk', 'sort-uniq']   # the roadmap's skills this scenario trains (a clear acquires them)


def values(pick):
    return {"seed": pick("seed", 2 ** 31), "hosts": 10 + pick("hosts", 5)}


def data_of(v):
    import random
    r = random.Random(v["seed"])
    hosts = ["192.168.%d.%d" % (r.randint(0, 9), r.randint(2, 250)) for _ in range(v["hosts"])]
    hosts = sorted(set(hosts))
    while True:
        rows, total = [], {}
        for i in range(320):
            h = r.choice(hosts)
            b = r.randint(100, 50000)
            rows.append("%s %d /files/%s-%d.zip" % (h, b, kit.WORDS[i % len(kit.WORDS)], i))
            total[h] = total.get(h, 0) + b
        top = sorted(total.items(), key=lambda x: -x[1])
        if len({x[1] for x in top[:6]}) == 6:
            break
    bad = ["%s - /files/broken.zip" % hosts[0], "%s 12k /files/size-in-kb.zip" % hosts[1], "%s /files/no-size.zip" % hosts[2],
           "%s 900 /files/a.zip extra-field" % hosts[3], "%s 0x1F /files/hex-size.zip" % hosts[4]]
    for i, b in enumerate(bad):
        rows.insert(30 + i * 47, b)
    return rows, bad, top[:5]


def fixture(v):
    rows, _bad, _top = data_of(v)
    return {"files": {"transfers.log": "\n".join(rows) + "\n"}}


def brief(v):
    return [
        {"p": "`transfers.log` has one download per line: the address, the number of bytes, and the path. A few lines "
              "are broken."},
        {"ol": ["Write in `bad.txt` every broken line, exactly as it is in the log. A good line has exactly 3 fields, "
                "and its second field is a whole number.",
                "Write in `top5.txt` the 5 addresses that downloaded the most bytes in total over the good lines, "
                "biggest first, one per line as `ADDRESS TOTAL`."]},
    ]


def hints(v):
    return [
        "`awk 'NF != 3 || $2 !~ /^[0-9]+$/' transfers.log` prints the lines that are not good.",
        "`awk '{sum[$1] += $2} END {for (a in sum) print a, sum[a]}'` adds the bytes per address. Give it only the good lines.",
        "`awk 'NF == 3 && $2 ~ /^[0-9]+$/ {s[$1] += $2} END {for (a in s) print a, s[a]}' transfers.log | sort -k2,2nr | head -5 > top5.txt`",
    ]


def collect(v, hidden):
    return {"tree": True, "texts": ["bad.txt", "top5.txt"]}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    _rows, bad, top = data_of(v)
    gb = t.text("bad.txt")
    got_bad = [ln.rstrip("\r") for ln in (gb or "").splitlines() if ln.strip()]
    out = [kit.ck("bad", "bad.txt holds every broken line, exactly", gb is not None and sorted(got_bad) == sorted(bad),
                  "there is no bad.txt" if gb is None else
                  ("bad.txt has %d line(s); the log has %d broken ones" % (len(got_bad), len(bad)) if len(got_bad) != len(bad)
                   else "the lines in bad.txt are not the broken ones, or were changed"))]
    gt = t.text("top5.txt")
    got = [" ".join(ln.split()) for ln in kit.lines(gt)]
    want = ["%s %d" % x for x in top]
    if gt is None:
        why = "there is no top5.txt"
    elif len(got) != 5:
        why = "top5.txt should have 5 lines, it has %d" % len(got)
    elif [g.split(" ")[0] for g in got] == [w.split(" ")[0] for w in want]:
        why = "the addresses are right, but a total is not"
    elif sorted(got) == sorted(want):
        why = "the right lines, in the wrong order: biggest first"
    else:
        why = "those are not the 5 biggest totals (did a broken line count?)"
    out.append(kit.ck("top", "top5.txt has the 5 biggest totals, biggest first", got == want, why))
    return out
