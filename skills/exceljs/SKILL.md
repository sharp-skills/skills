---
name: exceljs
description: Work with exceljs — integrate, configure, and automate. Use when asked to set up exceljs, use exceljs API, integrate exceljs into a project, troubleshoot exceljs errors, or build exceljs automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [exceljs, api, automation, integration]
---

# Exceljs Skill

## Quick Start

```bash
npm install exceljs
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('exceljs');
```

## When to Use
Use this skill when asked to:
- Set up exceljs
- Integrate exceljs API
- Configure exceljs authentication
- Troubleshoot exceljs errors
- Build automation with exceljs

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
- Docs: https://exceljs.com/docs
- GitHub: https://github.com/exceljs
