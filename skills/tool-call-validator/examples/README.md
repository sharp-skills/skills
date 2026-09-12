# tool-call-validator examples

Fixtures that prove the pre-flight check offline. Run `sh selftest.sh` (stdlib only).

| File | Role |
|---|---|
| `tools.json` | The allowed tools: `bash` (with destructive patterns), `write_file` (always destructive), `read_file`, `http_get`. |
| `calls.good.jsonl` | Five safe calls in order — a read, a build, an *approved* `rm -rf dist`, an approved write, a health check. No repeats. |
| `calls.bad.jsonl` | One fault per line: placeholder `<path-to-config>`, unapproved `rm -rf node_modules`, the same `rm -rf` repeated (redundant), a `write_file` missing `content`, and a hallucinated `delete_database` tool. |
| `selftest.sh` | Asserts safe → 0; each fault → 1; missing schema → 2. |

Try it:

```bash
python3 ../scripts/tool_call_check.py --schema tools.json --calls calls.bad.jsonl
```

Add your own tools and destructive verbs to `tools.json`; the destructive
patterns are matched against argument *values*, so `bash` is safe until its
`command` says `rm -rf`.
