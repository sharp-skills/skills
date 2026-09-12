# Failure catalog — contract drift observed in production

Every entry below is a real incident from operating a production multi-agent
pipeline (30+ agents, event-driven routing, registry as single source of
truth). Names and paths are genericized; the mechanics are exact. This is the
material the checker's design decisions come from — read it before weakening
any of them.

## F-1: The schema taught a status the router rejects

**What happened.** The very first live pipeline run died in a reject/retry
loop. The agent's output schema offered `SUCCESS` in its `status` enum. The
model — reasonably — picked it. The dispatcher treats the output status as the
agent's routing event, and `SUCCESS` was not among that agent's publishable
events in the registry, so every retry was rejected with the same verdict.

**Why nothing caught it.** Each file was individually valid: the schema was
well-formed JSON Schema, the prompt was fine, the registry was fine. The
*relationship* between them was the defect, and nothing checked relationships.

**Lesson encoded.** The enum-subset check exists (schema status ⊆ registry
publishes + allowed skips + shared failure event). An enum that merely
duplicates the registry is a second copy of the truth — when in doubt, drop
the enum and let the runtime gate be the sole enforcer.

## F-2: The forbidden status hid inside a `oneOf` branch

**What happened.** After F-1, a top-level enum check was added. Weeks later an
audit found a `["SUCCESS"]` status enum sitting inside a `oneOf` variant of
another agent's schema. The top-level check never looked there; the drift had
simply moved one level down.

**Lesson encoded.** Enum collection recurses through `oneOf` / `anyOf` /
`allOf` (and `definitions`/`$defs`). A non-recursive contract check is a false
sense of safety.

## F-3: An ID alias made the check silently skip an agent

**What happened.** The check derived the agent↔schema mapping by transforming
IDs between two wiring layers (`SOME_AGENT` → `some-agent` → registry short
ID). One agent's transformed ID didn't match its registry short ID (a
human-friendly alias), the lookup returned nothing, and the code — written
fail-open, "not a registry agent, skip" — silently checked nothing for that
agent. Found only by a later audit; the agent's schema had meanwhile been
rewritten.

**Lesson encoded.** The checker refuses to derive wiring. The config maps
agents to registry IDs, schemas, and prompts **explicitly**, and a mapping
that resolves to nothing is a loud error (exit 2), not a skip. Fail-open
"convenience" in a guard is how unguarded surface is born.

## F-4: The prompt's worked example out-taught the schema

**What happened.** An orchestrator prompt contained a canonical worked example
("reference output") written months earlier. The example's `status` values
(`SUCCESS` / `BLOCKED`) predated the current registry vocabulary. The schema
had been fixed; the example had not. Models imitate examples more strongly
than they follow rules — under pressure the agent reproduced the example's
status and hit the gate.

**Lesson encoded.** Prompts are a contract layer, equal to schemas. The
checker scans prompt files for taught status literals, including inside JSON
code blocks. During repair, grep the prompt for the removed statuses —
worked examples and "reference output" blocks are where stale statuses hide.

## F-5: The relax-shim outlived its incident

**What happened.** During an earlier incident a "temporary" relaxation was
added: the validator accepted a superset of statuses "until prompts are
fixed". The prompts were fixed; the shim stayed. It was found much later,
still silently accepting statuses nothing should emit.

**Lesson encoded.** Deleting the workaround is part of the incident's
definition of done. The contract rule is *narrow-only*: layers may narrow the
registry, never extend it — and a shim is an extension.

## F-6: Observers are a *named* exemption, not a loophole

**What happened (design decision, not an incident).** Two agents (an event-bus
observer and a governance watchdog) legitimately report a delivery/ack outcome
in `status` — it is not a routing event, and forcing it into the registry
vocabulary would corrupt the routing graph.

**Lesson encoded.** Exemptions exist, but only as an explicit named list in
the config. The dangerous version is the implicit exemption ("whatever the
check can't resolve is skipped") — that is F-3 wearing a different hat.

## The repair sequence that worked

Two full alignment passes over ~29 prompts and ~25 schemas produced this
order of operations; deviating from it re-created drift:

1. Fix the **registry** only if the routing design is actually wrong (rare;
   review it as a routing change, not a validation fix).
2. Align **schemas** (or delete redundant enums).
3. Grep and fix **prompts**, especially worked examples and any "canonical
   reference" documents other prompts imitate.
4. Delete shims.
5. Re-run the static check, then confirm with one recorded pipeline run —
   static agreement first, behavior second.
