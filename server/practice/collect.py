#!/usr/bin/env python3
"""Practice room: the student's side of a setup or a check. It runs AS THE STUDENT.

runner.py (root) starts it with `runuser`, a clean environment (`env -i`, no login shell, so ~/.bashrc never runs)
and `python3 -I -S`, from a folder only root can write, inside a systemd scope with limits. It does what root asks
on stdin and answers on stdout, then exits:

    setup    make ~/practice/<scenario>/ again from the starting files root sends (the old one is removed)
    collect  bring back the workspace (names, types, modes, sizes, times, inodes, link targets, small files' text),
             the student's processes, and the results of running the student's script on inputs root sends

It imports no scenario and never judges anything: root does that on the data. It makes itself non-dumpable first,
so the student's other processes cannot read its pipes or attach to it, then says "ready" and waits for the request.
Standard library only.
"""
import ctypes
import grp
import gzip
import json
import os
import pwd
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

SCENARIO_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
MAX_FILE = 65536          # text kept per file
MAX_TOTAL = 4_000_000     # text kept per snapshot
MAX_ENTRIES = 3000
MAX_OUT = 262144          # stdout or stderr kept per run
MAX_COPY = 20_000_000     # a run copies at most this much of the workspace
SAFE_PATH = "/usr/local/bin:/usr/bin:/bin"


class Fail(Exception):
    pass


def nodump():
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        libc.prctl(4, 0, 0, 0, 0)  # PR_SET_DUMPABLE, 0
    except Exception:
        pass


def home():
    return Path(pwd.getpwuid(os.getuid()).pw_dir)


def workspace(sid, create=False):
    if not SCENARIO_RE.match(str(sid)):
        raise Fail("bad scenario")
    top = home() / "practice"
    if top.is_symlink() or (top.exists() and not top.is_dir()):
        raise Fail("~/practice is not a plain folder")
    if create:
        top.mkdir(mode=0o750, exist_ok=True)
    w = top / sid
    if w.is_symlink() or (w.exists() and not w.is_dir()):
        raise Fail("~/practice/%s is not a plain folder" % sid)
    return w


def safe_rel(rel):
    if not isinstance(rel, str) or not rel or rel.startswith("/") or "\0" in rel:
        raise Fail("bad path %r" % rel)
    parts = rel.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise Fail("bad path %r" % rel)
    return rel


def make_tree(base, spec, root_text=None):
    """Write a tree: {"dirs": [...], "files": {rel: text | {"t": text, "m": mode, "age": days} | {"l": target} |
    {"h": other rel} }}. "{ROOT}" in a link target becomes the tree's own absolute path. Returns inodes."""
    base.mkdir(mode=0o750, parents=True, exist_ok=True)
    root_text = root_text or str(base)
    for d in spec.get("dirs") or []:
        (base / safe_rel(d)).mkdir(mode=0o750, parents=True, exist_ok=True)
    later, ages = [], []
    for rel, item in (spec.get("files") or {}).items():
        p = base / safe_rel(rel)
        p.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        if isinstance(item, str):
            item = {"t": item}
        if "h" in item:
            later.append((p, base / safe_rel(item["h"])))
        elif "l" in item:
            os.symlink(str(item["l"]).replace("{ROOT}", root_text), str(p))
        else:
            fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(str(item.get("t", "")))
            os.chmod(str(p), int(item.get("m", 0o640)))
        if item.get("age") is not None:
            ages.append((p, float(item["age"])))
    for p, src in later:
        os.link(str(src), str(p))
    now = time.time()
    for p, days in ages:
        t = now - days * 86400
        os.utime(str(p), (t, t), follow_symlinks=False)
    inodes = {}
    for rel in (spec.get("files") or {}):
        try:
            inodes[rel] = os.lstat(str(base / rel)).st_ino
        except OSError:
            pass
    return inodes


