---
name: woocommerce
description: Work with woocommerce — integrate, configure, and automate. Use when asked to set up woocommerce, use woocommerce API, integrate woocommerce into a project, troubleshoot woocommerce errors, or build woocommerce automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [woocommerce, javascript, nodejs, npm]
---

# Woocommerce Skill

## Quick Start

```bash
pip install woocommerce
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('woocommerce');
```

## When to Use
Use this skill when asked to:
- Set up woocommerce
- Integrate woocommerce API
- Configure woocommerce authentication
- Troubleshoot woocommerce errors
- Build automation with woocommerce

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
- Docs: https://woocommerce.com/docs
- GitHub: https://github.com/woocommerce
