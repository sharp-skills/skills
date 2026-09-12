---
name: model-version-pinning
description: Pin every model choice to an exact artifact instead of a floating alias, keep a frozen probe set per component, shadow-run each release before users meet it, and compare trajectories rather than scores — because a score delta stays flat while behaviour moves. Pin the runtime alongside the model. Use when a system's behaviour changes with no commit, before or during a model migration, when deciding whether a new release is safe to adopt, or when per-component model choices have never been revisited.
license: Apache-2.0
---

# Model version pinning

In a system built on models, **changing anything changes everything**. A prompt that
was tuned against one version, a parser that tolerated one output shape, a router
calibrated on one refusal rate — all of it is coupled to weights you do not control
and cannot diff.

So the risk is not that a new model is worse. It is that the change arrives **with no
commit**: nothing to review, nothing to bisect, nothing to roll back to. A floating
alias is an undeclared dependency that redeploys itself.

## Use this when

- Behaviour changed and nobody changed anything.
- A migration is coming and you need to know what it will cost before committing to it.
- A new release is out and the question "is it safe to adopt?" has no procedure behind it.
- Model choices were made once, per component, and never revisited.
- A cheaper model is being considered and the comparison is about to be run on price.

## The pin test: the name you request equals the artifact you receive

Vendor naming schemes differ and will keep changing, so do not pattern-match on them.
Use the property that holds everywhere:

> Record both the identifier you **requested** and the identifier the provider **resolved**.
> If they differ, you did not pin — you named an alias and the provider chose.

This catches the dangerous case, which is not `-latest`. Everyone spots `-latest`. The
one that survives review is a family name that *looks* specific — a major version, a
tier name — and quietly resolves to whatever is newest inside that family. Same weights
today, different weights after a release, identical config.

⚠️ **Pin the runtime in the same breath.** A model swap can be blocked by a client that
predates it: the new identifier is simply rejected until the CLI/SDK is upgraded, and the
migration stalls on a dependency nobody wrote down. Record the client version that was
verified with each model, or an explicit `null` when there genuinely is no client — a
decision on the record, never an omission.

## A frozen probe set per component, or the pin is decorative

Pinning without a probe set only defers the problem: when the pin is finally moved, there
is still no way to say whether behaviour changed. Each component needs a **frozen set of
inputs replayed against both versions**.

Two rules that make the set worth keeping:

- **Build it from recent production traffic**, including the malformed, truncated and
  mistyped inputs. A probe set of clean hand-written examples measures a system that does
  not exist; the gap between development inputs and real ones is where regressions hide.
- **Freeze it.** A probe set that gets edited while you migrate cannot answer the only
  question you are asking, which is what changed.

## Compare trajectories, not scores

The single most reported trap, and the reason this skill exists as more than "write the
version down":

> A score can hold perfectly steady while behaviour shifts enough that users notice.

Aggregate scores are compressive by construction. Two independent practitioner accounts
describe the same experience — the eval number moves a point or two in either direction,
which reads as "no meaningful change", while the model has started structuring answers
differently, calling a different tool first, or refusing a category it used to accept.

So the artifact of a version comparison is **two recorded runs side by side**, read step
by step: which tools were called, in what order, where the run branched, what was refused.
Scores are a coarse tripwire for collapse; they are not evidence of sameness.

⚠️ Note the direction of the interaction with `eval-harness`: that skill's baseline gate is
correct for catching a *collapse* and is explicitly the wrong instrument here. A model swap
is exactly the case where its own documentation says to read the runs.

**Baseline against the mix you actually run, not against the newest release.** The
comparison that matters is "does this change what my users experience today", and what
they experience is whatever versions are actually deployed — usually several, sometimes
including one you forgot about.

## Shadow first, then move the pin

Ordering, and each step is load-bearing:

1. New release appears. **Nothing changes yet.**
2. Run it beside the current version on the frozen probe set.
3. Diff the trajectories. Investigate every behavioural difference, including improvements —
   an unexplained improvement is an unexplained change.