def setup(req):
    w = workspace(req.get("sid"), create=True)
    if w.exists():
        shutil.rmtree(str(w))  # fd-based on Linux: never follows a link out of the workspace
    w.mkdir(mode=0o750)
    inodes = make_tree(w, req)
    for staff in req.get("staff") or []:  # the instructor may look at the workspace (like the lab folders)
        if re.match(r"^[a-z_][a-z0-9_-]{0,31}$", staff) and shutil.which("setfacl"):
            subprocess.run(["setfacl", "-R", "-m", "u:%s:rX" % staff, str(w)], capture_output=True)
            subprocess.run(["setfacl", "-R", "-d", "-m", "u:%s:rX" % staff, str(w)], capture_output=True)
    return {"ok": True, "inodes": inodes, "root": str(w)}


def text_name(name):
    return name.encode("utf-8", "surrogateescape").decode("utf-8", "replace")


def read_small(path, size, budget):
    if size > MAX_FILE or size > budget[0]:
        return None
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        data = os.read(fd, MAX_FILE + 1)
    finally:
        os.close(fd)
    budget[0] -= len(data)
    return data[:MAX_FILE].decode("utf-8", "replace")


def snapshot(base, want=None):
    """want: read the text only of these paths (and what is under them); None reads every small file."""
    out, budget = [], [MAX_TOTAL]
    base = Path(base)
    if not base.is_dir() or base.is_symlink():
        return {"entries": [], "root": str(base), "missing": True}
    truncated = False
    for dirpath, dirnames, filenames in os.walk(str(base), followlinks=False):
        dirnames.sort()
        for name in sorted(dirnames) + sorted(filenames):
            if len(out) >= MAX_ENTRIES:
                truncated = True
                break
            full = os.path.join(dirpath, name)
            try:
                st = os.lstat(full)
            except OSError:
                continue
            rel = text_name(os.path.relpath(full, str(base)).replace(os.sep, "/"))
            if stat.S_ISLNK(st.st_mode):
                kind = "l"
            elif stat.S_ISDIR(st.st_mode):
                kind = "d"
            elif stat.S_ISREG(st.st_mode):
                kind = "f"
            else:
                kind = "o"
            e = {"p": rel, "t": kind, "m": stat.S_IMODE(st.st_mode), "s": st.st_size, "mt": round(st.st_mtime, 3),
                 "i": st.st_ino, "n": st.st_nlink}
            if kind == "l":
                try:
                    e["x"] = text_name(os.readlink(full))
                except OSError:
                    e["x"] = ""
            elif kind == "f":
                if want is None or any(rel == x or rel.startswith(x.rstrip("/") + "/") for x in want):
                    e["c"] = read_small(full, st.st_size, budget)
                else:
                    e["c"] = None
            out.append(e)
        if truncated:
            break
    return {"entries": out, "root": str(base), "truncated": truncated}


def procs():
    me, mine = os.getuid(), os.getpid()
    out = []
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == mine:
            continue
        try:
            if os.stat("/proc/" + name).st_uid != me:
                continue
            with open("/proc/%s/stat" % name, "r", encoding="utf-8", errors="replace") as f:
                st = f.read()
            comm = st[st.index("(") + 1:st.rindex(")")]
            rest = st[st.rindex(")") + 2:].split()
            with open("/proc/%s/cmdline" % name, "rb") as f:
                raw = f.read(4096)
            args = [a.decode("utf-8", "replace") for a in raw.split(b"\0") if a]
            entry = {"pid": int(name), "ppid": int(rest[1]), "state": rest[0], "comm": comm, "args": args[:30]}
            try:
                entry["nice"] = int(rest[16])   # field 19 of /proc/<pid>/stat
            except (ValueError, IndexError):
                pass
            sig = sigmask(name)
            if sig is not None:
                entry["sigign"] = sig["ign"]
                entry["sigcgt"] = sig["cgt"]
            out.append(entry)
        except (OSError, ValueError, IndexError):
            continue
    return sorted(out, key=lambda p: p["pid"])


