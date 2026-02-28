---
name: cheerio
description: Work with cheerio — integrate, configure, and automate. Use when asked to set up cheerio, use cheerio API, integrate cheerio into a project, troubleshoot cheerio errors, or build cheerio automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [cheerio, api, automation, integration]
---

# Cheerio Skill

## Quick Start

```bash
pip install cheerio
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('cheerio');
```

## When to Use
Use this skill when asked to:
- Set up cheerio
- Integrate cheerio API
- Configure cheerio authentication
- Troubleshoot cheerio errors
- Build automation with cheerio

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
- Docs: https://cheerio.com/docs
- GitHub: https://github.com/cheerio
