# Prompt versioning design

Loaded on demand. The manifest shape, the promote/rollback flow, A/B via
versions, and keeping prompts reproducible with the code that reads them.

## Manifest shape

One manifest is the source of truth for prompt versions; keep it beside the
wiring registry (`registry-ssot`), not scattered across the codebase.

```json
{"prompts": {
  "planner": {
    "active": "v3",
    "file": "planner.txt",
    "rollback_to": "v2",
    "versions": {
      "v1": {"hash": "…", "changelog": "initial planner"},
      "v2": {"hash": "…", "changelog": "forbid inventing files"},
      "v3": {"hash": "<sha256 of planner.txt>",
             "changelog": "order steps, require verifiability"}}}}}
```

- **`hash`** is sha256 of the prompt file's bytes. It's the pin; the on-disk
  file must hash to the active version's value.
- **`active`** is the live version. Promotion is changing this pointer, not
  editing a file.
- **`rollback_to`** is the version a revert jumps to — usually the previous
  known-good active.
- **`changelog`** is per version: what changed and why, one line minimum.

## Promote and roll back as pointer moves

The payoff of versioning is that live-behavior changes are pointer moves over an
immutable history, not edits:

- **Promote:** add the new version (new file content → new hash → new entry with
  a changelog), then move `active` to it. The old version stays in the history,
  bytes intact.
- **Roll back:** move `active` back to `rollback_to`. Because every version's
  content is pinned and retained, the revert lands on exact known bytes — no
  reconstruction, no "which edit was it".

Never *edit* a released version's file. A change is always a *new* version; the
history is append-only. That's what makes "what is running and what changed"
answerable at any moment.

## A/B testing via versions

Two active candidates is just two version pointers plus a split:

- Keep `v3` and `v4` both in the history, each pinned and changelogged.
- Route a fraction of runs to each (the split lives in your dispatcher, not the
  manifest).
- Measure with `eval-harness` against a baseline; the winner becomes `active`,
  the loser stays in history (and is a ready rollback target if the winner
  regresses later).

Because both candidates are pinned, an A/B result is attributable to exact prompt
bytes — not "the prompt around that week".

## Version the prompt *with* what reads it

A prompt is only reproducible alongside its contract. If the output schema, the
registry enums, or the code path that consumes the prompt changed in the same
breath, a pinned prompt alone won't reproduce the behavior. Two practices keep
them coherent:

- **Bump in the same change.** The commit that edits `planner.txt` also adds the
  new version entry and moves `active`. Never let the file and the manifest
  drift apart, even for a minute — that minute is when someone hits the mismatch.
- **Co-pin the contract.** When a prompt version depends on a specific schema
  version (`prompt-contracts`), record that in the changelog or a `requires`
  field, so a rollback of the prompt knows whether the schema must roll back too.

## Where the check runs

- **CI, on every change** to a prompt file or the manifest: the pin check fails
  the build if a file was edited without a bump, catching the drift at review
  time rather than in production.
- **Pre-deploy:** verify `active` resolves and the rollback target exists before
  a release, so you never ship a dangling pointer.

The check is deterministic and stdlib-only, so it runs the same in CI, on a
laptop, and in a pre-deploy hook — no environment to reproduce.
