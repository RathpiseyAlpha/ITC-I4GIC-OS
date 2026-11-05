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
                        OSLAB_TEST_USER='student-lab3', OSLAB_TEACH_TRUST_NAME='1',
                        OSLAB_TEACH_STATE=str(self.home / 'teacher'))
        self.cli('start')
        self.lab = self.base / 'lab3'
        (self.lab / 'evidence').mkdir()

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

    def finish_core(self):
        (self.lab / 'evidence/wildcards.txt').write_text(
            '<practice/report1.txt>\n<practice/report2.txt>\n' * 2 + '<practice/*.txt>\n')
        links = self.lab / 'links'
        os.link(links / 'source.txt', links / 'hard.txt')
        (links / 'source.txt').rename(links / 'renamed.txt')
        (links / 'soft.txt').symlink_to('./renamed.txt')
        (links / 'source.txt').write_text('version 2\n')

    def test_collection_release_and_dashboard(self):
        self.assertIn('milestones: 0/4', self.cli('check'))
        self.cli('predict', 'no\nyes\n2\nI think both store the filename\n')
        first = (self.base / '.records/lab3-predict.json').read_bytes()
        self.assertIn('already saved', self.cli('predict', ok=False))
        self.assertIn('not open yet', self.cli('checkpoint', ok=False))
        self.finish_core()
        self.assertIn('milestones: 4/4', self.cli('check'))
        self.teacher('release')
        self.assertIn('already released', self.teacher_error('release'))
        nonce = (self.release / 'lab3.checkpoint').read_text().strip()
        values, _, questions, _ = oslab.checkpoint_task('lab3', 'student-lab3', nonce)
        target = values['name']
        self.cli('checkpoint', f'no\n{target}\nThe directory containing the symbolic link\n')
        self.assertIn('already saved', self.cli('checkpoint', ok=False))
        self.assertIn('milestones: 4/5', self.cli('check'))
        folder = self.lab / values['folder']
        folder.mkdir()
        (folder / target).write_text(values['content'] + '\n')
        (folder / 'shortcut.txt').symlink_to('./' + target)
        self.assertIn('milestones: 5/5', self.cli('check'))
        self.cli('debrief', 'yes\nno\n1\n')
        self.assertEqual((self.base / '.records/lab3-predict.json').read_bytes(), first)
        board = self.teacher('board')
        self.assertIn('student-lab3', board)
        self.assertIn('2/2', board)
        export = self.teacher('export')
        self.assertIn('The directory containing the symbolic link', export)
        self.assertIn('checkpoint values', self.teacher('key'))

        spec = importlib.util.spec_from_file_location('lab3_presence_test', ROOT / 'app/server/app.py')
        app = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, self.env):
            spec.loader.exec_module(app)
            activity = app._oslab_activity('student-lab3', 'lab3')
        self.assertTrue(activity['available'])
        self.assertTrue(activity['checkpoint']['taskDone'])
        self.assertEqual([a['ok'] for a in activity['checkpoint']['answers']], [True, True, None])
        rubric = app._rubric('lab3')
        grade = {'found': True, 'items': [{'status': 'ok'}]}
        suggested = app._mark_suggestions(rubric, activity, grade, lab='lab3')
        self.assertEqual({key: row['points'] for key, row in suggested.items()},
                         {'r1': 3.0, 'r2': 1.0, 'r3': 2.0, 'r4': 2.0, 'r5': 1.0})
        self.assertIn('add up to 1', suggested['r2']['note'])
        practice = dict(activity, checkpoint=dict(activity['checkpoint'], practice=True))
        self.assertNotIn('r4', app._mark_suggestions(rubric, practice, grade, lab='lab3'))
        old = dict(activity, checks=[dict(activity['checks'][0], lab3Checks=None)])
        self.assertNotIn('r1', app._mark_suggestions(rubric, old, grade, lab='lab3'))

    def teacher_error(self, command):
        result = subprocess.run([sys.executable, str(ROOT / 'server/oslab_teach.py'), command, 'lab3'],
                                env=self.env, text=True, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        return result.stdout + result.stderr

    def test_copies_and_wrong_targets_do_not_pass(self):
        self.finish_core()
        links = self.lab / 'links'
        (links / 'hard.txt').unlink()
        (links / 'hard.txt').write_text('version 1\n')  # equal bytes are not a hard link
        results = oslab.check_lab3(self.lab, {})
        self.assertTrue(results[1][1])
        (links / 'hard.txt').unlink()
        os.link(links / 'renamed.txt', links / 'hard.txt')
        (links / 'soft.txt').unlink()
        (links / 'soft.txt').symlink_to('source.txt')  # valid path, wrong file
        results = oslab.check_lab3(self.lab, {})
        self.assertTrue(results[2][1])
        (links / 'soft.txt').unlink()
        (links / 'soft.txt').write_text('version 1\n')  # a copy is not a symbolic link
        self.assertTrue(oslab.check_lab3(self.lab, {})[2][1])
        (self.lab / 'evidence/wildcards.txt').write_text('practice/*.txt\n')
        self.assertTrue(oslab.check_lab3(self.lab, {})[0][1])

    def test_practice_checkpoint_printed_task_and_isolation(self):
        # No class release directory means local practice, never a graded release.
        self.release.rmdir()
        self.finish_core()
        values, _, _, after = oslab.checkpoint_task('lab3', 'student-lab3', 'practice')
        self.cli('checkpoint', f"no\n{values['name']}\nThe link's own directory\n")
        before = (self.lab / 'links/source.txt').read_bytes()
        commands = '\n'.join(after[1:-1]).replace('YOUR_TARGET', values['name'])
        result = subprocess.run(['bash', '-e'], input=commands, env=self.env,
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('milestones: 5/5', self.cli('check'))
        self.assertEqual((self.lab / 'links/source.txt').read_bytes(), before)
        self.assertIn('practice', self.teacher('board'))


if __name__ == '__main__':
    unittest.main()
