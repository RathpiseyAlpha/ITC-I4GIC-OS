#!/usr/bin/env python3
"""examctl: the administrator tool of the exam room. Run as root (sudo), from the repository or /opt/itc-os-exam.

Every command that changes the system prints what it does; add --dry-run to print without doing it.

    sudo python3 server/examroom/examctl.py install --staff pisey [--port 5010] [--origin https://...]
    sudo examctl config path/to/exam.json             # check and install the exam config
    sudo examctl group --roster ROSTER                 # the class group (osclass) = exactly the roster accounts
    sudo examctl keys --roster ROSTER                  # gateway key for each student, accepted only from 127.0.0.1
    sudo examctl open --roster ROSTER [--minutes 60]   # starting files, then the paper and the terminals open
    sudo examctl extend 10                             # ten more minutes for everyone
    sudo examctl close --roster ROSTER                 # terminals close; snapshot of every exam folder
    sudo examctl report --roster ROSTER > marks.csv    # automatic points per task, from the snapshot
    sudo examctl harden on|off|status --roster ROSTER [--kick] [--hidepid]
    sudo examctl status
    examctl agent                                      # (systemd, root) run the control panel's requests

With `install --web-control --roster ROSTER`, the instructor board can also open, extend, close, harden and change
settings: an instructor login on the website can then start these root actions (only these, with checked numbers).

`install` also sets up the practice room (Practice Linux Commands, server/practice/): its files in
/opt/itc-os-exam/practice, the runner service (root, itc-os-practice.service), /srv/practice for the API, and
/etc/itc-os-exam/practice.json. Add --roster so the runner knows the class; --no-practice leaves it out.

ROSTER is the website's roster.json ({"id": {"user": .., "name": ..}}) or a text file with one account per line.
"""
import argparse
import grp
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # no .pyc of the paper with looser permissions than the source
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import common  # noqa: E402

OPT = Path("/opt/itc-os-exam")
GROUP_EXAM = "itc-exam"          # can read the config, the ticket key and the recordings: staff + gateway
GROUP_CLASS = "osclass"          # the students; hardening applies to this group only
GW_USER = "examgw"
GW_UNIT = "itc-os-examgw.service"
API_UNIT = "itc-os-presence.service"
AGENT_UNIT = "itc-os-examctl.service"
PRACTICE_UNIT = "itc-os-practice.service"
PRACTICE_SOCK = "/run/itc-os-practice/runner.sock"
SSHD_KEYS_CONF = Path("/etc/ssh/sshd_config.d/20-itc-exam-keys.conf")
SSHD_WINDOW_CONF = Path("/etc/ssh/sshd_config.d/21-itc-exam-window.conf")
EXAM_KEYS = Path("/etc/ssh/exam_keys")
IPT_COMMENT = "itc-exam"
WALL_TOOLS = ("/usr/bin/wall", "/usr/bin/write.ul", "/usr/bin/write")
SNAPSHOT_LIMIT_KB = 51200

DRY = False
DEV = False  # agent --dev: the local preview, not root; system changes are refused


def say(msg):
    print(msg, flush=True)


def run(cmd, check=True, capture=False, quiet=False):
    if not quiet:
        say(("[dry-run] " if DRY else "+ ") + " ".join(cmd))
    if DRY:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(cmd, check=check, text=True, capture_output=capture)


def probe(cmd):
    """Read-only command, also run in dry-run."""
    return subprocess.run(cmd, text=True, capture_output=True)


def write(path, text, mode=0o644, owner=None, group=None):
    path = Path(path)
    say(("[dry-run] write " if DRY else "+ write ") + "%s (%o%s)" % (path, mode, (" %s:%s" % (owner, group)) if owner else ""))
    if DRY:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(tmp, mode)
    if owner and not DEV:
        shutil.chown(tmp, owner, group)
    os.replace(tmp, path)


def mkdir(path, mode, owner="root", group="root"):
    say(("[dry-run] mkdir " if DRY else "+ mkdir ") + "%s (%o %s:%s)" % (path, mode, owner, group))
    if DRY:
        return
    Path(path).mkdir(parents=True, exist_ok=True)
    os.chmod(path, mode)
    if not DEV:
        shutil.chown(path, owner, group)


def need_root():
    if os.geteuid() != 0 and not DRY and not DEV:
        sys.exit("examctl: run with sudo (or add --dry-run to see the plan)")


def roster_users(path):
    if not path:
        sys.exit("examctl: --roster FILE is required")
    text = Path(path).read_text(encoding="utf-8")
    users = []
    try:
        data = json.loads(text)
        users = [str(v["user"]) for v in data.values() if isinstance(v, dict) and v.get("user")]
    except ValueError:
        users = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    bad = [u for u in users if not common.USER_RE.match(u)]
    if bad:
        sys.exit("examctl: bad account names in roster: %s" % ", ".join(bad[:5]))
    missing = []
    for u in users:
        try:
            pwd.getpwnam(u)
        except KeyError:
            missing.append(u)
    if missing:
        say("warning: %d roster accounts do not exist and are skipped: %s" % (len(missing), ", ".join(missing[:8])))
    users = sorted(set(u for u in users if u not in missing))
    guard_accounts(users)
    return users


def guard_accounts(users):
    """Root actions run as the roster's accounts (runuser, chmod): never as root, staff, the gateway or a system account."""
    staff = staff_accounts()
    bad = [u for u in users if u in ("root", GW_USER) or u in staff or pwd.getpwnam(u).pw_uid < 1000]
    if bad:
        sys.exit("examctl: refusing: staff, service or system accounts are on the roster: %s" % ", ".join(bad[:8]))


def config_or_exit():
    cfg = common.load_config()
    if not cfg:
        sys.exit("examctl: no valid %s; run `examctl config FILE` first" % (common.etc_dir() / "exam.json"))
    return cfg


def staff_accounts():
    try:
        return set(grp.getgrnam(GROUP_EXAM).gr_mem)
    except KeyError:
        return set()


# ── install ───────────────────────────────────────────────────

