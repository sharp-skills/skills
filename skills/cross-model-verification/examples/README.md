# Examples — cross-model-verification

Run the self-test (no network, stdlib only — the "model" is a shipped fake):

```bash
sh selftest.sh
```

| Case | Fixture | Expected |
|---|---|---|
| Complete hand-off | `handoff.good.json` | exit 0 |
| Empty required field + no-touch/modify contradiction | `handoff.bad.json` | exit 1, both named |
| Cross-model layer wired | `fake_verifier.py` reports one blueprint gap | exit 1, gap surfaces with `(cross-model)` tag |
| Dead verifier | `--verifier-cmd /nonexistent-model-cli` | exit 0 + "control arm" note — fails SOFT |

`fake_verifier.py` demonstrates the verifier contract: any CLI that takes
the prompt as its last argument and prints `{"gaps": [], "contradictions": []}`
JSON. Swap in a real model CLI without changing anything else.
