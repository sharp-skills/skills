# Envelope design notes

Loaded on demand. The rationale behind each field and each rule in the wire
contract, plus how to evolve it without a flag day.

## Envelope vs payload — the dividing line

One question decides where a field goes: **does the bus or the tracer read it?**

- The **bus** routes on `event` and needs `agent`, `runtime`, `trace_id`, `ts`
  to route, correlate, and record. Those are envelope fields.
- Everything an agent produces for the *next agent* to consume — file lists,
  diffs, scores, blueprints, verdict reasons — is `payload`. The bus treats
  `payload` as opaque bytes; it is validated against the per-event output
  schema by the receiving side, never by the envelope check.

The discipline pays off when you add an agent: its payload schema is its own
business, and the bus, the tracer, and every other runtime are untouched. Put
an agent-specific field in the envelope and you've coupled all of them to it.

## Why each required field is required

- **`trace_id`** — without it the tracer cannot stitch a run that hops
  runtimes; the event is orphaned the instant it leaves the process that made
  it. This is the field people are tempted to drop on "internal" events and the
  one they most regret dropping.
- **`agent`** / **`event`** — routing and attribution. `event` is the
  subscription key; a typo here is a silent dead-end, which is why
  `status-gates` validates the value at the boundary.
- **`runtime`** — lets the tracer show *where* work happened and lets policy
  differ by runtime (e.g. a browser runtime is untrusted; see
  `agent-isolation`). Closed enum, kept equal to the dispatcher's set.
- **`ts`** — ISO-8601 UTC. Ordering and latency come from it; local wall-clock
  strings from mixed runtimes are unorderable.

## Optional fields

- **`pipeline_mode`** (FAST/STANDARD/DEEP/CRISIS) — set once at phase 0,
  read-only downstream. Lets tiering (`two-layer-critic`, `cost-budgeting`)
  read one value instead of re-deciding stakes per agent.
- **`confidence_score`** — 0–100 for decision agents, `null`/absent for
  infra/L0 agents. The validator allows null precisely so infra events aren't
  forced to fake a score. Booleans are rejected explicitly (`true` would slip
  through a naive `0 <= x <= 100`).

## Why stdlib validation, not a schema library

The envelope's job is to be identical across runtimes. A validation dependency
that one runtime has and another lacks quietly reintroduces the exact split the
envelope exists to remove: an envelope "passes" where the library is installed
and "fails" where it isn't, or two library versions disagree on a corner. So
the canonical rules are a few dozen lines of stdlib that you either run directly
or vendor byte-for-byte into every runtime. The JSON Schema file is the
*human* spec and the drift anchor for the runtime enum; it is not the runtime
validator.

## `additionalProperties: true` on purpose

The envelope is a **floor**, not a cage. A runtime may attach extra fields
(a provider request id, a cache flag) without a schema change, and older
consumers ignore them. Set `false` and every additive change becomes a breaking
change for whichever runtime updates last — the slowest one gates the fastest.
Requiredness and the closed enums carry the safety; open extension carries the
evolvability.

## Evolving the envelope without a flag day

- **Adding an optional field:** safe any time — old consumers ignore it.
- **Adding a runtime or mode:** update the schema enum *and* the dispatcher set
  in the same change; the drift check turns a forgotten half into a red build.
- **Making a field required, or removing one:** this is breaking. Roll it as a
  two-step: emit-and-tolerate (all runtimes emit the field, validation still
  optional) until every runtime is updated, then flip validation to required.
  If you version the envelope, a top-level `v` lets consumers branch during the
  transition; prefer additive evolution so you rarely need it.

## Where this sits in the stack

The registry (`registry-ssot`) is the source of truth for *which* agents and
events exist. The envelope is the source of truth for their *shape on the wire*.
Status gates check the `event` value at the routing boundary; tracing reads
`trace_id`/`ts`/`runtime` to build the timeline. The envelope is the thin,
boring layer all three stand on — boring on purpose.
