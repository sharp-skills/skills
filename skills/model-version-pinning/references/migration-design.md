# Migration design

Reference for the manifest format, building a probe set, reading a trajectory diff, and
staging a migration. Read this before changing the checker's expectations or writing a
project's first manifest.

## The manifest

One entry per place a model is chosen. Not one per vendor and not one for the system —
the granularity is the point, because migrations are staged per component.

```json
{
  "components": [
    {
      "id": "orchestrator",
      "model": "vendor-large-4-1-20260318",
      "resolved": "vendor-large-4-1-20260318",
      "probe_set": "probes/orchestrator.jsonl",
      "upgrade": "shadow",
      "runtime": { "client": "vendor-cli", "version": "2.1.216" },
      "compare": "trajectory",
      "pinned_at": "2026-03-20"
    }
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Component name. Must be unique; duplicates are a config error, not a violation. |
| `model` | yes | The identifier your code requests. |
| `resolved` | yes | The identifier the provider reported. **Equality with `model` is the pin test.** |
| `probe_set` | checked | Path to the frozen inputs replayed against both versions. |
| `upgrade` | checked | `shadow` or `manual`. `auto` is refused. |
| `runtime` | checked | Client/SDK/CLI version verified with this model, or explicit `null`. |
| `compare` | `--strict` | `trajectory` or `trajectory+score`. `score` alone is refused under `--strict`. |
| `pinned_at` | no | Date the pin was last moved. Useful for spotting components nobody revisits. |

`resolved` has to be captured, not typed. Read it from the provider's response metadata at
pin time and paste it in; a hand-copied value defeats the check it exists to perform.

### Why `runtime` must be present even when it is null

An absent key is ambiguous — nobody can tell whether the toolchain was considered and found
irrelevant, or forgotten. An explicit `null` is a decision on the record. The checker
therefore refuses the missing key and accepts the null, the same shape as `replay: skip` in
`durable-sessions`.

This is not theoretical: swapping to a newer model can fail outright against a client
released before it, and the error surfaces as a rejected model identifier rather than as
"upgrade your CLI". Pinning both is what turns that into a one-line diagnosis.

## Building a probe set

**Draw from recent production traffic.** The single most useful property of a probe set is
that it looks like what actually arrives: fragments, typos, wrong casing, truncated pastes,
the input someone sent from a phone. A set of clean hand-authored examples measures a system
that does not exist, passes every migration, and catches nothing.

Practical shape:

- 30–100 inputs per component is enough to see behavioural drift; this is not a statistical
  exercise, it is a diff.
- Include the inputs behind past incidents. Those are the behaviours you already know matter.
- Include a few inputs the component should *refuse*. Refusal-boundary movement is one of
  the most common and least noticed version changes.
- Store expected *behaviour* loosely if at all. The probe set's job is to produce comparable
  runs, not to assert correctness — that is `eval-harness`'s job.

**Freeze it.** Edit it between migrations, never during one. A set that changed while you
were comparing cannot tell you what changed.

## Reading a trajectory diff

Run both versions over the frozen set with tracing on (`observability-tracing`), then read
the pairs. What to look for, in rough order of how often it bites:

1. **Tool-call sequence.** Same answer reached a different way is still a change — it will
   surface later as a latency, cost, or permission difference.
2. **Output shape.** Field ordering, nesting, markdown vs plain, list vs prose. Parsers
   downstream are coupled to this even when nobody wrote that down.
3. **Refusal and hedging boundaries.** What it now declines, and what it now accepts that it
   used to decline.
4. **Verbosity and turn count.** A model that takes more turns to reach the same place
   changes cost per task without changing cost per token.
5. **Confidence-like self-reports**, if the pipeline records them. These move sharply between
   versions and any threshold calibrated on the old values is now mis-set.

Investigate improvements as well as regressions. An unexplained improvement means the
mechanism is not understood, so the next release's change cannot be predicted either.

## Staging a migration

Per component, not per system:

1. **Order by blast radius, ascending.** Move the narrow, low-consequence components first;
   they surface the shared surprises cheaply.
2. **One component per reviewed commit**, so a later bisect can attribute a behaviour change
   to a specific pin move.
3. **Keep the previous identifier reachable** until the new pin has run in production long
   enough to have met real traffic. Rollback is the cheapest mitigation available and it
   expires the moment the old identifier stops resolving.
4. **Re-bootstrap accumulated per-agent state.** Confidence and learnings recorded under the
   old version describe a different agent (`experience-loop`).
5. **Re-check the cost profile per task.** Cost per token is not the unit that moved.

## What this skill deliberately does not do

- It does not benchmark models against each other. There is no leaderboard here and no claim
  about which model is better; the only question is whether *your* behaviour changed.
- It does not verify correctness. A pinned, probed, shadow-run model can still be wrong —
  `eval-harness` and `cross-model-verification` cover that axis.
- It does not talk to any provider. Everything is checked from the declaration, so the gate
  runs in CI with no credentials and no network.
