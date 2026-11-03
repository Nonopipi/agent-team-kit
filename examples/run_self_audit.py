"""Replay actual Kit review defects on an isolated copy, with unchanged tests."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent_team import takeover


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New directory outside the Kit for the isolated case')
    args = parser.parse_args()
    output = takeover.output_path(args.output, ROOT)
    started = time.monotonic()
    output.mkdir()
    project = output / 'project'; project.mkdir()
    source_files = sorted([*ROOT.glob('agent_team/*.py'), *ROOT.glob('agent_team/templates/*.md'),
                           *ROOT.glob('tests/*.py'), ROOT / 'team.toml', ROOT / 'LICENSE', ROOT / 'NOTICE.md'])
    for source in source_files:
        if source.is_symlink() or not source.is_file():
            raise ValueError('unexpected source type in Kit reconstruction')
        target = project / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    baseline = json.loads((ROOT / 'examples/self_audit/baseline_sources.json').read_text())
    expected = {'agent_team/core.py', 'agent_team/takeover.py', 'agent_team/__init__.py'}
    if set(baseline['files']) != expected:
        raise ValueError('unexpected historical module list')
    for name, item in baseline['files'].items():
        if takeover.digest(item['content'].encode()) != item['sha256']:
            raise ValueError('historical module digest mismatch')
        (project / name).write_text(item['content'])
    criteria = {p.relative_to(project).as_posix(): takeover.digest(p.read_bytes())
                for p in (project / 'tests').glob('*.py')}
    checks = []
    for name, filename in (('review-regressions', 'test_review_regressions.py'),
                            ('existing-generator', 'test_generator.py'),
                            ('existing-takeover', 'test_takeover.py')):
        checks.append({'id': name, 'description': f'Run unchanged acceptance module {filename}.',
                       'argv': ['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-p', filename, '-v'],
                       'timeout_seconds': 60})
    plan = {'schema_version': 1, 'kind': 'takeover-plan', 'name': 'agent-team-kit-self-audit',
            'scope': 'Actual Kit defects: skipped tests, credential redaction, malformed evidence, symlink paths, nonregular inputs, extra native definitions; retain existing behavior.',
            'acceptance_paths': ['tests', 'team.toml'], 'checks': checks}
    plan_path = output / 'plan.json'; takeover.write_json(plan_path, plan)
    before, before_code = takeover.run(project, plan_path, output / 'before.json')
    if before_code != 1 or before['results'][0]['status'] != 'failed':
        raise ValueError('historical defects did not reproduce; inspect evidence')
    if any(r['status'] != 'passed' for r in before['results'][1:]):
        raise ValueError('pre-existing checks failed unexpectedly; inspect baseline/environment')
    for name in sorted(expected):
        shutil.copyfile(ROOT / name, project / name)
    after, after_code = takeover.run(project, plan_path, output / 'after.json')
    if after_code != 0:
        raise ValueError('fixed copy failed acceptance; inspect evidence')
    comparison, compare_code = takeover.compare(output / 'before.json', output / 'after.json', output / 'comparison.json')
    if compare_code or set(comparison['changed_files']) != expected or comparison['acceptance_changed']:
        raise ValueError('unexpected changes or invalid comparison')
    if criteria != {p.relative_to(project).as_posix(): takeover.digest(p.read_bytes())
                    for p in (project / 'tests').glob('*.py')}:
        raise ValueError('acceptance tests changed')
    costs = {'before_check_seconds': round(sum(r['duration_seconds'] for r in before['results']), 4),
             'after_check_seconds': round(sum(r['duration_seconds'] for r in after['results']), 4),
             'case_wall_seconds': round(time.monotonic() - started, 4),
             'model_calls_started_by_case': 0, 'host_assistant_tokens': None, 'monetary_cost': None,
             'limits': 'Local Python commands only. Host assistant usage/billing is unavailable. This single run is not a general speed or token benchmark.'}
    takeover.write_json(output / 'costs.json', costs)
    summary = {'case': 'Actual Kit defects, self-audit; not an external app/customer validation',
               'before': [{'id': r['id'], 'status': r['status'], 'tests': r.get('test_summary')} for r in before['results']],
               'after': [{'id': r['id'], 'status': r['status'], 'tests': r.get('test_summary')} for r in after['results']],
               'acceptance_tests_unchanged': True, 'changed_files': comparison['changed_files'], 'costs': costs}
    takeover.write_json(output / 'summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