def cmd_install(a):
    need_root()
    repo_server = _HERE.parent
    for tool in ("tmux", "setfacl", "runuser", "ssh-keygen"):
        if not shutil.which(tool):
            sys.exit("examctl: %s is missing (apt install tmux acl openssh-client)" % tool)
    for mod in ("websockets", "asyncssh"):
        if probe([sys.executable, "-c", "import %s" % mod]).returncode != 0:
            sys.exit("examctl: python3 module %s is missing (apt install python3-websockets python3-asyncssh)" % mod)
    ws_version = probe([sys.executable, "-c", "import websockets; print(websockets.__version__)"]).stdout.strip()
    if int((ws_version or "0").split(".")[0]) < 13:
        sys.exit("examctl: websockets %s is too old; 13 or later is needed" % ws_version)
    try:
        pwd.getpwnam(a.staff)
    except KeyError:
        sys.exit("examctl: staff account %s does not exist" % a.staff)

    if probe(["getent", "group", GROUP_EXAM]).returncode != 0:
        run(["groupadd", "--system", GROUP_EXAM])
    if probe(["getent", "passwd", GW_USER]).returncode != 0:
        run(["useradd", "--system", "--gid", GROUP_EXAM, "--home-dir", "/nonexistent", "--no-create-home",
             "--shell", "/usr/sbin/nologin", GW_USER])
    run(["usermod", "-aG", GROUP_EXAM, a.staff])

    if not (_HERE / "midterm.py").exists():
        sys.exit("examctl: %s is missing. The paper is not in git: copy midterm.py here first (README)." % (_HERE / "midterm.py"))
    bank_src = _HERE / "bank"
    bank_files = sorted(p for p in bank_src.glob("*.py") if not p.name.startswith(("_", "test"))) if bank_src.is_dir() else []
    if not bank_files:
        sys.exit("examctl: %s has no scenario files. The scenario bank is not in git: copy bank/ here first (README)." % bank_src)
    mkdir(OPT, 0o755)
    for name in ("common.py", "exambank.py", "midterm.py", "gateway.py", "examctl.py", "loadtest.py", "tmux.conf", "exam.example.json"):
        src = _HERE / name
        say(("[dry-run] " if DRY else "+ ") + "install %s -> %s" % (src, OPT / name))
        if not DRY:
            shutil.copy2(src, OPT / name)
            if name == "midterm.py":  # the paper: students have shell accounts on this server
                os.chmod(OPT / name, 0o640)
                shutil.chown(OPT / name, "root", GROUP_EXAM)
            else:
                os.chmod(OPT / name, 0o755 if name.endswith("ctl.py") or name == "gateway.py" else 0o644)
    # The scenarios are the paper too: a root-only folder (0750 root:itc-exam), files 0640. A scenario file that is no
    # longer in the repository is removed, because the bank is loaded strictly and a stale file would be drawn from.
    say(("[dry-run] " if DRY else "+ ") + "install %d scenario files -> %s (0750 root:%s)" % (len(bank_files), OPT / "bank", GROUP_EXAM))
    if not DRY:
        mkdir(OPT / "bank", 0o750, "root", GROUP_EXAM)
        keep = {p.name for p in bank_files}
        for old in (OPT / "bank").glob("*.py"):
            if old.name not in keep:
                old.unlink()
        for p in bank_files:
            shutil.copy2(p, OPT / "bank" / p.name)
            os.chmod(OPT / "bank" / p.name, 0o640)
            shutil.chown(OPT / "bank" / p.name, "root", GROUP_EXAM)
    say(("[dry-run] " if DRY else "+ ") + "install %s -> %s" % (repo_server / "oslab.py", OPT / "oslab.py"))
    if not DRY:
        shutil.copy2(repo_server / "oslab.py", OPT / "oslab.py")
        os.chmod(OPT / "oslab.py", 0o644)
    link = Path("/usr/local/sbin/examctl")
    say(("[dry-run] " if DRY else "+ ") + "ln -sf %s %s" % (OPT / "examctl.py", link))
    if not DRY:
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(OPT / "examctl.py")

    etc = common.etc_dir()
    mkdir(etc, 0o750, "root", GROUP_EXAM)
    mkdir(common.var_dir(), 0o750, "root", GROUP_EXAM)
    mkdir(common.rec_dir(), 0o2770, GW_USER, GROUP_EXAM)
    mkdir(common.control_dir(), 0o2770, "root", GROUP_EXAM)  # unlock requests from the board to the gateway
    key = etc / "ticket.key"
    if not key.exists():
        say(("[dry-run] " if DRY else "+ ") + "create %s (0640 root:%s)" % (key, GROUP_EXAM))
        if not DRY:
            import secrets
            write(key, secrets.token_hex(32) + "\n", 0o640, "root", GROUP_EXAM)
    gw_key = etc / "gateway_ed25519"
    if not gw_key.exists():
        run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "itc-exam-gateway", "-f", str(gw_key)])
        run(["chown", "%s:%s" % (GW_USER, GROUP_EXAM), str(gw_key), str(gw_key) + ".pub"])
        run(["chmod", "600", str(gw_key)])
        run(["chmod", "644", str(gw_key) + ".pub"])
    hosts = []
    for pub in sorted(Path("/etc/ssh").glob("ssh_host_*_key.pub")):
        parts = pub.read_text().split()
        if len(parts) >= 2:
            hosts.append("127.0.0.1 %s %s" % (parts[0], parts[1]))
    write(etc / "known_hosts", "\n".join(hosts) + "\n", 0o644)

    # The students' own keys keep working for labs; the gateway key lives in a root-owned file per account.
    write(SSHD_KEYS_CONF, "# itc-exam: the exam room gateway logs in with a key kept in /etc/ssh/exam_keys/<user>\n"
          "AuthorizedKeysFile .ssh/authorized_keys %s/%%u\n" % EXAM_KEYS, 0o644)
    mkdir(EXAM_KEYS, 0o755)
    sshd_reload()

    origins = "".join(" --origin %s" % o for o in a.origin)
    unit = """[Unit]
Description=ITC OS exam room terminal gateway
After=network.target ssh.service

[Service]
Type=simple
User={gw}
Group={grp}
Environment=ITC_EXAM_ETC={etc} ITC_EXAM_VAR={var} PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 {opt}/gateway.py --host 127.0.0.1 --port {port} --tmux-conf {opt}/tmux.conf{origins}
Restart=always
RestartSec=2
UMask=0027
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths={rec} {control}

[Install]
WantedBy=multi-user.target
""".format(gw=GW_USER, grp=GROUP_EXAM, etc=etc, var=common.var_dir(), opt=OPT, port=a.port, origins=origins,
           rec=common.rec_dir(), control=common.control_dir())
    write(Path("/etc/systemd/system") / GW_UNIT, unit, 0o644)
    write(Path("/etc/systemd/system") / (API_UNIT + ".d") / "50-itc-exam.conf",
          "[Service]\nSupplementaryGroups=%s\nEnvironment=ITC_EXAM_ETC=%s ITC_EXAM_VAR=%s ITC_PRACTICE_VAR=%s ITC_PRACTICE_SOCK=%s\n"
          % (GROUP_EXAM, etc, common.var_dir(), common.practice_var(), PRACTICE_SOCK),
          0o644)
    if a.web_control:
        install_web_control(a)
    if not a.no_practice:
        install_practice(a)
    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", "--now", GW_UNIT])
    if not a.no_practice:
        run(["systemctl", "enable", "--now", PRACTICE_UNIT])
        run(["systemctl", "restart", PRACTICE_UNIT])  # new scenario files and code
    if a.web_control:
        run(["systemctl", "enable", "--now", AGENT_UNIT.replace(".service", ".path")])
    run(["systemctl", "restart", API_UNIT])
    say("\nInstalled. Next: examctl config FILE, examctl group, examctl keys. The tunnel must route the gateway "
        "(see README: /term to 127.0.0.1:%d)." % a.port)


