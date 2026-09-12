# Output parsing design

Loaded on demand. Why ambiguity beats first-match, prompting for labels, handling
each outcome, and when to abandon prose parsing for JSON.

## Why ambiguity handling is the whole point

Extracting a signal from prose is easy until the prose disagrees with itself,
which model prose does constantly — it reasons through options before concluding.
"I'd reject this on the edge case, but actually approve given the tests" contains
both verdicts. First-match extraction returns `reject`; last-match returns
`approve`; both are guesses that happen to be right or wrong depending on the
model's rhetorical order, and neither knows it guessed.

The correct behavior is to notice the conflict and refuse to resolve it silently:
report `ambiguous`, hand it back to the caller, and let a re-ask or a human decide.
This costs a round-trip occasionally; it saves you from a decision pipeline that
confidently acts on the opposite of what the model meant. The rule: **never
convert uncertainty in the source into false certainty in the output.**

## Prompt for labels — it collapses the ambiguity

The single most effective thing you can do is make the producer *label* its
signals, even while answering in prose:

```
End your response with these lines, exactly:
Verdict: <approve|reject|revise>
Score: <0-100>
Blocking: <yes|no>
```

A labeled value is extracted by the label, so the reasoning above it can mention
anything without creating ambiguity. This turns free-form output into something
nearly as reliable as JSON while keeping the model's natural narrative — the best
of both when you can't or don't want strict JSON mode. The extractor is
label-first precisely to reward this; unlabeled scanning is the fallback, and the
fallback is where ambiguity lives.

## Handling each outcome

- **ok** — use the value. It's typed and validated (enum membership, numeric
  bounds), so downstream code can trust it.
- **not_found** — the signal isn't there. Two honest responses: re-ask (prompt
  the label explicitly), or apply a *documented, deliberate* default. Never
  silently substitute a zero/false — "no verdict" and "reject" are different
  facts, and conflating them hides real failures.
- **ambiguous** — re-ask with a sharper prompt ("Respond with only `Verdict:`
  and one of approve/reject/revise"), or escalate. Bound the retries like any
  model loop (the JSON-validation path of this skill shares this discipline).
- **invalid** — a value was found but breaks its constraints (score 150, an enum
  word outside the set). Treat like ambiguous: re-ask with the constraint stated.

## Type constraints make invalid detectable

Declare the constraints in the spec so the extractor can reject nonsense:

- **enum** — the closed set of allowed values; anything else is `invalid`.
- **number** — `min`/`max` bounds; an out-of-range figure is `invalid`, and
  bounds also help disambiguate (a `0-100` score ignores a "2026" in the prose).
- **boolean** — the yes/true vs no/false vocabulary.

Without constraints, everything that parses is "valid", and you lose the
`invalid` outcome that catches the model's out-of-range or off-menu answers.

## When to stop parsing prose and demand JSON

Prose parsing (Half 1) is a fallback, and it has a ceiling. Reach for JSON +
the validation path (Half 2, `output_validate.py`) when:

- You control the producer (then just ask for JSON — strictly more reliable).
- The structure is more than a few flat signals (nested objects, lists of
  records — prose extraction gets brittle fast).
- The cost of a wrong extraction is high and re-asks are cheap (make the format
  strict rather than lean on recovery).

Use this skill when the producer is fixed, the signals are few and flat, and
narrative output is what you've got. It's a good tool for a real situation — not
the situation to design toward.
