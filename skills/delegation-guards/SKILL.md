---
name: delegation-guards
description: Bound agent-to-agent delegation with explicit budgets — max recursion depth, max fan-out per agent, max total agents, and cycle detection — so a system where agents spawn subagents can't explode into a runaway swarm. Use this when agents can delegate to or spawn other agents (orchestrator-subagent, swarm, recursive planning), when a run's cost or latency grows unpredictably, or when you suspect a delegation loop. Depth and fan-out each look reasonable locally while their product is a bomb.
license: Apache-2.0
---

# Delegation Guards

Give an agent the ability to spawn subagents and you've added a multiplier to your system — and multipliers cut both ways. The useful case is a planner fanning work to a few specialists. The failure case is the same mechanism with no ceiling: an agent that keeps delegating one level deeper, or spawns a dozen children each of which spawns a dozen more, or delegates in a circle. What makes this dangerous is that it's *quiet* — every individual decision to delegate looks locally reasonable; the explosion is an emergent property of the tree, visible only when you look at the whole shape. This skill puts explicit budgets on that shape.

It's the structural cousin of `cost-budgeting`: that caps tokens per run, this caps the *topology* that generates the tokens. You want both — a tree can blow the token budget long before you'd want it to, and catching it at the delegation layer is earlier and cheaper.

## The four budgets

1. **Depth.** No delegation path from the root exceeds `max_depth`. Recursion depth is where "just delegate the hard part" turns into an exponential — each level looks like one more reasonable hop, and three reasonable hops is a different order of magnitude than one.
2. **Fan-out.** No single agent spawns more than `max_fanout` children. One node fanning wide is a swarm in miniature; capping per-node fan-out keeps any single delegation decision bounded.
3. **Total.** The whole tree stays under `max_total` nodes. This is the guard that catches what depth and fan-out miss individually: depth 3 and fan-out 4 are each fine, but 4³ is 64 agents. The product is the bomb; cap it directly.
4. **Cycles.** No agent is its own ancestor, and every parent reference resolves. A delegation cycle (A → B → A) is an infinite loop with a token meter running — the most expensive failure and the one a local check can't see.

## Budgets are a forcing function, not just a safety net

A tight delegation budget does more than prevent runaways — it *shapes the design*. If a task genuinely needs depth 6 and fan-out 10, the budget forces you to notice that and decide deliberately (raise it, or restructure), instead of discovering it as a surprise bill. Set the caps at what the work *should* need with headroom, and let a breach be a signal that either the task grew or an agent is misbehaving. This is the same philosophy as `cost-budgeting`'s decompose-over-extend: the limit is where you think, not just where you stop.

The check itself is intentionally small — a graph walk over depth, fan-out, total, and cycles. The value isn't a clever algorithm; it's the **discipline of gating every spawn against a budget you chose at design time**, and the insight that the bomb is the *product* of locally-reasonable decisions, not any one of them. A simple check wired at the spawn point beats a sophisticated one run after the swarm exists.

## Audit the tree, but *gate the spawn*

A budget you only check after the run tells you why the bill was huge; a budget checked *before each spawn* stops the bill from happening. So the check runs both ways, over the same tree and policy:

- **Audit** (`--tree`) — verify a whole delegation tree (completed, or in-flight and reconstructed from the trace): depth, fan-out, total, cycles, dangling parents. This is the backstop.
- **Admission** (`--candidate parent=<id>`) — the pre-spawn gate. Given the current tree and one proposed child, it computes the *would-be* depth (parent depth + 1), the parent's would-be fan-out, and the new total, and answers **ALLOW** or **DENY** *before the spawn happens*. Wire this where an agent actually spawns: the orchestrator asks admission first, and a DENY means "restructure or raise the cap deliberately", never a surprise bill.

Enforcement belongs at admission — refusing the breaching spawn is strictly better than explaining it afterwards. The audit is what catches whatever slipped past the gate (a spawn that bypassed it, a tree assembled by hand). Because both read the same policy, the number that gates a spawn can't drift from the number that audits the run.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/delegation_check.py` | **RUN** | Two modes: **audit** a whole tree against depth/fan-out/total + cycles/dangling parents, or **admit** one proposed spawn (`--candidate parent=<id>`) before it happens (ALLOW/DENY). |
| `scripts/extract_spawns.py` | **RUN** | Reconstruct the delegation tree from an `observability-tracing` trace (span `parent` links) so you audit the *real* shape, not a hand-written manifest. Pipe it straight into the checker. |
| `references/budget-design.md` | **READ** | Setting the caps, where to enforce (the pre-spawn gate vs the post-hoc audit), handling a breach, and the relationship to cost and triage. |
| `examples/selftest.sh` | **RUN** | Proves the audit (within-budget passes; depth/fan-out/cycle/total/dangling fail) and admission (ALLOW plus DENY per budget and unknown parent). |

```bash
# audit a whole tree (backstop)
python3 .../delegation_check.py --tree spawns.json --policy policy.json
# gate one spawn before it happens (enforcement)
python3 .../delegation_check.py --tree spawns.json --policy policy.json --candidate parent=n3
```

## Common pitfalls

- **Guarding depth or fan-out but not total.** Each can be within cap while their product isn't; the total cap is the one that actually bounds cost.
- **No cycle detection.** A delegation loop never terminates on its own; without an ancestor check it runs until a timeout or the budget dies.
- **Auditing but never gating.** A post-hoc audit tells you why the bill was huge; the admission mode (`--candidate`) refuses the spawn that would breach *before* it happens. Gate every spawn and keep the audit as a backstop — don't settle for the autopsy.
- **Caps set at the runaway, not the design.** If the budget is so loose it only trips on catastrophe, it never shapes the design; set it near intended usage with headroom.
- **Ignoring dangling parents.** A node whose parent isn't in the tree means the trace is incomplete or corrupted — trust nothing else about it until it's explained.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes: audit (within budget → 0; depth/fan-out/cycle/total/dangling → 1; missing tree → 2) and admission (ALLOW → 0; DENY on depth/fan-out/total/unknown parent → 1; malformed candidate → 2).
- [ ] `max_depth`, `max_fanout`, and `max_total` are all set — total especially.
- [ ] The spawn path calls admission (`--candidate`) and honours a DENY, not just an after-the-fact audit.
- [ ] Cycles and unresolved parents are treated as hard failures.
- [ ] Caps are set near intended usage with headroom, so a breach is a real signal.

## Related skills in this bundle

- `cost-budgeting` — caps tokens/run; this caps the delegation topology that spends them. Enforce at both layers.
- `task-triage` — decides the *right* crew for a task; delegation guards ensure that crew can't recursively balloon past it.
- `observability-tracing` — the delegation tree is reconstructed from the trace; `trace_id`/parent links are what this check reads.
- `multi-agent-trust` — a spawned subagent is a peer; its instructions carry peer-tier authority, not the spawner's.
