"""Execute core walkthroughs in disposable workspaces; no live cron, VM or FUSE changes.

Run with an ordinary Linux user: python3 tools/test_lab_walkthroughs.py.
Checks document commands plus representative repairs and edge cases. It does not
establish real-server, peer-access, cron-daemon, boot-recovery or FUSE capability.
"""
import os
import re
import shlex
import subprocess
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if os.geteuid() == 0:
    raise SystemExit('Run as an ordinary user: root bypasses the permission-denial case.')


def blocks(path):
    section = ''
    lines = path.read_text(encoding='utf-8').splitlines()
    result = []
    i = 0
    while i < len(lines):
        if lines[i].startswith('## '):
            section = lines[i]
        if lines[i].strip() == '```bash':
            start = i + 1
            i = start
            while i < len(lines) and lines[i].strip() != '```':
                i += 1
            result.append((section, textwrap.dedent('\n'.join(lines[start:i])) + '\n'))
        i += 1
    return result


def shell(code, cwd, env, label):
    result = subprocess.run(['bash'], input=code, text=True, cwd=cwd, env=env,
                            capture_output=True, timeout=45)
    if result.returncode:
        raise AssertionError(f'{label}: {result.returncode}\n{result.stdout}\n{result.stderr}')
    return result.stdout


for path in [ROOT/'labs/SETUP.md', *sorted((ROOT/'labs').glob('lab*/*.md')),
             *sorted((ROOT/'teaching/instructor').glob('lab*/plan.md'))]:
    for section, code in blocks(path):
        result = subprocess.run(['bash', '-n'], input=code, text=True, capture_output=True)
        assert result.returncode == 0, (path, section, result.stderr)
print('All teaching Bash fences syntax PASS', flush=True)

