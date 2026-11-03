"""Reproduce failure -> minimal code fix -> unchanged acceptance checks pass."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New scratch directory for synthetic demo artifacts')
    args = parser.parse_args()
    output = Path(args.output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        parser.error('output must be a new scratch directory')
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('choose a directory outside the Kit source tree')
    output.mkdir(parents=True)
    project = output / 'project'
    shutil.copytree(ROOT / 'examples/takeover_demo', project,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    tests = project / 'tests/test_persistence.py'
    criteria_before = hashlib.sha256(tests.read_bytes()).hexdigest()
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')

    def cli(arguments, expected):
        result = subprocess.run([sys.executable, '-m', 'agent_team', 'takeover', *arguments],
                                cwd=ROOT, env=environment, text=True, capture_output=True)
        if result.returncode != expected:
            raise RuntimeError(f'Unexpected CLI exit code {result.returncode}: {result.stderr}')
        return json.loads(result.stdout)

    plan = output / 'plan.json'
    cli(['init', '--project', str(project), '--output', str(plan)], 0)
    data = json.loads(plan.read_text())
    data['name'] = 'synthetic-persistence-demo'
    data['scope'] = 'WSGI POST/GET persistence across application instances; invalid title and unknown route.'
    plan.write_text(json.dumps(data, indent=2) + '\n')
    command = ['run', '--project', str(project), '--plan', str(plan)]
    cli([*command, '--output', str(output / 'before.json')], 1)
    app = project / 'app.py'
    text = app.read_text()
    marker = '                    # Intentional fixture defect: the successful write is never persisted.'
    if text.count(marker) != 1:
        raise RuntimeError('Fixture changed; inspect the fix rather than applying it blindly')
    app.write_text(text.replace(marker, '                    storage.write_text(json.dumps(items))'))
    cli([*command, '--output', str(output / 'after.json')], 0)
    summary = cli(['compare', '--before', str(output / 'before.json'), '--after', str(output / 'after.json'),
                   '--output', str(output / 'comparison.json')], 0)
    if hashlib.sha256(tests.read_bytes()).hexdigest() != criteria_before:
        raise RuntimeError('Acceptance tests changed during the demo')
    comparison = json.loads((output / 'comparison.json').read_text())
    if comparison['changed_files'] != ['app.py'] or comparison['recovered_checks'] != ['tests']:
        raise RuntimeError('Unexpected evidence; review the artifacts')
    print(json.dumps({'demo': 'synthetic WSGI persistence', 'acceptance_tests_unchanged': True,
                      'changed_files': comparison['changed_files'], **summary}, indent=2))


if __name__ == '__main__':
    main()