4. Fix what the diff surfaced: prompts, parsers, tool descriptions, thresholds.
5. Move the pin in a reviewed commit. Keep the old identifier reachable for rollback.

`upgrade: auto` — a component configured to move its own pin — nullifies all five steps
while leaving the probe set in place, unused. That configuration is the one this skill's
checker refuses most bluntly, because it is the one that looks safest.

## Migration is budgeted work, not a config edit

Treat a model change as a project with a cost, not a one-line diff. The cost lands in
prompts tuned to the old version's habits, output parsing, tool descriptions, cost and
latency profiles that shift under the same workload, and the toolchain upgrade above.
Budget it before committing to a date, and stage it per component rather than
all-at-once — the manifest exists to make that staging visible.

## Per-component choice, revisited on a schedule

Model choice is not one decision for the system. A narrowly scoped sub-agent can usually
run a smaller or cheaper model while the component doing the reasoning keeps the strongest
one — and which is which changes as releases land. Re-run the comparison per component
rather than adopting one model everywhere by default.

⚠️ **Routing between models has a hidden cost: switching model mid-session invalidates the
prompt cache.** A router that looks cheaper per call can cost more per task once the cache
misses are counted. Measure the saving per completed task, not per token — see
`cost-budgeting`.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/pin_check.py` | **RUN** | Reads a model manifest and refuses floating aliases, silent alias drift, missing probe sets, self-upgrading components, and unpinned runtimes. `--strict` also demands trajectory comparison. |
| `references/migration-design.md` | **READ** | Manifest fields, building a probe set from production traffic, what a trajectory diff looks for, staging a migration. |
| `examples/models.good.json` | **READ** | A manifest that can survive a release. |
| `examples/models.bad.json` | **READ** | Five plausible manifests that cannot, each carrying `_fails_because`. |
| `examples/selftest.sh` | **RUN** | 14 assertions over both fixtures. |

```sh
python3 scripts/pin_check.py --manifest models.json           # 0 pinned / 1 violations / 2 unreadable
python3 scripts/pin_check.py --manifest models.json --strict   # also demand trajectory comparison
sh examples/selftest.sh
```

The checker reads the declaration, not the provider, so it needs no credentials and no
network — it belongs in CI beside the other structural gates.

## Common pitfalls

- **Pattern-matching vendor names instead of comparing request to artifact.** Naming
  schemes change; the request-vs-resolved property does not.
- **Pinning the model and floating the client.** Half a pin. The rejected-by-old-CLI
  failure is common enough to be the default assumption, not an edge case.
- **A probe set of clean examples.** It will pass every migration and catch nothing. Build
  it from real traffic, typos included.
- **Reading the score and stopping.** The number is designed to be stable; that is what
  makes it useless as evidence of sameness.
- **Migrating everything at once.** One component at a time keeps the diff attributable.
- **Deleting the old pin on the day of the switch.** Rollback is the cheapest mitigation
  available, and only while the old identifier is still reachable.
- **Treating an improvement as self-explanatory.** An unexplained change is a change you
  cannot predict the next instance of.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (14 assertions).
- [ ] Every component declares `model`, `resolved`, `probe_set`, `upgrade`, `runtime`.
- [ ] No component is on `upgrade: auto`.
- [ ] Probe sets are frozen, and drawn from recent production inputs.
- [ ] The last migration left a reviewed commit moving the pin, and the previous
      identifier is still reachable.
- [ ] The last comparison produced a trajectory diff, not only a score.

## Related skills in this bundle

- `eval-harness` — the structural gate; explicitly *not* the instrument for a version
  change (its own baseline section says so). Use it to catch collapse, use this to catch drift.
- `observability-tracing` — produces the recorded runs that a trajectory diff reads. Without
  it there is nothing to compare but scores.
- `cost-budgeting` — where the per-task-not-per-token rule and the cache-invalidation cost
  of routing are enforced.
- `experience-loop` — an agent's accumulated confidence describes the agent *as it was*;
  after a model change it describes a different agent and must be re-bootstrapped.
- `prompt-contracts` — prompts and schemas are the parts most tightly coupled to a version;
  a migration usually lands there first.
