---
name: axios
description: Work with axios — integrate, configure, and automate. Use when asked to set up axios, use axios API, integrate axios into a project, troubleshoot axios errors, or build axios automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [axios, javascript, nodejs, npm]
---

# Axios Skill

## Quick Start

```bash
pip install axios
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('axios');
```

## When to Use
Use this skill when asked to:
- Set up axios
- Integrate axios API
- Configure axios authentication
- Troubleshoot axios errors
- Build automation with axios

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
- Docs: https://axios.com/docs
- GitHub: https://github.com/axios
