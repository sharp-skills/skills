# Tool-call policy design

Loaded on demand. How to write the tool schema, design destructive patterns,
wire the check, and handle a rejection well.

## The tool schema is a source of truth

`tools.json` declares every tool the agent may call and, per tool, its required
arguments, whether it is destructive, and any destructive argument patterns.
Because an unknown tool is rejected, this file is load-bearing: an incomplete
schema blocks legitimate work, a stale one lets a removed tool through. Keep it
where the rest of your wiring truth lives (`registry-ssot`) and update it in the
same change that adds or removes a tool — never as an afterthought in a prompt.

Minimal shape:

```json
{"tools": {
  "bash":       {"required": ["command"],
                 "destructive_patterns": ["rm -rf", "\\bdrop\\s+table\\b", "truncate"]},
  "write_file": {"required": ["path", "content"], "destructive": true},
  "read_file":  {"required": ["path"]},
  "http_get":   {"required": ["url"]}}}
```

## Destructiveness lives in the argument, not the tool name

`bash` is not destructive; `bash` running `rm -rf /` is. `write_file` usually
is (it overwrites). So model destructiveness two ways:

- **`destructive: true`** — the tool is *always* side-effectful (write, delete,
  deploy). Every call needs approval.
- **`destructive_patterns`** — regexes matched against argument *values*, for
  tools that are usually safe but can be dangerous (`bash`, `sql`). Cover the
  irreversible verbs you actually run: `rm -rf`, `drop table`, `truncate`,
  `mkfs`, `> /dev/sd`, force-push, `DELETE FROM ... ` without a `WHERE`.

Patterns are a floor, not a proof — they catch the common shapes, not every
possible phrasing. Pair them with the `destructive: true` flag for whole classes
of tools, and with `agent-isolation` so the *capability* isn't in a session that
also reads untrusted input.

## Approval must come from outside the model

`approved: true` is the consent signal for a destructive call. It must be set by
a human, a policy engine, or an allowlist rule — **never by the model that
proposed the call**, or you have built self-approval. In practice: the check
runs, a destructive call without approval is surfaced to a human-in-the-loop
(see `agent-isolation`'s irreversible-action gate), the human approves, and only
then does the approved call re-enter the executor.

## Placeholders: more common than you think

Models emit unfilled placeholders constantly — `<path>`, `TODO`, `assumed`,
`your-api-key-here`, `""`. Each is a value the model *intended* to resolve and
didn't. Executing on one writes to the literal path `<path>` or POSTs an empty
body. The default placeholder regex covers the common shapes; extend it for your
domain (ticket ids like `PROJ-000`, obvious sample hosts like `example.com` when
that's never real for you).

## Where to wire it

- **Pre-dispatch hook / wrapper.** The check belongs *between* the model's
  proposed call and the executor — a `PreToolUse` hook in Claude Code, a
  middleware around function-call dispatch in an SDK, a wrapper on the tool
  runner in LangGraph/CrewAI. It reads the proposed `{tool, args}`, returns
  allow or block-with-reason. Exit `0` allow, `1` block, `2` its own error
  (fail-open on `2` if you'd rather never wedge — see `governance-hooks`).
- **Batch/plan review.** When an agent emits a *plan* of several calls at once,
  run the whole batch through so the redundant-repeat check has the batch to
  compare against.

## Handle rejections so the model can recover

A bare "denied" produces retry loops (the same lesson as `status-gates` and
`governance-hooks`). Return *why*, in terms the model can act on:

- placeholder → "arg `path` is still `<path>`; resolve it to a real path and
  re-issue."
- unapproved destructive → "this call matches `rm -rf`; request approval before
  it can run."
- redundant → "this exact call already ran this turn; use the prior result."

The model reads the reason and routes around it legitimately, instead of
rephrasing the same bad call.

## What this check is not

It is not a sandbox and not a permission system — it validates the *shape and
intent* of a call, it does not contain what a call can do once approved.
Containment is `agent-isolation` (what capabilities share a session) and the
runtime's own sandbox. Layer them: this catches the obviously-wrong call early
and cheaply; isolation bounds the damage of the ones that get through.
