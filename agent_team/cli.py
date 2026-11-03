"""Local-only command-line interface. AGPL-3.0."""

import argparse
import json
import sys

from . import __version__, core, takeover


def main(argv=None):
    parser = argparse.ArgumentParser(description='Generate agent definitions and capture project takeover evidence.')
    parser.add_argument('--version', action='version', version=__version__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'generate', 'check'):
        command = commands.add_parser(name)
        command.add_argument('--spec', default='team.toml', help='Shared TOML specification (default: team.toml)')
        if name != 'validate':
            command.add_argument('--output', default='.', help='Project output directory (default: current directory)')
    evidence = commands.add_parser('takeover', help='Initialize, run and compare explicit acceptance checks')
    actions = evidence.add_subparsers(dest='action', required=True)
    for name in ('init', 'run', 'compare'):
        action = actions.add_parser(name)
        action.add_argument('--output', required=True, help='New JSON evidence file; existing files are never replaced')
        if name in {'init', 'run'}:
            action.add_argument('--project', required=True, help='Trusted target project directory')
        if name == 'run':
            action.add_argument('--plan', required=True, help='Reviewed plan; its commands will execute without a sandbox')
        if name == 'compare':
            action.add_argument('--before', required=True)
            action.add_argument('--after', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'takeover':
            if args.action == 'init':
                print(json.dumps(takeover.init(args.project, args.output)))
                return 0
            if args.action == 'run':
                report, status = takeover.run(args.project, args.plan, args.output)
                print(json.dumps({'checks': [{'id': r['id'], 'status': r['status']} for r in report['results']],
                                  'source_stable': report['evidence_stable']}))
                return status
            report, status = takeover.compare(args.before, args.after, args.output)
            print(json.dumps({'verdict': report['verdict'], 'recovered_checks': report['recovered_checks'],
                              'regressed_checks': report['regressed_checks']}))
            return status
        spec = core.load_spec(args.spec)
        files = core.render(spec)
        if args.command == 'validate':
            print(f'Valid specification: {len(spec["agents"])} roles; two client formats.')
        elif args.command == 'generate':
            count = core.generate(args.output, files)
            print(f'Generated or verified {count} files. Existing AGENTS.md was preserved if present.')
        else:
            issues = core.check(args.output, files)
            if issues:
                for issue in issues:
                    print(f'error: {issue}', file=sys.stderr)
                return 1
            print(f'Configuration matches source: {len(files)} generated files. Runtime dispatch is not tested by this check.')
        return 0
    except (ValueError, OSError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