def sigmask(pid):
    """The signals a process ignores and catches (bit n-1 is signal n), from /proc/<pid>/status."""
    got = {}
    try:
        with open("/proc/%s/status" % pid, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith(("SigIgn:", "SigCgt:")):
                    k, _, val = line.partition(":")
                    got[k] = int(val.strip(), 16)
    except (OSError, ValueError):
        return None
    if "SigIgn" not in got or "SigCgt" not in got:
        return None
    return {"ign": got["SigIgn"], "cgt": got["SigCgt"]}


# ── read-only facts about the system ──────────────────────────
# The request only names a fact ("kernel", "owner:/etc/passwd"); the code that reads it is fixed here, and a path
# must be on the list below. Nothing is run that a request spells out, and nothing is changed.

FACT_PATHS = ("/etc/passwd", "/etc/shadow", "/etc/group", "/etc/hosts", "/etc/hostname", "/etc/os-release", "/var/log",
              "/tmp", "/home", "/usr/bin/passwd", "/usr/bin/su", "/usr/bin/chsh", "/usr/bin/chfn", "/usr/bin/sudo",
              "/usr/bin/newgrp", "/usr/bin/mount", "/usr/bin/ls", "/usr/bin/cat", "/usr/bin/grep", "/usr/bin/tar",
              "/usr/bin/sed", "/usr/bin/gzip", "/usr/bin/ssh", "/usr/bin/awk", "/usr/bin/find", "/usr/bin/sort")
FACT_HOME = "~"          # "mount:~" is the mount point of the student's home


def read_text(path, limit=65536):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return None


def fact_kernel():
    try:
        return os.uname().release
    except AttributeError:
        return None


def fact_cpus():
    try:
        return len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        return os.cpu_count()


def fact_cpus_listed():
    """The CPUs /proc/cpuinfo lists (a container may allow fewer than it lists; either count is a fair answer)."""
    text = read_text("/proc/cpuinfo", 1_000_000) or ""
    n = sum(1 for line in text.splitlines() if line.startswith("processor"))
    return n or None


def fact_memtotal_kib():
    text = read_text("/proc/meminfo") or ""
    m = re.search(r"^MemTotal:\s+(\d+)\s+kB", text, re.M)
    return int(m.group(1)) if m else None


def fact_osrelease():
    text = read_text("/etc/os-release") or ""
    out = {}
    for line in text.splitlines():
        k, eq, val = line.partition("=")
        if eq and k in ("NAME", "PRETTY_NAME", "ID", "VERSION_ID", "VERSION"):
            out[k] = val.strip().strip('"')
    return out or None


def fact_pid1():
    text = read_text("/proc/1/comm", 256)
    return text.strip() if text else None


def fact_ports():
    """TCP ports in the LISTEN state (IPv4 and IPv6), sorted."""
    ports = set()
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        text = read_text(path, 1_000_000) or ""
        for line in text.splitlines()[1:]:
            cols = line.split()
            if len(cols) > 3 and cols[3] == "0A":
                try:
                    ports.add(int(cols[1].rsplit(":", 1)[1], 16))
                except (ValueError, IndexError):
                    continue
    return sorted(ports)


def fact_account():
    pw = pwd.getpwuid(os.getuid())
    try:
        group = grp.getgrgid(pw.pw_gid).gr_name
    except KeyError:
        group = str(pw.pw_gid)
    return {"name": pw.pw_name, "uid": pw.pw_uid, "gid": pw.pw_gid, "group": group, "home": pw.pw_dir,
            "shell": pw.pw_shell}


def fact_owner(path):
    if path not in FACT_PATHS:
        return None
    try:
        st = os.stat(path)
    except OSError:
        return None
    try:
        user = pwd.getpwuid(st.st_uid).pw_name
    except KeyError:
        user = str(st.st_uid)
    try:
        group = grp.getgrgid(st.st_gid).gr_name
    except KeyError:
        group = str(st.st_gid)
    return {"user": user, "group": group, "uid": st.st_uid, "gid": st.st_gid, "mode": stat.S_IMODE(st.st_mode),
            "setuid": bool(st.st_mode & stat.S_ISUID), "setgid": bool(st.st_mode & stat.S_ISGID)}


def fact_mount(path):
    p = str(home()) if path == FACT_HOME else path
    if path != FACT_HOME and path not in FACT_PATHS:
        return None
    try:
        p = os.path.realpath(p)
    except OSError:
        return None
    while not os.path.ismount(p):
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    return p


def fact_package(path):
    """The package that owns a file (dpkg-query -S); /usr/bin and /bin are tried both ways (merged /usr)."""
    if path not in FACT_PATHS or not shutil.which("dpkg-query"):
        return None
    tries = [path]
    if path.startswith("/usr/bin/"):
        tries.append(path[len("/usr"):])
    try:
        tries.append(os.path.realpath(path))
    except OSError:
        pass
    for t in dict.fromkeys(tries):
        try:
            r = subprocess.run(["dpkg-query", "-S", t], capture_output=True, text=True, timeout=5,
                               env={"PATH": SAFE_PATH, "LANG": "C"})
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0 and ":" in r.stdout:
            first = r.stdout.splitlines()[0]
            names = first.rsplit(": ", 1)[0] if ": " in first else first.split(":", 1)[0]
            pkg = names.split(",")[0].strip().split(":")[0]   # "coreutils", or "libc6:amd64"
            if pkg and not pkg.startswith("diversion"):
                return pkg
    return None


FACTS = {"kernel": fact_kernel, "cpus": fact_cpus, "cpus_listed": fact_cpus_listed, "memtotal_kib": fact_memtotal_kib, "osrelease": fact_osrelease,
         "pid1": fact_pid1, "ports": fact_ports, "account": fact_account}
FACTS_WITH_ARG = {"owner": fact_owner, "mount": fact_mount, "package": fact_package}


def facts(names):
    """{"name" or "name:arg": value}; None when it cannot be read here. Unknown names are skipped."""
    out = {}
    for n in names or []:
        n = str(n)
        name, _, arg = n.partition(":")
        try:
            if arg and name in FACTS_WITH_ARG:
                out[n] = FACTS_WITH_ARG[name](arg)
            elif not arg and name in FACTS:
                out[n] = FACTS[name]()
        except Exception:   # a fact that cannot be read is None, never a failed check
            out[n] = None
    return out


# ── archives: list, never extract ─────────────────────────────

MAX_TAR_FILE = 20_000_000       # the archive itself
MAX_TAR_BYTES = 100_000_000     # decompressed bytes read while listing
MAX_TAR_MEMBERS = 5000


class _Limited:
    """A file object that stops after a number of bytes (a gzip bomb listed as an archive must not run away)."""

    def __init__(self, raw, limit):
        self.raw, self.left = raw, limit

    def read(self, n=-1):
        data = self.raw.read(n if n is not None and n >= 0 else 1 << 20)
        self.left -= len(data)
        if self.left < 0:
            raise OSError("too much data")
        return data


def tar_listing(rel, w):
    """What a .tar.gz holds, by name, without extracting anything: {"ok", "gzip", "names", "error"}."""
    out = {"ok": False, "gzip": False, "names": []}
    path = w / safe_rel(rel)
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        out["error"] = "missing"
        return out
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_TAR_FILE:
            out["error"] = "not a regular file, or too big"
            return out
        with os.fdopen(fd, "rb") as raw:
            fd = None
            out["gzip"] = raw.read(2) == b"\x1f\x8b"
            raw.seek(0)
            if not out["gzip"]:
                out["error"] = "not gzip"
                return out
            limited = _Limited(gzip.GzipFile(fileobj=raw, mode="rb"), MAX_TAR_BYTES)
            with tarfile.open(fileobj=limited, mode="r|") as tf:
                for m in tf:
                    if len(out["names"]) >= MAX_TAR_MEMBERS:
                        out["error"] = "too many members"
                        return out
                    out["names"].append(text_name(m.name))
            out["ok"] = True
    except (OSError, tarfile.TarError, EOFError, ValueError) as e:
        out["error"] = type(e).__name__
    finally:
        if fd is not None:
            os.close(fd)
    return out


def copy_tree(src, dst):
    """The workspace for one run: folders, regular files and symbolic links, up to MAX_COPY bytes."""
    size = [0]

    def ignore(folder, names):
        skip = []
        for n in names:
            full = os.path.join(folder, n)
            try:
                st = os.lstat(full)
            except OSError:
                skip.append(n)
                continue
            if stat.S_ISREG(st.st_mode):
                size[0] += st.st_size
                if size[0] > MAX_COPY:
                    skip.append(n)
            elif not (stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode)):
                skip.append(n)
        return skip
    if src.is_dir():
        shutil.copytree(str(src), str(dst), symlinks=True, ignore=ignore)
    else:
        dst.mkdir(mode=0o750)