with tempfile.TemporaryDirectory(prefix='oslab-walkthrough-') as temp:
    home = Path(temp)/'home with spaces'
    home.mkdir(mode=0o700)
    env = dict(os.environ, HOME=str(home), OSLAB_WORKSPACE=str(home/'work space'))
    base = Path(env['OSLAB_WORKSPACE'])
    cli = f'python3 {shlex.quote(str(ROOT/"server/oslab.py"))}'
    prefix = f'oslab() {{ {cli} "$@"; }}\n'
    routes = {}
    for n in range(1, 12):
        routes[n] = blocks(ROOT/f'labs/lab{n}/lab{n}-instruction.md')
        setup = '\n'.join(code for section, code in routes[n] if section.startswith('## Lab Setup'))
        guided = '\n'.join(code for section, code in routes[n] if 'Guided' in section)
        shell(prefix+setup+guided, home, env, f'Lab {n} guided')
        print(f'Lab {n} setup/guided commands PASS', flush=True)

    assert 'NAME=' in (base/'lab1/evidence/os-info.txt').read_text()
    # Exact owned-process block includes bounded sleeps; allow its real timing.
    shell('\n'.join(code for section, code in routes[1] if section.startswith('## Tasks 4')), base/'lab1', env, 'Lab1 processes')
    assert 'sleep' in (base/'lab1/evidence/processes.txt').read_text()

    shell('''set -e
mv -- 'incoming/quarter 1.txt' reports/
mv -- 'incoming/quarter 2.txt' reports/
mkdir -p TechCorp/Finance/archive TechCorp/Engineering TechCorp/HR
cp -- reports/'quarter 1.txt' reports/'quarter 2.txt' TechCorp/Finance/
cp -- TechCorp/Finance/'quarter 1.txt' TechCorp/Finance/archive/
cmp -- reports/'quarter 1.txt' TechCorp/Finance/'quarter 1.txt'
cd TechCorp/HR
cat '../Finance/quarter 1.txt'
''', base/'lab2', env, 'Lab2 path/content')

    core = [code for section, code in routes[3] if section.startswith('## Task 2')]
    shell(core[0]+core[1]+'rm -- soft.txt\nln -s renamed.txt soft.txt\n'+core[2]+core[3], base/'lab3', env, 'Lab3 rename/repair')
    assert (base/'lab3/links/hard.txt').read_text() == 'version 1\n'
    assert (base/'lab3/links/source.txt').read_text() == 'version 2\n'
    assert os.stat(base/'lab3/links/hard.txt').st_ino == os.stat(base/'lab3/links/renamed.txt').st_ino

    report = shlex.quote(str(ROOT/'teaching/instructor/lab4/report_solution.sh'))
    shell(f'''set -e
test "$(bash {report} data/events.csv)" = 'ok total: 8'
printf 'fail,2\n' > data/no-ok.csv
test "$(bash {report} data/no-ok.csv)" = 'ok total: 0'
printf 'ok,3\nok,5\nok,7\nnot-ok,99\n' > data/changed.csv
test "$(bash {report} data/changed.csv)" = 'ok total: 15'
if bash {report} data/missing.csv; then exit 1; fi
''', base/'lab4', env, 'Lab4 report edges')

    core = [code for section, code in routes[5] if section.startswith('## Task 2')]
    shell(core[0], base/'lab5', env, 'Lab5 unfinished starter')
    source = base/'lab5/threads/two_workers.c'
    content = source.read_text().replace('/* TODO: join both workers and check each return code. */',
        'rc = pthread_join(ta, NULL); if (rc) return 1;\n'
        'rc = pthread_join(tb, NULL); if (rc) return 1;').replace(
        '/* TODO: after both joins, print a.result and b.result. */',
        'printf("A result=%d B result=%d\\n", a.result, b.result);')
    source.write_text(content)
    out = shell('set -e\ngcc -Wall -Wextra -Werror -pthread threads/two_workers.c -o threads/two_workers\ntimeout 5 threads/two_workers\n', base/'lab5', env, 'Lab5 repaired')
    assert 'A result=6 B result=12' in out
    source.write_text(content.replace('b = {3, 4, 0}', 'b = {3, 2, 0}'))
    out = shell('set -e\ngcc -Wall -Wextra -Werror -pthread threads/two_workers.c -o threads/two_workers\ntimeout 5 threads/two_workers\n', base/'lab5', env, 'Lab5 changed')
    assert 'A result=6 B result=6' in out
    source.write_text(content.replace('b = {3, 4, 0}', 'b = {3, 0, 0}'))
    out = shell('set -e\ngcc -Wall -Wextra -Werror -pthread threads/two_workers.c -o threads/two_workers\ntimeout 5 threads/two_workers\n', base/'lab5', env, 'Lab5 zero')
    assert 'A result=6 B result=0' in out
    model = shlex.quote(str(ROOT/'teaching/instructor/lab5/two_workers_solution.c'))
    out = shell(f'set -e\ngcc -Wall -Wextra -Werror -pthread {model} -o threads/model\ntimeout 5 threads/model\n', base/'lab5', env, 'Lab5 public model')
    assert 'A result=6' in out and 'B result=12' in out

    shell('''set -e
chmod 700 private; chmod 600 private/record.txt
chmod 755 shared; chmod 644 shared/notice.txt
mkdir -p demo/sealed; printf 'inside\n' > demo/sealed/item.txt
chmod 600 demo/sealed
ls demo/sealed
if cat demo/sealed/item.txt; then exit 1; fi
chmod 700 demo/sealed
cat demo/sealed/item.txt
''', base/'lab6', env, 'Lab6 traversal denial')

    count = shlex.quote(str(ROOT/'teaching/instructor/lab7/count_words_solution.sh'))
    out = shell(f'''set -e
bash {count} 'input/one file.txt' input/-dash.txt
if bash {count}; then exit 1; fi
if bash {count} input/missing.txt 'input/one file.txt'; then exit 1; fi
cd input
bash {count} -dash.txt
''', base/'lab7', env, 'Lab7 boundaries/errors')
    assert 'one file.txt: 2 words' in out and '-dash.txt: 1 words' in out

    race = '\n'.join(code for section, code in routes[8] if section.startswith('## Level 3'))
    shell(race, base/'lab8', env, 'Lab8 student race')
    sales = (base/'lab8/store/sales.log').read_text()
    assert sales.count('sold 4') == 2 and (base/'lab8/store/stock.txt').read_text() == '1\n'
    buy = base/'lab8/store/buy.sh'
    buy.write_text(buy.read_text().replace('# TODO: a bounded lock must protect the complete transaction below.',
        'exec 9>"$store/stock.lock"\nflock -x -w 2 9 || exit 3').replace(
        'sleep 1  # teaching delay to widen the stale-read window; remove in final version', ':'))
    shell("printf '5\\n' > store/stock.txt\n: > store/sales.log\n"+race, base/'lab8', env, 'Lab8 student repaired')
    assert (base/'lab8/store/sales.log').read_text().count('sold 4') == 1
    assert (base/'lab8/store/stock.txt').read_text() == '1\n'
    shell('''set -e
printf '5\n' > store/stock.txt; : > store/sales.log
for bad in 0 -1 abc 0001 1000; do
  if bash store/buy.sh "$bad"; then exit 1; fi
done
if bash store/buy.sh; then exit 1; fi
if bash store/buy.sh 6; then exit 1; fi
test "$(cat store/stock.txt)" = 5
test ! -s store/sales.log
bash store/buy.sh 2
test "$(cat store/stock.txt)" = 3
(flock -x 9; touch evidence/held; sleep 3) 9>store/stock.lock & holder=$!
for attempt in {1..30}; do test -f evidence/held && break; sleep 0.1; done
if timeout 5 bash store/buy.sh 1; then exit 1; else test "$?" -eq 3; fi
wait "$holder"
''', base/'lab8', env, 'Lab8 validation/lock bound')

    opposite = '\n'.join(code for section, code in routes[9] if section.startswith('## Levels 2'))
    shell(opposite, base/'lab9', env, 'Lab9 student opposite')
    assert 'second lock timeout' in (base/'lab9/evidence/opposite.txt').read_text()
    worker = base/'lab9/vault/worker.sh'
    worker.write_text(worker.read_text().replace('if [[ "$role" = B ]]', 'if [[ "$mode" = opposite && "$role" = B ]]', 1))
    ordered = '\n'.join(code for section, code in routes[9] if section.startswith('## Levels 5'))
    shell(ordered, base/'lab9', env, 'Lab9 student ordered')
    output = (base/'lab9/evidence/ordered.txt').read_text()
    assert 'A=0 B=0' in output and output.count('holds both') == 2
    shell('rm -f -- vault/coord/A.ready vault/coord/B.ready\nif timeout 6 bash vault/worker.sh A opposite; then exit 1; else test "$?" -eq 4; fi\n', base/'lab9', env, 'Lab9 missing peer')

    starter = [code for section, code in routes[10] if section.startswith('## Level 2')][0]
    shell(starter, base/'lab10', env, 'Lab10 starter')
    (base/'lab10/backup.sh').write_text((ROOT/'teaching/instructor/lab10/backup_solution.sh').read_text())
    backup = shlex.quote(str(base/'lab10/backup.sh'))
    shell(f'''set -e
printf 'preserve\n' > backups/keep-me.txt
printf 'foreign archive name\n' > backups/backup-unrelated.tar.gz
for i in 1 2 3 4; do bash backup.sh; done
cd "$HOME"
env -i HOME="$HOME" PATH=/usr/bin:/bin /bin/bash {backup}
''', base/'lab10', env, 'Lab10 retention/environment')
    archives = [p for p in (base/'lab10/backups').glob('backup-*') if p.name != 'backup-unrelated.tar.gz']
    assert len(archives) == 3
    assert (base/'lab10/backups/keep-me.txt').read_text() == 'preserve\n'
    assert (base/'lab10/backups/backup-unrelated.tar.gz').is_file()
    shell('''set -e
archive=$(find backups -maxdepth 1 -type f -name 'backup-[0-9]*.tar.gz' | sort | tail -n 1)
mkdir restore-test
tar -tzf "$archive"
tar -xzf "$archive" -C restore-test
cmp -- project/report.txt restore-test/project/report.txt
cmp -- project/config.ini restore-test/project/config.ini
''', base/'lab10', env, 'Lab10 restore')

    imageblocks = [code for section, code in routes[11] if section.startswith('## Level 2')]
    formatblocks = [code for section, code in routes[11] if section.startswith('## Level 3')]
    shell('\n'.join(imageblocks+formatblocks[:2]), base/'lab11', env, 'Lab11 regular-image format')
    assert (base/'lab11/images/scratch.img').stat().st_size == 32*1024*1024
    assert 'Block count:' in (base/'lab11/evidence/filesystem.txt').read_text()
    # Optional user-local library guide is runnable without privileges.
    extension = blocks(ROOT/'labs/lab3/extensions.md')
    library = '\n'.join(code for section, code in extension if section.startswith('## B.'))
    out = shell(library, base/'lab3', env, 'Lab3 local shared library')
    assert 'hello from the library' in out
    print('All core walkthrough/model checks and user-local library PASS; no live cron/VM/FUSE test', flush=True)
