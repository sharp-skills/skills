---
name: sequelize
description: Work with sequelize — integrate, configure, and automate. Use when asked to set up sequelize, use sequelize API, integrate sequelize into a project, troubleshoot sequelize errors, or build sequelize automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [sequelize, api, automation, integration]
---

# Sequelize Skill

## Quick Start

```bash
npm install sequelize
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('sequelize');
```

## When to Use
Use this skill when asked to:
- Set up sequelize
- Integrate sequelize API
- Configure sequelize authentication
- Troubleshoot sequelize errors
- Build automation with sequelize

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
- Docs: https://sequelize.com/docs
- GitHub: https://github.com/sequelize
