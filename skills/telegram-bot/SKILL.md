---
name: telegram-bot
description: Work with telegram-bot — integrate, configure, and automate. Use when asked to set up telegram-bot, use telegram-bot API, integrate telegram-bot into a project, troubleshoot telegram-bot errors, or build telegram-bot automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [telegram-bot]
---

# Telegram-Bot Skill

## Quick Start

```bash
pip install telegram-bot
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('telegram-bot');
```

## When to Use
Use this skill when asked to:
- Set up telegram-bot
- Integrate telegram-bot API
- Configure telegram-bot authentication
- Troubleshoot telegram-bot errors
- Build automation with telegram-bot

## Core Patterns

### Pattern 1: Basic Usage (Source: official)
```javascript
// TODO: Set ANTHROPIC_API_KEY for AI-generated patterns from official docs
```

## Production Notes

Set `ANTHROPIC_API_KEY` in `.env` for AI-generated production notes from real GitHub Issues data.

## Failure Modes
| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Auth error | Invalid API key | Check environment variable |
| Timeout | Network issue | Add retry with backoff |

## Pre-Deploy Checklist
- [ ] API key set in production environment
- [ ] Error handling on all API calls
- [ ] Rate limiting / retry logic added

## Resources
- Docs: https://telegram-bot.com/docs
- GitHub: https://github.com/telegram-bot
