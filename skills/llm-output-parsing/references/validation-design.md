# Output validation design

Loaded on demand. Where the safe-repair line is, how the bounded retry works,
prompting for cleaner output, and the boundary with schema contracts.

## The safe-repair line

The single decision this skill turns on: a repair is allowed only if it **cannot
change the parsed value**. On the safe side, and roughly all you should do
deterministically:

- Strip a ```json / ``` fence.
- Ignore prose before/after a balanced JSON block.
- Remove trailing commas before `}` or `]`.
- Trim surrounding whitespace.

On the unsafe side — never do these silently:

- Add a missing required field (you'd be inventing data).
- Quote a bareword or fix a broken string (you'd be guessing intent).
- Insert a missing brace/bracket (you'd be guessing structure).
- Coerce a wrong enum to the "nearest" allowed value (you'd be overriding the
  model's answer with yours).

Everything on the unsafe side is *authorship*, and authorship belongs to the
model. A parser that authors produces output that looks validated but isn't —
the worst failure mode, because nothing downstream knows to distrust it. When in
doubt, fail to a re-ask; a clean failure is cheap, a silent wrong value is not.

## The bounded retry loop

`output_validate.py` is the deterministic core of a small loop the caller owns:

```
for attempt in 1..MAX:
    raw = model(prompt)
    result = output_validate(raw, schema)     # exit 0 / 1
    if result.ok: return result.object
    prompt = original + "\nYour previous output was invalid: " + result.errors
raise NeedsHuman(last_errors)
```

Two properties make it work:

- **Feedback is specific.** Pass the exact validation errors back
  ("field `confidence` = 150 is above maximum 100"), not "invalid". Specific
  feedback fixes on the next attempt most of the time; a bare retry usually
  reproduces the same output.
- **It is bounded.** Two or three attempts is almost always enough; a model that
  can't produce a valid object by then won't at attempt ten, and each retry
  costs tokens and latency. Cap it and escalate to a human or a fallback, the
  same discipline `two-layer-critic` applies to review retries.

The script deliberately does not run the model — it stays deterministic, offline,
and testable. The loop lives in the caller, which is where the model and the cap
policy belong.

## Prompt for cleaner output (reduce the need)

Validation is the safety net; a good prompt shrinks how often you need it:

- Ask for *only* JSON, explicitly ("Respond with a single JSON object and no
  other text").
- Provide the schema or a filled example in the prompt.
- Use the provider's structured-output / JSON mode when available — it removes
  the fence-and-prose problem at the source. Validation still runs, because JSON
  mode guarantees *parseable*, not *schema-valid* (an out-of-range number is
  still parseable), but you skip most extraction work.

Extraction exists precisely because not every model or call supports a strict
mode, and because "and no other text" is a request, not a guarantee.

## Boundary with prompt-contracts and the envelope

Three layers, don't conflate:

- **prompt-contracts** — *static*, pre-runtime: is the output schema itself
  sound (its enums narrow the registry, its examples don't contradict it)?
- **this skill's JSON-validation path** (`output_validate.py`) — *runtime, per
  instance*: does *this* model response conform to that schema?
- **event-envelope** — the envelope treats the agent body as an opaque
  `payload`; this skill is how the receiving side turns that payload text into a
  validated object without trusting it blindly.

You want all three: a sound schema, checked instances, and a wire format that
keeps the body opaque to the bus until a consumer validates it.
