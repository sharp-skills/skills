---
name: shopify
description: Work with shopify — integrate, configure, and automate. Use when asked to set up shopify, use shopify API, integrate shopify into a project, troubleshoot shopify errors, or build shopify automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [shopify]
---

# Shopify Skill

## Quick Start

```bash
pip install shopify
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('shopify');
```

## When to Use
Use this skill when asked to:
- Set up shopify
- Integrate shopify API
- Configure shopify authentication
- Troubleshoot shopify errors
- Build automation with shopify

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
- Docs: https://shopify.com/docs
- GitHub: https://github.com/shopify
