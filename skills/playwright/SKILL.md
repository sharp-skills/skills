---
name: playwright
description: Work with playwright — integrate, configure, and automate. Use when asked to set up playwright, use playwright API, integrate playwright into a project, troubleshoot playwright errors, or build playwright automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [playwright, api, automation, integration]
---

# Playwright Skill

## Quick Start

```bash
pip install playwright
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('playwright');
```

## When to Use
Use this skill when asked to:
- Set up playwright
- Integrate playwright API
- Configure playwright authentication
- Troubleshoot playwright errors
- Build automation with playwright

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
- Docs: https://playwright.com/docs
- GitHub: https://github.com/playwright
