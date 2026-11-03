# Origin and modifications

This is an adaptation of **Claude Code Agents** by **Aidan-M-Dev**:
https://github.com/Aidan-M-Dev/claude-code-agents

Upstream revision examined: `1cdef66c3d4a4aa5ae75a1e047d2ad76046883ff`.
Upstream LICENSE blob: `0ad25db4bd1d86c452db3f9602ccdbe172438f52`.
The original GNU Affero General Public License version 3 text is preserved
verbatim in `LICENSE`.

Modified on **2026-11-01** by Agent Team Kit contributors:

- Adapted the role prompts and main-session workflow for Codex.
- Added a shared specification, Codex/Claude Code generators and static checks.
- Added preservation of existing files, digest-based drift checks and tests.
- Added a test-runner bootstrap exception and evidence-based status reporting.
- Added a risk-based default workflow, optional delegation and proportional checks.
- Renamed the adaptation Agent Team Kit to describe both client formats.
- Replaced local identity/path examples with reusable English documentation.

Earlier revisions incorrectly labelled this adaptation MIT. That label did not
relicense the upstream material. This adaptation is distributed under AGPL-3.0;
retain applicable notices and the license when redistributing it. The project
does not claim the upstream prompts or workflow as an entirely original work.

Additional implementation on **2026-11-02** by Agent Team Kit contributors:

- Added a local takeover evidence runner, source/acceptance comparison and CLI.
- Added behavioral checks and a reproducible, intentionally defective WSGI demo.
- Documented execution limits and the distinction between named-check results
  and full application correctness. No upstream prompt authorship is claimed.

Review corrections on **2026-11-02** by Agent Team Kit contributors:

- Corrected skipped-test classification, credential redaction and report validation.
- Hardened source/output paths and disclosed extra native agent definitions.
- Unified specialist guidance with the risk-based workflow; added regression
  tests and a reproducible self-audit of actual pre-fix Kit modules.
