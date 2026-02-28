---
name: netlify
description: Work with netlify — integrate, configure, and automate. Use when asked to set up netlify, use netlify API, integrate netlify into a project, troubleshoot netlify errors, or build netlify automation.
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [netlify]
---

# Netlify Skill

## Quick Start

```bash
npm install netlify
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('netlify');
```

## When to Use
Use this skill when asked to:
- Set up netlify
- Integrate netlify API
- Configure netlify authentication
- Troubleshoot netlify errors
- Build automation with netlify

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
- Docs: https://netlify.com/docs
- GitHub: https://github.com/netlify
