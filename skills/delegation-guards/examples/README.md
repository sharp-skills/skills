# delegation-guards examples

Fixtures that prove the budget check offline. Run `sh selftest.sh` (stdlib only).

| File | Role |
|---|---|
| `policy.json` | Budgets: `max_depth` 3, `max_fanout` 4, `max_total` 12. |
| `tree.good.json` | A healthy tree — root fans to 3, deepest path is 3, 8 nodes total, no cycles. |
| `tree.bad.json` | Four breaches: node `w` spawns 5 children (fan-out), path to `d4` is depth 4, `cyc1↔cyc2` form a cycle, and 13 nodes exceed the total cap. |
| `tree.admit.json` | A valid 9-node tree used for the pre-spawn gate: `p` already holds 4 children (fan-out at cap), `deep3` sits at depth 3 (at cap). |
| `policy.tighttotal.json` | Loose depth/fan-out, `max_total` 9 — isolates the total-budget DENY in admission. |
| `selftest.sh` | Audit: within budget → 0; depth/fan-out/cycle/total/dangling → 1; missing tree → 2. Admission: ALLOW → 0; DENY on depth/fan-out/total/unknown parent → 1; malformed candidate → 2. |

Try it:

```bash
# audit the whole tree (post-hoc backstop)
python3 ../scripts/delegation_check.py --tree tree.bad.json --policy policy.json
# gate one spawn before it happens (enforcement): DENY — p is already at fan-out cap
python3 ../scripts/delegation_check.py --tree tree.admit.json --policy policy.json --candidate parent=p
```

The same check works two ways: `--tree` alone audits a *completed* tree; adding
`--candidate parent=<id>` gates the *next spawn* before it happens (see
`references/budget-design.md`).
