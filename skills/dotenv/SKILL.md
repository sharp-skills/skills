---
name: dotenv
description: Work with dotenv — integrate, configure, and automate. Use when asked to set up dotenv, use dotenv API, integrate dotenv into a project, troubleshoot dotenv errors, or build dotenv automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [dotenv, javascript, nodejs, npm]
---

# Dotenv Skill

## Quick Start

```bash
pip install dotenv
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('dotenv');
```

## When to Use
Use this skill when asked to:
- Set up dotenv
- Integrate dotenv API
- Configure dotenv authentication
- Troubleshoot dotenv errors
- Build automation with dotenv

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
- Docs: https://dotenv.com/docs
- GitHub: https://github.com/dotenv
