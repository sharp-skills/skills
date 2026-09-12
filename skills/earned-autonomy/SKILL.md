---
name: earned-autonomy
description: Let an agent earn the right to act instead of being configured with it — a four-rung ladder from observe to act, promotion paid for by a trailing run of clean human verdicts that one edit resets, grants keyed on (action, resource, principal), and the invariant that an agent can never grant itself. Choose the rung by whether a human actually watches the review channel, not by how important the action feels. Use when deciding what an agent may do without asking, when approval fatigue is pushing a team toward blanket permissions, or when permissions were set once at integration time and never revisited.
license: Apache-2.0
---

# Earned autonomy

Most systems treat autonomy as a setting: a permission list written at integration
time by whoever was configuring the thing, then never revisited. That produces the two
failure modes everyone recognises — an agent that asks about everything until people
approve blindly, or an agent handed broad authority on the strength of a demo.

Autonomy is better modelled as **a position on a ladder that has to be paid for**, and
the currency is a track record a human produced.

## Use this when

- Deciding what an agent may do without asking, and the honest answer is "we guessed".
- Approval fatigue has set in — people are clicking approve without reading, which is
  indistinguishable from having no control at all.
- An agent's permissions were set once and nobody can say what they are now.
- An agent operates on a channel nobody reads, and asking there means the work stalls.
- You are about to grant a capability because the agent "has been fine so far", and
  nobody can produce the evidence behind that sentence.

## The ladder

| Rung | What the agent does | What it costs |
|---|---|---|
| `observe` | reads; produces no artifact | nothing — reading is not authority |
| `propose` | produces a **proposal**: a draft, a pull request, a queued item | nothing; this is the default |
| `ask` | may act, after a human approves **that instance** | a channel someone actually reads |
| `act` | acts within the grant without asking | a trailing run of clean verdicts |

**The default rung for anything that leaves the building is `propose`.** The agent does
not send the email; it writes the draft. It does not change the config; it opens the pull
request. A bad proposal costs the reader ten seconds of annoyance. A bad *action* costs
trust, and trust is earned over months and lost in one incident — deliberately choosing
less capability for a smaller blast radius is the trade this whole skill is built on.

⚠️ A `propose` rung that actually causes the effect is worse than having no ladder,
because it reports a level of safety nobody has. The checker refuses it.

## Promotion is paid for, and the payment is trailing

Move a grant up when the agent has produced **N consecutive clean human verdicts on
that exact grant** — accepted with no edit. The default is ten.

**The streak is trailing, never cumulative.** One edited or rejected proposal resets it
to zero. This is the whole mechanism: a cumulative counter rewards an agent for having
been right a long time ago, which is precisely the agent you should not promote.

**The evidence must belong to the grant it is buying.** Twelve clean refunds on small
accounts is a real record and it is evidence about a cheaper mistake; it does not buy
autonomy on enterprise accounts. Borrowed evidence is the failure that passes a review
meeting, because everyone can see that the record is genuine.

⚠️ **Never show the agent its own streak.** A counter the measured thing can read becomes
a target: the reachable strategy is to propose only trivially acceptable things until the
number is high enough, which is exactly the behaviour the streak exists to rule out. See
`eval-harness` on the gate-vs-feedback split — this ledger is a gate.

## The invariant: an agent cannot grant itself

Promotion is an out-of-band act by a human principal. The ledger is not writable by the
thing it governs, and the agent has no tool that edits it.

Without this, every other rule here is decoration — an agent that can raise its own rung
holds unbounded authority no matter what the ledger says it holds. The checker treats a
non-human `granted_by` as the loudest violation in the file, even when the track record
behind it is perfect.

## Grants key on (action, resource, principal)

Not on the workflow, and not on the agent. The same verb against two targets is two
different risks: adding someone to a mailing list and adding them to the group that
confers production access are the same action and nowhere near the same permission.

A wildcard resource means the consequential case was never assessed — it was merely
included. The checker refuses `*`.

## Choose the rung by who is watching, not by what it costs

The most counter-intuitive rule here, and the one that inverts most people's instinct:

> An approval request in a channel nobody reads is not a safeguard. It is a silent
> guarantee that the work never happens.

