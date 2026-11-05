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
PILOTS = (1, 2, 4, 5, 6, 7, 8, 9, 10)  # labs whose fences use personal values and Core sections
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
    values = {}

    def personal(n, code, **override):
        """Replace the example values in a pilot lab's fences with this test account's own values."""
        for key, value in dict(values[n], **override).items():
            code = re.sub(rf'^(\s*){key}=.*$', lambda m: f'{m.group(1)}{key}={shlex.quote(str(value))}', code, flags=re.M)
        code = code.replace('~/oslab-work', '"$OSLAB_WORKSPACE"')
        if n == 1:  # Lab 1 shows placeholders instead of shell variables
            code = code.replace('FILE1', values[1]['file1']).replace('FILE2', values[1]['file2'])
        if n == 4:  # Lab 4 shows capital placeholders too
            code = code.replace('STATUS', values[4]['status']).replace('OTHER', values[4]['other'])
        if n == 6:  # Lab 6 shows BOX for the personal demo folder
            code = code.replace('BOX', values[6]['box'])
        if n == 9:  # Lab 9 shows RES1 and RES2 for the personal lock names
            code = code.replace('RES1', values[9]['res1']).replace('RES2', values[9]['res2'])
        if n == 10:  # Lab 10 shows NAME and KEEP for the personal archive name and count
            code = code.replace('NAME', values[10]['name']).replace('KEEP', str(values[10]['keep']))
        if n == 7:  # Lab 7 shows FILE1 and FILE2 for the personal file names
            code = code.replace('FILE1', values[7]['file1']).replace('FILE2', values[7]['file2'])
        return code

    def section(n, *starts, **override):
        return personal(n, '\n'.join(code for name, code in routes[n] if name.startswith(tuple(f'## {s}' for s in starts))), **override)

    for n in range(1, 12):
        routes[n] = blocks(ROOT/f'labs/lab{n}/lab{n}-instruction.md')
        if n in PILOTS:
            listing = shell(prefix+f'oslab values lab{n}\n', home, env, f'Lab {n} values')
            values[n] = dict(re.findall(r'^\s+(\w+)\s+= (.*)$', listing, re.M))
            assert values[n], listing
            guided = section(n, 'Setup', 'Guided', 'Read and Trace')
            if n == 2:  # Guided step 4 fails on purpose: an unquoted name with a space is two names
                assert guided.count('ls -l incoming/$file1\n') == 1, 'Lab 2 guided step 4 changed'
                guided = guided.replace('ls -l incoming/$file1\n', 'if ls -l incoming/$file1; then exit 1; fi\n')
            shell(prefix+guided, home, env, f'Lab {n} setup/guided')
        else:
            setup = '\n'.join(code for name, code in routes[n] if name.startswith('## Lab Setup'))
            guided = '\n'.join(code for name, code in routes[n] if 'Guided' in name)
            shell(prefix+setup+guided, home, env, f'Lab {n} guided')
        print(f'Lab {n} setup/guided commands PASS', flush=True)

    count = int(values[1]['count'])
    first, second = values[1]['file1'], values[1]['file2']
    # Tasks 1, 2, 4, 5, 6 as written; Task 5's single `sleep 300 &` line is typed COUNT times, as the student does.
    task5 = section(1, 'Task 5').replace('sleep 300 &\n', 'sleep 300 &\n' * count, 1)
    task4 = section(1, 'Task 4').replace('sleep 30 &', 'sleep 3 &')
    shell(prefix + section(1, 'Setup') + section(1, 'Task 1') + section(1, 'Task 2') + task4 + task5
          + section(1, 'Task 6') + 'kill $(jobs -p) 2>/dev/null || true\n', home, env, 'Lab1 tasks')
    lab1 = base/'lab1'
    assert (lab1/'task2_files'/f'{first}.txt').read_text() == f'This is file {first}\n'
    assert (lab1/'task2_files'/f'{second}_renamed.txt').is_file()
    out = shell(prefix + 'oslab check lab1\n', home, env, 'Lab1 check')
    assert 'milestones: 4/4' in out, out
    # Task 3 (APT) is homework on the student's own machine; it needs sudo and a real install, so it is not run here.
    # A student who typed the placeholder literally must not pass.
    (lab1/'task2_files'/f'{first}.txt').write_text('This is file FILE1\n')
    assert 'TRY : task2_files' in shell(prefix + 'oslab check lab1\n', home, env, 'Lab1 wrong content'), 'placeholder text passed'
    (lab1/'task2_files'/f'{first}.txt').write_text(f'This is file {first}\n')

    out = shell(prefix+section(2, 'Setup')+section(2, 'Core 1')+'''
cd incoming
mv -- "$file1" ../reports/
cd "$OSLAB_WORKSPACE/lab2"
mv -- "$OSLAB_WORKSPACE/lab2/incoming/$file2" "$OSLAB_WORKSPACE/lab2/reports/"
cp -- "reports/$file1" "reports/$file2" "TechCorp/$owner/"
cp -- "reports/$file1" "TechCorp/$owner/archive/first-original.txt"
cd "TechCorp/$reader"
cat "../$owner/$file1"
cat "$OSLAB_WORKSPACE/lab2/TechCorp/$owner/$file1"
if cat "reports/$file1" 2>/dev/null; then exit 1; fi
cd "$OSLAB_WORKSPACE/lab2"
printf '%s\\n' "cat ../$owner/$file1" "cat $OSLAB_WORKSPACE/lab2/TechCorp/$owner/$file1" > evidence/paths.txt
# Core 3 step 2 is typed into nano by the student; these are the two lines it asks for.
printf '%s\\n' "Error: cat: 'reports/$file1': No such file or directory" "Fix: ../../reports/$file1" >> evidence/paths.txt
'''+section(2, 'Core 3')+section(2, 'Plus')+'''
cd mess/c
mv -- '../a/b/lost file.txt' found.txt
cd ../a/b
cp -- ../../c/found.txt "../../../TechCorp/$third/"
test -f "$OSLAB_WORKSPACE/lab2/TechCorp/$third/found.txt"
''', home, env, 'Lab2 path/content')
    assert 'milestones: 5/5' in out, out

    core = [code for section, code in routes[3] if section.startswith('## Task 2')]
    shell(core[0]+core[1]+'rm -- soft.txt\nln -s renamed.txt soft.txt\n'+core[2]+core[3], base/'lab3', env, 'Lab3 rename/repair')
    assert (base/'lab3/links/hard.txt').read_text() == 'version 1\n'
    assert (base/'lab3/links/source.txt').read_text() == 'version 2\n'
    assert os.stat(base/'lab3/links/hard.txt').st_ino == os.stat(base/'lab3/links/renamed.txt').st_ino
    out = shell(prefix + 'oslab check lab3\n', home, env, 'Lab3 checked walkthrough')
    assert 'milestones: 4/4' in out, out
    trace = (base/'lab3/evidence/links.txt').read_text()
    assert all(label in trace for label in ('BEFORE RENAME', 'AFTER RENAME, BEFORE REPAIR', 'AFTER REPAIR'))
    assert 'No such file or directory' in trace

    # Lab 4: the student's own report.sh is the public model with the personal status word in front of it.
    status4 = values[4]['status']
    solution4 = (ROOT/'teaching/instructor/lab4/report_solution.sh').read_text()
    (base/'lab4/report.sh').write_text(f'STATUS={shlex.quote(status4)}\n' + solution4)

    def fences4(*starts):
        return [personal(4, code) for name, code in routes[4] if name.startswith(tuple(f'## {s}' for s in starts))]
    # The error-message fence of Core 1 exits 1 on purpose when run without an argument; it is a pattern, not a step.
    core1 = [code for code in fences4('Core 1') if 'exit 1' not in code]
    shell(prefix + section(4, 'Setup') + ''.join(core1) + ''.join(fences4('Core 2')) + ''.join(fences4('Instructor')),
          base/'lab4', env, 'Lab4 core, Plus and Challenge as written')
    out = shell(prefix + 'oslab check lab4\n', home, env, 'Lab4 check')
    assert 'milestones: 4/4' in out, out
    edge = (base/'lab4/evidence/edge.txt').read_text()
    assert f'{status4} total: 0' in edge and 'missing-input status=' in edge and 'missing-input status=0' not in edge, edge
    assert (base/'lab4/evidence/normal.txt').read_text() == (base/'lab4/data/expected.txt').read_text()
    # Every wrong way the objectives warn about must fail a milestone.
    wrong = {'rows': f'echo "{status4} total: $(grep -c "^{status4}," "$1")"\n',
             'prefix': f'awk -F, -v s="{status4}" \'$1 ~ "^"s {{ t += $2 }} END {{ print s " total: " t+0 }}\' "$1"\n',
             'first': f'grep "^{status4}," "$1" | head -n 1 | cut -d, -f2 | sed "s/^/{status4} total: /"\n'}
    for label, body in wrong.items():
        (base/'lab4/report.sh').write_text('#!/usr/bin/env bash\n' + body)
        result = subprocess.run(['bash', '-c', prefix + 'oslab check lab4\n'], cwd=home, env=env, capture_output=True, text=True)
        assert 'milestones: 4/4' not in result.stdout, (label, result.stdout)
    (base/'lab4/report.sh').write_text(f'STATUS={shlex.quote(status4)}\n' + solution4)

    # Lab 5: the program arrives with two gaps; the model fills them as a student would, then breaks them in turn.
    def fences5(*starts):
        return [personal(5, code) for name, code in routes[5] if name.startswith(tuple(f'## {s}' for s in starts))]
    core1 = fences5('Core 1')
    assert len(core1) == 3, len(core1)
    shell(prefix + section(5, 'Setup') + core1[0] + core1[1], base/'lab5', env, 'Lab5 unfinished program')
    source = base/'lab5/threads/two_workers.c'
    unfinished = source.read_text()
    join_todo = '/* TODO: join both workers and check each return code. */'
    print_todo = '/* TODO: after both joins, print a.result and b.result. */'
    joins = 'rc = pthread_join(ta, NULL); if (rc) return 1;\n    rc = pthread_join(tb, NULL); if (rc) return 1;'
    report = 'printf("A result=%d B result=%d\\n", a.result, b.result);'
    assert join_todo in unfinished and print_todo in unfinished
    model5 = unfinished.replace(join_todo, joins).replace(print_todo, report)
    source.write_text(model5)
    shell(prefix + core1[2], base/'lab5', env, 'Lab5 finished program')
    core2 = fences5('Core 2')
    assert len(core2) == 4, len(core2)
    shell(prefix + core2[0], base/'lab5', env, 'Lab5 normal run')
    shell('cp -- threads/two_workers.c threads/changed.c\n', base/'lab5', env, 'Lab5 copy')
    changed = base/'lab5/threads/changed.c'
    job = re.search(r'struct job a = \{(\d+), (\d+), 0\}, b = \{(\d+), (\d+), 0\};', changed.read_text())
    assert job, 'job line changed'
    changed.write_text(changed.read_text().replace(job.group(0), f'struct job a = {{{job.group(1)}, 0, 0}}, b = {{{job.group(3)}, 1, 0}};'))
    shell(prefix + core2[2], base/'lab5', env, 'Lab5 changed run')
    assert (base/'lab5/evidence/changed.txt').read_text().startswith('worker ' + values[5]['id_b'] + ' finished') or 'exit=0' in (base/'lab5/evidence/changed.txt').read_text()
    out = shell(prefix + core2[3], base/'lab5', env, 'Lab5 check')
    assert 'milestones: 4/4' in out, out
    ra5, rb5 = (int(values[5][k]) * int(values[5][s]) for k, s in (('id_a', 'steps_a'), ('id_b', 'steps_b')))
    assert f'A result={ra5} B result={rb5}' in (base/'lab5/evidence/normal.txt').read_text()
    # Each way of getting the joins wrong must fail a milestone.
    broken5 = {'one join': (model5.replace('rc = pthread_join(tb, NULL); if (rc) return 1;', ''), 'TRY : the return code'),
               'unchecked joins': (model5.replace('rc = pthread_join(ta, NULL); if (rc) return 1;', 'pthread_join(ta, NULL);')
                                   .replace('rc = pthread_join(tb, NULL); if (rc) return 1;', 'pthread_join(tb, NULL);'), 'TRY : the return code'),
               'report before the joins': (unfinished.replace(join_todo, report).replace(print_todo, joins), 'TRY : both workers')}
    for label, (text5, expected) in broken5.items():
        source.write_text(text5)
        result = subprocess.run(['bash', '-c', prefix + 'oslab check lab5\n'], cwd=base/'lab5', env=env, capture_output=True, text=True)
        assert 'milestones: 4/4' not in result.stdout and expected in result.stdout, (label, result.stdout)
    source.write_text(model5)
    model = shlex.quote(str(ROOT/'teaching/instructor/lab5/two_workers_solution.c'))
    out = shell(f'set -e\ngcc -Wall -Wextra -Werror -pthread {model} -o threads/model\ntimeout 5 threads/model\n', base/'lab5', env, 'Lab5 public model')
    assert 'A result=6 B result=12' in out

    # Lab 6: the student turns a policy sentence into modes; the model does it from the sentence, then breaks it in turn.
    notice6, box6 = values[6]['notice'], values[6]['box']
    modes6 = (('The owner may change the file.', '640', '750'), ('Everyone may read the file', '644', '711'),
              ("The owner and the owner's group", '660', '770'))
    fm6, dm6 = next((f, d) for start, f, d in modes6 if notice6.startswith(start))

    def fences6(*starts):
        return [personal(6, code) for name, code in routes[6] if name.startswith(tuple(f'## {s}' for s in starts))]
    core1, core2, extras = fences6('Core 1'), fences6('Core 2'), fences6('Instructor')
    assert len(core1) == 2 and len(core2) == 4 and len(extras) == 1, (len(core1), len(core2), len(extras))
    chmods6 = f'chmod 700 private\nchmod 600 private/record.txt\nchmod {dm6} shared\nchmod {fm6} shared/notice.txt\n'
    out = shell(prefix + section(6, 'Setup') + chmods6 + core1[0] + core1[1] + core2[0] + core2[1] + core2[2], base/'lab6', env, 'Lab6 core as written')
    assert 'milestones: 4/4' in out, out
    trace6 = (base/'lab6/evidence/traversal.txt').read_text()
    assert 'Permission denied' in trace6 and 'inside' in trace6, trace6
    assert oct((base/'lab6/demo'/box6).stat().st_mode & 0o777) == '0o700'
    shell(prefix + core2[3], base/'lab6', env, 'Lab6 namei')
    out = shell(extras[0], base/'lab6', env, 'Lab6 challenge')
    assert ' 600 ' in out, out
    # A wrong mode must fail its milestone and say which mode is needed.
    for rel, mode, expected in (('private', '755', 'TRY : private/ is 700'), ('shared/notice.txt', '666', 'TRY : shared/ and shared/notice.txt follow')):
        shell(f'chmod {mode} {rel}\n', base/'lab6', env, 'Lab6 wrong mode')
        result = subprocess.run(['bash', '-c', prefix + 'oslab check lab6\n'], cwd=base/'lab6', env=env, capture_output=True, text=True)
        assert 'milestones: 4/4' not in result.stdout and expected in result.stdout, result.stdout
        shell(chmods6, base/'lab6', env, 'Lab6 restore modes')
    # The traversal evidence must be real: an evidence file without the failed read does not pass.
    keep6 = (base/'lab6/evidence/traversal.txt').read_text()
    (base/'lab6/evidence/traversal.txt').write_text('inside\n')
    result = subprocess.run(['bash', '-c', prefix + 'oslab check lab6\n'], cwd=base/'lab6', env=env, capture_output=True, text=True)
    assert 'milestones: 3/4' in result.stdout and 'Permission denied' in result.stdout, result.stdout
    (base/'lab6/evidence/traversal.txt').write_text(keep6)
    # The folder left at 600 must not crash the helper.
    shell(f'chmod 600 demo/{box6}\n', base/'lab6', env, 'Lab6 seal')
    out = shell(prefix + 'oslab check lab6\n', home, env, 'Lab6 check with a sealed folder')
    assert 'milestones: 3/4' in out, out
    shell(f'chmod 700 demo/{box6}\n', base/'lab6', env, 'Lab6 unseal')

    # Lab 7: the student writes count_words.sh; the model is the public script, and the fences run as written.
    name1, name2 = values[7]['file1'], values[7]['file2']

    def fences7(*starts):
        return [personal(7, code) for name, code in routes[7] if name.startswith(tuple(f'## {s}' for s in starts))]
    core1, core2, extras = fences7('Core 1'), fences7('Core 2'), fences7('Instructor')
    assert len(core1) == 3 and len(core2) == 4 and len(extras) == 1, (len(core1), len(core2), len(extras))
    (base/'lab7/count_words.sh').write_text((ROOT/'teaching/instructor/lab7/count_words_solution.sh').read_text())
    out = shell(prefix + section(7, 'Setup') + ''.join(core1) + ''.join(core2), base/'lab7', env, 'Lab7 core as written')
    assert 'milestones: 4/4' in out, out
    assert f'{name1}' in (base/'lab7/evidence/normal.txt').read_text() and f'{name2}' in (base/'lab7/evidence/normal.txt').read_text()
    edge7 = (base/'lab7/evidence/edge.txt').read_text()
    assert 'status=1' in edge7 and name1 in edge7, edge7
    assert name2 in (base/'lab7/evidence/dash.txt').read_text()
    shell(prefix + extras[0], base/'lab7', env, 'Lab7 challenge')
    # A name that is a folder is not a regular file; the model rejects it and ends with a status other than 0.
    shell('mkdir -p input/folder\nif bash count_words.sh input/folder; then exit 1; fi\nrmdir input/folder\n', base/'lab7', env, 'Lab7 plus')
    # The placeholder typed literally must not pass as a student's own file name.
    result = subprocess.run(['bash', '-c', 'bash count_words.sh "input/FILE1"; echo "status=$?"'], cwd=base/'lab7', env=env, capture_output=True, text=True)
    assert 'status=1' in result.stdout and 'FILE1' in result.stderr, (result.stdout, result.stderr)

    stock, buyer_a, buyer_b = (int(values[8][key]) for key in ('stock', 'buyer_a', 'buyer_b'))
    setup8 = prefix+section(8, 'Setup')
    reset = "printf '%s\\n' \"$stock\" > store/stock.txt\n: > store/sales.log\n"
    shell(setup8+reset+section(8, 'Core 1'), home, env, 'Lab8 student race')
    sold = [int(line.split()[1]) for line in (base/'lab8/store/sales.log').read_text().splitlines()]
    assert sorted(sold) == sorted((buyer_a, buyer_b)), sold
    assert int((base/'lab8/store/stock.txt').read_text()) in (stock - buyer_a, stock - buyer_b)
    assert f'start={stock}' in (base/'lab8/evidence/race.txt').read_text()
    # Core 2 keeps the unsafe copy and tries flock; the Plus block shows a wrong answer still selling twice.
    shell(setup8+section(8, 'Core 2')+section(8, 'Plus'), home, env, 'Lab8 flock demo and wrong answer')
    assert len((base/'lab8/try/sales.log').read_text().splitlines()) == 2
    (base/'lab8/store/buy.sh').write_text((ROOT/'teaching/instructor/lab8/buy_fixed.sh').read_text())
    out = shell(setup8+reset+section(8, 'Core 1')+'oslab check lab8\n', home, env, 'Lab8 student repaired')
    sold = [int(line.split()[1]) for line in (base/'lab8/store/sales.log').read_text().splitlines()]
    assert len(sold) == 1 and sold[0] + int((base/'lab8/store/stock.txt').read_text()) == stock, sold
    assert 'milestones: 3/3' in out, out
    shell(setup8+reset+'''set -e
for bad in 0 -1 abc 0001 1000; do
  if bash store/buy.sh "$bad"; then exit 1; fi
done
if bash store/buy.sh; then exit 1; fi
if bash store/buy.sh "$((stock + 1))"; then exit 1; fi
test "$(cat store/stock.txt)" = "$stock"
test ! -s store/sales.log
bash store/buy.sh 2
test "$(cat store/stock.txt)" = "$((stock - 2))"
(flock -x 9; touch evidence/held; sleep 7) 9>store/stock.lock & holder=$!
for attempt in {1..30}; do test -f evidence/held && break; sleep 0.1; done
if timeout 8 bash store/buy.sh 1; then exit 1; else test "$?" -eq 3; fi
wait "$holder"
''', home, env, 'Lab8 validation/lock bound')

    # Lab 9: the worker arrives with one TODO; the model repairs it, then a name-dependent rule must fail milestone 3.
    res1, a_first = values[9]['res1'], values[9]['a_first']

    def fences9(*starts):
        return [personal(9, code) for name, code in routes[9] if name.startswith(tuple(f'## {s}' for s in starts))]
    core1, core2, extras = fences9('Core 1'), fences9('Core 2'), fences9('Instructor')
    assert len(core1) == 2 and len(core2) == 3 and len(extras) == 1, (len(core1), len(core2), len(extras))
    shell(prefix + section(9, 'Setup') + core1[0] + core1[1], base/'lab9', env, 'Lab9 opposite as written')
    opposite9 = (base/'lab9/evidence/opposite.txt').read_text()
    assert 'second lock timeout' in opposite9 and opposite9.startswith('opposite A='), opposite9
    worker = base/'lab9/vault/worker.sh'
    swap = 'if [[ "$role" = B ]]; then tmp=$first; first=$second; second=$tmp; fi'
    original9 = worker.read_text()
    assert swap in original9, 'the TODO line of the worker changed'
    # A rule that works only for the student's own names: B swaps in ordered mode too, unless the first lock has that name.
    worker.write_text(original9.replace(swap, f'if [[ "$role" = B && ( "$mode" = opposite || "$first" != "{a_first}" ) ]]; then tmp=$first; first=$second; second=$tmp; fi'))
    result = subprocess.run(['bash', '-c', prefix + 'oslab check lab9\n'], cwd=base/'lab9', env=env, capture_output=True, text=True)
    assert 'PASS: ordered mode' in result.stdout and 'TRY : your ordering rule does not depend on the names' in result.stdout, result.stdout
    worker.write_text(original9.replace(swap, 'if [[ "$role" = B && "$mode" = opposite ]]; then tmp=$first; first=$second; second=$tmp; fi'))
    out = shell(prefix + core2[0] + core2[1] + core2[2], base/'lab9', env, 'Lab9 core 2 as written')
    assert 'milestones: 4/4' in out, out
    output9 = (base/'lab9/evidence/ordered.txt').read_text()
    assert 'A=0 B=0' in output9 and output9.count('holds both') == 2, output9
    shell(prefix + extras[0], base/'lab9', env, 'Lab9 plus')
    shell(f'rm -f -- vault/coord/A.ready vault/coord/B.ready\nif timeout 6 bash vault/worker.sh A opposite; then exit 1; else test "$?" -eq 4; fi\n', base/'lab9', env, 'Lab9 missing peer')

    # Lab 10: the student writes the retention; the model is the public script with this account's own keep= and name=.
    name10, keep10 = values[10]['name'], int(values[10]['keep'])
    model = (ROOT/'teaching/instructor/lab10/backup_solution.sh').read_text()
    model = re.sub(r'^keep=.*$', f'keep={keep10}', model, flags=re.M)
    model = re.sub(r'^name=.*$', f'name={name10}', model, flags=re.M)
    (base/'lab10/backup.sh').write_text(model)
    core10 = [personal(10, code) for name, code in routes[10] if name.startswith('## Core 1') or name.startswith('## Core 2')]
    out = shell(prefix + '\n'.join(core10), base/'lab10', env, 'Lab10 core as written')
    archives = [p for p in (base/'lab10/backups').glob(f'{name10}-[0-9]*.tar.gz') if p.name != f'{name10}-notes.tar.gz']
    assert len(archives) == keep10, archives
    assert (base/'lab10/backups/keep-me.txt').read_text() == 'unrelated; preserve me\n'
    assert (base/'lab10/backups'/f'{name10}-notes.tar.gz').is_file()
    out = shell(prefix + 'oslab check lab10\n', base/'lab10', env, 'Lab10 check')
    assert 'milestones: 4/4' in out or 'PASS' in out, out

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