def install_practice(a):
    """The practice room: files, the runner (root), /srv/practice (written by the API, read by the gateway)."""
    src = _HERE.parent / "practice"
    dst = OPT / "practice"
    mkdir(dst, 0o755)
    mkdir(dst / "scenarios", 0o755)
    mkdir(dst / "drills", 0o755)   # the Linux skill roadmap's drills (public, like the Easy to Hard scenarios)
    for name in ("practice.py", "kit.py", "drillkit.py", "quizzes.py", "collect.py", "runner.py"):
        say(("[dry-run] " if DRY else "+ ") + "install %s -> %s" % (src / name, dst / name))
        if not DRY:
            shutil.copy2(src / name, dst / name)
            os.chmod(dst / name, 0o755 if name == "runner.py" else 0o644)  # collect.py runs as the student: readable
    for f in sorted((src / "scenarios").glob("*.py")):
        if not DRY:
            shutil.copy2(f, dst / "scenarios" / f.name)
            os.chmod(dst / "scenarios" / f.name, 0o644)
    drill_files = sorted((src / "drills").glob("*.py")) if (src / "drills").is_dir() else []
    drill_files = [f for f in drill_files if not f.name.startswith(("_", "test"))]
    for f in drill_files:
        if not DRY:
            shutil.copy2(f, dst / "drills" / f.name)
            os.chmod(dst / "drills" / f.name, 0o644)
    say("practice: %d drills" % len(drill_files))
    private = sorted((src / "private").glob("*.py")) if (src / "private").is_dir() else []
    private = [f for f in private if not f.name.startswith("test")]
    mkdir(dst / "private", 0o750, "root", GROUP_EXAM)  # the Super challenges: students cannot read them
    for f in private:
        if not DRY:
            shutil.copy2(f, dst / "private" / f.name)
            os.chmod(dst / "private" / f.name, 0o640)
            shutil.chown(dst / "private" / f.name, "root", GROUP_EXAM)
    qsrc = src / "private" / "quizzes"   # the quizzes' keys: private like the Super challenges (not in git)
    quiz_files = sorted(f for f in qsrc.glob("*.py") if not f.name.startswith(("_", "test"))) if qsrc.is_dir() else []
    mkdir(dst / "private" / "quizzes", 0o750, "root", GROUP_EXAM)
    for f in quiz_files:
        if not DRY:
            shutil.copy2(f, dst / "private" / "quizzes" / f.name)
            os.chmod(dst / "private" / "quizzes" / f.name, 0o640)
            shutil.chown(dst / "private" / "quizzes" / f.name, "root", GROUP_EXAM)
    say("practice: %d quizzes (keys, private)" % len(quiz_files))
    if not quiz_files:
        say("note: no quizzes: copy server/practice/private/quizzes/*.py here first (they are not in git)")
    say("practice: %d public scenarios, %d private (Super challenges)" % (len(list((src / "scenarios").glob("*.py"))), len(private)))
    if not private:
        say("warning: no Super challenges: copy server/practice/private/*.py here first (they are not in git)")
    pvar = common.practice_var()
    mkdir(pvar, 0o2750, a.staff, GROUP_EXAM)  # the API (the staff account) writes; the gateway reads settings.json
    key = common.etc_dir() / "practice.key"   # hidden inputs of the Super challenges; root only
    if not key.exists():
        import secrets
        write(key, secrets.token_hex(32) + "\n", 0o600, "root", "root")
    conf = common.etc_dir() / "practice.json"
    old = common.read_json(conf, {}) or {}
    exam = common.read_json(common.etc_dir() / "exam.json", {}) or {}
    data = {"gateway_url": a.practice_url or old.get("gateway_url") or exam.get("gateway_url", ""),
            "roster": str(Path(a.roster).resolve()) if a.roster else old.get("roster", "")}
    if not data["gateway_url"]:
        say("warning: no gateway address for practice; give --practice-url wss://.../term")
    if not data["roster"]:
        say("warning: no roster for practice; the runner refuses every student until --roster is given")
    write(conf, json.dumps(data, indent=1) + "\n", 0o644)
    write(Path("/etc/systemd/system") / PRACTICE_UNIT, """[Unit]
Description=ITC OS practice room runner (root): sets up and checks scenarios for the API
After=network.target

[Service]
Type=simple
Environment=ITC_EXAM_ETC={etc} ITC_EXAM_VAR={var} ITC_PRACTICE_VAR={pvar} PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
ExecStart=/usr/bin/python3 {opt}/practice/runner.py --socket {sock} --group {grp}
RuntimeDirectory=itc-os-practice
RuntimeDirectoryMode=0755
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
""".format(etc=common.etc_dir(), var=common.var_dir(), pvar=pvar, opt=OPT, sock=PRACTICE_SOCK, grp=GROUP_EXAM), 0o644)
    say("practice room installed: the runner listens on %s (group %s)" % (PRACTICE_SOCK, GROUP_EXAM))


def install_web_control(a):
    """The control panel's root helper: a path unit starts `examctl agent` when the board queues a request."""
    roster = Path(a.roster).resolve() if a.roster else None
    if not roster or not roster.is_file():
        sys.exit("examctl: --web-control needs --roster FILE (the website's roster.json)")
    roster_users(str(roster))  # refuses staff, service and system accounts now rather than on exam day
    write(common.etc_dir() / "agent.json", json.dumps({"roster": str(roster)}, indent=1) + "\n", 0o640, "root", GROUP_EXAM)
    for name in ("tmp", "queue", "work", "done"):
        mkdir(common.req_dir(name), 0o2770, "root", GROUP_EXAM)
    write(Path("/etc/systemd/system") / AGENT_UNIT.replace(".service", ".path"), """[Unit]
Description=ITC OS exam room: requests from the instructor board

[Path]
DirectoryNotEmpty={queue}

[Install]
WantedBy=multi-user.target
""".format(queue=common.req_dir("queue")), 0o644)
    write(Path("/etc/systemd/system") / AGENT_UNIT, """[Unit]
Description=ITC OS exam room: run requests from the instructor board (root)

[Service]
Type=oneshot
Environment=ITC_EXAM_ETC={etc} ITC_EXAM_VAR={var} PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 {opt}/examctl.py agent
""".format(etc=common.etc_dir(), var=common.var_dir(), opt=OPT), 0o644)
    say("web control on: the instructor board can open, extend, close, harden and change settings. "
        "Turn it off: systemctl disable --now %s; rm %s" % (AGENT_UNIT.replace(".service", ".path"), common.etc_dir() / "agent.json"))


def sshd_reload():
    t = probe(["sshd", "-t"]) if not DRY else None
    if t is not None and t.returncode != 0:
        sys.exit("examctl: sshd -t failed, nothing reloaded:\n" + t.stderr)
    unit = "ssh" if probe(["systemctl", "cat", "ssh.service"]).returncode == 0 else "sshd"
    run(["systemctl", "try-reload-or-restart", unit])  # Ubuntu's ssh may be socket-activated and idle


# ── config, group, keys ───────────────────────────────────────

