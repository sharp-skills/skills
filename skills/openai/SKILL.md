---
name: openai
description: Work with openai — integrate, configure, and automate. Use when asked to set up openai, use openai API, integrate openai into a project, troubleshoot openai errors, or build openai automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [openai, api, automation, integration]
---

# Openai Skill

## Quick Start

```bash
pip install openai
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('openai');
```

## When to Use
Use this skill when asked to:
- Set up openai
- Integrate openai API
- Configure openai authentication
- Troubleshoot openai errors
- Build automation with openai

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
- Docs: https://openai.com/docs
- GitHub: https://github.com/openai
