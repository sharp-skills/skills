---
name: datadog
description: Work with datadog — integrate, configure, and automate. Use when asked to set up datadog, use datadog API, integrate datadog into a project, troubleshoot datadog errors, or build datadog automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [datadog]
---

# Datadog Skill

## Quick Start

```bash
pip install datadog
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('datadog');
```

## When to Use
Use this skill when asked to:
- Set up datadog
- Integrate datadog API
- Configure datadog authentication
- Troubleshoot datadog errors
- Build automation with datadog

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
- Docs: https://datadog.com/docs
- GitHub: https://github.com/datadog