def cmd_config(a):
    need_root()
    data = json.loads(Path(a.file).read_text(encoding="utf-8"))
    if not common.EXAM_ID_RE.match(str(data.get("id", ""))):
        sys.exit("examctl: id must be lowercase letters, digits and dashes")
    if data["id"] == common.PRACTICE_ID:
        sys.exit("examctl: the id %r is taken by the practice room" % common.PRACTICE_ID)
    if data.get("kind", "midterm") != "midterm":
        sys.exit("examctl: only kind \"midterm\" is built")
    if not re.match(r"^[A-Za-z0-9_-]{1,40}$", str(data.get("folder", "midterm"))):
        sys.exit("examctl: folder must be one plain folder name")
    if not set(data.get("parts", [])) <= set("ABCD") or not data.get("parts"):
        sys.exit("examctl: parts must be a non-empty list of A, B, C, D")
    if not str(data.get("gateway_url", "")).startswith(("wss://", "ws://")):
        say("warning: gateway_url should be wss://...; the page cannot open terminals without it")
    write(common.etc_dir() / "exam.json", json.dumps(data, indent=1) + "\n", 0o644)
    mkdir(common.var_dir() / data["id"], 0o750, "root", GROUP_EXAM)
    say("config %s installed; phase stays as it was (examctl status)" % data["id"])


def cmd_group(a):
    need_root()
    users = roster_users(a.roster)
    clash = (staff_accounts() | {GW_USER, "root"}) & set(users)
    if clash:
        sys.exit("examctl: staff or service accounts are on the roster: %s" % ", ".join(sorted(clash)))
    exists = probe(["getent", "group", GROUP_CLASS]).returncode == 0
    if not exists:
        run(["groupadd", GROUP_CLASS])
    current = set(grp.getgrnam(GROUP_CLASS).gr_mem) if exists else set()
    for u in users:
        if u not in current:
            run(["usermod", "-aG", GROUP_CLASS, u])
    for u in sorted(current - set(users)):
        run(["gpasswd", "-d", u, GROUP_CLASS])
    say("%s = %d roster accounts. Members get the group at their next login." % (GROUP_CLASS, len(users)))


def cmd_keys(a):
    need_root()
    pub = (common.etc_dir() / "gateway_ed25519.pub").read_text().split()
    line = 'from="127.0.0.1,::1",restrict,pty %s %s itc-exam-gateway\n' % (pub[0], pub[1])
    for u in roster_users(a.roster):
        write(EXAM_KEYS / u, line, 0o644)
    say("gateway key placed for the roster; it is accepted only from 127.0.0.1")


# ── open, extend, close ───────────────────────────────────────

def draw_counts(draws, bank):
    """{part: {scenario id: number of students}} for a {user: draw}."""
    out = {p: {sid: 0 for sid in bank.ids(p)} for p in bank.order}
    for d in draws.values():
        for p, sid in d["scenarios"].items():
            out[p][sid] = out[p].get(sid, 0) + 1
    return out


def say_counts(counts):
    for p in sorted(counts):
        say("  part %s: %s" % (p, ", ".join("%s %d" % (sid, n) for sid, n in sorted(counts[p].items()))))


def ensure_draws(cfg, users, midterm):
    """Write the draw of the whole roster (balanced, with the config's seed, pool and pins) unless the exam has drawn; a student
    missing from an existing draw is added with a stable pick. The draw folder is written in one step."""
    import exambank as eb
    bank = midterm.bank()
    group = None if DEV else GROUP_EXAM
    if eb.drawn(cfg["id"]):
        missing = [u for u in users if not eb.draw_path(cfg["id"], u).exists()]
        for u in missing:
            say("  %s has no draw: added with a stable pick (not part of the balanced deal)" % u)
            if not DRY:
                eb.add_draw(cfg["id"], u, midterm.plan_late(u, cfg), group)
        say("the draw of %s was already made: kept (%d students%s)" % (cfg["id"], len(users) - len(missing),
                                                                       ", %d added" % len(missing) if missing else ""))
        return
    draws = midterm.plan(users, cfg)
    say(("[dry-run] would write" if DRY else "drawing") + " %d students' scenarios for %s:" % (len(draws), cfg["id"]))
    say_counts(draw_counts(draws, bank))
    if DRY:
        return
    mkdir(common.var_dir() / cfg["id"], 0o750, "root", GROUP_EXAM)
    eb.write_draws(cfg["id"], draws, group)


def exam_never_opened(cfg):
    st = common.read_json(common.state_path(cfg), {}) or {}
    return st.get("phase", "sealed") == "sealed" and not st.get("start")


def cmd_draw(a):
    """examctl draw write|show|report|check|add|redraw|discard: the scenario draw (the instructor's exam bank plan)."""
    need_root()
    import exambank as eb
    import midterm
    cfg = config_or_exit()
    users = roster_users(a.roster) if a.roster else []
    midterm.set_roster_source(lambda: users)
    try:
        bank = midterm.bank()
    except eb.BankError as e:
        sys.exit("examctl: %s" % e)
    act, user = a.action, a.user
    group = None if DEV else GROUP_EXAM
    if act in ("write", "report", "check") and not a.roster:
        sys.exit("examctl: draw %s needs --roster" % act)
    if act in ("show", "add", "redraw") and not user:
        sys.exit("examctl: draw %s needs a user name" % act)
    if act == "write":
        if not exam_never_opened(cfg):
            sys.exit("examctl: %s has been opened; the draw is final (examctl draw add for a late student)" % cfg["id"])
        ensure_draws(cfg, users, midterm)
    elif act == "discard":
        if not exam_never_opened(cfg):
            sys.exit("examctl: %s has been opened: its draw cannot be discarded" % cfg["id"])
        say(("[dry-run] " if DRY else "") + "discarding the draw of %s" % cfg["id"])
        if not DRY:
            eb.discard_draws(cfg["id"])
    elif act == "show":
        d = midterm.draw(user)
        say("%s: %s (%s)" % (user, ", ".join("%s=%s" % kv for kv in sorted(d["scenarios"].items())),
                             "recorded" if eb.read_draw(cfg["id"], user, bank) else "not drawn yet: this is what the draw will give"))
    elif act == "report":
        draws = {u: midterm.draw(u) for u in users}
        say("%s: %d students, %s" % (cfg["id"], len(draws), "drawn" if eb.drawn(cfg["id"]) else "not drawn yet (a preview)"))
        say_counts(draw_counts(draws, bank))
        for u in users:
            say("  %-14s %s" % (u, " ".join("%s=%s" % kv for kv in sorted(draws[u]["scenarios"].items()))))
    elif act == "check":
        bad = 0
        for u in users:
            try:
                d = eb.read_draw(cfg["id"], u, bank)
            except eb.BankError as e:
                say("  PROBLEM %s: %s" % (u, e))
                bad += 1
                continue
            if d is None:
                if eb.drawn(cfg["id"]):
                    say("  PROBLEM %s: no draw" % u)
                    bad += 1
            elif eb.bank_changed(d, bank):
                say("  NOTE %s: the bank changed since the draw (the recorded scenario and values still hold)" % u)
        say("draw check: %s" % ("%d problem(s)" % bad if bad else "no problems"))
        if bad:
            sys.exit(1)
    elif act == "add":
        if not eb.drawn(cfg["id"]):
            sys.exit("examctl: nothing is drawn yet; draw write does the whole roster")
        if eb.draw_path(cfg["id"], user).exists():
            sys.exit("examctl: %s already has a draw" % user)
        say(("[dry-run] " if DRY else "") + "adding %s to the draw" % user)
        if not DRY:
            eb.add_draw(cfg["id"], user, midterm.plan_late(user, cfg), group)
    elif act == "redraw":
        if not eb.drawn(cfg["id"]):
            sys.exit("examctl: nothing is drawn yet")
        if not exam_never_opened(cfg):
            sys.exit("examctl: %s has been opened. A redraw during the exam would destroy the student's work and is not built; "
                     "close and reopen is the only way (examctl open --force keeps the draw)." % cfg["id"])
        old = eb.read_draw(cfg["id"], user, bank)
        if old is None:
            sys.exit("examctl: %s has no draw" % user)
        pick = {}
        for item in a.scenario or []:
            part, _, sid = item.partition("=")
            if part not in bank.order or sid not in bank.by_id or bank.by_id[sid].part != part:
                sys.exit("examctl: --scenario PART=ID, for example B=B-office (got %r)" % item)
            pick[part] = sid
        if not pick:
            sys.exit("examctl: redraw needs --scenario PART=ID")
        assign = dict(old["scenarios"], **pick)
        say(("[dry-run] " if DRY else "") + "%s: %s" % (user, ", ".join("%s=%s" % kv for kv in sorted(assign.items()))))
        if not DRY:
            path = eb.draw_path(cfg["id"], user)
            path.unlink()
            eb.add_draw(cfg["id"], user, eb.make_draw(bank, user, cfg["id"], assign, midterm.LABEL), group)


