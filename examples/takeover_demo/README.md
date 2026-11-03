# Deliberately broken persistence fixture

This small Python WSGI application reports a successful POST but loses the item
when a new application instance handles GET. One of its three acceptance tests
is expected to fail. Do not treat it as production-ready application code.

From the Agent Team Kit root, run:

```sh
python3 examples/run_takeover_demo.py --output /tmp/agent-team-kit-demo
```

Choose a new output directory. The script copies this fixture there, records
the failing check, adds the missing persistence write in the copy, reruns the
same tests and compares both reports. It preserves the original broken fixture.
The requests run in process through the WSGI interface, without opening a port.
This demonstrates the evidence workflow, not a browser or real-customer audit.