The instinct is to route important things through approval and let unimportant things
run free. Invert it where attention is the scarce resource. A channel receiving a
thousand automated alerts a day has no human attention in it, so `ask` there means
*never* — that grant belongs at `act` with after-the-fact review, and the artifact
(a pull request, a log entry) is what makes it reviewable. Conversely, a rare
consequential event that a person will genuinely look at is exactly where `ask` earns
its cost.

Ask two questions per grant: **does a human actually read this channel**, and **is the
result reviewable after the fact?** Those decide the rung. Importance alone does not.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/autonomy_check.py` | **RUN** | Audits a grant ledger: self-granted authority, unearned or borrowed promotion, wildcard scope, proposal rungs that act, approvals routed into unwatched channels. `--strict` adds an expiry requirement. |
| `references/ladder-design.md` | **READ** | Grant record fields, running the promotion loop, demotion, what to do about approval fatigue, wiring the ledger so the agent cannot reach it. |
| `examples/grants.good.jsonl` | **READ** | A defensible ledger, including the counter-intuitive `act`-on-an-unwatched-channel case. |
| `examples/grants.bad.jsonl` | **READ** | Six plausible grants that are not defensible, each with `_fails_because`. |
| `examples/selftest.sh` | **RUN** | 18 assertions over both fixtures. |

```sh
python3 scripts/autonomy_check.py --grants grants.jsonl              # 0 clean / 1 violations / 2 unreadable
python3 scripts/autonomy_check.py --grants grants.jsonl --min-streak 20 --strict
sh examples/selftest.sh
```

## Common pitfalls

- **A ledger the agent can write.** Everything else here is decoration. Check the tool
  list, not the intention.
- **A cumulative counter instead of a trailing streak.** It only ever goes up, so it
  eventually promotes everything.
- **Counting approvals nobody read.** Blind approval is not a clean verdict; it is the
  absence of a verdict. Approval fatigue corrupts the evidence at its source — if people
  are clicking through, the grant is generating too many proposals and the fix is to
  narrow it, not to promote it.
- **Promoting on a neighbouring grant's record.** Evidence is scoped to (action, resource).
- **Granting the workflow rather than the resource.** The dangerous target rides along
  with the harmless one.
- **Treating the rung as a property of the agent.** It is a property of a grant. The same
  agent can be at `act` on one resource and `observe` on another, and usually should be.
- **No demotion path.** A ladder that only goes up is a permission list with extra steps —
  an incident should demote the grant, not just be logged against it.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (18 assertions).
- [ ] No grant's `granted_by` is an agent, and no agent has a tool that writes the ledger.
- [ ] Every `act` grant has a trailing clean streak at or above the threshold, scoped to
      that exact (action, resource).
- [ ] No grant has a wildcard resource.
- [ ] No `propose` grant causes an effect.
- [ ] Every `ask` grant routes to a channel someone actually reads.
- [ ] Grants carry an expiry, and at least one grant has been demoted at some point —
      if nothing has ever gone down, the ladder is not being used.

## Related skills in this bundle

- `experience-loop` — the closest neighbour, and the interaction is worth stating.
  It accumulates smoothed per-agent confidence and **loads it into the agent's context**
  at session start. This skill's streak is the opposite kind of object: per-*grant*, from
  human verdicts rather than self-report, and deliberately unreadable by the agent. Do not
  implement one on top of the other; a confidence score is not a permission.
- `tool-call-validator` — validates a single proposed call at execution time. This decides
  whether the call may execute unattended at all. The validator is the runtime gate; the
  ledger is the standing policy behind it.
- `durable-sessions` — governs *whether* a side effect happens; that skill governs how it
  does not happen **twice**. A grant plus an idempotency key is the complete story.
- `agent-isolation` — the ceiling on what an agent could ever touch. This skill is movement
  underneath that ceiling; it never raises it.
- `multi-agent-trust` — authority carried by an inbound message, judged by channel. Related
  question, different subject: that is trust in what arrives, this is trust in the actor.
- `delegation-guards` — structural caps (depth, fan-out) that hold regardless of behaviour.
  Orthogonal: a well-behaved agent still cannot exceed them.