def cmd_fixture(a):
    """Runs AS THE STUDENT (examctl calls it with runuser): create the exam folder and the starting files.

    Root builds the files and passes them as JSON on stdin ({"dirs": [...], "files": {path: text}}), so this side
    never reads the paper, which students cannot read. Existing files are never overwritten, so opening again after a
    crash keeps the student's work.
    """
    user = pwd.getpwuid(os.getuid()).pw_name
    home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    root = home / a.folder
    data = json.loads(sys.stdin.read())
    dirs, files = data["dirs"], data["files"]
    for rel in list(dirs) + list(files):
        if rel.startswith("/") or ".." in rel.split("/"):
            sys.exit("%s: bad path %r" % (user, rel))
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        sys.exit("%s: %s is not a plain folder" % (user, root))
    root.mkdir(mode=0o750, exist_ok=True)
    for d in dirs:
        p = root / d
        if p.is_symlink():
            sys.exit("%s: %s is a symbolic link" % (user, p))
        p.mkdir(mode=0o750, parents=True, exist_ok=True)
    made = 0
    for rel, text in files.items():
        p = root / rel
        try:
            fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o640)
        except FileExistsError:
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        made += 1
    for staff in [x for x in a.staff.split(",") if x]:  # the instructor reads the folder for the board and marking
        subprocess.run(["setfacl", "-R", "-m", "u:%s:rX" % staff, str(root)], check=False)
        subprocess.run(["setfacl", "-R", "-d", "-m", "u:%s:rX" % staff, str(root)], check=False)
    print("%s: %d new files in %s" % (user, made, root))


PRACTICE_TMUX = "itcexam-practice"  # the gateway's practice tmux server (its socket name + "-practice")


def practice_processes(uid, home):
    """The student's processes started in practice: their working folder is under ~/practice/."""
    top = os.path.join(home, "practice") + os.sep
    out = []
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == os.getpid():
            continue
        try:
            if os.stat("/proc/" + name).st_uid != uid:
                continue
            cwd = os.readlink("/proc/%s/cwd" % name)
        except OSError:
            continue
        if (cwd + os.sep).startswith(top):
            out.append(int(name))
    return out


def stop_practice(users, socket=PRACTICE_TMUX):
    """Before an exam: end each student's practice tmux server and the background jobs practice scenarios start
    (they would hold PIDs, zombies and CPU in the exam; an open exam also closes the practice room)."""
    stopped = 0
    me = pwd.getpwuid(os.getuid()).pw_name
    for u in users:
        if DEV and u != me:
            continue
        try:
            pw = pwd.getpwnam(u)
        except KeyError:
            continue
        cmd = ["tmux", "-L", socket, "kill-server"]
        if not DEV:
            cmd = ["runuser", "-u", u, "--"] + cmd
        if DRY:
            say("[dry-run] %s; kill %s's processes under ~/practice" % (" ".join(cmd), u))
            continue
        subprocess.run(cmd, capture_output=True)
        for pid in practice_processes(pw.pw_uid, pw.pw_dir):
            try:
                os.kill(pid, 9)
                stopped += 1
            except OSError:
                pass
    if stopped:
        say("practice: stopped %d leftover process(es) before the exam" % stopped)
    return stopped


def cmd_open(a):
    need_root()
    cfg = config_or_exit()
    users = roster_users(a.roster)
    staff_acl = a.staff or ",".join(sorted(staff_accounts()))
    st = common.load_state(cfg)
    if st["phase"] == "open" and not a.force:
        sys.exit("examctl: %s is already open (until %s). Use extend, or --force to restart the clock." % (cfg["id"], st["end"]))
    import midterm  # root reads the paper; the student side only receives the files
    midterm.set_roster_source(lambda: users)
    try:
        midterm.bank()   # a broken bank must leave the exam sealed: nothing below has happened yet
    except Exception as e:
        sys.exit("examctl: the scenario bank is not usable, so the exam is not opened: %s" % e)
    ensure_draws(cfg, users, midterm)
    stop_practice(users)
    failed = []
    for u in users:
        dirs, files = midterm.fixture(u)
        cmd = ["runuser", "-u", u, "--", sys.executable, str(Path(__file__).resolve()), "_fixture",
               "--folder", cfg["folder"], "--staff", staff_acl]
        if DEV:  # the local preview: no root, so only the developer's own account
            if u != pwd.getpwuid(os.getuid()).pw_name:
                continue
            cmd = cmd[4:]
        if DRY:
            say("[dry-run] %s  (%d folders, %d files on stdin)" % (" ".join(cmd), len(dirs), len(files)))
            continue
        r = subprocess.run(cmd, input=json.dumps({"dirs": dirs, "files": files}), text=True, capture_output=True)
        if r.returncode != 0:
            failed.append(u)
            say("  %s: %s" % (u, (r.stderr or r.stdout).strip()[-200:]))
    if failed:
        say("warning: starting files failed for %s" % ", ".join(failed))
    minutes = a.minutes or int(cfg["duration_min"])
    start = time.time()
    state = {"phase": "open", "start": common.iso(start), "end": common.iso(start + minutes * 60),
             "extended_min": 0, "opened_for": len(users)}
    write_state(cfg, state)
    say("%s is open: %s to %s (%d minutes), %d students" % (cfg["id"], state["start"], state["end"], minutes, len(users)))


def write_state(cfg, state):
    path = common.state_path(cfg)
    if not DRY:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not DEV:
            shutil.chown(path.parent, "root", GROUP_EXAM)
        os.chmod(path.parent, 0o750)
    write(path, json.dumps(state, indent=1) + "\n", 0o644, "root", GROUP_EXAM)


