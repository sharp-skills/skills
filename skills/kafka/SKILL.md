---
name: kafka
description: Work with kafka — integrate, configure, and automate. Use when asked to set up kafka, use kafka API, integrate kafka into a project, troubleshoot kafka errors, or build kafka automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [kafka, api, automation, integration, queue, async, messaging]
---

# Kafka Skill

## Quick Start

```bash
pip install kafka
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('kafka');
```

## When to Use
Use this skill when asked to:
- Set up kafka
- Integrate kafka API
- Configure kafka authentication
- Troubleshoot kafka errors
- Build automation with kafka

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
- Docs: https://kafka.com/docs
- GitHub: https://github.com/kafka
