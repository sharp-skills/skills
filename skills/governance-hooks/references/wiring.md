# Wiring governance hooks

## zones.json shape

```json
{
  "override_env": "GOVERNANCE_OVERRIDE",
  "no_touch": [
    {"path": "config/registry.json", "reason": "single source of truth"},
    {"path": "config/protocols/*",   "reason": "core protocol files"},
    {"path": "migrations/*",         "reason": "immutable once applied"},
    {"path": "**/auth/**",           "reason": "requires explicit security review"}
  ],
  "secret_globs": [".env", ".env.*", "*.pem", "*.key", "*credentials*", "*token*", "id_rsa*"],
  "secret_cmd_patterns": ["\\bcat\\b[^|;&]*\\.env\\b", "printenv", "\\benv\\b\\s*($|\\|)"],
  "drift_files": ["config/*.json", "config/protocols/*.md"],
  "write_tools": ["Edit", "Write", "MultiEdit", "NotebookEdit"],
  "read_tools": ["Read"],
  "shell_tools": ["Bash"]
}
```

Field notes:

- `no_touch[].reason` is not decoration — it is what the blocked model reads.
  Write it as an instruction ("request a review via the owner"), not a label.
- `secret_cmd_patterns` are regexes over the raw command string. Keep them
  few and high-signal; a pattern that misfires on routine commands will get
  the hook disabled by an annoyed human — the fail-open failure mode.
- `drift_files` are globs relative to `--root`. Put the sources of truth
  here (registry, protocols) — and `zones.json` itself.

## Hook wiring (pre-tool-use)

Any harness that supports pre-tool-use hooks with JSON on stdin and
"non-zero exit blocks" semantics can run the adapter directly:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit|Read|Bash",
        "hooks": [{"type": "command",
                   "command": "python3 skills/governance-hooks/scripts/governance_check.py hook --config zones.json --root ."}]
      }
    ]
  }
}
```

Conventions the adapter follows (match your harness's contract):

- stdin: `{"tool_name": "...", "tool_input": {...}}`
- exit 0 = allow; exit 2 = block, stderr is surfaced to the model
- unparseable input or internal error = exit 0 (fail-open; see SKILL.md)

Keep the hook wiring file itself out of version-controlled agent-editable
space, or list it as a no-touch zone — otherwise the first thing a confused
agent edits is the guard.

## CI wiring (drift)

```yaml
- name: Governed config drift check
  run: |
    python3 skills/governance-hooks/scripts/governance_check.py drift-check \
      --config zones.json --lock governance.lock.json
```

Commit `governance.lock.json`. Refreshing it (`drift-snapshot`) must be a
reviewed change: the diff of the lock file *is* the review of the config
change. A CI job that re-snapshots automatically is a gate that agrees with
everything.

## Session-start pattern

Run `drift-check` at session start as well as in CI: an agent session that
begins on drifted config should know before it builds on sand. Pair with the
registry validator from `registry-ssot` — drift says "something changed",
the validator says whether what changed is still coherent.

## Override discipline

- One env var, named in the config, default off.
- Set it in the shell for a maintenance window; never export it in profiles,
  CI configs, or wrapper scripts.
- Grep for the variable name in the repo as part of security review — any
  committed occurrence is a finding.
