# Project takeover and acceptance evidence

This mode helps a person or coding agent take over a trusted repository, run
named checks, fix a reproduced problem, and compare the same checks afterwards.
The executable contribution is a bounded evidence runner and comparator. It does
not independently understand requirements, discover every defect, repair apps,
launch models, perform penetration testing or certify an app for production.

Python 3.11+ is required. Command execution currently supports macOS/Linux and
other POSIX systems. The configuration generator remains separate.

## Reproducible demonstration

From the Kit root:

```sh
python3 examples/run_takeover_demo.py --output /tmp/agent-team-kit-demo
```

Use a fresh output directory. The fixture reports a successful save but loses
the item across application instances. Its tests exercise the WSGI request
interface in process; this is not a live-browser test or a customer case.
The script records an initial failing test command, adds the missing persistence
write in a scratch copy, reruns unchanged acceptance tests and compares results.
Only `app.py` changes. The original deliberately broken fixture is preserved.

Inspect `before.json`, `after.json`, `comparison.json` and the scratch `project/`.
One command contains three acceptance tests: initially two pass and one fails;
after the fix all three pass. A recovered command is not three recovered bugs.

## Take over another project

Run from the Kit root. Replace `/path/to/app` with a project you own or are
authorized to work on. Choose new evidence filenames outside the target project.

```sh
python3 -m agent_team takeover init --project /path/to/app --output /tmp/takeover-plan.json
```

Initialization hashes a bounded source inventory and suggests existing Python
unittest checks and explicitly defined npm test/lint/build scripts. It does not
execute project code, install dependencies or open a server. These suggestions
do not prove that tests exist, are appropriate, or cover the user's requirements.
No detected checks means you must write a plan before running.

Review the generated plan in an editor. Give `scope` the actual behavior to
check; read each command and the code it will execute. Declare `acceptance_paths`
for the test files, fixtures and configuration that define success. Node plans
initially include `package.json`; add their actual test files/directories too.
Document external dependencies and any acceptance logic outside the repository.

For example:

```json
{
  "schema_version": 1,
  "kind": "takeover-plan",
  "name": "sample-app",
  "scope": "Saved items survive a new application instance; invalid titles are rejected.",
  "acceptance_paths": ["tests"],
  "checks": [
    {
      "id": "persistence",
      "description": "Run the accepted persistence scenarios.",
      "argv": ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
      "timeout_seconds": 60
    }
  ]
}
```

The next command executes the plan. Use a disposable local copy/container for
unfamiliar code. This runner is not a sandbox: commands can read accessible files,
change data and use the network. `shell=False` does not make arbitrary programs
safe. Interactive prompts receive no stdin. No setup or dependency installation
is performed automatically; configure a throwaway environment separately.

```sh
python3 -m agent_team takeover run --project /path/to/app --plan /tmp/takeover-plan.json --output /tmp/takeover-before.json
```

Use failures as evidence, then reproduce the underlying behavior. A missing
executable or timeout is unverified execution, not a confirmed application bug.
Recognized `python -m unittest` runs finding zero tests or skipping every test
are marked unverified, including when the command returns exit code zero.
Discovered/skipped/executed counts are recorded; partially skipped suites retain
visible skip counts. A successful recognized unittest command without a captured
summary is also unverified. Other frameworks still require human review for
empty, skipped or inadequate checks; the runner cannot infer their coverage.
Record real findings with their affected behavior, reproduction, evidence,
impact, proposed fix and unresolved questions. A green build alone is not proof
that a user journey works. The operator or coding agent implements the bounded
fix; the runner does not edit application code.

Keep the plan and acceptance files unchanged for a comparable rerun:

```sh
python3 -m agent_team takeover run --project /path/to/app --plan /tmp/takeover-plan.json --output /tmp/takeover-after.json
python3 -m agent_team takeover compare --before /tmp/takeover-before.json --after /tmp/takeover-after.json --output /tmp/takeover-comparison.json
```

