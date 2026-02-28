---
name: keycloak
description: Work with keycloak — integrate, configure, and automate. Use when asked to set up keycloak, use keycloak API, integrate keycloak into a project, troubleshoot keycloak errors, or build keycloak automation.
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: development
  tags: [keycloak, api, automation, integration]
---

# Keycloak Skill

## Quick Start

```bash
pip install keycloak
```

```javascript
// Source: official — set ANTHROPIC_API_KEY to generate real patterns
const client = require('keycloak');
```

## When to Use
Use this skill when asked to:
- Set up keycloak
- Integrate keycloak API
- Configure keycloak authentication
- Troubleshoot keycloak errors
- Build automation with keycloak

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
- Docs: https://keycloak.com/docs
- GitHub: https://github.com/keycloak
