# SharpSkills

An open-source library of AI agent skills following the [Agent Skills](https://agentskills.io) open standard. Built for Claude Code, OpenAI Codex, Gemini CLI, Cursor, and other AI-powered development tools. Automatically tested before publish.

Browse the full catalog at [sharpskills.io](https://sharpskills.io).

## Install a Skill

### Claude Code

```bash
npx @sharpskills/cli install stripe
```

Or using curl:

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/stripe/SKILL.md \
  -o .claude/skills/stripe.md
```

### OpenAI Codex

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/stripe/SKILL.md \
  -o .codex/skills/stripe.md
```

### Gemini CLI

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/stripe/SKILL.md \
  -o .gemini/skills/stripe.md
```

### Cursor

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/stripe/SKILL.md \
  -o .cursor/skills/stripe.md
```

Replace `stripe` with the skill name you want to install.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

Apache-2.0. See [LICENSE](LICENSE).

