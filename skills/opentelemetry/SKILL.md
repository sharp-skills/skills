---
name: opentelemetry
description: Work with opentelemetry — integrate, configure, and automate. Use when asked to set up opentelemetry, use opentelemetry API, integrate opentelemetry into a project, troubleshoot opentelemetry errors, or build opentelemetry automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [opentelemetry, api, automation, integration]
---

# Opentelemetry Skill

## Quick Start

```bash
npm install opentelemetry
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('opentelemetry');
```

## When to Use
Use this skill when asked to:
- Set up opentelemetry
- Integrate opentelemetry API
- Configure opentelemetry authentication
- Troubleshoot opentelemetry errors
- Build automation with opentelemetry

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
- Docs: https://opentelemetry.com/docs
- GitHub: https://github.com/opentelemetry
