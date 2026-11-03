# Executed synthetic takeover demonstration

Generated on 2026-11-02 by `examples/run_takeover_demo.py` with Agent Team Kit
0.2.1. These are actual local command results against a deliberately broken
WSGI fixture, not a customer application or an autonomous AI repair benchmark.

- Before: the command ran three tests; persistence failed, invalid-title and
  unknown-route scenarios passed.
- Fix: one missing persistence write in a scratch copy of `app.py`.
- After: the same three tests passed. Acceptance files were unchanged.
- Comparison: one recovered check command (`tests`), no regressed check commands,
  and `app.py` as the only changed source file.

The JSON reports include source manifests and the runner hash. Output paths are
redacted. Reports are editable local evidence, not signed attestations; review
the fixture, test contract and exact code change. This demonstrates the evidence
mechanism only. It does not measure model tokens, general bug-finding ability,
production safety, performance improvements or commercial demand.

Reproduce from the Kit root using a fresh directory:

```sh
python3 examples/run_takeover_demo.py --output /tmp/agent-team-kit-demo
```
