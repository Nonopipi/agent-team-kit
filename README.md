# Agent Team Kit

> **Experimental preview 0.2.1.** Includes configuration generation and evidence
> tools for explicit acceptance checks. Verified through local regression tests
> and a Kit self-audit; cross-application use and real agent dispatch remain
> unverified. This is not a production-readiness or security certification.

A local toolkit for Codex and Claude Code, with a shared agent configuration
generator and a project takeover evidence workflow. Define roles once in
`team.toml`, generate both native formats, and compare explicit acceptance
checks before and after a fix. Python 3.11+ is the only dependency; takeover
command execution currently requires a POSIX system such as macOS or Linux.

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

## Take over and verify an existing project

Version 0.2 adds executable evidence tools, in addition to agent prompts.
Version 0.2.1 fixes the review defects and unifies specialist rules.

```sh
python3 examples/run_takeover_demo.py --output /tmp/agent-team-kit-demo
```

This synthetic demonstration reproduces a lost-save bug, fixes only application
code in a scratch copy, then verifies the unchanged tests and compares reports.
The fixture uses an in-process WSGI app; no browser or AI model is launched.
Choose a new scratch directory for each run.

For your own project, `takeover init` suggests an editable check plan; `takeover
run` executes its reviewed commands and records bounded output, source hashes
and outcomes; `takeover compare` detects recovered/regressed checks and changed
acceptance criteria. It refuses to call changed tests a verified recovery.

Read the [takeover guide](docs/takeover.md) before executing project commands.
Commands run without a sandbox. The tool does not automatically find every bug,
repair apps or certify security. It captures evidence for the operator or coding
agent doing that work. No token, latency or customer-demand benefit is claimed.

## Reproduce the actual Kit review fixes

```sh
python3 examples/run_self_audit.py --output /tmp/agent-team-kit-self-audit
```

This is a self-audit of actual Kit code, distinct from the deliberately broken
WSGI demonstration. The recorded run preserves the same acceptance plan/tests:
the historical source fails the new regression group while retaining its 36
previously passing tests; the fixed copy passes all 44 tests. See the
[self-audit case](examples/self_audit/README.md) for exact source provenance,
findings, results, timing, omissions and an offline replay. It is not validation
of a different application or an independent review.

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

The default workflow scales with risk rather than running every role:

| Task | Default workflow |
| --- | --- |
| Small, reversible change | Main agent implements and checks directly |
| Several coupled steps | Brief acceptance criteria, implementation and targeted checks; delegate only when useful |
| High-impact change | Reversible preparation, focused independent review and relevant actual tests |
| Explicit full-team request | Use the specialist roles needed for the requested workflow |

The main agent can implement, test and commit within authorization. Architect,
planner, test writer and committer handoffs are optional; unchanged evidence is
reused. Role prompts apply only when that specialist is actually delegated a
task. Existing projects retain their own `AGENTS.md`, so merge this workflow
explicitly when adopting it there. See the generated starter for the full rules.

These rules aim to reduce unnecessary handoffs and repeated context. No token,
latency or quality improvement has been measured; this is not a runtime scheduler
or an enforced spending limit.

The client runs the workflow; this Python tool generates and checks its
configuration. It does not execute the workflow or create sandbox boundaries.
No model or permission override is generated; each client applies its defaults
and parent-session settings. Reviewer instructions do not create a separately
enforced read-only sandbox.

## File preservation

- Identical output files can be adopted without overwriting their contents.
- Existing managed files can be updated if their digests still match the previous
  manifest. Manually changed or conflicting unmanaged files are refused.
- Existing unrelated files are preserved. Custom output symlink ancestors and
  targets, nonregular source inputs and unsafe manifest paths are refused.
  Standard macOS `/tmp/...` and `/var/...` aliases are normalized. Role removal is not silently pruned; review stale files
  explicitly or generate into a new directory.
- Conflicts are checked before writes. Each write is atomic, but the whole batch
  is not a single filesystem transaction. Do not run concurrent generators in
  the same output directory.
- `check` compares expected bytes and the manifest, and flags extra native
  agent definitions for explicit review without overwriting them. Exit code 0 means a matching
  static snapshot, 1 means drift, and 2 means invalid input or an operation error.

## Verification limits

Behavioral tests cover both formats, name collisions, invalid source files,
determinism, managed updates, drift, CLI exit codes, overwrite prevention and
symlink escapes. The repository snapshot can be checked without using any AI
credits. Generator configuration checks are static. Takeover checks execute only the
reviewed commands. Neither establishes client agent discovery/dispatch, model
performance, cost savings or complete application correctness.
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
