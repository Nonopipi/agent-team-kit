# Origin and modifications

This is an adaptation of **Claude Code Agents** by **Aidan-M-Dev**:
https://github.com/Aidan-M-Dev/claude-code-agents

Upstream revision examined: `1cdef66c3d4a4aa5ae75a1e047d2ad76046883ff`.
Upstream LICENSE blob: `0ad25db4bd1d86c452db3f9602ccdbe172438f52`.
The original GNU Affero General Public License version 3 text is preserved
verbatim in `LICENSE`.

Modified on **2026-11-01** by Codex Agent Team contributors:

- Adapted the role prompts and main-session workflow for Codex.
- Added a shared specification, Codex/Claude Code generators and static checks.
- Added preservation of existing files, digest-based drift checks and tests.
- Added a test-runner bootstrap exception and evidence-based status reporting.
- Replaced local identity/path examples with reusable English documentation.

Earlier revisions incorrectly labelled this adaptation MIT. That label did not
relicense the upstream material. This adaptation is distributed under AGPL-3.0;
retain applicable notices and the license when redistributing it. The project
does not claim the upstream prompts or workflow as an entirely original work.
