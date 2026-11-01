# Implementation status

| Task | Acceptance | Status |
| --- | --- | --- |
| English documentation and provenance | English files, original AGPL license, source and modification notices | Verified locally |
| Shared specification and generator | Two native formats from one source; strict errors; no unrelated overwrites | Verified locally |
| Local verification | Behavioral tests, deterministic snapshot, native-format syntax checks | Verified locally |

## Verification record: 2026-11-01

- `python3 -m unittest discover -s tests -v`: 13 tests passed, including
  subprocess CLI generation/check/drift and conflict-preservation cases.
- `python3 -m agent_team validate`: nine source roles accepted.
- `python3 -m agent_team generate --output .` and `check --output .`: 20
  generated files match the source; the nine real prompt bodies are preserved.
- Python tomllib parsed all native Codex files. Ruby's independent YAML parser
  parsed all nine Claude frontmatter blocks and checked names against filenames.
  Ruby was a local verification tool, not a runtime dependency.
- Codex CLI 0.166.0 strict startup configuration check exited 0. It reported
  a PATH-alias warning in the execution environment. This does not prove that
  project trust, agent discovery or dispatch succeeded.
- LICENSE Git blob equals upstream `0ad25db4bd1d86c452db3f9602ccdbe172438f52`.
- English/privacy checks covered all 35 shareable source and configuration
  files. Known personal identifiers, local home paths and credential-shaped
  values were not found. Runtime caches are excluded from delivery.

Version bindings (SHA-256):

- `agent_team/core.py`: `e5d81980e7f878a180fdd438ae536feddd99834f651a767965c3a6938cb91f6c`
- `tests/test_generator.py`: `eb713a51b7563024bf13cf38e0ae0a1ec4b6322132672168ad94fb001c1aa93c`

Review method: original license and official client documentation, direct code
inspection, format round trips and behavioral filesystem/CLI tests. No independent
human or second-agent review has been recorded. Real AI sessions, client agent
discovery/dispatch, performance and cost comparisons have not been run.

These are local verification results. Remote delivery is checked separately
against GitHub's branch/tree and visibility; commits identify delivered snapshots.

## Naming and workflow update: 2026-11-01

- Project name: Agent Team Kit. GitHub repository: `Nonopipi/agent-team-kit`.
  The repository name, dual-client description and public visibility were
  verified through GitHub metadata after the user-authorized settings changes.
- Replaced the mandatory specialist pipeline with a risk-based default in
  project guidance and the generated starter. The main agent can implement;
  delegation is optional for bounded needs. High-impact work adds focused
  independent review and checks of original evidence.
- Updated Claude's generated guidance to describe this default. Existing
  project instructions remain preserved during generation.
- Post-change checks: 13 behavioral tests passed; 20 generated files matched
  source; Claude Code CLI validation of all nine role files passed.
- Review method: inspected final policy and generated output, preserved the
  original license, and checked generator behavior. No second reviewer or
  actual AI dispatch was used. Token, latency and quality gains are unmeasured.
- Final `agent_team/core.py` SHA-256: `703b2fdb491ee6ab11484beb788e9363e3a5fdc8302a49cbc272973c68cbe3dd`.
