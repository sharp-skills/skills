# Triage design notes

## Where triage sits

```
goal ──> [ triage ] ──scope──> dispatcher (offers only scoped agents)
              │
              └─ scope=None  ->  legacy full-graph (triage disabled in one line)
```

Triage is a *filter over the dispatcher*, never an edit to the registry or
the routing graph. That makes it removable, testable in isolation, and
incapable of corrupting the wiring it reads.

## Why hybrid (the two failure modes it balances)

- **LLM-only routing** under-scopes: a cheap classifier reads "add a billing
  endpoint" and proposes the minimal engineering crew — without legal. That
  is not a quality miss, it's a compliance incident. Deterministic force
  rules exist because this exact class of miss is unacceptable at any rate.
- **Rules-only routing** plateaus: keyword lists misclassify novel phrasings
  and everything lands in the full-crew default, which is safe but erases
  the savings. The classifier's job is to beat keywords on recall, not to
  hold authority.

Hence the asymmetry: the LLM can only *narrow within a template*, rules can
only *add*, and the spine can't be touched by either.

## The stall class

The measured savings (33 → 16 steps on a routine task in the source system)
came with one hard lesson: every stall observed during validation was a
missing spine agent — someone whose published event was the only trigger for
a downstream scoped agent. A stalled pipeline reports no error; it simply
stops being scheduled.

The reachability check turns that into CI: within the scope, walk entry
events through publishes/subscribes until fixpoint; require a terminal event
in the reachable set. Run it for **every template** whenever the registry or
the triage config changes — both evolve, and their drift meets in the middle.

## Short routes

Some task classes shouldn't pay for the default spine at all. Pure content
in the source system branches off early: goal → analysis → copy → shipped,
skipping architecture, finance gates, engineering, and QA entirely. A short
route therefore carries its *own* core (with its own terminal), rather than
subtracting from the default spine — subtraction is how spines get severed.

## External classifier wiring

`--llm-cmd` takes any CLI; the prompt is appended as the last argument, and
stdout is scanned for the first JSON object. Requirements on the CLI: cheap,
fast, and allowed to fail — triage falls back to keyword routing on any
error, timeout, or malformed output. Do not point this at your most capable
model: the classifier holds no authority, so paying premium rates for it
buys nothing (the source system uses its cheapest available tier).

## Rollout

1. Ship with triage **logging only**: compute the scope, log it, run
   unscoped. Diff what *would* have been skipped against what actually
   contributed (traces make this a query — see `observability-tracing`).
2. Enable scoping for the task classes where the log shows clean separation
   (content is usually first).
3. Keep the full-crew default forever. New task classes earn templates by
   appearing in logs, not by speculation.
