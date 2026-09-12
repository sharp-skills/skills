---
name: prompt-contracts
description: >-
  Keep a multi-agent system's agent prompts, output JSON schemas, and routing registry aligned as one enforced contract — no layer silently teaches or accepts a status the router will reject — and keep each prompt under real change control: pinned by content hash, changelogged, rollback-ready. Use this when a run dies in a reject/retry loop on a "valid-looking" output, when schemas or prompts drift from the registry, when a prompt's reference example contradicts the schema, before flipping a contract from warn to enforce, or when a prompt edited in place makes a regression untraceable to a version.
license: Apache-2.0
---

# Prompt Contracts for Multi-Agent Pipelines

In an event-driven multi-agent system the agent's output `status` is not decoration — it usually **is the routing event**. The dispatcher reads it and decides who runs next. That means three artifacts must agree at all times: the **registry** (which events each agent may publish), the **schema** (which statuses the output validator accepts), and the **prompt** (which statuses the model is taught to emit, explicitly or by example). Any two of them drifting apart produces the worst failure class: outputs that look valid, validate locally, and are rejected by the router every single time.

This skill exists because of a production incident: the first live run of a multi-agent pipeline died on `status: "SUCCESS"`. The schema offered `SUCCESS` in its enum, the model dutifully picked it, and the dispatcher — which only accepts statuses listed as that agent's publishable events — rejected every retry. Nothing was "broken" in any single file; the contract between files was.

## Use this when

- A pipeline run loops on reject/retry although each output "looks fine".
- Prompts, schemas, or the routing registry are edited by different people (or different agents) without a cross-check.
- A prompt contains worked examples ("reference output") that were written before the current schema.
- You are about to flip a soft contract (log-and-warn) to hard enforcement and need to know the prompts won't fight the gate.
- You inherited a pipeline and want to know whether its three layers still agree.

Do not use this as a substitute for output validation at runtime. The contract check is static: it guarantees the layers *agree*, not that the model will comply. Keep the runtime gate; this skill makes sure the gate and the prompts are on the same side.

## The contract rule

> **One layer is the source of truth (the registry). Every other layer may only narrow it, never extend it.**

Concretely, for every non-observer agent:

