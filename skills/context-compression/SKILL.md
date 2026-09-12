---
name: context-compression
description: >-
  Configure the context compaction that modern agent runtimes already provide, instead of coding your own — and get the settings right so it shrinks history without destroying it. Use this when long or multi-agent runs overflow the model's context window, when you're choosing which model should summarize old turns, or when compaction is "on" but the agent keeps losing track of things. The load-bearing rule: the summarizer's context window must be at least as large as the main model's, or the compaction that was supposed to save the run silently corrupts it.
license: Apache-2.0
---

# Context Compression

Long agent runs — and multi-agent runs especially — outgrow the model's context window. The instinct is to build a `compress(history) -> shorter_history` component and make it swappable. Don't. Every serious agent runtime already ships context compaction as a **configuration surface** — Claude Code's compaction, Hermes's `ContextCompressor`, OpenClaw's compaction, and the orchestration SDKs (LangGraph, CrewAI, and the rest) all expose the same knobs: you pick the summary model and a few thresholds, the runtime does the rewriting. The swappability you wanted is one config field. What's left is not code — it's getting four settings right, one of which is quietly load-bearing.

This skill is that config discipline, learned the expensive way: the appealing "use a tiny cheap local model to summarize" choice is exactly the one that breaks compaction.

## Don't build it — configure it

The correct realization is that compaction is native and config-driven. So the artifact you own is not a compressor; it's a **config you can lint**. Treat the compaction block like any other contract: check it in CI, don't eyeball it. That's what `compression_lint.py` does.

## The load-bearing rule: summarizer window ≥ main model window

Compaction fires when the running context approaches the main model's window. To summarize that context, the **summary model has to read it** — the whole thing, at once. If the summary model's context window is *smaller* than the main model's, it physically cannot ingest the history that overflowed:

> You get API errors and lost context, not a shorter conversation.

This is why the tempting choice — a small local 1.5–3B model with an 8K window as the cheap summarizer for a 400K-window main model — is wrong. The summarizer must have a window **at least as large** as the main model's. In practice that means the summarizer is another large-window model (a fast, cheap large-context model), or the main model summarizing itself. "Small and local" fails the one rule that matters.

The corollary that makes the rule cheap to satisfy: summarizing is not reasoning. You can send the summary work to a **fast, inexpensive** large-window model and keep the expensive model for the actual thinking — cost drops, the window rule still holds. (Cost tiering across models is `cost-budgeting`'s subject; this skill only insists the summarizer clear the window bar.)

## The other three settings

- **`protect_last_n`** — the freshest turns are never compacted. The agent is actively reasoning over them; summarize those and you lop off its short-term memory mid-thought. Must be a positive integer.
- **`threshold`** — the fraction of the window that triggers compaction. Fire *before* full (e.g. 0.5), not at the brink, so there's headroom to write the summary.
- **`target_ratio`** — how small to compress to. It must be meaningfully **below** the threshold (e.g. 0.2 vs 0.5). If target ≥ threshold, you compact and are immediately back over the trigger — thrashing, compacting every turn.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/compression_lint.py` | **RUN** | Resolves both models' windows from a catalog and enforces: summarizer window ≥ main, recent turns protected, ratios sane, compaction enabled. |
| `references/compaction-config.md` | **READ** | Why native beats custom, choosing the summarizer, memory-flush vs compaction, and what *not* to compress. |
| `examples/selftest.sh` | **RUN** | Proves the linter on a safe config and on one that picks a too-small summarizer. |

```bash
python3 .../compression_lint.py --config compaction.json --models models.json
```

## Common pitfalls

- **Building a custom compressor.** The runtime already has one; your version is one config field's worth of value and a maintenance burden. Configure, don't code.
- **A small-window summarizer.** The headline failure: it can't read the overflowing context, so compaction errors and drops history instead of shrinking it.
- **Assuming a model's window instead of looking it up.** The linter forces both models through a catalog so the window comparison is a fact, not a guess. A renamed model with an unknown window is a violation, not a pass.
- **`protect_last_n: 0`.** Compacts the turns the agent is mid-thought on.
- **`target_ratio ≥ threshold`.** Thrash: compact, immediately over threshold, compact again.
- **Compaction disabled on a long-running pipeline.** No error — just an overflow and silently truncated context. Enable it, or run that task on a model whose window fits the whole job.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (safe → 0; too-small summarizer, bad ratios, protect_last_n 0, disabled, unknown model → 1; missing file → 2).
- [ ] The summarizer's context window is ≥ the main model's, checked against a real model catalog, in CI.
- [ ] `protect_last_n` is set and positive.
- [ ] `target_ratio < threshold`, both in (0,1).
- [ ] Compaction is enabled on any run that can exceed the window, and you chose the summary model deliberately (no silent default).

## Related skills in this bundle

- `cost-budgeting` — sending summary work to a cheap large-window model is a cost decision; budgets there, the window rule here.
- `event-envelope` — `pipeline_mode` on the envelope can select heavier or lighter compaction per run mode.
- `observability-tracing` — a trace shows when compaction fired; if the agent "forgot" something, the timeline tells you whether a compaction ate it.
- `experience-loop` — distilled learnings are a form of hand-authored compression that survives across runs, complementary to per-run compaction.
