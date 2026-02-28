---
name: react-query
description: Work with react-query — integrate, configure, and automate. Use when asked to set up react-query, use react-query API, integrate react-query into a project, troubleshoot react-query errors, or build react-query automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [react-query]
---

# React-Query Skill

## Quick Start

```bash
npm install react-query
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('react-query');
```

## When to Use
Use this skill when asked to:
- Set up react-query
- Integrate react-query API
- Configure react-query authentication
- Troubleshoot react-query errors
- Build automation with react-query

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
- Docs: https://react-query.com/docs
- GitHub: https://github.com/react-query
