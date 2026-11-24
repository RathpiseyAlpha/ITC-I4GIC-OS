#!/usr/bin/env python3
"""Load test for the exam room: N scripted terminals running typical midterm commands at once.

Run on the server, before an exam, with the exam OPEN for a practice config and test accounts (not real students:
every session leaves a recording and a tmux session in the account). The ticket key must be readable, so run it as
root or as a member of itc-exam:

    sudo python3 /opt/itc-os-exam/loadtest.py --users /secure/test-accounts.txt --minutes 5
    sudo python3 /opt/itc-os-exam/loadtest.py --users ... --url ws://127.0.0.1:5010/term --every 2

It prints, every 10 seconds, how many terminals are up, the command round-trip time (median and 95th percentile) and
the server's available memory. Stop if available memory falls under 1 GB (see the spec's Capacity section).
"""
import argparse
import asyncio
import json
import random
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common  # noqa: E402

COMMANDS = [
    "ls -la | wc -l",
    "grep -c a values.txt",
    "cut -d, -f2 d/data/*.csv | head -n 3",
    "find b -type f | wc -l",
    "ps | wc -l",
    "cat values.txt > /dev/null",
    "ls -li c | head -n 5",
]


def mem_available_mb():
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except OSError:
        pass
    return -1


class Stats:
    def __init__(self):
        self.up = 0
        self.failed = 0
        self.rtt = []
        self.errors = []


async def one(user, url, key, exam_id, stats, end, every, origin):
    import websockets
    try:
        ws = await websockets.connect(url, max_size=None, open_timeout=20, origin=origin or None)
        await ws.send(json.dumps({"t": "auth", "ticket": common.make_ticket(user, exam_id, key), "cols": 100, "rows": 30}))
        while True:
            m = await asyncio.wait_for(ws.recv(), 30)
            if isinstance(m, str):
                msg = json.loads(m)
                if msg.get("t") == "hello":
                    break
                if msg.get("t") == "bye":
                    raise RuntimeError("refused: %s" % msg.get("why"))
    except Exception as e:
        stats.failed += 1
        stats.errors.append("%s: %s" % (user, e))
        return
    stats.up += 1
    seq = 0
    try:
        await asyncio.sleep(random.random() * every)
        while time.time() < end:
            seq += 1
            marker = "lt%d-%d" % (seq, random.randint(1000, 9999))
            cmd = random.choice(COMMANDS) + "; echo %s\r" % marker.replace("-", "-''")
            t0 = time.time()
            await ws.send(json.dumps({"t": "i", "d": cmd}))
            buf = b""
            while marker.encode() not in buf:
                m = await asyncio.wait_for(ws.recv(), 30)
                if isinstance(m, bytes):
                    buf = (buf + m)[-8192:]
            stats.rtt.append(time.time() - t0)
            await asyncio.sleep(every)
    except Exception as e:
        stats.errors.append("%s: %s" % (user, e))
    finally:
        stats.up -= 1
        await ws.close()


async def main_async(a):
    users = [ln.strip() for ln in Path(a.users).read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    users = users[: a.n] if a.n else users
    cfg = common.load_config()
    if not cfg or common.load_state(cfg)["phase"] != "open":
        sys.exit("loadtest: the exam must be configured and open (examctl open) for a practice config")
    key = common.ticket_key()
    stats = Stats()
    end = time.time() + a.minutes * 60
    tasks = [asyncio.ensure_future(one(u, a.url, key, cfg["id"], stats, end, a.every, a.origin)) for u in users]
    print("starting %d terminals against %s for %.1f minutes; memory available %d MB" % (len(users), a.url, a.minutes, mem_available_mb()))
    low = 10 ** 9
    while not all(t.done() for t in tasks):
        await asyncio.sleep(10)
        r = sorted(stats.rtt[-500:])
        med = statistics.median(r) if r else 0
        p95 = r[int(0.95 * (len(r) - 1))] if r else 0
        mem = mem_available_mb()
        low = min(low, mem)
        print("%s  up %3d  failed %d  commands %5d  rtt median %.0f ms  p95 %.0f ms  memory available %d MB" % (
            time.strftime("%H:%M:%S"), stats.up, stats.failed, len(stats.rtt), med * 1000, p95 * 1000, mem), flush=True)
    r = sorted(stats.rtt)
    print("\ndone: %d terminals, %d failed to open, %d commands, rtt median %.0f ms, p95 %.0f ms, lowest memory available %d MB"
          % (len(users), stats.failed, len(r), (statistics.median(r) if r else 0) * 1000,
             (r[int(0.95 * (len(r) - 1))] if r else 0) * 1000, low))
    for e in stats.errors[:10]:
        print("  " + e)
    if low < 1024:
        print("WARNING: available memory went under 1 GB. Raise the VM's memory or lower MemoryMax before the exam.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--users", required=True, help="file with one test account per line")
    p.add_argument("--n", type=int, default=0, help="use only the first N accounts")
    p.add_argument("--url", default="ws://127.0.0.1:5010/term")
    p.add_argument("--minutes", type=float, default=5)
    p.add_argument("--every", type=float, default=2.0, help="seconds between commands in one terminal")
    p.add_argument("--origin", default="https://rathpiseyalpha.github.io",
                   help="Origin header to send; must be one the gateway allows (its --origin), empty for none")
    asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    main()
