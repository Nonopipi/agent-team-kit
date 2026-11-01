import copy
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.spec = {
            'schema_version': 1,
            'modified_date': '2026-11-01',
            'codex': {'enabled': True, 'max_concurrent_threads_per_session': 1},
            'agents': [{'name': 'test_writer', 'description': 'Review: "quotes" and Unicode →',
                        'instructions': 'Read AGENTS.md.\nKeep \\n literal; quote """ safely.\n'}],
        }

    def tearDown(self):
        self.temp.cleanup()

    def core(self):
        from agent_team import core
        return core

    def test_native_formats_round_trip_without_prompt_loss(self):
        core = self.core()
        files = core.render(self.spec)
        codex = tomllib.loads(files['.codex/agents/test_writer.toml'])
        self.assertEqual(codex['developer_instructions'], self.spec['agents'][0]['instructions'])
        text = files['.claude/agents/test-writer.md']
        self.assertTrue(text.startswith('---\n'))
        header = text.split('---\n', 2)[1]
        fields = {k: json.loads(v.strip()) for k, v in (line.split(':', 1) for line in header.splitlines())}
        self.assertEqual(fields, {'name': 'test-writer', 'description': self.spec['agents'][0]['description']})
        self.assertTrue(text.endswith(self.spec['agents'][0]['instructions']))
        self.assertIn('@AGENTS.md', files['CLAUDE.md'])
        self.assertIn('test_writer', files['CLAUDE.md'])

    def test_unknown_fields_and_invalid_types_are_rejected(self):
        mutations = [lambda s: s.update(model='unexpected'),
                     lambda s: s.update(schema_version=True),
                     lambda s: s.update(modified_date='2026-99-99'),
                     lambda s: s['codex'].update(max_concurrent_threads_per_session=True),
                     lambda s: s['codex'].update(sandbox_mode='danger-full-access'),
                     lambda s: s['agents'][0].update(permissionMode='bypassPermissions'),
                     lambda s: s['agents'][0].update(instructions='  '),
                     lambda s: s['agents'][0].update(instructions='bad\x00text')]
        for mutate in mutations:
            spec = copy.deepcopy(self.spec)
            mutate(spec)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                self.core().render(spec)

    def test_path_traversal_duplicate_and_client_collision_rejected(self):
        for name in ['../outside', '/absolute', 'bad/name', 'bad:name']:
            spec = copy.deepcopy(self.spec)
            spec['agents'][0]['name'] = name
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.core().render(spec)
        for name in ['test_writer', 'test-writer']:
            spec = copy.deepcopy(self.spec)
            spec['agents'].append(dict(spec['agents'][0], name=name))
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.core().render(spec)

    def test_generation_is_deterministic_and_preserves_project_rules(self):
        core = self.core()
        self.root.joinpath('AGENTS.md').write_text('Existing project guidance\n')
        files = core.render(self.spec)
        core.generate(self.root, files)
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        core.generate(self.root, files)
        after = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(self.root.joinpath('AGENTS.md').read_text(), 'Existing project guidance\n')
        self.assertEqual(core.check(self.root, files), [])

    def test_unmanaged_conflict_refuses_all_writes(self):
        core = self.core()
        self.root.joinpath('CLAUDE.md').write_text('User-owned guidance')
        self.root.joinpath('keep.txt').write_text('keep')
        with self.assertRaises(ValueError):
            core.generate(self.root, core.render(self.spec))
        self.assertFalse(self.root.joinpath('.codex').exists())
        self.assertFalse(self.root.joinpath('.agent-team-generated.json').exists())
        self.assertEqual(self.root.joinpath('keep.txt').read_text(), 'keep')

    def test_drift_detected_and_not_overwritten(self):
        core = self.core()
        files = core.render(self.spec)
        core.generate(self.root, files)
        edited = self.root / '.claude/agents/test-writer.md'
        edited.write_text(edited.read_text() + 'Manual change\n')
        self.assertTrue(any('test-writer.md' in issue for issue in core.check(self.root, files)))
        with self.assertRaises(ValueError):
            core.generate(self.root, files)
        self.assertTrue(edited.read_text().endswith('Manual change\n'))

    def test_changed_source_updates_unedited_managed_files(self):
        core = self.core()
        core.generate(self.root, core.render(self.spec))
        self.spec['agents'][0]['instructions'] = 'Updated instruction\n'
        files = core.render(self.spec)
        self.assertTrue(core.check(self.root, files))
        core.generate(self.root, files)
        self.assertEqual(core.check(self.root, files), [])
        parsed = tomllib.loads((self.root / '.codex/agents/test_writer.toml').read_text())
        self.assertEqual(parsed['developer_instructions'], 'Updated instruction\n')

    def test_symlink_parent_or_guidance_cannot_escape_output(self):
        core = self.core()
        outside = self.root / 'outside'
        outside.mkdir()
        output = self.root / 'project'
        output.mkdir()
        (output / '.codex').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            core.generate(output, core.render(self.spec))
        self.assertEqual(list(outside.iterdir()), [])
        (output / '.codex').unlink()
        target = outside / 'rules.md'
        target.write_text('Private unrelated rules')
        (output / 'AGENTS.md').symlink_to(target)
        with self.assertRaises(ValueError):
            core.generate(output, core.render(self.spec))
        self.assertEqual(target.read_text(), 'Private unrelated rules')

    def test_unsafe_manifest_and_removed_roles_refused(self):
        core = self.core()
        manifest = self.root / '.agent-team-generated.json'
        manifest.write_text(json.dumps({'schema_version': 1, 'files': {'../outside': '0' * 64}}))
        with self.assertRaises(ValueError):
            core.generate(self.root, core.render(self.spec))
        manifest.unlink()
        core.generate(self.root, core.render(self.spec))
        changed = copy.deepcopy(self.spec)
        changed['agents'][0]['name'] = 'other_role'
        with self.assertRaises(ValueError):
            core.generate(self.root, core.render(changed))
        self.assertTrue((self.root / '.claude/agents/test-writer.md').exists())

    def test_cli_rejects_invalid_spec_without_traceback_or_output(self):
        spec = self.root / 'bad.toml'
        spec.write_text('schema_version = 1\nunknown = true\n')
        output = self.root / 'output'
        run = subprocess.run([sys.executable, '-m', 'agent_team', 'generate', '--spec', str(spec), '--output', str(output)],
                             cwd=ROOT, text=True, capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('error:', run.stderr.lower())
        self.assertNotIn('Traceback', run.stderr)
        self.assertFalse(output.exists())

    def test_repository_spec_contains_all_nine_roles(self):
        core = self.core()
        spec = core.load_spec(ROOT / 'team.toml')
        self.assertEqual(len(spec['agents']), 9)
        self.assertEqual(len(core.render(spec)), 20)

    def test_oversized_source_rejected(self):
        path = self.root / 'oversized.toml'
        path.write_bytes(b'#' + b'x' * (1024 * 1024))
        with self.assertRaisesRegex(ValueError, 'size limit'):
            self.core().load_spec(path)

    def test_cli_generate_check_and_drift_end_to_end(self):
        output = self.root / 'generated'
        base = [sys.executable, '-m', 'agent_team']
        options = ['--spec', str(ROOT / 'team.toml'), '--output', str(output)]
        created = subprocess.run(base + ['generate'] + options, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(created.returncode, 0, created.stderr)
        verified = subprocess.run(base + ['check'] + options, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertEqual(len(list((output / '.claude/agents').glob('*.md'))), 9)
        edited = output / '.codex/config.toml'
        edited.write_text(edited.read_text() + '# drift\n')
        failed = subprocess.run(base + ['check'] + options, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(failed.returncode, 1)
        self.assertIn('.codex/config.toml', failed.stderr)
        refused = subprocess.run(base + ['generate'] + options, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(refused.returncode, 2)
        self.assertTrue(edited.read_text().endswith('# drift\n'))


if __name__ == '__main__':
    unittest.main()