def run_one(w, r, tmp):
    work = tmp / "work"
    copy_tree(w, work)
    for name, spec in (r.get("trees") or {}).items():
        make_tree(tmp / safe_rel(name), spec)
    script = work / safe_rel(r.get("script", "run.sh"))
    res = {"script": r.get("script")}
    if not script.is_file() or script.is_symlink():
        res["missing"] = True
        return res
    args = [str(a).replace("{TMP}", str(tmp)) for a in r.get("args") or []]
    cwd = tmp / safe_rel(r["cwd"]) if r.get("cwd") else work
    env = {"PATH": SAFE_PATH, "HOME": str(tmp), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TMPDIR": str(tmp),
           "USER": pwd.getpwuid(os.getuid()).pw_name}
    t0 = time.monotonic()
    p = subprocess.Popen(["/bin/bash", str(script)] + args, cwd=str(cwd), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=env, start_new_session=True)
    try:
        out, err = p.communicate(str(r.get("stdin", "")).encode("utf-8"), timeout=float(r.get("timeout", 5)))
        res["timeout"] = False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            out, err = p.communicate(timeout=2)   # a child that left the process group may still hold the pipes
        except subprocess.TimeoutExpired:
            out, err = b"", b""
        res["timeout"] = True
    try:
        os.killpg(p.pid, signal.SIGKILL)  # anything the script left running in the background
    except OSError:
        pass
    res.update(rc=p.returncode, secs=round(time.monotonic() - t0, 3),
               out=out[:MAX_OUT].decode("utf-8", "replace"), err=err[:MAX_OUT].decode("utf-8", "replace"))
    snaps = {}
    for name in r.get("snap") or []:
        snaps[name] = snapshot(tmp / safe_rel(name))
    res["trees"] = snaps
    return res


