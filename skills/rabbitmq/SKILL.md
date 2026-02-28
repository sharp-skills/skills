---
name: rabbitmq
description: Work with rabbitmq — integrate, configure, and automate. Use when asked to set up rabbitmq, use rabbitmq API, integrate rabbitmq into a project, troubleshoot rabbitmq errors, or build rabbitmq automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [rabbitmq, api, automation, integration]
---

# Rabbitmq Skill

## Quick Start

```bash
pip install rabbitmq
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('rabbitmq');
```

## When to Use
Use this skill when asked to:
- Set up rabbitmq
- Integrate rabbitmq API
- Configure rabbitmq authentication
- Troubleshoot rabbitmq errors
- Build automation with rabbitmq

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
- Docs: https://rabbitmq.com/docs
- GitHub: https://github.com/rabbitmq
