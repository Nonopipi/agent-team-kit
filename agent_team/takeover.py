"""Local, version-bound acceptance evidence for taking over trusted projects.

AGPL-3.0. Runs explicit check commands; does not sandbox or repair project code.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import time
from datetime import datetime, timezone

from . import __version__

MAX_FILES = 3000
MAX_FILE = 1024 * 1024
MAX_TOTAL = 24 * MAX_FILE
MAX_LOG = 32 * 1024
SKIP = {'.git', '.hg', '.svn', 'node_modules', '.venv', 'venv', '__pycache__',
        '.next', 'dist', 'build', 'coverage', '.pytest_cache', '.mypy_cache',
        '.ssh', '.aws', '.gnupg', '.kube', '.config', '.codex', '.claude', '.agents'}
STATUSES = {'passed', 'failed', 'timeout', 'error'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def project_root(path):
    path = Path(path).expanduser().absolute()
    if path.is_symlink() or not path.is_dir():
        raise ValueError('project must be an existing directory, not a symlink')
    return path.resolve()


def secret_name(name):
    lower = name.lower()
    return (lower.startswith('.env') or lower in {'auth.json', 'credentials', 'credentials.json',
            'id_rsa', 'id_ed25519', '.npmrc', '.pypirc', '.netrc'}
            or lower.endswith(('.pem', '.key', '.p12', '.pfx')))


def relative_path(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('acceptance paths must be relative POSIX paths')
    parts = value.split('/')
    if value.startswith('/') or any(p in {'', '.', '..'} or secret_name(p) for p in parts):
        raise ValueError('unsafe acceptance path')
    return value


def snapshot(root):
    """Hash regular source files. Exclusions and omissions remain visible."""
    files, omissions, total = {}, [], 0

    def finish():
        return {'digest': digest(canonical(files)), 'files': files,
                'complete': not omissions, 'omissions': omissions,
                'excluded': sorted(SKIP), 'secret_files_excluded': True}

    def unreadable(error):
        try:
            name = Path(error.filename).relative_to(root).as_posix()
        except (TypeError, ValueError):
            name = '<directory>'
        omissions.append({'path': name, 'reason': 'unreadable directory'})

    for index, (folder, dirs, names) in enumerate(os.walk(root, followlinks=False, onerror=unreadable)):
        if index >= MAX_FILES:
            omissions.append({'path': '<remaining>', 'reason': 'directory limit'})
            return finish()
        folder = Path(folder)
        kept = []
        for name in sorted(dirs):
            path = folder / name
            if name in SKIP or secret_name(name):
                continue
            if path.is_symlink():
                omissions.append({'path': path.relative_to(root).as_posix(), 'reason': 'symlink'})
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            if name == '.DS_Store' or secret_name(name) or name.endswith(('.pyc', '.log', '.tmp')):
                continue
            path = folder / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                omissions.append({'path': relative, 'reason': 'symlink'})
                continue
            if len(files) >= MAX_FILES or total >= MAX_TOTAL:
                omissions.append({'path': '<remaining>', 'reason': 'inventory limit'})
                return finish()
            try:
                flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
                fd = os.open(path, flags)
                with os.fdopen(fd, 'rb') as stream:
                    before = os.fstat(stream.fileno())
                    if not stat.S_ISREG(before.st_mode):
                        omissions.append({'path': relative, 'reason': 'not a regular file'})
                        continue
                    if before.st_size > MAX_FILE:
                        omissions.append({'path': relative, 'reason': 'file size limit'})
                        continue
                    data = stream.read(MAX_FILE + 1)
                    after = os.fstat(stream.fileno())
                if len(data) > MAX_FILE or total + len(data) > MAX_TOTAL:
                    omissions.append({'path': relative, 'reason': 'size limit'})
                    continue
                if (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size):
                    omissions.append({'path': relative, 'reason': 'changed while reading'})
                    continue
                files[relative] = digest(data)
                total += len(data)
            except OSError:
                omissions.append({'path': relative, 'reason': 'unreadable'})
    return finish()


def read_json(path):
    path = Path(path)
    if secret_name(path.name) or path.is_symlink() or not path.is_file():
        raise ValueError('input must be a regular JSON file of at most 4 MiB')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('JSON input is not a regular file')
        data = stream.read(4 * MAX_FILE + 1)
    if len(data) > 4 * MAX_FILE:
        raise ValueError('JSON input exceeds 4 MiB')
    return json.loads(data.decode('utf-8'))


def output_path(path, root=None):
    path = Path(path).expanduser().absolute()
    system_aliases = {'/tmp': '/private/tmp', '/var': '/private/var'}
    if any(p.is_symlink() and system_aliases.get(str(p)) != str(p.resolve())
           for p in (path, *path.parents)):
        raise ValueError('output symlinks are not allowed')
    path = path.resolve()
    if path.exists():
        raise ValueError('output already exists; choose a new file')
    if root is not None and (path == root or root in path.parents):
        raise ValueError('write evidence outside the target project')
    if not path.parent.is_dir():
        raise ValueError('output parent directory must already exist')
    return path


def write_json(path, value):
    # Exclusive creation also prevents accidental replacement after preflight.
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n'
    if len(text.encode('utf-8')) > 4 * MAX_FILE:
        raise ValueError('evidence exceeds 4 MiB; narrow the scope')
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        stream.write(text)


def checked_plan(plan):
    fields = {'schema_version', 'kind', 'name', 'scope', 'acceptance_paths', 'checks'}
    if not isinstance(plan, dict) or set(plan) != fields or type(plan['schema_version']) is not int:
        raise ValueError('invalid plan fields')
    if plan['schema_version'] != 1 or plan['kind'] != 'takeover-plan':
        raise ValueError('unsupported plan')
    for field in ('name', 'scope'):
        if not isinstance(plan[field], str) or not plan[field].strip() or len(plan[field]) > 2000:
            raise ValueError(f'plan {field} must be non-empty text')
    paths = plan['acceptance_paths']
    if not isinstance(paths, list) or not paths or len(paths) > 64:
        raise ValueError('declare 1-64 acceptance files or directories')
    for path in paths:
        relative_path(path)
    if not isinstance(plan['checks'], list) or not 1 <= len(plan['checks']) <= 20:
        raise ValueError('configure 1-20 checks before running')
    names = set()
    for check in plan['checks']:
        if not isinstance(check, dict) or set(check) != {'id', 'description', 'argv', 'timeout_seconds'}:
            raise ValueError('invalid check fields')
        name = check['id']
        if not isinstance(name, str) or not re.fullmatch('[a-z][a-z0-9_-]{0,63}', name) or name in names:
            raise ValueError('check IDs must be safe and unique')
        names.add(name)
        if not isinstance(check['description'], str) or not check['description'].strip():
            raise ValueError('check description is required')
        argv = check['argv']
        if not isinstance(argv, list) or not 1 <= len(argv) <= 64 or any(
                not isinstance(a, str) or not a or len(a) > 4096 or any(ord(c) < 32 for c in a) for a in argv):
            raise ValueError('argv must be a non-empty list of arguments without control characters')
        timeout = check['timeout_seconds']
        if type(timeout) is not int or not 1 <= timeout <= 120:
            raise ValueError('check timeout must be an integer from 1 to 120 seconds')
    return plan


def init(project, output):
    root = project_root(project)
    target = output_path(output, root)
    source = snapshot(root)
    checks, paths = [], []
    # Suggestions are never executed by initialization.
    if any(p.startswith('tests/') and p.endswith('.py') for p in source['files']):
        paths.append('tests')
        checks.append({'id': 'tests', 'description': 'Existing Python unittest checks; review their coverage.',
                       'argv': ['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                       'timeout_seconds': 60})
    if 'package.json' in source['files']:
        package = read_json(root / 'package.json')
        scripts = package.get('scripts', {}) if isinstance(package, dict) else {}
        if isinstance(scripts, dict):
            for name in ('test', 'lint', 'build'):
                if isinstance(scripts.get(name), str) and scripts[name].strip():
                    checks.append({'id': name, 'description': f'Existing npm {name} script; review it before execution.',
                                   'argv': ['npm', 'run', name], 'timeout_seconds': 60})
        paths.append('package.json')
    plan = {'schema_version': 1, 'kind': 'takeover-plan', 'name': 'local-project',
            'scope': 'Review this scope and add the expected user-visible behavior before running.',
            'acceptance_paths': paths, 'checks': checks}
    write_json(target, plan)
    return {'suggested_checks': len(checks), 'source_complete': source['complete'],
            'source_digest': source['digest'], 'note': 'Review commands, acceptance paths and coverage. No project code ran.'}


def redact(text, root):
    text = text.replace(str(root), '<project>')
    text = re.sub(r'/(?:Users|home)/[^/\s\"\']+', '<home>', text)
    text = re.sub(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b', '<redacted-token>', text)
    keys = r'(?:api[_-]?key|(?:access[_-]?|refresh[_-]?)?token|password|passwd|secret|(?:proxy-)?authorization)'
    # Quoted JSON/configuration keys and values, including escaped characters.
    # Redact the whole quoted value before processing unquoted log assignments.
    quoted = rf'''(?ix)(["']?\b{keys}\b["']?\s*[:=]\s*)("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')'''
    def quoted_value(match):
        quote = match.group(2)[0]
        return match.group(1) + quote + '<redacted>' + quote
    text = re.sub(quoted, quoted_value, text)
    # Consume the authentication scheme with its credential; do not merely
    # replace "Bearer"/"Basic" and leave the actual value behind.
    authorization = r'(?im)(\b(?:proxy-)?authorization\b\s*[:=]\s*)(?:(?:Bearer|Basic)\s+)?[^\s,;\r\n]+'
    text = re.sub(authorization, r'\1<redacted>', text)
    assignment = rf'(?im)(\b{keys}\b\s*[:=]\s*)[^\s,;\r\n]+'
    text = re.sub(assignment, r'\1<redacted>', text)
    # Avoid terminal escapes becoming executable control sequences in reports.
    return ''.join(c if c in '\n\r\t' or ord(c) >= 32 and ord(c) != 127 else '?' for c in text)


def _unittest_command(argv):
    arguments = argv[1:]
    return any(arguments[i:i + 2] == ['-m', 'unittest'] for i in range(len(arguments)))


def _unittest_summary(output):
    counts = re.findall(r'(?m)^Ran (\d+) tests? in ', output)
    endings = re.findall(r'(?m)^(?:OK|FAILED)(?: \(([^\n]*)\))?\s*$', output)
    if not counts or not endings and int(counts[-1]) != 0:
        return None
    count = int(counts[-1])
    skipped = re.search(r'\bskipped=(\d+)\b', endings[-1]) if endings else None
    skipped = int(skipped.group(1)) if skipped else 0
    return {'framework': 'unittest', 'discovered': count, 'skipped': skipped,
            'executed': max(0, count - skipped)}


def execute(check, root):
    if os.name != 'posix':
        raise ValueError('command execution currently supports POSIX systems only')
    started = time.monotonic()
    result = {'id': check['id'], 'status': 'error', 'exit_code': None,
              'duration_seconds': 0.0, 'output': '', 'output_truncated': False}
    environment = {k: v for k, v in os.environ.items()
                   if k in {'PATH', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TMPDIR', 'TMP', 'TEMP'}}
    environment.update({'PYTHONDONTWRITEBYTECODE': '1', 'CI': '1'})
    command = check['argv'][0]
    if '/' in command:
        candidate = Path(command)
        if not candidate.is_absolute():
            candidate = root / candidate
        executable = str(candidate) if candidate.is_file() and os.access(candidate, os.X_OK) else None
    else:
        executable = shutil.which(command, path=environment.get('PATH', os.defpath))
    if executable is None:
        result['output'] = 'Executable was not found. Install/setup is a separate step.'
        return result
    chunks, count, timed_out = bytearray(), 0, False
    proc = subprocess.Popen([executable, *check['argv'][1:]], cwd=root, env=environment,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, start_new_session=True)
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout, selectors.EVENT_READ)
            deadline = started + check['timeout_seconds']
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    break
                for key, _ in selector.select(min(remaining, 0.1)):
                    data = os.read(key.fileobj.fileno(), 8192)
                    if not data:
                        selector.unregister(key.fileobj)
                    else:
                        count += len(data)
                        chunks.extend(data[:max(0, MAX_LOG - len(chunks))])
            if not timed_out:
                try:
                    proc.wait(timeout=max(0.001, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    timed_out = True
    finally:
        # Kill only this check's process group, including surviving descendants.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        proc.stdout.close()
    result.update(status='timeout' if timed_out else 'passed' if proc.returncode == 0 else 'failed',
                  exit_code=proc.returncode, duration_seconds=round(time.monotonic() - started, 4),
                  output=redact(chunks.decode('utf-8', errors='replace'), root),
                  output_truncated=count > MAX_LOG)
    if result['status'] in {'passed', 'failed'} and _unittest_command(check['argv']):
        summary = _unittest_summary(result['output'])
        if summary is not None:
            result['test_summary'] = summary
            if summary['executed'] == 0:
                result['status'] = 'error'
                result['output'] += ('\nNo unittest tests were discovered; execution is unverified.\n' if summary['discovered'] == 0
                                     else '\nAll unittest tests were skipped; execution is unverified.\n')
        elif result['status'] == 'passed':
            result['status'] = 'error'
            result['output'] += '\nUnittest execution summary was not captured; execution is unverified.\n'
    return result


def acceptance_files(source, paths):
    return {name: sha for name, sha in source['files'].items()
            if any(name == path or name.startswith(path + '/') for path in paths)}


def run(project, plan_path, output):
    root = project_root(project)
    target = output_path(output, root)
    plan = checked_plan(read_json(plan_path))
    before = snapshot(root)
    # Every declared acceptance path must exist in the captured source.
    for path in plan['acceptance_paths']:
        if not acceptance_files(before, [path]):
            raise ValueError('an acceptance path is absent or excluded from the source snapshot')
    results = []
    for check in plan['checks']:
        try:
            results.append(execute(check, root))
        except OSError:
            results.append({'id': check['id'], 'status': 'error', 'exit_code': None,
                            'duration_seconds': 0.0, 'output': 'Could not start the check process.',
                            'output_truncated': False})
    after = snapshot(root)
    stable = before['digest'] == after['digest'] and before['complete'] and after['complete']
    report = {'schema_version': 1, 'kind': 'takeover-run', 'created_at': datetime.now(timezone.utc).isoformat(),
              'tool': {'version': __version__, 'runner_sha256': digest(Path(__file__).read_bytes())},
              'plan': plan, 'plan_digest': digest(canonical(plan)), 'source': before,
              'source_after': after, 'evidence_stable': stable, 'results': results,
              'limits': ['Explicit checks only; no exhaustive audit or security certification.',
                         'Trusted commands run without a sandbox and may modify files or access the network.',
                         'Logs are redacted best-effort only; review before sharing.',
                         'Source stability means matching captured endpoints, not continuous monitoring.',
                         'Dependencies, external services and model tokens are not measured.']}
    write_json(target, report)
    passed = stable and all(r['status'] == 'passed' for r in results)
    return report, 0 if passed else 1


def checked_report(path):
    report = read_json(path)
    if (not isinstance(report, dict) or report.get('kind') != 'takeover-run'
            or type(report.get('schema_version')) is not int or report['schema_version'] != 1):
        raise ValueError('not a supported takeover run report')
    plan = checked_plan(report.get('plan'))
    tool = report.get('tool')
    if (not isinstance(tool, dict) or not isinstance(tool.get('version'), str)
            or not isinstance(tool.get('runner_sha256'), str)
            or not re.fullmatch('[0-9a-f]{64}', tool['runner_sha256'])):
        raise ValueError('missing runner identity')
    if report.get('plan_digest') != digest(canonical(plan)):
        raise ValueError('report plan digest does not match its plan')
    for key in ('source', 'source_after'):
        source = report.get(key)
        if not isinstance(source, dict) or not isinstance(source.get('files'), dict):
            raise ValueError('invalid source evidence')
        for name, sha in source['files'].items():
            relative_path(name)
            if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha):
                raise ValueError('invalid source file digest')
        if source.get('digest') != digest(canonical(source['files'])):
            raise ValueError('source digest does not match its manifest')
        if source.get('complete') is not True or source.get('omissions') != []:
            raise ValueError('incomplete source evidence cannot establish a comparison')
    if report.get('evidence_stable') is not True or report['source']['digest'] != report['source_after']['digest']:
        raise ValueError('source changed during checks; repeat on a stable source version')
    results = report.get('results')
    expected = [c['id'] for c in plan['checks']]
    if (not isinstance(results, list) or any(not isinstance(item, dict) for item in results)
            or [r.get('id') for r in results] != expected):
        raise ValueError('missing, duplicate or reordered check evidence')
    for check, result in zip(plan['checks'], results):
        status = result.get('status')
        code = result.get('exit_code')
        if not isinstance(status, str) or status not in STATUSES or status == 'passed' and (type(code) is not int or code != 0):
            raise ValueError('invalid check status or exit code')
        if status == 'failed' and (type(code) is not int or code == 0):
            raise ValueError('failed check must have a nonzero exit code')
        if not isinstance(result.get('output'), str):
            raise ValueError('check output must be text')
        if _unittest_command(check['argv']):
            summary = _unittest_summary(result['output'])
            if status == 'passed' and (summary is None or summary['executed'] == 0):
                raise ValueError('passed unittest evidence must show executed tests')
            if 'test_summary' in result and result['test_summary'] != summary:
                raise ValueError('test summary does not match captured output')
    return report


def compare(before_path, after_path, output):
    target = output_path(output)
    before, after = checked_report(before_path), checked_report(after_path)
    if before['plan_digest'] != after['plan_digest']:
        raise ValueError('acceptance plans differ; results are not comparable')
    if before['tool'] != after['tool']:
        raise ValueError('runner versions differ; repeat the baseline using the same runner')
    old, new = before['source']['files'], after['source']['files']
    changed = sorted(name for name in old.keys() | new.keys() if old.get(name) != new.get(name))
    criteria_changed = acceptance_files(before['source'], before['plan']['acceptance_paths']) != acceptance_files(
        after['source'], after['plan']['acceptance_paths'])
    recovered, regressed, unresolved, unverified = [], [], [], []
    for left, right in zip(before['results'], after['results']):
        if left['status'] == 'passed' and right['status'] != 'passed':
            regressed.append(left['id'])
        if right['status'] != 'passed':
            unresolved.append(right['id'])
        elif left['status'] == 'failed':
            recovered.append(left['id'])
        elif left['status'] in {'timeout', 'error'}:
            unverified.append(left['id'])
    result = {'schema_version': 1, 'kind': 'takeover-comparison',
              'before_source': before['source']['digest'], 'after_source': after['source']['digest'],
              'plan_digest': before['plan_digest'], 'changed_files': changed,
              'acceptance_changed': criteria_changed,
              'recovered_checks': [] if criteria_changed else recovered,
              'regressed_checks': regressed, 'unresolved_checks': unresolved,
              'previously_unverified_checks_now_passing': unverified,
              'verdict': 'criteria-changed' if criteria_changed else 'checks-failing' if unresolved else 'named-checks-pass',
              'limits': ['Passing named checks is not proof of full correctness or a security certification.',
                         'Reports are local evidence, not signed or tamper-proof attestations.',
                         'Undeclared test files, external test logic and dependencies require separate review.']}
    write_json(target, result)
    return result, 1 if criteria_changed or unresolved else 0
