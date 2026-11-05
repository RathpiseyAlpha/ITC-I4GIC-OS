"""Exercise Lab 3 collection, real link checks and dashboard suggestions in isolation.

Run with the website dependencies installed: python3 tools/test_lab3_collection.py.
No live student homes, class inbox, release or marks are touched.
"""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
import oslab

USER = 'student-lab3'


class Lab3Collection(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='oslab3-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'home with spaces'
        self.home.mkdir()
        self.base = self.home / 'work space'
        self.inbox = Path(self.temp.name) / 'inbox'
        self.release = Path(self.temp.name) / 'release'
        self.inbox.mkdir()
        self.release.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), OSLAB_WORKSPACE=str(self.base),
                        OSLAB_INBOX=str(self.inbox), OSLAB_RELEASE_DIR=str(self.release),
                        OSLAB_TEST_USER=USER, OSLAB_TEACH_TRUST_NAME='1',
                        OSLAB_TEACH_STATE=str(self.home / 'teacher'))
        self.cli('start')
        self.lab = self.base / 'lab3'
        (self.lab / 'evidence').mkdir()
        self.values = oslab.lab_values('lab3', USER)
        self.name, self.tag = self.values['name'], self.values['tag']
        self.v1, self.v2 = self.values['v1'], self.values['v2']

    def cli(self, command, answers=None, ok=True):
        result = subprocess.run([sys.executable, str(ROOT / 'server/oslab.py'), command, 'lab3'],
                                env=self.env, input=answers, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def teacher(self, command):
        result = subprocess.run([sys.executable, str(ROOT / 'server/oslab_teach.py'), command, 'lab3'],
                                env=self.env, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def teacher_error(self, command):
        result = subprocess.run([sys.executable, str(ROOT / 'server/oslab_teach.py'), command, 'lab3'],
                                env=self.env, text=True, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        return result.stdout + result.stderr

    def finish_core(self):
        n, t = self.name, self.tag
        evidence = self.lab / 'evidence'
        (evidence / 'wildcards.txt').write_text(
            f'<notes/{n}1.txt>\n<notes/{n}12.txt>\n<notes/{n}2.txt>\n<notes/{n}1.txt>\n<notes/{n}2.txt>\n<notes/*.txt>\n')
        links = self.lab / 'links'
        os.link(links / f'{n}.txt', links / f'{n}-hard.txt')
        (links / f'{n}-soft.txt').symlink_to(f'{n}.txt')
        (links / f'{n}.txt').rename(links / f'{n}-{t}.txt')
        (links / f'{n}.txt').write_text(f'version {self.v2}\n')
        (evidence / 'replacement.txt').write_text(f'hard: version {self.v1}\nsoft: version {self.v2}\n')
        (links / f'{n}-soft.txt').unlink()
        (links / f'{n}-soft.txt').symlink_to(f'./{n}-{t}.txt')
        (evidence / 'links.txt').write_text(
            f'\n=== BEFORE RENAME ===\nhard: version {self.v1}\nsoft: version {self.v1}\nstored target: {n}.txt\n'
            f'\n=== AFTER RENAME, BEFORE REPAIR ===\nhard: version {self.v1}\nstored target: {n}.txt\n'
            f'soft: cat: {n}-soft.txt: No such file or directory\n'
            f'\n=== AFTER REPAIR ===\nstored target: ./{n}-{t}.txt\nhard: version {self.v1}\nsoft: version {self.v1}\n'
            'Decision: relative\n')

    def build_checkpoint(self, values):
        box = self.lab / values['folder']
        (box / 'links').mkdir(parents=True)
        data, moved = box / values['data'], box / values['moved']
        data.write_text(values['content'] + '\n')
        os.link(data, box / 'links/hard.txt')
        (box / 'links/first.txt').symlink_to(f"../{values['data']}")
        (box / 'links/second.txt').symlink_to('first.txt')
        data.rename(moved)
        (box / 'links/first.txt').unlink()
        (box / 'links/first.txt').symlink_to(f"../{values['moved']}")
        (self.lab / 'evidence/checkpoint.txt').write_text((values['content'] + '\n') * 2)

    def test_values_are_personal_and_fixture_matches(self):
        other = oslab.lab_values('lab3', 'student-other')
        self.assertNotEqual(self.values, other)
        self.assertGreater(self.v2, self.v1)
        self.assertEqual((self.lab / 'links' / f'{self.name}.txt').read_text(), f'version {self.v1}\n')
        notes = sorted(p.name for p in (self.lab / 'notes').iterdir())
        self.assertEqual(notes, sorted([f'.{self.name}.txt', f'{self.name}.log', f'{self.name}1.txt',
                                        f'{self.name}2.txt', f'{self.name}12.txt']))
        self.assertIn('milestones: 0/5', self.cli('check'))

    def test_collection_release_and_dashboard(self):
        self.assertIn('milestones: 0/5', self.cli('check'))
        self.cli('predict', f'no\n{self.v1}\n{self.v2}\nI think the symbolic link stores a name\n')
        first = (self.base / '.records/lab3-predict.json').read_bytes()
        self.assertIn('already saved', self.cli('predict', ok=False))
        self.assertIn('not open yet', self.cli('checkpoint', ok=False))
        self.finish_core()
        self.assertIn('milestones: 5/5', self.cli('check'))
        self.teacher('release')
        self.assertIn('already released', self.teacher_error('release'))
        nonce = (self.release / 'lab3.checkpoint').read_text().strip()
        values, _, questions, _ = oslab.checkpoint_task('lab3', USER, nonce)
        self.cli('checkpoint', f"yes\nno\n../{values['moved']}\nyes\nThe folder that holds the link\n")
        self.assertIn('already saved', self.cli('checkpoint', ok=False))
        self.assertIn('milestones: 5/6', self.cli('check'))
        self.build_checkpoint(values)
        self.assertIn('milestones: 6/6', self.cli('check'))
        self.cli('debrief', f'no\n{self.v1}\n{self.v2}\n')
        self.assertEqual((self.base / '.records/lab3-predict.json').read_bytes(), first)
        board = self.teacher('board')
        self.assertIn(USER, board)
        export = self.teacher('export')
        self.assertIn('The folder that holds the link', export)
        self.assertIn('checkpoint values', self.teacher('key'))

        spec = importlib.util.spec_from_file_location('lab3_presence_test', ROOT / 'app/server/app.py')
        app = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, self.env):
            spec.loader.exec_module(app)
            activity = app._oslab_activity(USER, 'lab3')
        self.assertTrue(activity['available'])
        self.assertTrue(activity['checkpoint']['taskDone'])
        self.assertEqual([a['ok'] for a in activity['checkpoint']['answers']], [True, True, True, True, None])
        self.assertEqual(activity['checks'][-1]['pathError'], {'error': True, 'fix': True})
        rubric = app._rubric('lab3')
        self.assertEqual([r['max'] for r in rubric], [2.0, 2.0, 2.0, 3.0, 1.0])
        grade = {'found': True, 'finalPercentage': 100, 'items': [{'status': 'ok'}]}
        suggested = app._mark_suggestions(rubric, activity, grade, lab='lab3')
        self.assertEqual({key: row['points'] for key, row in suggested.items()},
                         {'r1': 2.0, 'r2': 2.0, 'r3': 2.0, 'r4': 2.0, 'r5': 1.0})
        self.assertIn('add up to 1', suggested['r4']['note'])
        self.assertIn('failure after the rename recorded', suggested['r2']['note'])
        practice = dict(activity, checkpoint=dict(activity['checkpoint'], practice=True))
        self.assertNotIn('r4', app._mark_suggestions(rubric, practice, grade, lab='lab3'))

    def test_copies_and_wrong_targets_do_not_pass(self):
        n, t = self.name, self.tag
        self.finish_core()
        links = self.lab / 'links'
        results = oslab.check_lab3(self.lab, self.values)
        self.assertEqual([problems for _, problems in results], [[]] * 5)
        (links / f'{n}-hard.txt').unlink()
        (links / f'{n}-hard.txt').write_text(f'version {self.v1}\n')  # equal bytes are not a hard link
        self.assertTrue(oslab.check_lab3(self.lab, self.values)[1][1])
        (links / f'{n}-hard.txt').unlink()
        os.link(links / f'{n}-{t}.txt', links / f'{n}-hard.txt')
        (links / f'{n}-soft.txt').unlink()
        (links / f'{n}-soft.txt').symlink_to(f'{n}.txt')  # valid path, the NEW file
        problems = oslab.check_lab3(self.lab, self.values)[2][1]
        self.assertIn('NEW file', problems[0])
        (links / f'{n}-soft.txt').unlink()
        (links / f'{n}-soft.txt').symlink_to(str(links / f'{n}-{t}.txt'))  # an absolute target
        self.assertIn('absolute', oslab.check_lab3(self.lab, self.values)[2][1][0])
        (links / f'{n}-soft.txt').unlink()
        (links / f'{n}-soft.txt').write_text(f'version {self.v1}\n')  # a copy is not a symbolic link
        self.assertTrue(oslab.check_lab3(self.lab, self.values)[2][1])
        (self.lab / 'evidence/wildcards.txt').write_text('notes/*.txt\n')
        self.assertTrue(oslab.check_lab3(self.lab, self.values)[0][1])
        (self.lab / 'evidence/links.txt').write_text('=== AFTER REPAIR ===\nstored target: x\n')
        self.assertTrue(oslab.check_lab3(self.lab, self.values)[4][1])

    def test_placeholders_and_old_values_do_not_pass(self):
        self.finish_core()
        text = (self.lab / 'evidence/links.txt').read_text().replace(self.name, 'maple')
        (self.lab / 'evidence/links.txt').write_text(text)
        if self.name != 'maple':
            self.assertTrue(oslab.check_lab3(self.lab, self.values)[4][1])

    def test_practice_checkpoint_printed_task_and_isolation(self):
        # No class release directory means local practice, never a graded release.
        self.release.rmdir()
        self.finish_core()
        values, _, _, after = oslab.checkpoint_task('lab3', USER, 'practice')
        self.cli('checkpoint', f"yes\nno\n../{values['moved']}\nyes\nThe link's own directory\n")
        before = (self.lab / 'links' / f'{self.name}-{self.tag}.txt').read_bytes()
        printed = [line.strip() for line in after[1:-1]]
        commands = '\n'.join(line for line in printed if not line.startswith('('))
        repair = f"rm -- links/first.txt\nln -s ../{values['moved']} links/first.txt\n"
        build, saver = commands.rsplit('\n', 1)
        result = subprocess.run(['bash', '-e'], input=build + '\n' + repair + saver + '\n', env=self.env,
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('milestones: 6/6', self.cli('check'))
        self.assertEqual((self.lab / 'links' / f'{self.name}-{self.tag}.txt').read_bytes(), before)
        self.assertIn('practice', self.teacher('board'))


if __name__ == '__main__':
    unittest.main()