If acceptance criteria need a legitimate correction, review and change them,
then establish a new baseline. Do not report that comparison as the original
defect being fixed. Tests stored outside declared acceptance paths require
separate review; the comparator cannot infer all hidden acceptance logic.

## Evidence and limits

- Plans use argument arrays and permit 1-20 sequential checks, each limited to
  1-120 seconds. Output captures at most 32 KiB of raw combined stdout/stderr
  per check; truncation is recorded. The check's process group is terminated
  after completion or timeout. Escaping processes are not OS-contained.
- Only a small environment allowlist is inherited: PATH, locale and temporary
  directory settings. `CI=1` and `PYTHONDONTWRITEBYTECODE=1` are set. A project
  needing additional environment setup must arrange it separately. File-based
  credentials remain accessible to commands unless an external sandbox prevents
  that access. Never put credentials into a plan or its arguments.
- Source fingerprints include relative filenames and content hashes, not source
  contents. Dependencies, generated build artifacts, VCS metadata, local agent
  state, credential directories and secret-shaped filenames are excluded.
  `.env` examples are excluded too. See `SKIP` and `secret_name` in the source
  for the exact rules. Excluded files are outside the recorded coverage.
- Captures allow up to 3,000 files and 3,000 directories, 1 MiB per file and
  24 MiB total source.
  Symlinks, unreadable directories/files, nonregular files and exceeded limits
  produce disclosed omissions and prevent a passing overall run/comparison.
- Each run stores its exact plan, runner version/hash and source fingerprints
  before/after. Matching endpoints are not continuous change monitoring.
  Comparisons require a matching plan and runner, complete captures and matching
  endpoints. Changed declared acceptance files block a recovered-check claim.
- Reports are new files with owner-only permissions. Existing files are refused;
  run/init output inside the target or through custom symlinks is refused.
  JSON input/output is limited to 4 MiB. Reports are not signed attestations and
  can be edited; keep original artifacts and independently review important work.
- Home paths, common token/password patterns, Bearer/Basic headers and quoted JSON credential values in captured logs are redacted
  best-effort. Other private material may remain. Review all evidence before
  sharing. No logs or source are automatically sent to an AI or uploaded.
- Passing checks establish only their named scope. Browser behavior, performance,
  dependency reproducibility, exhaustive security, model quality, token usage
  and commercial demand are not established by this tool.

Exit codes: `0` means the named checks passed with comparable evidence; `1`
means failed/unverified checks, incomplete/changed source, or changed criteria;
`2` means invalid input, incompatible evidence or an operation error. A failing
run saves available evidence when the output write succeeds; operation errors
may prevent a report. Errors before execution do not run checks.

## Instruction for a coding assistant

> Read the existing project rules and confirm the intended user behavior. Inspect
> the actual source and commands; treat prior AI summaries as leads. Create a
> bounded acceptance plan, run it on trusted isolated data, reproduce concrete
> failures, and make the smallest justified fixes. Preserve the approved tests
> when comparing before/after. Report observed findings separately from
> suspicions, failed execution and untested areas. Add independent review for
> high-impact changes. Stop when the accepted scope is verified or blocked.
> Reuse valid evidence rather than restarting a multi-agent review pipeline.
> Publishing or touching production data requires its own authorization.

## Distribution and paid work

The project remains AGPL-3.0 with its upstream attribution. Open source does not
prevent charging for copies, support or services; applicable source and license
obligations remain. The initial recommendation is a freely available core and
reproducible examples, followed by validation of bounded, human-reviewed repair
services. No paid service, price, customer demand or revenue has been validated.

## Review fixes and actual self-audit

See [the actual Kit case](../examples/self_audit/README.md) for a replay against
pre-fix Kit code with unchanged tests, measured local command times and explicit
omissions. This is a self-audit, not an independent or cross-application review.
Extra non-object result entries are rejected as invalid input. Recognized
unittest evidence cannot claim passed when its captured summary shows no executed
tests. Log redaction remains best-effort even after the documented format fixes.