def cmd_extend(a):
    need_root()
    cfg = config_or_exit()
    st = common.read_json(common.state_path(cfg), {}) or {}
    if st.get("phase") != "open":
        sys.exit("examctl: the exam is not open")
    st["end"] = common.iso(common.parse_iso(st["end"]) + a.minutes * 60)
    st["extended_min"] = int(st.get("extended_min", 0)) + a.minutes
    write_state(cfg, st)
    say("new end: %s" % st["end"])


def cmd_close(a):
    need_root()
    cfg = config_or_exit()
    users = roster_users(a.roster)  # before closing: a bad roster must not close the exam without a snapshot
    st = common.read_json(common.state_path(cfg), {}) or {}
    st["phase"] = "closed"
    st["closed_at"] = common.iso(time.time())
    write_state(cfg, st)  # terminals close within 10 seconds; the paper is no longer served
    say("closed; terminals end within 10 s. Waiting 12 s, then taking the snapshot.")
    time.sleep(0 if DRY else 12)
    dest_root = common.var_dir() / cfg["id"] / "collect"
    mkdir(dest_root, 0o750, "root", GROUP_EXAM)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for u in users:
        src = Path(os.path.expanduser("~" + u)) / cfg["folder"]
        if not src.is_dir() or src.is_symlink():
            say("  %s: no exam folder" % u)
            continue
        size = probe(["du", "-sk", "-P", str(src)]).stdout.split()
        if size and int(size[0]) > SNAPSHOT_LIMIT_KB:
            say("  %s: folder is %s KB, over the limit; copy it by hand" % (u, size[0]))
            continue
        dest = dest_root / u / stamp
        run(["mkdir", "-p", str(dest.parent)], quiet=True)
        run(["cp", "-a", "--no-preserve=ownership", str(src) + "/.", str(dest)], check=False, quiet=True)
        if not DEV:
            run(["chown", "-R", "root:%s" % GROUP_EXAM, str(dest_root / u)], check=False, quiet=True)
        run(["chmod", "-R", "u=rwX,g=rX,o=", str(dest_root / u)], check=False, quiet=True)
        say(("[dry-run] " if DRY else "  ") + "%s -> %s" % (u, dest))
    say("snapshot in %s. Marking reads this copy." % dest_root)


def cmd_report(a):
    """CSV of the automatic checks on each student's latest snapshot, for marking: the scenario of each part, the points per
    slot with the regrade (`corrections.json`) applied, the raw points. The written answers (xQ) are marked by hand from
    answers.md in the snapshot."""
    import csv
    import midterm
    cfg = config_or_exit()
    parts = [x for x in cfg["parts"] if x in midterm.PART_TITLES]
    text = Path(a.roster).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        people = sorted((str(sid), v["user"], v.get("name", "")) for sid, v in data.items() if isinstance(v, dict) and v.get("user"))
    except ValueError:
        people = [("", u, "") for u in roster_users(a.roster)]
    midterm.set_roster_source(lambda: [u for _s, u, _n in people])
    base = common.var_dir() / cfg["id"] / "collect"
    fixes = midterm.corrections()
    w = csv.writer(sys.stdout)
    w.writerow(midterm.report_header(parts))
    for sid, user, name in people:
        snaps = sorted((base / user).glob("*")) if (base / user).is_dir() else []
        w.writerow(midterm.report_row(sid, name, user, snaps[-1].name if snaps else "none", parts, snaps[-1] if snaps else None, fixes))


# ── harden ────────────────────────────────────────────────────

HARDEN_STATE = lambda: common.var_dir() / "harden.json"  # noqa: E731


def cmd_harden(a):
    need_root()
    if a.action == "status":
        return harden_status(a)
    users = roster_users(a.roster)
    if probe(["getent", "group", GROUP_CLASS]).returncode != 0:
        sys.exit("examctl: run `examctl group --roster ...` first")
    clash = staff_accounts() & set(grp.getgrnam(GROUP_CLASS).gr_mem)
    if clash:
        sys.exit("examctl: staff accounts are in %s: %s" % (GROUP_CLASS, ", ".join(sorted(clash))))
    saved = common.read_json(HARDEN_STATE(), {}) or {}
    if a.action == "on":
        # 1. SSH from outside: students get a message instead of a shell. The gateway (127.0.0.1) still works.
        write(SSHD_WINDOW_CONF, """# itc-exam: written by `examctl harden on`, removed by `examctl harden off`
Match Group {g} Address *,!127.0.0.1,!::1
    ForceCommand /bin/echo "The exam is running. Use the exam page; SSH is closed for students until it ends."
    PermitTTY no
    AllowTcpForwarding no
    AllowAgentForwarding no
    X11Forwarding no
    PermitTunnel no
""".format(g=GROUP_CLASS), 0o644)
        sshd_reload()
        # 2. No network out for the class group, loopback included (local model servers, the API).
        for tool in ("iptables", "ip6tables"):
            if shutil.which(tool) and not rule_present(tool):
                run([tool, "-I", "OUTPUT", "1", "-m", "owner", "--gid-owner", GROUP_CLASS, "--suppl-groups",
                     "-m", "comment", "--comment", IPT_COMMENT, "-j", "REJECT"])
        # 3. Per-student limits, at runtime only, so a reboot does not keep them.
        for u in users:
            uid = pwd.getpwnam(u).pw_uid
            run(["systemctl", "set-property", "--runtime", "user-%d.slice" % uid,
                 "MemoryMax=%s" % a.memory, "TasksMax=128", "CPUQuota=100%"], check=False)
        # 4. Homes closed to others (never the group bits: on an ACL'd home they are the mask and would cut the staff ACL).
        for u in users:
            run(["chmod", "o-rwx", os.path.expanduser("~" + u)], check=False)
        # 5. No messages between students.
        modes = saved.get("wall_modes", {})
        for tool in WALL_TOOLS:
            p = Path(tool)
            if p.exists() and not p.is_symlink():
                modes.setdefault(tool, oct(p.stat().st_mode & 0o7777))
                run(["chmod", "o-x", tool])
        saved["wall_modes"] = modes
        # 6. Optional: hide other users' processes.
        if a.hidepid:
            gid = grp.getgrnam(GROUP_EXAM).gr_gid
            run(["mount", "-o", "remount,hidepid=invisible,gid=%d" % gid, "/proc"])
            saved["hidepid"] = True
        if a.kick:
            kick_remote(users)
        saved["on"] = True
        saved["since"] = common.iso(time.time())
        if not DRY:
            common.write_json_atomic(HARDEN_STATE(), saved, mode=0o640)
            shutil.chown(HARDEN_STATE(), "root", GROUP_EXAM)
        say("hardening on. It does not survive a reboot except the sshd file; run `examctl harden off` after the exam.")
        harden_status(a)
    else:
        if SSHD_WINDOW_CONF.exists():
            run(["rm", "-f", str(SSHD_WINDOW_CONF)])
            sshd_reload()
        for tool in ("iptables", "ip6tables"):
            while shutil.which(tool) and rule_present(tool):
                run([tool, "-D", "OUTPUT", "-m", "owner", "--gid-owner", GROUP_CLASS, "--suppl-groups",
                     "-m", "comment", "--comment", IPT_COMMENT, "-j", "REJECT"])
                if DRY:
                    break
        for u in users:
            uid = pwd.getpwnam(u).pw_uid
            run(["systemctl", "set-property", "--runtime", "user-%d.slice" % uid,
                 "MemoryMax=infinity", "TasksMax=infinity", "CPUQuota="], check=False)
        for tool, mode in (saved.get("wall_modes") or {}).items():
            run(["chmod", mode[2:] if mode.startswith("0o") else mode, tool])
        if saved.get("hidepid"):
            run(["mount", "-o", "remount,hidepid=off", "/proc"], check=False)
        if not DRY:
            common.write_json_atomic(HARDEN_STATE(), {"on": False, "off_at": common.iso(time.time())}, mode=0o640)
            shutil.chown(HARDEN_STATE(), "root", GROUP_EXAM)
        say("hardening off. Home folders stay o-rwx (that is the normal setting for this course).")


