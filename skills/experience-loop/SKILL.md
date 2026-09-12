---
name: experience-loop
description: Give a multi-agent system persistent experience — per-agent smoothed confidence and structured learnings recorded at run completion, loaded at session start, and periodically distilled into prompt/skill improvements. Use this when every session starts from zero and repeats last month's mistakes, when agent performance data exists only in people's memory, when accumulated "learnings" JSON grows but nothing changes, or when you need to know which agents are trending down.
license: Apache-2.0
---

# Agent Experience Loop

Models don't learn between sessions — **the system around them has to**. Each run produces evidence: how confident each agent's outputs were, what worked, what failed and why. Untracked, that evidence evaporates at session end and every pipeline run starts amnesiac. This skill is the loop that captures it: record per-agent experience as structured data at run completion, load it at session start, and — the step everyone skips — periodically distill it into actual prompt and skill changes.

The hard-won insight behind the design: **the JSON file is a buffer, not a knowledge base.** Accumulating learnings feels like progress; it is inventory. The leverage arrives only when a recurring learning graduates into a prompt rule, a schema tightening, or a bundle skill — after which the learning is *retired* from the buffer. A learnings file that only grows is a diary, not a loop.

## Use this when

- The same class of mistake recurs across sessions and everyone remembers fixing it before.
- You can't answer "which agent has been trending down this month?" with data.
- A learnings/memory file exists, grows, and has never caused a single prompt change.
- Sessions are orchestrated by different runtimes/people and experience fragments across them.

## The loop, precisely

```
run completes ──> record: per-agent confidence (EMA) + structured learnings
                            │
session starts <── load: agent bootstraps context with its prior experience
                            │
periodically  ──> distill: recurring categories → prompt/skill changes → retire entries
                            │
continuously  ──> staleness check: a memory nobody writes is decoration (CI)
```

Four design decisions, each paid for:

1. **EMA, not average.** Confidence is smoothed exponentially (`new = α·observation + (1−α)·old`, α≈0.3): recent behavior dominates, ancient history fades, and one outlier can't swing the number. A plain average makes month-old behavior forever equal to yesterday's.
2. **Structured entries, not prose.** Each learning is `{category, insight, outcome}`. Categories are what make distillation possible — you can count them; counting free-text is archaeology.
3. **Capture at completion, not at approval.** Real bug from the source system: experience was recorded at the final approval gate, so every agent that ran *after* it (deploy, analytics, growth) accumulated nothing — invisibly, for weeks. Hook the recorder to the actual end of the run.
4. **Staleness is an error.** If the file hasn't been written in N days of active development, the loop is broken at the capture end — and everything downstream is silently running on stale experience. The check belongs in CI/session start, not in someone's memory.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/learnings.py` | **RUN** | The loop's mechanics: `record` (EMA + entry), `show`, `check-staleness` (CI-friendly). One JSON file, no dependencies. |
| `references/loop-design.md` | **READ** | The capture-point bug, why EMA, the distillation discipline, retirement rules. |
| `examples/selftest.sh` | **RUN** | Proves EMA math, recording, and staleness detection on a shipped fixture. |

```bash
python3 .../learnings.py record --file learnings.json --agent analyst \
    --confidence 88 --category schema_drift \
    --insight "output enum drifted from registry" --outcome "aligned; added CI check"
python3 .../learnings.py show --file learnings.json [analyst]
python3 .../learnings.py check-staleness --file learnings.json --max-age-days 14
```

## Common pitfalls

- **Hoarding.** A thousand learnings and zero prompt changes means the distillation step is missing — the loop's entire ROI lives there.
- **Recording prose.** "Agent did okay-ish, some issues with the schema thing" cannot be counted, so it cannot graduate. Category + insight + outcome, always.
- **Capture at the wrong boundary.** Anything that runs after your capture point learns nothing; audit which agents actually write entries (the staleness check per agent, not just per file).
- **Trusting the memory across structural changes.** After a prompt rewrite or model change, an agent's old EMA describes a different agent; re-bootstrap it (the record notes when and why).
- **Loading raw learnings into every context.** Load the distilled summary per agent, not the archive — context is a budget (see `cost-budgeting`).

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (EMA math exact, entries recorded, staleness caught).
- [ ] The recorder runs at run completion, and post-approval agents demonstrably accumulate entries.
- [ ] `check-staleness` runs in CI or at session start.
- [ ] At least one prompt/skill change in the repo history traces back to a distilled learning (the loop has closed at least once).
- [ ] Retired learnings are marked, not deleted — the audit trail of *why a prompt changed* is part of the system's provenance.

## Related skills in this bundle

- `observability-tracing` — traces are the raw evidence; learnings are its digested form. Confidence values recorded here often originate in trace `meta`.
- `eval-harness` — eval scores over time and EMA confidence are two views of the same question ("is this agent getting worse?"); disagreements between them are worth investigating.
- `prompt-contracts` — distillation's most common output is a contract tightening; the loop feeds the contract.
- `two-layer-critic` — review findings are high-grade learning input; wire the critic's structured findings into the same categories.
