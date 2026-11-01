# Codex Agent Team

A local configuration generator for Codex and Claude Code. Define roles once in
`team.toml`, generate both native formats, and check that the generated files
still match the source. Python 3.11+ is the only requirement.

This is an AGPL-3.0 adaptation of [Claude Code Agents by Aidan-M-Dev](https://github.com/Aidan-M-Dev/claude-code-agents).
See [NOTICE.md](NOTICE.md) for the source and modifications, and [LICENSE](LICENSE)
for the preserved upstream license. The upstream prompts and workflow are not
claimed as an entirely original work.

## Quick start

From the repository root:

```sh
python3 -m agent_team validate
python3 -m agent_team generate --output .
python3 -m agent_team check --output .
python3 -m unittest discover -s tests -v
```

Edit `team.toml`, update its `modified_date`, then regenerate and check. Edit the
source definition rather than the generated role files. The generator makes no
network requests, launches no AI sessions, and installs no dependencies.

## What is generated

| Shared source | Codex output | Claude Code output |
| --- | --- | --- |
| Each role in `team.toml` | `.codex/agents/<name>.toml` | `.claude/agents/<hyphenated-name>.md` |
| `[codex]` settings | `.codex/config.toml` | No equivalent setting is invented |
| Shared project guidance | Existing `AGENTS.md` is preserved | `CLAUDE.md` imports `AGENTS.md` |

The bundled specification has nine roles and produces 20 managed files. A
SHA-256 manifest, `.agent-team-generated.json`, records that generated snapshot.
On a new output directory, a starter `AGENTS.md` is added only if none exists.
The starter then belongs to the user and is not overwritten during regeneration.

Hidden directories are required. Include `.codex/`, `.claude/`, `.gitignore` and
`.agent-team-generated.json` when sharing or copying this repository.

## Use in another project

Render into a separate directory first if you want to inspect the files:

```sh
python3 -m agent_team generate --output /path/to/project
python3 -m agent_team check --output /path/to/project
```

Inspect existing project guidance and merge the relevant workflow instructions
into its `AGENTS.md`. Existing `AGENTS.md` is preserved, so the generator does not
silently replace that project's rules. An existing, different `CLAUDE.md` or
other conflicting output file causes an error before writes. Resolve that
conflict deliberately or choose another output directory; there is no force flag.

Open the target directory in the client and verify agent discovery there:

- Codex reads `.codex/agents/*.toml`. Review the project before trusting it;
  project configuration loads only for trusted projects.
- Claude Code reads `.claude/agents/*.md`, with YAML frontmatter and a Markdown
  prompt. `CLAUDE.md` imports the shared `AGENTS.md` instructions.
- Codex role names such as `backend_dev` become `backend-dev` in Claude Code.
  The generated `CLAUDE.md` lists every mapping. Prompt content is preserved.

See the official documentation for [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[Claude Code subagents](https://code.claude.com/docs/en/sub-agents), and
[Claude Code project instructions](https://code.claude.com/docs/en/memory).

## Specification

Only these fields are supported in version 1:

```toml
schema_version = 1
modified_date = "2026-11-01"

[codex]
enabled = true
max_concurrent_threads_per_session = 1

[[agents]]
name = "example_reviewer"
description = "Review proposed changes and report concrete findings."
instructions = "Read the project instructions. Review without editing files."
```

Names start with a lowercase letter and contain lowercase letters, digits,
underscores or hyphens, up to 64 characters. Claude names replace underscores
with hyphens; collisions are rejected. Dates, field types, duplicate names,
empty prompts, control characters and unknown fields are checked. Unsupported
model, permission or tool settings cause an error rather than being dropped.
Sources are limited to 1 MiB and 1-64 roles.

## Roles and workflow

| Shared role / Codex name | Claude Code name | Responsibility |
| --- | --- | --- |
| `architect` | `architect` | Architecture and design decisions |
| `planner` | `planner` | Tasks and acceptance criteria |
| `tdd_test_writer` | `tdd-test-writer` | Behavioral tests and expected failures |
| `frontend_dev` | `frontend-dev` | Frontend implementation |
| `backend_dev` | `backend-dev` | Backend implementation and test-runner bootstrap |
| `database_dev` | `database-dev` | Schemas, migrations and test data |
| `code_reviewer` | `code-reviewer` | Read-only review |
| `security_auditor` | `security-auditor` | Security review |
| `git_committer` | `git-committer` | Validation and local Git commits |

```text
Requirements -> architecture -> task plan -> tests -> implementation
-> code review -> fixes and security review when needed -> local commit
```

The client runs the workflow; this Python tool generates and checks its
configuration. It does not execute the workflow or create sandbox boundaries.
No model or permission override is generated; each client applies its defaults
and parent-session settings. Reviewer instructions do not create a separately
enforced read-only sandbox.

## File preservation

- Identical output files can be adopted without overwriting their contents.
- Existing managed files can be updated if their digests still match the previous
  manifest. Manually changed or conflicting unmanaged files are refused.
- Existing unrelated files are preserved. Symlink targets and unsafe manifest
  paths are refused. Role removal is not silently pruned; review stale files
  explicitly or generate into a new directory.
- Conflicts are checked before writes. Each write is atomic, but the whole batch
  is not a single filesystem transaction. Do not run concurrent generators in
  the same output directory.
- `check` compares expected bytes and the manifest. Exit code 0 means a matching
  static snapshot, 1 means drift, and 2 means invalid input or an operation error.

## Verification limits

Behavioral tests cover both formats, name collisions, invalid source files,
determinism, managed updates, drift, CLI exit codes, overwrite prevention and
symlink escapes. The repository snapshot can be checked without using any AI
credits. Validation is local and static: it does not establish client discovery,
agent dispatch, model performance, cost savings or successful application delivery.
Client-runtime results and remaining limitations are recorded in
[tasks/overview.md](tasks/overview.md).

Codex CLI versions supporting the options below can also check startup settings:

```sh
codex --strict-config -C . app-server --print-startup-config
```

## License and attribution

AGPL-3.0. Preserve the upstream license and applicable notices, identify changes
and their dates, and follow the license when redistributing an adaptation.
Earlier MIT-labelled revisions did not relicense the upstream material; see
[NOTICE.md](NOTICE.md). Publishing a repository or making it public remains a
separate user decision.
