# multi-agent-trust examples

Fixtures that prove the trust check offline. Run `sh selftest.sh` (stdlib only).

| File | Role |
|---|---|
| `messages.good.jsonl` | Four legitimate messages: a human may ask anything; an *authenticated* orchestrator assigns a task; a peer agent makes a normal read; env content carries no instructions. |
| `messages.bad.jsonl` | Four hostile ones: an "orchestrator" arriving forwarded (spoof), a peer agent asking `disable_safety` (privileged from tier 3), env content asking `delete_data` (data as orders), and a forwarded message claiming to be human while asking `escalate_scope`. |
| `selftest.sh` | Asserts legitimate → 0; each attack and an unknown channel → 1; missing file → 2. |

Try it:

```bash
python3 ../scripts/trust_check.py --messages messages.bad.jsonl
```

The channel→tier and privileged-action maps live at the top of
`scripts/trust_check.py` — adjust them to your topology (e.g. add a signed
`transport` channel at tier 2, or add domain-specific privileged verbs).
