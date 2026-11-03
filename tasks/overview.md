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

## Takeover evidence workflow: 2026-11-02

Historical status on 2026-11-02: local 0.2.0 preview; superseded by 0.2.1.

| Acceptance | Evidence | Result |
| --- | --- | --- |
| Read-only bounded initialization | Init tests, exclusion/symlink/unreadable-directory and inventory-limit cases | Verified |
| Explicit bounded command execution | Timeout, large-output, missing executable, empty unittest discovery and environment tests | Verified on macOS/POSIX |
| Comparable before/after evidence | Same plan/runner, source stability, changed acceptance and regression cases | Verified |
| Preserve existing behavior | Full `python3 -m unittest discover -s tests -v` | 36 tests passed |
| Preserve generated configurations | `python3 -m agent_team check --output .` | 20 files match source |
| Demonstrate a real executed repair sequence | `python3 examples/run_takeover_demo.py --output <new scratch directory>` | Synthetic fixture: 2/3 tests before, 3/3 after; only app.py changed |

Runnable demonstration: `examples/run_takeover_demo.py`. Executed reports:
`examples/evidence_demo/{before,after,comparison}.json`. The original fixture is
intentionally broken; the script fixes a scratch copy. The case exercises WSGI
requests in process, not a browser or a customer application.

Review method: direct inspection of code/input/output limits, original license,
behavioral filesystem/process/CLI tests, and a replay with unchanged acceptance
tests. No separate human or second-agent review was available. No Git repository
is initialized locally; no local commit, remote upload or production action was
performed for this increment.

Limitations: the CLI captures explicit check evidence and does not autonomously
discover all defects or repair applications. Trusted commands are not sandboxed;
reports require privacy review. Captures exclude documented paths and are
endpoint observations, not continuous or signed attestations. Actual third-party
apps, browser journeys, model dispatch, token/latency advantages, paid demand and
revenue remain unverified.

Version bindings (SHA-256):

- `agent_team/takeover.py`: `50abc33a0f86c089a970aa8b174c53ed4d498fac882136e7189e19b59922ee38`
- `agent_team/cli.py`: `4f59ca02cc65a7020553f3beb6268cefef57d84ba5c0135b4a85882dd193402a`
- `tests/test_takeover.py`: `883c3a8520ddb651c32cf9b13480966c128303f207c29684c5b00093e6c70da9`

## Review corrections and self-audit: 2026-11-02

Verification snapshot on 2026-11-02: local 0.2.1 superseded the 0.2.0 preview's
acceptance claims for the reviewed areas. No deployment or external application
modification was performed.

| Requirement | Evidence | Result |
| --- | --- | --- |
| Skipped-test and malformed-report corrections | Unchanged regression methods, including old false-pass evidence | Passed |
| Common credential output formats | Synthetic Bearer/Basic and quoted credential regression cases | Passed; best-effort limits remain |
| Generator path/input corrections and extra-role disclosure | Symlink ancestor, FIFO and unmanaged native-definition regressions | Passed |
| Preserve prior behavior | 13 generator and 23 takeover tests | Passed |
| Complete local suite | `python3 -m unittest discover -s tests -q` | 44 tests passed |
| Unify nine role prompts and both client outputs | Source inspection, prompt round trips, generation/check; Claude CLI validation | Verified statically; dispatch untested |
| Replay actual defects on a separate Kit copy | `python3 examples/run_self_audit.py --output <new scratch directory>` | Regression group fails before, all 44 methods pass after; tests unchanged |
| External application case | Awaiting a user-selected authorized target | Not executed |

Evidence: `examples/self_audit/` contains the captured historical module contents,
plan, before/after/comparison, summary and costs. Only core.py, takeover.py and
the version module change in the reconstructed case. Current tests and role
source remain constant. The historical takeover module was an unreleased local
preview; the generator matches the previously published version. This is actual
Kit code, but is self-audit evidence, not external-app/customer validation.

Measured local command time: 6.4249 seconds before, 4.4777 seconds after, 10.9384
seconds for the case. The before-run includes the two-second FIFO regression
deadline. The case starts zero model calls. Host assistant tokens and monetary
cost are unknown. General performance, token savings, demand and revenue remain
unverified. Role text changed from 18,599 to 12,811 characters; this is not a token
or quality measurement.

Review method: original before/after modules, reproducible failure-first tests,
full behavioral suite, static native-format validation and exact unchanged-test
comparison. No second human/model reviewer was used. Logs remain best-effort
redacted; no sandbox, continuous source monitoring or security certification.

Exact final source bindings (SHA-256):

- `agent_team/core.py`: `12f6bc7f5acbbe6603c76129965c4ad0487137da96d299a8c7ed55a458f152bf`
- `agent_team/takeover.py`: `ea2ef19fe2fa0a88aa1db36e27373c15e1d44bd1fcaab24b23071469dccf2ddc`
- `team.toml`: `e57ac6e17d77fc849a1a12d5b1edd84d177215f2ad111c6d4e73c162a5bc0e5c`
- `tests/test_review_regressions.py`: `02a60e782147ea0e946de0f49ffa14f866c6aad8bd93971689d87ab4bee6b72a`

## Public experimental preview scope: 2026-11-03

The user authorized updating `Nonopipi/agent-team-kit` on `main` with the reviewed
0.2.1 preview. The README prominently identifies the experimental scope. The
source matches the 44-test verification and self-audit bindings above; the 20
managed configuration files still match the source. AGPL attribution is retained.
Cross-application acceptance, real agent dispatch, general token/latency savings
and commercial demand remain unverified. GitHub's final branch/commit/tree
metadata is used separately to confirm delivery; preparation is not publication.
