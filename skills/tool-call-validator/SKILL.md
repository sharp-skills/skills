---
name: tool-call-validator
description: Validate an agent's proposed tool calls before they execute — known tool, complete arguments, destructive operations explicitly approved, no redundant repeats — so a model's mistake can't become a real side effect, and shrink what needs validating by pinning the parameters that never legitimately vary instead of delegating them all to the model. Use this when an agent can run shell commands, write files, call APIs, or otherwise act with consequences; when you see loops of the same call fired repeatedly; when a tool ran on a placeholder path the model never filled in; or when defining a tool's parameters. Works for any tool-using runtime (Claude Code, OpenAI/Codex function calls, LangGraph/CrewAI tool nodes) — it inspects the call, not the model.
license: Apache-2.0
---

# Tool Call Validator

A human calling a tool has intent; a model calling a tool has a probability distribution. Most of the time they coincide — and then the model proposes `rm -rf node_modules`, decides the call "seemed to hang," and proposes it twice more; or it writes to `<path-to-config>` because it never resolved the placeholder; or it fires the same fetch seven times "to be sure." None of these are exotic — they're the ordinary texture of a model driving tools under uncertainty. This skill is a **pre-flight check between the proposed call and the executor**: cheap, deterministic, and it inspects the call, not the model, so it works under any tool-using runtime.

It is the runtime cousin of `mechanize-agents`' rule that LLM-authored payloads are untrusted input — here the untrusted thing is the whole tool call.

## The four rejections

1. **Unknown tool.** The tool isn't in the declared schema — a typo or a hallucinated tool name. You never dispatch to a tool you didn't allow; an unrecognized tool is a hard stop, not a best-effort guess.
2. **Incomplete or placeholder arguments.** A required argument is missing, or an argument still carries a placeholder the model never filled — `<path>`, `TODO`, `assumed`, `your-key-here`, an empty string. Executing on a guessed value is exactly how the wrong file is overwritten or the wrong record deleted. Reject and make the model resolve it first.
3. **Unapproved destructive call.** The tool is marked destructive, or an argument matches a destructive pattern (`rm -rf`, `drop table`, `truncate`, `mkfs`). Destructive calls require explicit approval — a flag a human or a policy sets — not the model's confidence. This is the same "dry-run by default, execution by explicit consent" discipline `mechanize-agents` applies to side-effectful handlers.
4. **Redundant repeat.** This exact (tool, args) already ran earlier in the batch. The "it didn't seem to work, run it again" loop is caught by comparing each call against the ones already issued. Redundant reads waste budget; redundant writes and requests cause real double-effects.

## Shrink the surface before you validate it

Validation happens at call time. There is a cheaper control one step earlier, at **tool-definition
time**, and it is routinely skipped: every parameter a tool exposes is either **pinned** — fixed by
whoever wired the tool up — or **delegated** to the model. That choice is yours to make per
parameter, and most tooling defaults to delegating everything, because it is one less decision and
it demos well.

**A pinned parameter cannot be wrong.** It needs no placeholder check, no destructive-pattern scan,
no approval flag, and it cannot be steered by an injected instruction. Every parameter you pin
removes a class of failure instead of catching it.

So decide deliberately, and delegate only what genuinely varies with the task:

| Usually pinned | Usually delegated |
|---|---|
| which calendar, which repo, which table | the event title, the commit message, the query |
| the recipient list of a broadcast | the body of a single reply |
| the root of a write path | the filename under it |
| region, environment, tenant | the record being acted on |

The four rejections above exist for what remains delegated. This section is about not digging the
hole; the validator is the net under it. Related: `prompt-injection-guard` — a pinned parameter is
one an injected instruction cannot reach, which is why the pin/delegate split is a security decision
and not only a correctness one.

## Why a check, not a prompt

You can *ask* a model to double-check its tool calls (many system prompts do — the draft this skill grew from was a "pre-flight checklist" the agent runs on itself). That help is real but it degrades under exactly the pressure that produces bad calls: a crowded context, a retry loop, a long session. A deterministic check outside the model doesn't degrade. Keep the self-check in the prompt if you like; put the *enforcement* in code.

## Run vs read

| Resource | Action | Why |
|---|---|---|
| `scripts/tool_call_check.py` | **RUN** | Validates a JSONL batch of proposed calls against a tool schema: unknown tool, missing/placeholder args, unapproved destructive, redundant repeat. |
| `scripts/extract_tools.py` | **RUN** | Build the allowlist schema from a real MCP `tools/list` (names + required args), so the source of truth is the server, not your memory. Flags for human destructive-review in two buckets — general executors (`bash`→ add `destructive_patterns`) vs side-effecting names (→ mark `destructive`) — but never guesses destructiveness. |
| `references/policy-design.md` | **READ** | Writing the tool schema, destructive-pattern design, where to wire the check (pre-dispatch hook), and what to do on a rejection. |
| `examples/selftest.sh` | **RUN** | Proves each rejection on shipped good/bad batches. |

```bash
python3 .../tool_call_check.py --schema tools.json --calls proposed.jsonl
```

## Common pitfalls

- **Allowlisting by omission.** A tool not in the schema is rejected — good — but that means the schema must be complete and current, or legitimate tools get blocked. Treat it as the source of truth (see `registry-ssot`).
- **Destructive by name only.** `bash` isn't destructive; `bash` running `rm -rf` is. Detect destructiveness on the *argument value* via patterns, not just a per-tool flag.
- **Approval as a model-set field.** `approved:true` must come from a human or a policy layer, never from the model itself — otherwise it approves its own destruction.
- **Placeholder blindness.** Models emit `<path>` and `TODO` far more than people expect; without the placeholder check they sail straight into the executor.
- **Dedup across the wrong scope.** Deduping within one batch/turn catches the tight loop; a legitimate retry after a genuine failure is different — scope the window so you flag the "to be sure" repeat, not a deliberate re-run.
- **Delegating every parameter because the builder made it the default.** "Let the model decide" is one click in most tool builders and one omitted field in most SDKs, so tools drift toward maximum delegation without anyone choosing it. Audit an existing tool's parameters and pin the ones that never legitimately vary — usually the target, the tenant, the recipient list.

## Verification checklist

- [ ] `sh examples/selftest.sh` passes (safe batch → 0; unknown/placeholder/unapproved-destructive/redundant/missing-arg → 1; missing schema → 2).
- [ ] The tool schema lists every allowed tool and its required args, and is kept current.
- [ ] Each parameter was a deliberate pin-or-delegate decision, not the builder's default; the ones that never legitimately vary are pinned.
- [ ] Destructive tools/patterns are declared, and `approved` is set outside the model.
- [ ] The check runs pre-dispatch (a hook or wrapper), not as advice the model may skip.
- [ ] Rejections return a message the model can read and act on (resolve the placeholder, request approval), not a bare denial.

## Related skills in this bundle

- `mechanize-agents` — "LLM-authored payloads are untrusted input" and "dry-run by default"; this skill applies both at the tool-call boundary.
- `governance-hooks` — a `PreToolUse` hook is the natural place to run this check; governance guards *which files/zones*, this guards *which calls*.
- `agent-isolation` — a tool call is where an exfil or destructive capability is actually exercised; validating the call complements isolating the session.
- `registry-ssot` — the tool schema is another source of truth; derive it once, don't scatter allowed-tool lists across prompts.