def rule_present(tool):
    r = probe([tool, "-S", "OUTPUT"])
    return IPT_COMMENT in (r.stdout or "")


def kick_remote(users):
    r = probe(["loginctl", "list-sessions", "--no-legend"])
    for line in (r.stdout or "").splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[2] not in users:
            continue
        info = probe(["loginctl", "show-session", parts[0], "-p", "RemoteHost", "-p", "Service"]).stdout
        host = re.search(r"RemoteHost=(.*)", info or "")
        host = host.group(1).strip() if host else ""
        if host and host not in ("127.0.0.1", "::1"):
            run(["loginctl", "terminate-session", parts[0]], check=False)


def harden_status(a):
    say("sshd window file: %s" % ("present" if SSHD_WINDOW_CONF.exists() else "absent"))
    for tool in ("iptables", "ip6tables"):
        if shutil.which(tool):
            say("%s egress rule: %s" % (tool, "present" if rule_present(tool) else "absent"))
    if a.roster:
        users = roster_users(a.roster)
        if users:
            u = users[0]
            out = probe(["sshd", "-T", "-C", "user=%s,addr=203.0.113.9,host=outside" % u]).stdout or ""
            fc = [ln for ln in out.splitlines() if ln.startswith("forcecommand")]
            say("sshd for %s from outside: %s" % (u, fc[0] if fc else "normal shell"))
            out = probe(["sshd", "-T", "-C", "user=%s,addr=127.0.0.1,host=localhost" % u]).stdout or ""
            fc = [ln for ln in out.splitlines() if ln.startswith("forcecommand")]
            ak = [ln for ln in out.splitlines() if ln.startswith("authorizedkeysfile")]
            say("sshd for %s from 127.0.0.1: %s; %s" % (u, fc[0] if fc else "normal shell", ak[0] if ak else "?"))
            uid = pwd.getpwnam(u).pw_uid
            lim = probe(["systemctl", "show", "user-%d.slice" % uid, "-p", "MemoryMax", "-p", "TasksMax"]).stdout
            say("limits for %s: %s" % (u, " ".join((lim or "").split())))



# ── web control: the root helper ──────────────────────────────
#
# The instructor board queues requests (see common.py, "Control panel"); this runs them as root. It is started by
# the systemd path unit itc-os-examctl.path whenever requests/queue/ is not empty, and exists only when installed with
# --web-control. A request carries an action name and small numbers, validated by the API and again here; the roster
# path comes from the root-owned agent.json, never from the request.

def _ns(**kw):
    return argparse.Namespace(**kw)


def agent_roster():
    ac = common.agent_config()
    if not ac:
        sys.exit("web control is off on this server (no %s)" % (common.etc_dir() / "agent.json"))
    return ac["roster"]


def run_settings(p):
    path = common.etc_dir() / "exam.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    changes = p["changes"]
    if any(k.startswith("bank.") for k in changes):
        import exambank as eb
        import midterm
        cfg = config_or_exit()
        if eb.drawn(cfg["id"]):
            sys.exit("the scenarios are already drawn: discard the draw first (only possible before the exam was opened)")
        try:
            midterm.check_bank_settings(changes, roster_users(agent_roster()), cfg)
        except (ValueError, eb.BankError) as e:
            sys.exit("refused: %s" % e)
    if changes.get("seb.required") is True and not (raw.get("seb") or {}).get("config_keys"):
        sys.exit("SEB cannot be required: the exam config has no SEB config keys (set them with examctl config)")
    common.apply_settings(raw, changes)
    write(path, json.dumps(raw, indent=1) + "\n", 0o644)
    say("saved: " + ", ".join("%s = %s" % (k, json.dumps(v)) for k, v in changes.items()))
    say("connected students get it within 10 seconds")


def run_draw(p):
    """Draw now: write every student's scenarios (what Open does anyway), so the papers can be looked at before the day."""
    import exambank as eb
    cfg = config_or_exit()
    if not exam_never_opened(cfg):
        sys.exit("the exam has been opened: the draw is final")
    if eb.drawn(cfg["id"]):
        sys.exit("already drawn: discard the draw first to draw again")
    cmd_draw(_ns(action="write", user="", roster=agent_roster(), scenario=None))


def run_undraw(p):
    cmd_draw(_ns(action="discard", user="", roster=agent_roster(), scenario=None))


CURRENT_BY = {"who": ""}


def run_correct(p):
    """A regrade of one slot of one scenario: give the marks, ignore the slot, or clear the correction."""
    import exambank as eb
    import midterm
    cfg = config_or_exit()
    try:
        midterm.check_correction(p["scenario"], p["slot"])
    except (ValueError, eb.BankError) as e:
        sys.exit("refused: %s" % e)
    items = [c for c in eb.read_corrections(cfg["id"]) if not (c["scenario"] == p["scenario"] and c["slot"] == p["slot"])]
    if p["mode"] != "clear":
        items.append({"scenario": p["scenario"], "slot": p["slot"], "mode": p["mode"], "reason": p["reason"],
                      "by": CURRENT_BY["who"], "at": common.iso(time.time())})
    if not DRY:
        mkdir(common.var_dir() / cfg["id"], 0o750, "root", GROUP_EXAM)
        eb.write_corrections(cfg["id"], items, None if DEV else GROUP_EXAM)
    say("%s %s: %s (%d corrections in all)" % (p["scenario"], p["slot"], p["mode"], len(items)))


def run_prepare(p):
    if DEV:
        sys.exit("not available in the local preview (it changes groups and SSH keys)")
    a = _ns(roster=agent_roster())
    cmd_group(a)
    cmd_keys(a)


def run_harden(on, p):
    if DEV:
        sys.exit("not available in the local preview (it changes sshd, the firewall and limits)")
    cmd_harden(_ns(action="on" if on else "off", roster=agent_roster(), kick=bool(p.get("kick")), hidepid=False, memory="512M"))


ACTION_RUN = {
    "open": lambda p: cmd_open(_ns(roster=agent_roster(), minutes=p["minutes"], staff="", force=False)),
    "extend": lambda p: cmd_extend(_ns(minutes=p["minutes"])),
    "close": lambda p: cmd_close(_ns(roster=agent_roster())),
    "harden_on": lambda p: run_harden(True, p),
    "harden_off": lambda p: run_harden(False, p),
    "prepare": run_prepare,
    "settings": run_settings,
    "draw": run_draw,
    "undraw": run_undraw,
    "correct": run_correct,
}


