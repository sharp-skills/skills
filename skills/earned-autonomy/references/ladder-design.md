# Ladder design

Reference for the grant record, running the promotion loop, demotion, approval fatigue,
and keeping the ledger out of the agent's reach. Read this before writing a project's
first ledger or changing the checker's expectations.

## The grant record

One JSON object per line, one record per `(action, resource, principal)`.

```json
{
  "grant_id": "g-act-alert-tuning",
  "action": "pr.open",
  "resource": "repo/alert-rules",
  "principal": "agent:sre",
  "rung": "act",
  "granted_by": "human:sre-lead",
  "granted_at": "2026-05-05",
  "expires": "2026-11-05",
  "side_effect": true,
  "review_channel": { "name": "alerts-firehose", "watched": false },
  "evidence": {
    "scope": "pr.open@repo/alert-rules",
    "verdicts": ["accepted", "accepted", "..."]
  }
}
```

| Field | Required | Meaning |
|---|---|---|
| `grant_id` | yes | Unique. Duplicates are a config error, not a violation. |
| `action` | yes | The verb, in whatever vocabulary the system already uses. |
| `resource` | yes | The specific target. `*` is refused. |
| `principal` | yes | Who is being granted — usually `agent:<name>`. |
| `rung` | yes | `observe` / `propose` / `ask` / `act`. |
| `granted_by` | yes | **Must start with `human:`.** The invariant. |
| `evidence.verdicts` | for `act` | Ordered oldest→newest. `accepted` / `edited` / `rejected` / `ignored`. |
| `evidence.scope` | for `act` | Must equal `<action>@<resource>`. Stops borrowed records. |
| `side_effect` | checked | Whether the action changes anything outside the system. |
| `review_channel` | for `ask` | `{name, watched}`. `watched` must be literally `true`. |
| `expires` | `--strict` | Date the grant must be revisited. |

`ignored` is a distinct verdict on purpose. A proposal nobody responded to is not an
approval, and recording it as one is the most common way a streak becomes fiction.

## Running the promotion loop

1. The agent operates at its current rung and produces proposals.
2. A human returns a verdict per proposal. Capture it where the human already works —
   a merged pull request, a sent draft, a click — never as a separate chore, or the
   verdicts stop being recorded and the ladder freezes.
3. `accepted` extends the streak. Anything else resets it to zero.
4. At the threshold, the system **offers** the promotion. It never applies it.
5. A human accepts, and that acceptance writes the ledger.

Step 4 is the part that gets collapsed in implementations and must not be: an automatic
promotion at a threshold is a self-grant with extra steps, because the only human input
is one that happened before the criterion was known.

### Choosing the threshold

Ten is a default, not a finding. Scale it to the cost of one bad instance and to how
often the grant is exercised — a grant used fifty times a day earns its streak in an
afternoon, so a low threshold there means almost nothing. Where the action is expensive
or irreversible, `ask` may simply be the permanent rung; not every grant should reach
`act`, and a ladder where everything ends up at the top was measuring the wrong thing.

## Demotion

A ladder that only goes up is a permission list with extra ceremony. Demote on:

- an incident traced to the grant — immediately, before the post-mortem;
- a streak reset at an autonomous rung (the agent acted, a human disagreed);
- expiry, if nobody renews;
- a change in the substrate: a new model version, a rewritten prompt, a new tool. The
  record was earned by a different agent than the one now running — see
  `model-version-pinning`, which makes those changes explicit and reviewable.

Demotion is cheap: the agent returns to producing proposals. Say so out loud when
designing, because teams resist demotion as if it were a punishment rather than a
return to the default.

## Approval fatigue is a design signal, not a user problem

When people start clicking approve without reading, the usual reaction is to widen
permissions "since they approve everything anyway". That reasoning inverts the evidence:
blind approvals are not clean verdicts, so the record supporting that promotion is
already corrupt.

The actual causes and their fixes:

- **Too many proposals** — the grant is too broad. Narrow the resource.
- **Proposals that are always fine** — the grant is a promotion candidate, but only if
  the verdicts were genuine. Sample a few and check they were read.
- **Proposals nobody can judge** — the proposal lacks the context needed to approve it.
  Fix the proposal, not the permission.

`ignored` exists for exactly this: it records the difference between "a human agreed"
and "nobody looked".

## Keeping the ledger out of reach

Three practical requirements, all checkable by inspection:

1. **No tool writes it.** Grep the agent's tool list for anything that can edit the
   ledger path. The most common leak is a general-purpose file-write tool with a
   working directory that happens to contain the ledger.
2. **The agent does not read its own streak.** A visible counter is farmable: propose
   only trivially acceptable things until the number is high enough. Give the agent its
   current *rung* if it needs to reason about what it may do — never the progress toward
   the next one.
3. **The ledger is not in the same trust domain as the workspace.** If a prompt injection
   can reach it, the ladder is advisory. `agent-isolation` covers that boundary.

## What this skill deliberately does not do

- It does not authenticate anyone. `human:sre-lead` is an identity your system already
  established; this skill records which identity conferred authority, not how it was proven.
- It does not validate individual calls at runtime — that is `tool-call-validator`. This is
  the standing policy the validator enforces.
- It does not bound recursion or fan-out. Those are structural caps that hold no matter how
  well-behaved an agent is (`delegation-guards`), and a grant never relaxes them.
