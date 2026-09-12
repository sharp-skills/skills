---
name: agent-memory-hygiene
description: Keep an agent's persistent memory trustworthy — every entry has provenance, entries expire and get re-verified, secrets never land in memory, and untrusted content is never stored as fact — so recall stays reliable instead of slowly poisoning the agent. Use this when agents write to and read from a long-lived memory store, when old remembered "facts" start misleading current runs, when memory grows without bound, or when you worry a prompt injection could persist into memory. The recall a stale or poisoned memory returns is worse than no memory at all.
license: Apache-2.0
---

# Agent Memory Hygiene

Persistent memory is what turns a stateless model into an agent that accrues context across runs — and it is exactly as dangerous as it is useful. Every property that makes memory helpful (it's durable, it's recalled automatically, it's trusted as background) is a liability when the memory is wrong: a stale fact is asserted as current, a secret written once is read into every future context, an attacker's "fact" survives long after the malicious page is closed. Unmaintained memory doesn't stay neutral; it rots, and rotten recall is worse than none.

This skill is the hygiene that keeps recall trustworthy. It comes from operating a file-per-fact agent memory: each memory is a small record with provenance and a timestamp, distilled and retired on a discipline rather than hoarded. The check enforces four properties over the store.

## The four properties

1. **Provenance.** Every entry records where it came from — a source or trace id. A fact with no origin can't be trusted, can't be audited, and can't be retired *on cause* when its source is later found wrong. "I remember this" is not enough; "I remember this from run X" is.
2. **Freshness.** Every entry carries a timestamp, and an entry past a max age without re-verification is flagged. Memory is point-in-time: the moment you assert an old fact as if it were checked today, you mislead. Old isn't automatically wrong — it's *unreviewed*, which is its own risk. The remedy is re-verify or retire, not blind trust.
3. **No secrets.** Memory is read into many contexts with little scoping, so a credential in memory is a credential leaked broadly and repeatedly. Keep the secret in a vault and a *reference* to it in memory ("token in vault at ops/deploy"), never the token itself. The check greps for API keys, tokens, private keys, inline passwords, and PII.
4. **No poison.** An entry sourced from untrusted content (a web page, an inbound message) may not be stored as an authoritative fact. This is how a prompt injection becomes *permanent*: the malicious instruction is recorded as truth and recalled forever. Untrusted-sourced entries stay typed as untrusted notes, never promoted to fact without verification (the memory-side of `agent-isolation`'s trifecta thinking).

Plus two store-level guards against **unbounded growth**: exact-duplicate text is flagged (dedupe), and a total-size cap forces the distill-and-retire discipline — an ever-growing store drowns the relevant memory in noise and degrades recall.

## Write-time, not just audit-time

The check is written to run as a lint (over the whole store, in CI or on a schedule), but its real value is at **write time**: gate what goes *into* memory. Reject the entry with no source, refuse to persist a secret, type an untrusted fact as a note. A memory that never admits rot doesn't need to be cleaned. Run the lint anyway — it catches what slipped in before the gate existed.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/memory_lint.py` | **RUN** | Lints a store for provenance, freshness (`--max-age-days`, `--now`), secrets/PII, untrusted-as-fact poison, duplicates, and a size cap (`--max-entries`). |
| `references/hygiene-design.md` | **READ** | The one-fact-per-entry model, distill-vs-hoard, write-time gating, and tuning age/size for your domain. |
| `examples/selftest.sh` | **RUN** | Proves each rot on a shipped healthy and rotten store. |

```bash
python3 .../memory_lint.py --store memory.json --max-age-days 180
```

## Common pitfalls

- **Storing the secret instead of a reference.** The most damaging and the easiest to do; memory is not a vault.
- **Promoting untrusted content to fact.** The recall looks authoritative later, and nothing in the entry reveals it began as an attacker's web page. Type-tag on write.
- **Hoarding.** "Might be useful someday" fills the store with noise that pushes the useful entry out of recall. Distill the lesson, retire the raw material.
- **Provenance-free writes.** Convenient at write time, impossible to audit at recall time; you can't clean what you can't trace.
- **Treating old as trusted.** Age is not correctness; an unreviewed old fact is a claim about *today* made from *then*. Re-verify or retire.
- **Linting but never gating.** Auditing after the fact finds rot late; the leverage is refusing to write it.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (healthy → 0; secret/no-provenance/stale/poison/duplicate/over-cap → 1; missing store → 2).
- [ ] Every entry has a source/trace id and a timestamp.
- [ ] Secrets are references to a vault, never literal values.
- [ ] Untrusted-sourced entries are typed as untrusted, never as authoritative facts.
- [ ] The store has a size cap and a distill/retire routine, and the check runs at write time, not only as an audit.

## Related skills in this bundle

- `experience-loop` — the *productive* side of memory: distilled learnings folded into prompts. This skill keeps the raw store the loop draws on clean; the two share the "distill then retire" discipline.
- `agent-isolation` — untrusted-input handling; poison prevention is the same principle applied to what memory records, so an injection can't persist.
- `observability-tracing` — provenance is a `trace_id`; a memory entry's source points back into the run that created it.
- `event-envelope` — the same "carry the correlation id" habit that makes traces auditable makes memory auditable.
