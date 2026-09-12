# Delegation budget design

Loaded on demand. Setting the caps, where to enforce them, handling a breach, and
how this composes with cost and triage.

## Setting the three caps

Start from what the work *should* need, add headroom, and treat a breach as a
signal — not from what a catastrophe looks like.

- **max_depth** — how many delegation hops a legitimate task needs. Most agent
  work is 2–4 deep (orchestrator → specialist → helper). Depth is the most
  dangerous axis because cost compounds with it, so keep it tight; a task that
  truly needs depth 6 should have to say so.
- **max_fanout** — how many children one agent should spawn. A planner splitting
  into 3–5 parallel specialists is normal; 20 is a red flag that the agent is
  enumerating rather than decomposing. Cap per node so one bad decision is
  bounded.
- **max_total** — the ceiling on the whole tree, and the one that actually bounds
  spend. Set it from the token/cost budget: if each agent costs roughly C and
  your per-run budget is B, `max_total ≈ B/C` with margin. This is the cap that
  catches the depth×fan-out product the other two miss.

If your tasks vary widely, carry the policy per task-type (a research task
tolerates more fan-out than a code fix) rather than one global number.

## Where to enforce: gate the spawn, audit the trace

Two enforcement points, both worth having:

- **Pre-spawn gate (prevention).** Before an agent actually spawns a child, call
  the admission mode against the tree-so-far:
  `delegation_check.py --tree tree-so-far.json --policy policy.json --candidate parent=<id>`.
  It computes this spawn's depth (parent depth + 1), the parent's resulting
  fan-out, and the new total, and returns **ALLOW** (exit 0) or **DENY** (exit 1)
  with a reason the agent can act on ("fan-out would hit 6; consolidate these
  sub-tasks"). This stops the explosion instead of explaining it.
- **Post-hoc audit (detection).** Run the same script in `--tree`-only mode over
  the completed delegation trace (reconstructed via `observability-tracing`) in CI
  or monitoring, so a slow drift toward bigger trees is caught before it becomes an
  incident.

The gate needs the tree-so-far plus the candidate; the audit needs the whole
trace. Same check, same policy — so the number that gates a spawn can't drift
from the number that audits the run.

## Handling a breach well

A breach should teach, like every other guard in this bundle:

- **Depth/fan-out:** return the specific cap and the shape ("depth would be 5,
  max 4"), so the agent restructures — consolidate siblings, flatten a chain —
  rather than blindly retrying the same spawn.
- **Total:** this usually means the task was under-scoped; surface it to
  `task-triage` or a human to re-plan, not to the spawning agent to squeeze.
- **Cycle:** hard stop, always. A cycle is never intended; break it and log the
  path (A→B→A) so the delegation logic that created it can be fixed.

Never respond to a breach by silently raising the cap in code — that's how the
guard becomes decorative. Raising a cap is a deliberate, reviewed decision.

## Composition with cost and triage

Three layers govern how much a run does, at different granularities:

- **task-triage** — chooses the *initial* crew for a task (the smallest that can
  deliver). It sets the starting shape.
- **delegation-guards** — bounds how that crew may *grow* at runtime through
  spawning, so a modest start can't balloon.
- **cost-budgeting** — the token/dollar backstop underneath both; even a
  well-shaped tree gets stopped if it spends past budget.

They fail independently and catch different things: triage prevents an oversized
start, delegation guards prevent runaway growth, cost budgeting prevents
expensive-but-small-tree runs. A system that spawns agents wants all three.

## Cycles deserve special care

A delegation cycle is qualitatively worse than a big tree: a big tree
*terminates* (expensively), a cycle does not. The ancestor check is cheap and
absolute — a node may never appear in its own parent chain. If your delegation
can route by agent *role* rather than instance, watch for role cycles too
(role A always delegates to role B which delegates to role A); the same guard
applies once you resolve roles to the concrete spawn tree.
