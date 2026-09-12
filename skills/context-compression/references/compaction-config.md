# Compaction config notes

Loaded on demand. Why compaction is a config surface, how to choose the
summary model, and what to keep out of the compressor entirely.

## Native, not hand-rolled

Agent runtimes that hold a conversation for you also compact it for you: when
context approaches the window, the runtime summarizes older turns into a shorter
form and continues. It is on by default and exposed as configuration — the
summary model, a trigger threshold, a target ratio, a count of recent turns to
protect. Concretely: Claude Code exposes compaction, Hermes ships a
`ContextCompressor` with a separately-configurable summary model, OpenClaw has
compaction (and a distinct memory-flush), and orchestration SDKs like LangGraph
and CrewAI expose equivalent summary/trim hooks. Different names, same knobs. The earlier instinct to build a swappable `compress(text) -> text`
component is redundant: swapping the summary model is a single config field, and
you get correct integration with the runtime's own turn accounting for free.

So the deliverable you actually own is a **config**, and the way you make a
config trustworthy is the same as any contract in this bundle: lint it in CI.

## Choosing the summary model

Two hard constraints and one soft one.

- **Hard — window ≥ main model.** The summarizer must ingest the context that
  overflowed the main model, all at once. A window smaller than the main
  model's cannot, and the runtime errors rather than summarizes. This kills the
  "tiny local model as summarizer" idea for any large-window main model.
- **Hard — actually declared.** Name the summary model explicitly. Leave it
  blank and the runtime falls back to a default you didn't choose — often the
  main model itself, which works but may be the expensive one you were trying to
  spare.
- **Soft — cheap is fine, because summarizing isn't reasoning.** The summary
  pass is a mechanical rewrite, not the hard thinking. A fast, inexpensive
  *large-window* model is the sweet spot: it clears the window bar and costs a
  fraction of the main model. Two common shapes: (a) a fast large-context
  hosted model as the summarizer, main model does the reasoning; (b) the main
  model summarizes itself — always window-safe, simplest, but you pay main-model
  rates for the rewrite.

Do **not** reach for a small local model to "save money/RAM" here — it fails
the window rule, and the money it saves is a run it corrupts.

## The three numeric settings

- **`threshold`** (fraction of window that triggers compaction): fire with
  headroom, not at the brink. ~0.5 is a common default — half-full triggers a
  compaction so there's room to hold both the old context and the new summary
  while the rewrite happens.
- **`target_ratio`** (how small to compress to): must sit well below the
  threshold. If you trigger at 0.5 and only compress to 0.5, the next turn is
  over threshold again — you compact every turn (thrash), burning summary calls
  and churning context. ~0.2 against a 0.5 threshold gives real breathing room.
- **`protect_last_n`** (recent turns never compacted): the agent is actively
  reasoning over the tail of the conversation. Compact those and you remove its
  working memory mid-task. Keep a generous window of recent turns verbatim.

## Compaction vs memory-flush vs distilled learnings

Three different time horizons, don't conflate them:

- **Compaction** — within one run, shrink old turns to fit the window. Lossy,
  automatic, ephemeral.
- **Memory-flush** — persist selected facts to durable memory so they survive
  the run. Configurable separately in most runtimes; use it for things that
  must outlive compaction.
- **Distilled learnings** — hand-curated lessons folded back into prompts and
  templates across runs. That's `experience-loop`, not compaction: it's how a
  system "compresses" experience permanently, where per-run compaction only
  buys window space for the current run.

## What not to let compaction touch

- **The task/goal statement and active contract** — protect or pin these; a
  summarizer that paraphrases the spec changes the job.
- **Structured state the pipeline routes on** — statuses and envelopes live on
  the bus and in traces, not in the chat history the summarizer rewrites; keep
  them out of the compressible transcript so a summary can't mangle a routing
  decision.
- **The freshest turns** — `protect_last_n` exists exactly for this.

The rule of thumb: compaction is allowed to blur *narrative history*, never
*load-bearing state*.
