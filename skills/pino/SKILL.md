---
name: pino
description: Work with pino — integrate, configure, and automate. Use when asked to set up pino, use pino API, integrate pino into a project, troubleshoot pino errors, or build pino automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [pino, javascript, nodejs, npm, logging, monitoring, observability]
---

# Pino Skill

## Quick Start

```bash
pip install pino
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('pino');
```

## When to Use
Use this skill when asked to:
- Set up pino
- Integrate pino API
- Configure pino authentication
- Troubleshoot pino errors
- Build automation with pino

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
- Docs: https://pino.com/docs
- GitHub: https://github.com/pino
