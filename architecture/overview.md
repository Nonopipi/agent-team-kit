# Dual-client configuration generator

This project turns one validated `team.toml` into native Codex TOML and Claude
Code Markdown definitions. Python 3.11+ and its standard library are sufficient.
It does not invoke a model, install dependencies, or enforce a security sandbox.

## Contract

- Source fields: `schema_version = 1`, ISO `modified_date`, a `codex` settings
  table, and a non-empty `agents` array of name/description/instructions tables.
- Reject unknown fields, duplicate or unsafe names, Claude-name collisions,
  malformed values and oversized source files before writing anything.
- Codex preserves source names; Claude changes underscores to hyphens. A generated
  `CLAUDE.md` imports `AGENTS.md` and records this mapping explicitly.
- Existing `AGENTS.md` is user-owned and preserved. A starter is created only
  when absent. Generated roles inherit client permissions and models.
- `.agent-team-generated.json` records generated paths and SHA-256 digests.
  Regeneration accepts unchanged managed files and identical unmanaged files;
  conflicting edits, unsafe manifests and symlinks are refused before writes.
- Removing a role that still owns generated files is refused, not silently pruned.
  Unrelated files are preserved. Writes are atomic per file, not one filesystem
  transaction across the whole output directory.

## Verification

`python3 -m unittest discover -s tests -v` exercises CLI failures, deterministic
generation, format round trips, drift, overwrite prevention and symlink escapes.
`python3 -m agent_team check --output .` compares the generated snapshot with
the source. Client discovery and actual agent dispatch are separate checks;
successful syntax validation does not establish either.

Upstream prompts remain an attributed AGPL-3.0 adaptation. See `NOTICE.md`.

## Workflow policy

The shared starter uses three risk tiers. The main agent completes ordinary
work directly and may call specialists for bounded needs. High-impact work adds
focused independent review and original-evidence checks. Existing project rules
are preserved, so adopting this policy requires an explicit merge there.
This is instruction-level routing; the generator does not select agents, meter
tokens or enforce a runtime budget. Savings and quality remain unmeasured.

## Takeover evidence workflow: first version

Add a standard-library CLI under `takeover init`, `takeover run` and
`takeover compare`. Init inventories a bounded source tree without executing
project code and proposes editable argv-based checks. Run executes only the
explicit plan, sequentially, with deadlines, bounded/redacted logs and source
fingerprints before/after. Compare requires the same plan and stable, complete
source captures; changed acceptance files prevent a claimed recovery.
Reports distinguish passed, failed, timed-out and errored checks. Passing
checks establish only their named scope. The tool neither discovers every bug
nor repairs applications autonomously; an operator or coding agent performs
bounded fixes between runs. Command execution is for trusted repositories on
POSIX systems and is not a sandbox. Reports stay local and are never uploaded.
A deliberately broken WSGI persistence example will demonstrate a reproduced
failure, a minimal code fix with unchanged tests, and a verified check recovery.

## Review fixes: local 0.2.1

Configuration input uses bounded regular-file reads. Custom output symlink
ancestors are refused before resolution; known macOS temporary-directory aliases
are normalized. Extra native agent definitions are disclosed without reading or
replacing them. Specialist prompts now follow the same scope/risk policy.
Recognized unittest evidence records executed/skipped counts, and empty or
all-skipped execution is unverified. Report validation rejects non-object result
entries and falsely passed skipped evidence. Credential redaction handles common
quoted values and authentication schemes but remains best-effort.
`examples/run_self_audit.py` reconstructs exact pre-fix modules with current
unchanged acceptance tests and role definitions. It is an offline self-audit,
not a full release checkout, independent review or another application case.
