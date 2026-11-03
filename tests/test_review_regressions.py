"""Regression contracts from observed Kit defects, not planted app defects."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agent_team import core, takeover


ROOT = Path(__file__).resolve().parents[1]


class GeneratorReviewRegressions(unittest.TestCase):
    def test_custom_symlink_in_output_ancestor_cannot_write_outside(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder).resolve()
            project, outside = base / 'project', base / 'outside'
            project.mkdir(); outside.mkdir()
            (project / 'alias').symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                core.generate(project / 'alias' / 'generated', core.render(core.load_spec(ROOT / 'team.toml')))
            self.assertEqual(list(outside.iterdir()), [])

    @unittest.skipUnless(os.name == 'posix', 'FIFO source is a POSIX case')
    def test_nonregular_source_refused_without_hanging(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.toml'; os.mkfifo(source)
            try:
                result = subprocess.run([sys.executable, '-m', 'agent_team', 'validate', '--spec', str(source)],
                                        cwd=ROOT, text=True, capture_output=True, timeout=2)
            except subprocess.TimeoutExpired:
                self.fail('configuration reader blocked on a nonregular source')
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)

    def test_unmanaged_native_agent_is_disclosed_without_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            files = core.render(core.load_spec(ROOT / 'team.toml'))
            core.generate(output, files)
            unexpected = output / '.codex/agents/unmanaged.toml'
            unexpected.write_text('deliberately invalid configuration = [')
            issues = core.check(output, files)
            self.assertTrue(any('unmanaged.toml' in item for item in issues))
            self.assertEqual(unexpected.read_text(), 'deliberately invalid configuration = [')


@unittest.skipUnless(os.name == 'posix', 'acceptance runner supports POSIX')
class TakeoverReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / 'app'; self.project.mkdir(); (self.project / 'tests').mkdir()
        (self.project / 'app.py').write_text('value = 1\n')
        self.plan = {'schema_version': 1, 'kind': 'takeover-plan', 'name': 'review-regressions',
                     'scope': 'Validate actual execution, log redaction and malformed evidence handling.',
                     'acceptance_paths': ['tests'], 'checks': [{'id': 'tests', 'description': 'Review contract',
                     'argv': [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], 'timeout_seconds': 5}]}
        self.plan_path = self.base / 'plan.json'

    def run_with_tests(self, text, name):
        (self.project / 'tests/test_case.py').write_text(text)
        self.plan_path.write_text(json.dumps(self.plan))
        return takeover.run(self.project, self.plan_path, self.base / name)

    def test_all_skipped_tests_are_unverified(self):
        text = 'import unittest\n@unittest.skip("not implemented")\nclass Cases(unittest.TestCase):\n def test_save(self): self.fail("not executed")\n'
        report, code = self.run_with_tests(text, 'skipped.json')
        self.assertEqual(report['results'][0]['status'], 'error')
        self.assertEqual(code, 1)
        self.assertEqual(report['results'][0]['test_summary']['executed'], 0)

    def test_partially_skipped_counts_are_visible(self):
        text = 'import unittest\nclass Cases(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n @unittest.skip("pending")\n def test_pending(self): self.fail("not executed")\n'
        report, code = self.run_with_tests(text, 'partial.json')
        self.assertEqual(code, 0)
        self.assertEqual(report['results'][0]['test_summary'],
                         {'framework': 'unittest', 'discovered': 2, 'skipped': 1, 'executed': 1})

    def test_common_credential_formats_are_redacted(self):
        examples = [
            'Authorization: Bearer SYNTHETIC_BEARER_VALUE',
            'Authorization: Basic SYNTHETIC_BASIC_VALUE',
            '{"password": "SYNTHETIC_PASSWORD_VALUE"}',
            '{"api_key":"SYNTHETIC_KEY_VALUE", "title":"keep"}',
            "password='SYNTHETIC_VALUE with spaces'",
            '{"authorization": "Bearer SYNTHETIC_BEARER_VALUE"}',
        ]
        for text in examples:
            with self.subTest(text=text):
                output = takeover.redact(text, self.project)
                self.assertNotIn('SYNTHETIC_', output)
                self.assertIn('<redacted>', output)
                if 'with spaces' in text:
                    self.assertNotIn('with spaces', output)
                if text.startswith('{'):
                    json.loads(output)
        self.assertIn('"title":"keep"', takeover.redact(examples[3], self.project))

    def test_malformed_result_items_are_rejected_without_traceback(self):
        report, _ = self.run_with_tests('import unittest\nclass Cases(unittest.TestCase):\n def test_ok(self): pass\n', 'valid.json')
        for item in ('unexpected', None, [], 3):
            corrupted = copy.deepcopy(report); corrupted['results'].append(item)
            bad = self.base / 'bad.json'; bad.write_text(json.dumps(corrupted))
            with self.subTest(item=item), self.assertRaises(ValueError):
                takeover.checked_report(bad)
        result = subprocess.run([sys.executable, '-m', 'agent_team', 'takeover', 'compare',
                                 '--before', str(self.base / 'valid.json'), '--after', str(bad),
                                 '--output', str(self.base / 'diff.json')],
                                cwd=ROOT, text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse((self.base / 'diff.json').exists())

    def test_passed_status_cannot_override_all_skipped_evidence(self):
        report, _ = self.run_with_tests('import unittest\n@unittest.skip("pending")\nclass Cases(unittest.TestCase):\n def test_pending(self): pass\n', 'skipped.json')
        report['results'][0]['status'] = 'passed'
        path = self.base / 'false-pass.json'; path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'executed tests'):
            takeover.checked_report(path)


if __name__ == '__main__':
    unittest.main()
