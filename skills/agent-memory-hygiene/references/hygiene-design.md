# Memory hygiene design

Loaded on demand. The record model, the distill-vs-hoard discipline, gating at
write time, and tuning the thresholds.

## One fact per entry, with a head

The record model that stays maintainable: **one memory = one fact**, small,
with a little structured head — an id, a source/trace id, a timestamp, a trust
level, a type (fact / project / reference / note). Small single-fact entries are
easy to verify, easy to retire, and easy to dedupe. A big blob "everything about
X" entry can't be partially retired: when one clause in it goes stale, the whole
blob is suspect and you either keep a lie or lose the rest.

Types earn different treatment:

- **fact / rule / policy** — authoritative; may steer behavior. Only verified
  sources may be this type (that's the poison check).
- **project** — ongoing-work state; expires fast, review often.
- **reference** — a pointer to an external source of truth (a dashboard, a
  vault path, a ticket). This is where a secret's *location* lives — never its
  value.
- **note** — a low-trust observation, including anything sourced from untrusted
  content. Recallable, but never asserted as fact.

## Distill, don't hoard

The instinct is to remember everything "in case." That instinct degrades recall:
every low-value entry is noise the retrieval has to rank around, and past some
size the useful memory stops surfacing. The discipline is the same as
`experience-loop`'s — **distill the lesson, retire the raw material.** Ten raw
run logs become one "runs that do X fail when Y; guard with Z," sourced and
dated; the ten logs go. The size cap in the lint is not an arbitrary limit; it's
a forcing function for this distillation.

## Gate at write time

The highest-leverage place to run these rules is the moment an entry is *written*,
not a nightly audit:

- **No source → refuse.** Make provenance mandatory at write; it's trivial then
  and impossible to reconstruct later.
- **Secret detected → refuse and rewrite.** Replace the value with a vault
  reference before it's ever persisted.
- **Untrusted source → force type `note`.** An entry created from a web page or
  inbound message cannot be written as `fact`; the writer must down-type it or
  verify it first.
- **Duplicate → merge, don't append.** On a near-identical write, update the
  existing entry's timestamp instead of adding a second.

A store fed through such a gate barely needs the audit. Run the audit anyway for
what predates the gate, and to catch freshness (which only accrues with time).

## Freshness: age is not correctness

An old entry is not wrong — it is *unreviewed*. The danger is asserting a
then-checked fact as if it were now-checked. So freshness is a review trigger,
not a delete trigger: past the max age, the entry is surfaced for
re-verification. Re-verify → bump the timestamp; can't re-verify → retire. Tune
`--max-age-days` to how fast your domain moves: infrastructure facts (regions,
endpoints) age in weeks; a user's stable preference ages in a year. If entries
vary widely, store a per-type max age and lint against it.

## Secrets and PII: memory is not a vault

Memory's whole design — durable, auto-recalled, low-scoped — is the opposite of
what a secret needs. A token written to memory is read into every future context
that recalls around it, logged wherever memory is logged, and copied wherever the
store is backed up. The rule is absolute: **the secret lives in a vault; memory
holds a reference.** The lint's secret patterns (API keys, tokens, private keys,
inline passwords) are a floor — add your own formats — and it flags email
addresses as a PII signal worth a human look before persisting.

## Poison: the injection that outlives the page

`agent-isolation` breaks the lethal trifecta *within a session*. Memory extends
the timeline: a malicious instruction read from untrusted content and written to
memory as a fact is recalled long after the session ends, in sessions that never
touched the untrusted source. The defense is the type discipline — untrusted in,
`note` out — plus verification before any promotion to `fact`. Treat "another
agent told me" and "a web page said" identically: not authoritative until
independently verified.

## Tuning the size cap

The cap is per store or per namespace; set it where recall quality starts to
drop, not where storage runs out (storage is never the constraint). If you can't
get under the cap by deduping, that's the distillation signal: the store is
carrying raw material that should have become a few distilled entries.
