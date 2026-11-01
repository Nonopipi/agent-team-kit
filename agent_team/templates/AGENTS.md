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

### Choose the smallest sufficient workflow

Use complexity, impact and reversibility to choose a tier. File count, the
presence of AI and a task's name do not determine its tier. Reuse the current
plan and evidence; raise the tier only when new risk appears.

| Tier | Typical trigger | Default execution | Verification |
| --- | --- | --- | --- |
| 1 | Clear, low-impact, reversible task | Main agent completes it directly; no delegation | Relevant direct check |
| 2 | Several steps or coupled changes | Briefly state deliverable, assumptions and acceptance; main agent implements | Targeted behavioral checks against acceptance |
| 3 | Errors could materially affect privacy, security, money, production or important data | Prepare reversibly; add focused independent review | Original evidence, final diff and relevant actual tests |

- The main agent may write application code, tests, configuration and docs.
  Specialist roles are optional capabilities, not a required assembly line.
- For tier 2, delegate a bounded task only when a concrete unknown, specialist
  need or context burden justifies the extra handoff. Do not summon architect,
  planner, test writer, reviewer and committer for every change.
- For tier 3, prefer a reviewer who did not produce the change. Where that is
  unavailable, independently check original evidence and tests, state the
  limitation and leave unresolved consequential actions pending. Changing your
  own role label is not independent review.
- If the user explicitly requests the full specialist workflow, use available
  roles and explain the extra handoffs. Respect client and session limits;
  report unavailable roles without repeatedly attempting to spawn them.

### Keep context and checks proportional

- Start with targeted searches and the files the task touches. Read surrounding
  code when needed; do not load every role, architecture file or task record.
- A delegation brief contains the task, acceptance, relevant paths, constraints,
  current evidence and expected output. Avoid copying the full conversation or
  unrelated files when the client allows a smaller context.
- Delegate one specialist at a time. Verify its report against the actual files
  and commands. Reuse valid evidence for unchanged parts.
- Run the smallest meaningful check, then any required broader checks. Do not
  repeat a passing test merely because another role received the task; rerun
  when a change, failure or unresolved concern affects the result.
- Add regression tests for meaningful behavior or defects. Simple copy edits
  and branding changes normally need direct checks, not new application tests.
- Stop after three unsuccessful fix rounds or two repeated infrastructure
  failures. Return the evidence and remaining blocker, without restarting the
  same review cycle under a different role.
- Update existing task or architecture records only when the change needs a
  durable handoff. Do not create a new plan file for each small task.
- Git commits can be handled by the main agent within authorization. Check
  whether Git exists; use exact file paths, preserve unrelated changes and
  never claim a commit that did not happen. Publishing is a separate action.
- Report what changed, the checks actually run and material limitations. Do not
  claim token savings, faster execution or better quality without measurements.

Claude Code uses hyphenated role names; see CLAUDE.md for the exact mapping.
