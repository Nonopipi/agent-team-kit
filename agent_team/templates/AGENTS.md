<!-- Adapted from Aidan-M-Dev/claude-code-agents; AGPL-3.0. Modified 2026-11-01. -->
# Shared project instructions

## Part A: everyone

- Inspect the actual project before proposing work. Product scope, stack,
  development commands and test commands must be confirmed rather than guessed.
- Preserve existing code, project guidance and unrelated user changes.
- Never read credentials, private environment files or browser profiles.
- Use isolated test data. Do not change production data or delete databases.
- Sending, publishing, uploading, deployment, payments and destructive operations
  require authorization for the specific action.
- Match existing conventions and use the smallest change that meets the task.
- Report actual commands, results, limitations and the version checked. A model's
  PASS verdict alone is not evidence that a command ran or a requirement passed.
- Subagents follow Part A and their own role instructions; Part B is for the
  main conversation. Read-only instructions are not a separate security sandbox.

## Part B: main conversation

- Inspect the configured role files for the current client. Delegate only to
  roles that are available, one at a time, and verify their reports on disk.
- With the bundled nine roles, use architect -> planner -> test writer ->
  implementation specialist -> code reviewer -> git committer. Add security
  review for security-sensitive changes. Present consequential design choices
  to the user and reuse existing approval for routine execution.
- If no test runner exists, backend_dev first establishes a passing smoke test
  and a working test command. Configuration-only changes use relevant checks.
- Claude Code uses hyphenated role names; see CLAUDE.md for the exact mapping.
- Custom teams may have fewer roles. State which review or implementation steps
  are unavailable instead of inventing agents or claiming the full pipeline ran.
- Read architecture/ and tasks/ if present. Update existing records instead of
  creating a second plan. If Git is absent, report that no commit was made.
- Stop after three unsuccessful fix rounds or two repeated infrastructure
  failures. Report the evidence and unresolved blocker to the user.
