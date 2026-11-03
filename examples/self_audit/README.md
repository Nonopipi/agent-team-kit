# Actual Kit defects: reproducible self-audit

This case exercises defects found in the actual Agent Team Kit source. It is a
self-audit of a developer tool, not validation of another app, a customer case,
or an independent security review. No application defects were planted.

The generator came from the published `0e516e29fda649974d1302d8d82a4ce85eb0ca8d`
version; the takeover module came from the unreleased local 0.2.0 preview.
`baseline_sources.json` retains those exact three module contents and SHA-256
digests for offline reproduction. The reconstructed baseline uses the current
acceptance tests and role definitions, held unchanged across both runs. It is
not a full historical release checkout.

## Reproduce

From the Kit root, choose a new directory outside the source tree:

```sh
python3 examples/run_self_audit.py --output /tmp/agent-team-kit-self-audit
```

The script copies Kit source/tests into that directory, restores the captured
pre-fix modules, runs the acceptance plan, replaces those modules with the fixed
versions, reruns the same plan and compares evidence. It does not edit the
original source, install dependencies, start a model or upload anything.
It runs trusted local code without an OS sandbox.

## Observed findings and changes

| Finding | Reproduction | Correction |
| --- | --- | --- |
| All-skipped tests reported passed | A unittest case marked skipped returned a successful overall run | Record discovered/skipped/executed counts; no executed tests means unverified |
| Common log credentials remained visible | Synthetic Bearer/Basic headers and quoted JSON credential values | Consume entire authentication/quoted values; retain non-sensitive fields |
| Invalid result entries caused a traceback | Append a string, null, list or integer to a valid report | Validate every entry before accessing fields; CLI returns an input error |
| Output ancestors could redirect writes | Custom directory symlink before the output leaf | Reject custom symlink ancestors before resolving output paths |
| Nonregular source input blocked | Pass a FIFO as a configuration source | Nonblocking open, regular-file validation and bounded reads |
| Extra native definitions went undisclosed | Add an unmanaged invalid agent definition | Flag the extra path for explicit review and preserve its contents |

Eight regression test methods cover these defects plus visible partial-skip
counts and rejection of falsely passed skipped-test evidence. Test methods are
not a count of independent vulnerabilities; one method includes several input
formats. Role rules were also unified in the main project and regenerated for
both clients, but agent dispatch is not evaluated by this case.

## Executed results

| Check group | Before | After |
| --- | --- | --- |
| New review regressions, 8 test methods | Failed | Passed |
| Existing generator tests, 13 | Passed | Passed |
| Existing takeover tests, 23 | Passed | Passed |

All 44 methods passed after the fixes. The plan, tests and role definitions were
unchanged between runs. The comparison records exactly three changed files:
`agent_team/core.py`, `agent_team/takeover.py` and `agent_team/__init__.py`.
The last is the version bump from 0.2.0 to 0.2.1.

Recorded command time: 6.4249 seconds before and 4.4777 seconds after; whole case
10.9384 seconds on the local machine. The before-run includes the intentional
two-second test deadline for the original blocked FIFO reader. This single run
is not a general speed comparison. The case started zero model calls. Host
assistant token usage and monetary cost are unavailable, not zero. See
`costs.json`, `summary.json` and the full before/after reports.

## What remains unverified

- Other applications and technology stacks, browser journeys and real user data.
- Full security, adversarial isolation, dependency reproducibility and production readiness.
- Behavior of delegated roles inside actual Codex/Claude sessions.
- General token/latency improvements, customer demand or willingness to pay.

Redaction is best-effort. Saved reports are editable local evidence, not signed
attestations. The regression plan was written after finding these defects, so
this case is subject to selection bias and does not measure general bug discovery.