1. Every value in the schema's `status` enum must be a registry-published event of that agent, an allowed skip form (e.g. `*_SKIPPED`), or the shared failure event (e.g. `PIPELINE_FAILED`).
2. Every status literal a prompt teaches — including inside worked examples — must satisfy the same rule.
3. Exemptions are explicit and named (observer/delivery agents whose status is an ack, not a bus event), never implicit.
4. Workaround supersets ("temporarily also allow X") are deleted, not accumulated. A relaxed shim that outlives its incident becomes the next incident.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/contract_check.py` | **RUN** | Static contract check across registry, schemas, and prompts; CI-friendly exit codes. |
| `scripts/prompt_version_check.py` | **RUN** | Versioning: prompt on-disk hash matches its active version's pin, active resolves, every version has a changelog, rollback target exists. |
| `references/failure-catalog.md` | **READ** | The real drift incidents this skill encodes — what leaked past naive checks and why. |
| `references/config.md` | **READ** | The JSON config shape: how to map your registry, schemas, prompts, and exemptions. |
| `references/versioning-design.md` | **READ** | The version manifest shape, promotion/rollback flow, A/B via versions, and how prompt versions ride with the code that reads them. |
| `examples/selftest.sh` | **RUN** | Proves the contract checker AND the versioning checker on shipped fixtures with planted incidents (exits 0 / 1 / 2). |

Start with help:

```bash
python3 multi-agent-engineering/prompt-contracts/scripts/contract_check.py --help
```

Run against a config:

```bash
python3 multi-agent-engineering/prompt-contracts/scripts/contract_check.py --config contract-config.json
```

Fail CI on any violation:

```bash
python3 multi-agent-engineering/prompt-contracts/scripts/contract_check.py --config contract-config.json && echo OK
```

Check prompt versioning (pins, changelog, rollback):

```bash
python3 multi-agent-engineering/prompt-contracts/scripts/prompt_version_check.py --manifest prompts.json
```

## What the checker enforces

1. **Enum subset (schemas).** For each agent, collect every `status` enum/const in its output schema — **recursively through `oneOf` / `anyOf` / `allOf`** — and require each value to be allowed by the registry. Recursion is not optional: in production, a forbidden `["SUCCESS"]` sat inside a `oneOf` branch and escaped a top-level-only check for weeks.
2. **Prompt exemplars.** Scan each agent's prompt files for taught status literals (`"status": "X"` in JSON examples and `status: X` in text) and require the same subset rule. Prompts teach by example more strongly than by instruction; a stale example beats a correct rule.
3. **Explicit wiring.** The config maps agents to schemas and prompts explicitly. This is a deliberate design choice: a previous version derived the mapping by transforming IDs between layers, and one agent whose alias didn't match was silently skipped — a fail-open hole found only by audit. Explicit maps fail loudly (`unknown agent`, `missing file`) instead of silently checking nothing.
4. **Named exemptions only.** Observer/ack agents are listed in the config; anything not listed is checked.

## Repair procedure (when the checker fails)

1. **Registry wins.** Do not widen the registry to make a schema pass — that inverts the source of truth. First ask: *should* this agent publish that event? If yes, that's a routing design change (review it as one); if no, fix the schema.
2. Align the schema enum to exactly the allowed set, or drop the enum entirely and let the runtime gate be the sole enforcer — an enum that repeats the registry adds a second copy of the truth that can drift.
3. Grep the prompt for the removed statuses, **including worked examples and "reference output" blocks** — that is where stale statuses hide.
4. Delete any relax-shims added during the incident.
5. Re-run the checker, then run one live/recorded pipeline pass before declaring the contract restored — static agreement first, behavioral confirmation second.

## Versioning: the same rigor for the prompt you *change*

Contracts keep the prompt you *have* aligned with the registry. But the prompt is the most load-bearing configuration in the system and the least likely to be under real change control: it gets edited in the file, in place, on a Tuesday, and every run's behavior shifts with no version, no changelog, no way back — so when a run regresses, the first question, *did the prompt change?*, has no answer. `scripts/prompt_version_check.py` closes that gap by treating each prompt as a **released artifact**, with four guarantees:

1. **Pinned by content hash.** The on-disk prompt's hash must equal the hash recorded for its active version. A mismatch means the file was edited without a version bump — the exact silent drift that makes regressions unattributable. **A version number is a claim; a content hash is a fact** — pin the bytes so the number can't lie.
2. **Active resolves.** The version marked live actually exists in the history — no dangling pointer to a prompt no record describes.
3. **Changelog per version.** Every version says *what changed and why*. "v3" tells you nothing; "v3: forbid inventing files after the hallucinated-path incident" tells the next person whether to trust it.
4. **Rollback target exists.** `rollback_to` points at a real prior version, so a regression at 2am is a one-pointer revert, not an archaeology dig.

Contracts and versioning are the two halves of **prompt governance**: contracts check the prompt is *sound* (it agrees with the registry today); versioning checks it is *governed* (you know which version is live, what changed, and how to revert). Wire both in CI on any change to a prompt.

## Common pitfalls

- **Checking only top-level enums.** Composed schemas (`oneOf`/`anyOf`/`allOf`) hide status variants; always collect recursively.
- **Trusting ID transformations between layers.** `MY_AGENT` → `my-agent` → `MA` conversions rot; one unmatched alias = one agent silently unchecked. Map explicitly.
- **Fixing the schema but not the prompt's examples.** The model imitates the example, the gate rejects it, and the loop returns.
- **Widening the registry under incident pressure.** The registry is the contract; widen it only as a reviewed routing change.
- **Exempting agents implicitly.** "The check skips what it can't map" is how fail-open holes are born. Exemptions must be a named list.
- **Keeping the relaxed shim.** Temporary supersets become permanent unless deletion is part of the incident's definition of done.
- **Editing the prompt file in place (versioning).** The default failure; the content-hash pin exists precisely to make it a red build instead of silent drift. Bump the version, don't overwrite.
- **A version number people bump by hand.** It drifts the moment someone forgets. Pin the *content* so the number can't lie; an empty or cosmetic changelog ("update") is the same failure one layer up.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes — contract (clean → 0, planted `oneOf` + prompt-example violations → 1, empty glob → 2) AND versioning (well-versioned → 0, edit-in-place/empty-changelog/dangling-rollback/missing-active → 1, missing manifest → 2).
- [ ] `python3 .../contract_check.py --help` works.
- [ ] Each live prompt is pinned by content hash to its active version, with a changelog and a resolvable rollback target.
- [ ] The config maps every non-observer agent to its schema and prompt files (checker reports counts).
- [ ] A deliberately planted forbidden status in a `oneOf` branch is caught (exit 1).
- [ ] A deliberately planted `"status": "BOGUS"` inside a prompt's worked example is caught (exit 1).
- [ ] Missing files or unparseable JSON exit 2, not 0.
- [ ] CI runs the checker on every change to prompts, schemas, or the registry.

## Related skills in this bundle

- `registry-ssot` — the layer below: makes the registry the machine-read source of truth this contract narrows from. Establish it first; without it there is nothing canonical to check against.
- `observability-tracing` — records the reject/retry loops this skill prevents; use a trace to confirm behavior after repair.
- `eval-harness` — the runtime complement: scores recorded outputs against the structural contract this skill keeps aligned.
