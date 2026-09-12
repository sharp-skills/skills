# SharpSkills

An open-source library of AI agent skills following the [Agent Skills](https://agentskills.io) open standard. Built for Claude Code, OpenAI Codex, Gemini CLI, Cursor, and other AI-powered development tools. Automatically tested before publish.

## Install a Skill

### Claude Code

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/tool-call-validator/SKILL.md \
  -o .claude/skills/tool-call-validator.md
```

### OpenAI Codex

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/tool-call-validator/SKILL.md \
  -o .codex/skills/tool-call-validator.md
```

### Gemini CLI

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/tool-call-validator/SKILL.md \
  -o .gemini/skills/tool-call-validator.md
```

### Cursor

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/tool-call-validator/SKILL.md \
  -o .cursor/skills/tool-call-validator.md
```

Replace `tool-call-validator` with the skill name you want to install.

Skills that ship with `scripts/`, `references/` or `examples/` (see the collections
below) need the whole folder, not just `SKILL.md` — clone the repo and copy
`skills/<name>/` into your agent's skills directory.

## Collections

Some skills are built as a set and audited together:

| Collection | Skills | What it is |
|---|---|---|
| [multi-agent-engineering](bundles/multi-agent-engineering/README.md) | 25 | Building and operating production multi-agent systems. Every skill ships a runnable checker, offline fixtures and a self-test; two end-to-end demos wire them together. `sh bundles/multi-agent-engineering/bundle_check.sh` audits the whole set. |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

Apache-2.0. See [LICENSE](LICENSE).