def collect(req):
    w = workspace(req.get("sid"))
    out = {"root": str(w), "realroot": os.path.realpath(str(w)), "exists": w.is_dir()}
    if req.get("tree", True):
        snap = snapshot(w, req.get("texts"))
        out["tree"], out["truncated"] = snap["entries"], snap.get("truncated", False)
    if req.get("procs"):
        out["procs"] = procs()
    runs = []
    for r in req.get("runs") or []:
        tmp = Path(tempfile.mkdtemp(prefix="practice-run-"))
        try:
            runs.append(run_one(w, r, tmp))
        except Fail as e:
            runs.append({"error": str(e)})
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)
    if runs:
        out["runs"] = runs
    if req.get("facts"):
        out["facts"] = facts(req["facts"])
    if req.get("tars"):
        out["tars"] = {str(r): tar_listing(r, w) for r in list(req["tars"])[:5]}
    again = req.get("again")
    if isinstance(again, dict):
        time.sleep(max(0.0, min(5.0, float(again.get("after", 2)))))
        st = {}
        for rel in again.get("paths") or []:
            try:
                s = os.lstat(str(w / safe_rel(rel)))
                st[rel] = [round(s.st_mtime, 3), s.st_size]
            except OSError:
                st[rel] = None
        out["again"] = {"procs": procs() if req.get("procs") else [], "stat": st}
    return out


def main():
    nodump()
    os.umask(0o027)
    os.chdir("/")
    sys.stdout.write("ready\n")
    sys.stdout.flush()
    try:
        req = json.loads(sys.stdin.readline())
        op = req.get("op")
        if op == "setup":
            out = setup(req)
        elif op == "collect":
            out = collect(req)
        else:
            out = {"error": "unknown op"}
    except Fail as e:
        out = {"error": str(e)}
    except Exception as e:  # never a traceback with paths to the runner's log
        out = {"error": "collector: %s" % type(e).__name__}
    sys.stdout.write(json.dumps(out) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
