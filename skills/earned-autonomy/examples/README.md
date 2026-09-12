# Fixtures

Two grant ledgers and a self-test. Actions, resources and principals are generic
(`email.send`, `queue/support-inbox`, `agent:responder`) so the fixtures carry no
project vocabulary.

- **`grants.good.jsonl`** — four grants that are each defensible for a *different*
  reason, which is the point: the ledger of a healthy system is not uniform. Most grants
  sit low, one is at `ask` with a channel a person genuinely reads, and one has been
  earned all the way to `act` — on the alert firehose nobody reads, which is exactly why
  asking there would have been the weaker choice. Passes with and without `--strict`.

- **`grants.bad.jsonl`** — seven grants, nothing malformed. Each is the kind of record a
  real implementation writes, and each carries `_fails_because`:

  | grant_id | what it demonstrates |
  |---|---|
  | `g-self-granted` | perfect record, correct scope, real expiry — and an agent wrote the grant |
  | `g-unearned` | promoted on three good proposals because someone decided that was enough |
  | `g-borrowed-record` | twelve genuine clean refunds — on small accounts, buying autonomy on enterprise ones |
  | `g-wildcard` | one verb, every target; the consequential case was never assessed |
  | `g-propose-that-acts` | labelled as the safe rung while actually creating the event |
  | `g-ask-into-the-void` | looks like the most cautious setting in the file and is the least effective |
  | `g-forever` | correct today, with no date on which anyone looks again (`--strict` only) |

  Six violations by default, seven under `--strict`.

- **`selftest.sh`** — 18 assertions: both fixtures at both strictness levels, every failure
  mode named individually, proof that a trailing streak resets on one edit (built inline,
  not from the fixtures), proof that low rungs are not asked for a track record, a
  configurable threshold that bites on an already-clean ledger, and four fail-loud cases
  (missing file, empty ledger, unknown verdict, malformed JSON).

```sh
sh selftest.sh
```

Two of the fail-loud cases are deliberate design statements. An empty ledger exits 2
because a file that governs nothing must not report success. An unrecognised verdict —
`"approved"` where the vocabulary says `"accepted"` — exits 2 rather than being counted
as unclean, because a typo that silently shortens a streak and a typo that silently
lengthens one are equally bad, and neither should be guessed at.
