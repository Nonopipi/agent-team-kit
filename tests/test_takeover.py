import copy
import json
import os
import errno
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent_team import takeover as tk


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'posix', 'runner currently supports POSIX process groups')
class TakeoverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = self.base / 'project'
        self.project.mkdir()
        (self.project / 'app.py').write_text('value = 1\n')
        (self.project / 'tests').mkdir()
        (self.project / 'tests/test_app.py').write_text('import unittest\n')
        self.plan = {'schema_version': 1, 'kind': 'takeover-plan', 'name': 'fixture',
                     'scope': 'Check the sample value against the acceptance contract.',
                     'acceptance_paths': ['tests'],
                     'checks': [{'id': 'value', 'description': 'Value must be two.',
                                 'argv': [sys.executable, '-c', 'import app; assert app.value == 2'],
                                 'timeout_seconds': 5}]}
        self.plan_path = self.base / 'plan.json'
        self.save_plan()

    def save_plan(self):
        self.plan_path.write_text(json.dumps(self.plan))

    def run_report(self, name):
        path = self.base / name
        report, code = tk.run(self.project, self.plan_path, path)
        return path, report, code

    def test_failed_check_recovers_only_after_source_fix(self):
        before, failed, code = self.run_report('before.json')
        self.assertEqual(code, 1)
        self.assertEqual(failed['results'][0]['status'], 'failed')
        (self.project / 'app.py').write_text('value = 2\n')
        after, passed, code = self.run_report('after.json')
        self.assertEqual(code, 0)
        result, code = tk.compare(before, after, self.base / 'comparison.json')
        self.assertEqual(code, 0)
        self.assertEqual(result['recovered_checks'], ['value'])
        self.assertEqual(result['changed_files'], ['app.py'])
        self.assertFalse(result['acceptance_changed'])

    def test_changed_acceptance_prevents_claimed_recovery(self):
        before, _, _ = self.run_report('before.json')
        (self.project / 'app.py').write_text('value = 2\n')
        (self.project / 'tests/test_app.py').write_text('# weakened acceptance\n')
        after, _, _ = self.run_report('after.json')
        result, code = tk.compare(before, after, self.base / 'comparison.json')
        self.assertEqual(code, 1)
        self.assertEqual(result['verdict'], 'criteria-changed')
        self.assertEqual(result['recovered_checks'], [])

    def test_regression_reported(self):
        (self.project / 'app.py').write_text('value = 2\n')
        before, _, _ = self.run_report('before.json')
        (self.project / 'app.py').write_text('value = 1\n')
        after, _, _ = self.run_report('after.json')
        report, code = tk.compare(before, after, self.base / 'diff.json')
        self.assertEqual(code, 1)
        self.assertEqual(report['regressed_checks'], ['value'])

    def test_changed_plan_rejected(self):
        before, _, _ = self.run_report('before.json')
        self.plan['checks'][0]['argv'] = [sys.executable, '-c', 'pass']
        self.save_plan()
        after, _, _ = self.run_report('after.json')
        with self.assertRaisesRegex(ValueError, 'plans differ'):
            tk.compare(before, after, self.base / 'diff.json')
        self.assertFalse((self.base / 'diff.json').exists())

    def test_changed_runner_rejected(self):
        before, _, _ = self.run_report('before.json')
        after, report, _ = self.run_report('after.json')
        report['tool']['runner_sha256'] = '0' * 64
        after.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'runner versions differ'):
            tk.compare(before, after, self.base / 'diff.json')

    def test_execution_error_is_not_a_confirmed_recovered_failure(self):
        before, report, _ = self.run_report('before.json')
        report['results'][0].update(status='error', exit_code=None)
        before.write_text(json.dumps(report))
        (self.project / 'app.py').write_text('value = 2\n')
        after, _, _ = self.run_report('after.json')
        result, code = tk.compare(before, after, self.base / 'diff.json')
        self.assertEqual(code, 0)
        self.assertEqual(result['recovered_checks'], [])
        self.assertEqual(result['previously_unverified_checks_now_passing'], ['value'])

    def test_source_change_during_checks_blocks_comparison(self):
        self.plan['checks'][0]['argv'] = [sys.executable, '-c', "open('app.py','a').write('# changed\\n')"]
        self.save_plan()
        before, report, code = self.run_report('before.json')
        self.assertEqual(code, 1)
        self.assertFalse(report['evidence_stable'])
        with self.assertRaisesRegex(ValueError, 'changed during checks'):
            tk.compare(before, before, self.base / 'diff.json')

    def test_secret_files_and_symlinks_not_read(self):
        (self.project / '.env').write_text('FAKE_SECRET=do-not-capture\n')
        (self.project / '.env.example').write_text('also excluded\n')
        (self.project / '.aws').mkdir()
        (self.project / '.aws/credentials').write_text('synthetic-only\n')
        outside = self.base / 'outside.py'
        outside.write_text('never inventory outside project\n')
        (self.project / 'escape.py').symlink_to(outside)
        evidence = tk.snapshot(self.project)
        self.assertNotIn('.env', evidence['files'])
        self.assertNotIn('.env.example', evidence['files'])
        self.assertNotIn('.aws/credentials', evidence['files'])
        self.assertNotIn('escape.py', evidence['files'])
        self.assertFalse(evidence['complete'])
        self.assertNotIn('do-not-capture', json.dumps(evidence))

    def test_inventory_limits_are_disclosed(self):
        with patch.object(tk, 'MAX_FILES', 1):
            evidence = tk.snapshot(self.project)
        self.assertFalse(evidence['complete'])
        self.assertEqual(len(evidence['files']), 1)

    def test_unreadable_directory_is_disclosed(self):
        scan = os.scandir
        def denied(path):
            if Path(path) == self.project / 'tests':
                raise PermissionError(errno.EACCES, 'synthetic denied directory', str(path))
            return scan(path)
        with patch.object(os, 'scandir', side_effect=denied):
            evidence = tk.snapshot(self.project)
        self.assertFalse(evidence['complete'])
        self.assertTrue(any(x['reason'] == 'unreadable directory' for x in evidence['omissions']))

    def test_fifo_is_not_read_and_reports_are_private(self):
        fifo = self.project / 'pipe.json'
        os.mkfifo(fifo)
        evidence = tk.snapshot(self.project)
        self.assertFalse(evidence['complete'])
        with self.assertRaises(ValueError):
            tk.read_json(fifo)
        fifo.unlink()
        path, _, _ = self.run_report('private.json')
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_incomplete_evidence_cannot_claim_pass(self):
        (self.project / 'unread.py').symlink_to(self.base / 'missing')
        self.plan['checks'][0]['argv'] = [sys.executable, '-c', 'pass']
        self.save_plan()
        path, report, code = self.run_report('incomplete.json')
        self.assertEqual(code, 1)
        self.assertEqual(report['results'][0]['status'], 'passed')
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            tk.compare(path, path, self.base / 'diff.json')

    def test_invalid_plans_fail_before_execution(self):
        for change in ('empty', 'traversal', 'boolean_timeout', 'unknown'):
            plan = copy.deepcopy(self.plan)
            if change == 'empty': plan['checks'] = []
            elif change == 'traversal': plan['acceptance_paths'] = ['../outside']
            elif change == 'boolean_timeout': plan['checks'][0]['timeout_seconds'] = True
            else: plan['force'] = True
            self.plan_path.write_text(json.dumps(plan))
            with self.subTest(change=change), patch.object(tk, 'execute') as execute:
                with self.assertRaises(ValueError):
                    tk.run(self.project, self.plan_path, self.base / 'invalid.json')
                execute.assert_not_called()

    def test_missing_acceptance_path_refused(self):
        self.plan['acceptance_paths'] = ['missing-test.py']
        self.save_plan()
        with self.assertRaisesRegex(ValueError, 'acceptance path'):
            self.run_report('missing.json')

    def test_output_inside_project_and_symlink_output_refused(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            tk.run(self.project, self.plan_path, self.project / 'report.json')
        alias = self.base / 'alias'
        alias.symlink_to(self.project, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            tk.run(self.project, self.plan_path, alias / 'report.json')
        self.assertFalse((self.project / 'report.json').exists())

    def test_existing_report_preserved_without_execution(self):
        output = self.base / 'existing.json'
        output.write_text('keep')
        with patch.object(tk, 'execute') as execute:
            with self.assertRaises(ValueError):
                tk.run(self.project, self.plan_path, output)
            execute.assert_not_called()
        self.assertEqual(output.read_text(), 'keep')

    def test_timeout_and_bounded_output(self):
        check = dict(self.plan['checks'][0], argv=[sys.executable, '-c', 'import time; time.sleep(8)'], timeout_seconds=1)
        result = tk.execute(check, self.project)
        self.assertEqual(result['status'], 'timeout')
        self.assertLess(result['duration_seconds'], 4)
        check['argv'] = [sys.executable, '-c', "print('x'*200000)"]
        check['timeout_seconds'] = 5
        result = tk.execute(check, self.project)
        self.assertEqual(result['status'], 'passed')
        self.assertTrue(result['output_truncated'])
        self.assertLessEqual(len(result['output'].encode()), tk.MAX_LOG)

    def test_redaction_and_environment_allowlist(self):
        text = str(self.project) + ' /Users/example/private token=sample-value ghp_' + 'a' * 30
        redacted = tk.redact(text, self.project)
        self.assertNotIn(str(self.project), redacted)
        self.assertNotIn('/Users/example', redacted)
        self.assertNotIn('sample-value', redacted)
        self.assertNotIn('ghp_', redacted)
        check = dict(self.plan['checks'][0], argv=[sys.executable, '-c', "import os; assert 'TAKEOVER_FAKE_CREDENTIAL' not in os.environ"])
        with patch.dict(os.environ, {'TAKEOVER_FAKE_CREDENTIAL': 'synthetic-only'}):
            self.assertEqual(tk.execute(check, self.project)['status'], 'passed')

    def test_missing_program_is_unverified_not_passed(self):
        check = dict(self.plan['checks'][0], argv=['takeover-nonexistent-program-abc'])
        self.assertEqual(tk.execute(check, self.project)['status'], 'error')

    def test_empty_unittest_discovery_is_unverified(self):
        check = dict(self.plan['checks'][0], argv=[sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'])
        result = tk.execute(check, self.project)
        self.assertIsInstance(result['exit_code'], int)
        self.assertEqual(result['status'], 'error')
        self.assertIn('No unittest tests were discovered', result['output'])

    def test_report_missing_results_and_inconsistent_exit_rejected(self):
        (self.project / 'app.py').write_text('value = 2\n')
        _, report, _ = self.run_report('valid.json')
        for mutation in ('missing', 'bad_exit', 'source', 'bad_status'):
            changed = copy.deepcopy(report)
            if mutation == 'missing': changed['results'] = []
            elif mutation == 'bad_exit': changed['results'][0]['exit_code'] = 1
            elif mutation == 'source': changed['source']['files']['app.py'] = '0' * 64
            else: changed['results'][0]['status'] = []
            path = self.base / f'{mutation}.json'
            path.write_text(json.dumps(changed))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                tk.checked_report(path)

    def test_init_does_not_execute_and_detects_defined_scripts_only(self):
        (self.project / 'package.json').write_text(json.dumps({'scripts': {'build': 'echo example'}}))
        with patch.object(tk, 'execute') as execute:
            summary = tk.init(self.project, self.base / 'init.json')
            execute.assert_not_called()
        plan = json.loads((self.base / 'init.json').read_text())
        self.assertEqual([c['id'] for c in plan['checks']], ['tests', 'build'])
        self.assertEqual(summary['suggested_checks'], 2)

    def test_cli_init_run_compare_and_errors(self):
        def cli(*args):
            return subprocess.run([sys.executable, '-m', 'agent_team', 'takeover', *args],
                                  cwd=ROOT, text=True, capture_output=True)
        initialized = cli('init', '--project', str(self.project), '--output', str(self.base / 'suggested.json'))
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        before, after, diff = (self.base / name for name in ('cli-before.json', 'cli-after.json', 'cli-diff.json'))
        command = ['run', '--project', str(self.project), '--plan', str(self.plan_path)]
        self.assertEqual(cli(*command, '--output', str(before)).returncode, 1)
        (self.project / 'app.py').write_text('value = 2\n')
        self.assertEqual(cli(*command, '--output', str(after)).returncode, 0)
        compared = cli('compare', '--before', str(before), '--after', str(after), '--output', str(diff))
        self.assertEqual(compared.returncode, 0, compared.stderr)
        repeated = cli(*command, '--output', str(before))
        self.assertEqual(repeated.returncode, 2)
        self.assertNotIn('Traceback', repeated.stderr)


if __name__ == '__main__':
    unittest.main()
