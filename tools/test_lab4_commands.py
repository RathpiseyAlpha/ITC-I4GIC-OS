"""Lab 4 command-evidence regressions; no student program is executed."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
import oslab


class Lab4Commands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lab4-commands-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.values = oslab.lab_values('lab4', 'student-lab4')
        self.status = self.values['status']
        rows = oslab.lab4_rows(self.values)
        selected = [(name, count) for name, count in rows if name == self.status]
        for name, text in oslab.lab4_fixture(self.values).items():
            self.write(name, text)
        self.write('evidence/selected.txt', ''.join(f'{n},{c}\n' for n, c in selected))
        self.write('evidence/fields.txt', ''.join(f'{c}\n' for _, c in selected))
        self.write('evidence/normal.txt', '   3\n')
        self.write('data/no-match.csv', oslab.lab4_csv([(self.values['other'], 2)]))
        self.write('data/changed.csv', oslab.lab4_csv(rows + [(self.status, 7), (self.status+'-late', 99)]))
        self.write('evidence/edge.txt', '0\n4\n')
        self.write('evidence/stdout.txt', '')
        self.write('evidence/stderr.txt', 'cat: data/missing.csv: fichier introuvable\n')
        self.write('evidence/status.txt', '1\n')

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def results(self, extra=None):
        return oslab.check_lab4(self.root, self.values, extra)

    def test_direct_evidence_passes_without_script(self):
        self.assertTrue(all(not errors for _, errors in self.results()))
        self.assertFalse((self.root/'report.sh').exists())

    def test_old_script_and_command_record_are_never_executed(self):
        for name in ('report.sh', 'evidence/commands.txt'):
            self.write(name, f'touch {self.root}/executed\n')
        self.assertTrue(all(not errors for _, errors in self.results()))
        self.assertFalse((self.root/'executed').exists())

    def test_missing_empty_stdout_file_does_not_pass(self):
        (self.root/'evidence/stdout.txt').unlink()
        self.assertTrue(self.results()[3][1])

    def test_internal_symlink_is_not_evidence(self):
        path = self.root/'evidence/stdout.txt'
        path.unlink()
        self.write('empty.txt', '')
        path.symlink_to('../empty.txt')
        self.assertTrue(self.results()[3][1])

    def test_wrong_fields_counts_and_streams_are_rejected(self):
        cases = [('evidence/fields.txt', '3\n', 0),
                 ('evidence/normal.txt', '999\n', 1),
                 ('evidence/edge.txt', '4\n', 2),
                 ('evidence/stdout.txt', 'error\n', 3),
                 ('evidence/status.txt', '0\n', 3)]
        for name, wrong, milestone in cases:
            with self.subTest(name=name):
                path = self.root/name
                good = path.read_text()
                self.write(name, wrong)
                self.assertTrue(self.results()[milestone][1])
                self.write(name, good)

    def test_existing_missing_input_is_rejected(self):
        self.write('data/missing.csv', '')
        self.assertTrue(self.results()[3][1])

    def test_checkpoint_requires_new_selection_and_count(self):
        extra, _, _, _ = oslab.lab4_checkpoint(lambda key, size: 0, self.values)
        self.write('data/'+extra['name'], oslab.lab4_csv(extra['rows']))
        self.write('checkpoint.txt', '2\n')
        self.assertTrue(self.results(extra)[4][1])
        self.write('evidence/checkpoint-selected.txt', ''.join(
            f'{name},{count}\n' for name, count in extra['rows'] if name == self.status))
        (self.root / 'checkpoint.txt').rename(self.root / 'evidence/checkpoint.txt')
        self.assertIn('lab4/checkpoint.txt', self.results(extra)[4][1][0])
        self.write('checkpoint.txt', '2\n')
        self.assertFalse(self.results(extra)[4][1])
        self.write('checkpoint.txt', '3\n')
        self.assertTrue(self.results(extra)[4][1])

    def test_script_era_checkpoint_is_flagged(self):
        self.assertTrue(self.results({'name': 'old.csv', 'rows': [], 'total': 0})[4][1])

    def test_submission_checklist_does_not_require_script(self):
        spec = importlib.util.spec_from_file_location('lab4_presence', ROOT/'app/server/app.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        required = module.LAB_SPECS['lab4']['files']
        self.assertNotIn('report.sh', required)
        self.assertIn('evidence/commands.txt', required)
        self.assertIn('evidence/stdout.txt', required)
        self.assertIn('checkpoint.txt', required)


if __name__ == '__main__':
    unittest.main()
