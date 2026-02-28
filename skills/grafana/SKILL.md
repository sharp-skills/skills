---
name: grafana
description: Work with grafana — integrate, configure, and automate. Use when asked to set up grafana, use grafana API, integrate grafana into a project, troubleshoot grafana errors, or build grafana automation.
license: Apache-2.0
compatibility:
- any
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [grafana, api, automation, integration, logging, monitoring, observability]
---

# Grafana Skill

## Quick Start

```bash
pip install grafana
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('grafana');
```

## When to Use
Use this skill when asked to:
- Set up grafana
- Integrate grafana API
- Configure grafana authentication
- Troubleshoot grafana errors
- Build automation with grafana

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
- Docs: https://grafana.com/docs
- GitHub: https://github.com/grafana
