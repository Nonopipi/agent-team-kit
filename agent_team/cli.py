"""Local-only command-line interface. AGPL-3.0."""

import argparse
import sys

from . import __version__, core


def main(argv=None):
    parser = argparse.ArgumentParser(description='Generate and check native Codex and Claude Code agent definitions.')
    parser.add_argument('--version', action='version', version=__version__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'generate', 'check'):
        command = commands.add_parser(name)
        command.add_argument('--spec', default='team.toml', help='Shared TOML specification (default: team.toml)')
        if name != 'validate':
            command.add_argument('--output', default='.', help='Project output directory (default: current directory)')
    args = parser.parse_args(argv)
    try:
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
