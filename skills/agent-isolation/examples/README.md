# agent-isolation examples

Fixtures that prove the checker offline. Run `sh selftest.sh` (stdlib only).

| File | Role |
|---|---|
| `sessions.good.json` | Split-session layout: a powerless `reader` for untrusted input, a self-initiated `operator` (sensitive + send, but no untrusted input and human-gated), a leg-free `compute` session. No session carries the trifecta. |
| `sessions.bad.json` | Three faults: `assistant` holds all three legs *and* runs as the owner's primary identity with no approval; `poster` can `publish` (irreversible) ungated; `mystery` declares an unclassified capability. |
| `selftest.sh` | Asserts safe → 0; trifecta, ungated irreversible, forbidden identity, unclassified → 1; missing file → 2. |

Try it:

```bash
python3 ../scripts/trifecta_check.py --manifest sessions.bad.json
```

The headline finding:

```
assistant: LETHAL TRIFECTA — this session holds sensitive access, untrusted
input, AND an exfil channel at once; an injection in untrusted content can read
the account and send it out. Split it: move untrusted-reading to a session with
no sensitive account and no send capability.
```

Capabilities are mapped to legs in `scripts/trifecta_check.py` (`TOOL_LEGS`);
add your own tools there, giving each its leg — or none — so nothing stays
unclassified.