def run_request(path, rid):
    import contextlib
    import io
    import stat
    result = {"id": rid, "action": "", "params": {}, "by": "", "at": None, "ok": False, "output": ""}
    try:
        fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as f:
            st = os.fstat(f.fileno())
            if not stat.S_ISREG(st.st_mode) or st.st_size > common.REQ_MAX_BYTES:
                raise ValueError("not a plain request file")
            body = json.loads(f.read(common.REQ_MAX_BYTES + 1).decode("utf-8"))
        if not isinstance(body, dict) or body.get("id") != rid:
            raise ValueError("bad request")
        result.update(action=str(body.get("action"))[:20], by=str(body.get("by", ""))[:40],
                      at=body.get("at") if isinstance(body.get("at"), (int, float)) else None)
        agent_roster()
        cfg = config_or_exit()
        params = common.clean_request(body.get("action"), body.get("params"), common.exam_running(common.load_state(cfg)))
        result["params"] = params
        CURRENT_BY["who"] = result["by"]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try:
                ACTION_RUN[result["action"]](params)
                result["ok"] = True
            except SystemExit as e:
                if e.code in (None, 0):
                    result["ok"] = True
                else:
                    print(e.code if isinstance(e.code, str) else "failed")
        result["output"] = out.getvalue()[-4000:]
    except SystemExit as e:
        result["output"] = "refused: %s" % (e.code if isinstance(e.code, str) else "failed")
    except (ValueError, OSError) as e:
        result["output"] = "refused: %s" % e
    except Exception as e:  # never leave a request behind: the path unit would start again and again
        result["output"] = "error: %r" % (e,)
    result["done_at"] = round(time.time(), 3)
    return result


def agent_once():
    queue = common.req_dir("queue")
    def sent(name):  # oldest first: the order the instructor pressed the buttons
        try:
            return (os.lstat(queue / name).st_mtime, name)
        except OSError:
            return (0, name)
    try:
        names = sorted(os.listdir(queue), key=sent)
    except OSError:
        return False
    for name in names:
        src = queue / name
        if not common.REQ_FILE_RE.match(name):
            _discard(src)
            continue
        work = common.req_dir("work") / name
        try:
            if not os.path.isfile(src) or os.path.islink(src):
                _discard(src)
                continue
            os.replace(src, work)
        except OSError:
            _discard(src)
            continue
        result = run_request(work, name[:-5])
        try:
            common.write_json_atomic(common.req_dir("done") / name, result, mode=0o640)
        finally:
            try:
                work.unlink()
            except OSError:
                pass
    return bool(names)


def _discard(path):
    try:
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            os.unlink(path)
    except OSError:
        pass


def cmd_agent(a):
    global DEV
    if a.dev:
        if os.geteuid() == 0:
            sys.exit("examctl: agent --dev is for the local preview and never runs as root")
        DEV = True
    else:
        need_root()
        if Path(__file__).resolve().parent != OPT:
            sys.exit("examctl: the agent runs only from %s, the root-owned copy" % OPT)
    while True:
        did = agent_once()
        if not did:
            if not a.loop:
                return
            time.sleep(1)

# ── status ────────────────────────────────────────────────────

def cmd_status(a):
    cfg = common.load_config()
    if not cfg:
        say("no exam configured (%s)" % (common.etc_dir() / "exam.json"))
        return
    st = common.load_state(cfg)
    say("exam %s (%s), parts %s, %d minutes" % (cfg["id"], cfg["title"], ",".join(cfg["parts"]), cfg["duration_min"]))
    say("phase %s, start %s, end %s, extended %s min" % (st["phase"], st["start"], st["end"], st["extended_min"]))
    say("gateway url %s; SEB required: %s" % (cfg.get("gateway_url"), cfg["seb"]["required"]))
    r = probe(["systemctl", "is-active", GW_UNIT])
    say("gateway service: %s" % (r.stdout.strip() or "unknown"))
    connected = 0
    try:
        for d in common.rec_dir().iterdir():
            s = common.read_json(d / "status.json", {}) or {}
            if s.get("connected") and time.time() - float(s.get("last_seen", 0)) < 20:
                connected += 1
    except OSError:
        pass
    say("terminals connected now: %d" % connected)


def main(argv=None):
    global DRY
    p = argparse.ArgumentParser(prog="examctl", description="Exam room administration")
    p.add_argument("--dry-run", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("install")
    s.add_argument("--staff", required=True)
    s.add_argument("--port", type=int, default=5010)
    s.add_argument("--origin", action="append", default=[])
    s.add_argument("--web-control", action="store_true", help="let the instructor board run open/extend/close/harden/settings")
    s.add_argument("--roster", help="the website's roster.json (needed with --web-control, and for practice)")
    s.add_argument("--no-practice", action="store_true", help="leave the practice room out")
    s.add_argument("--practice-url", default="", help="the practice room's gateway address (default: the exam's)")
    s = sub.add_parser("config")
    s.add_argument("file")
    for name in ("group", "keys", "close", "report"):
        s = sub.add_parser(name)
        s.add_argument("--roster", required=True)
    s = sub.add_parser("open")
    s.add_argument("--roster", required=True)
    s.add_argument("--minutes", type=int)
    s.add_argument("--staff", default="")
    s.add_argument("--force", action="store_true")
    s = sub.add_parser("draw", help="the scenario draw: write, show, report, check, add, redraw, discard")
    s.add_argument("action", choices=("write", "show", "report", "check", "add", "redraw", "discard"))
    s.add_argument("user", nargs="?", default="")
    s.add_argument("--roster")
    s.add_argument("--scenario", action="append", help="redraw: PART=ID, for example B=B-office (repeat)")
    s = sub.add_parser("extend")
    s.add_argument("minutes", type=int)
    s = sub.add_parser("harden")
    s.add_argument("action", choices=("on", "off", "status"))
    s.add_argument("--roster")
    s.add_argument("--kick", action="store_true", help="end students' SSH sessions from outside")
    s.add_argument("--hidepid", action="store_true", help="also hide other users' processes (opt-in)")
    s.add_argument("--memory", default="512M")
    sub.add_parser("status")
    s = sub.add_parser("agent")
    s.add_argument("--dev", action="store_true", help="local preview: not root; system changes are refused")
    s.add_argument("--loop", action="store_true", help="keep watching the queue (the preview has no systemd)")
    s = sub.add_parser("_fixture")
    s.add_argument("--folder", required=True)
    s.add_argument("--staff", default="")
    a = p.parse_args(argv)
    DRY = a.dry_run
    if a.cmd in ("harden",) and a.action in ("on", "off") and not a.roster:
        p.error("harden on/off needs --roster")
    {"install": cmd_install, "config": cmd_config, "group": cmd_group, "keys": cmd_keys, "open": cmd_open,
     "extend": cmd_extend, "close": cmd_close, "harden": cmd_harden, "status": cmd_status,
     "report": cmd_report, "agent": cmd_agent, "_fixture": cmd_fixture, "draw": cmd_draw}[a.cmd](a)


if __name__ == "__main__":
    main()
