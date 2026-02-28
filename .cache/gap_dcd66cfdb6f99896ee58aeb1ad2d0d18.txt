---
name: docker-compose
description: >-
  Assists with defining and running multi-container applications using Docker Compose. Use
  when configuring services, networking, volumes, health checks, development environments
  with hot-reload, or production-ready compose files with resource limits. Trigger words:
  docker compose, docker-compose, multi-container, services, compose file, depends_on.
license: Apache-2.0
compatibility: "Requires Docker Engine 20+"
metadata:
  author: terminal-skills
  version: "1.0.0"
  category: devops
  tags: ["docker-compose", "docker", "containers", "orchestration", "devops"]
---

# Docker Compose

## Overview

Docker Compose is a tool for defining and running multi-container applications using a declarative YAML file. It manages service definitions, networking between containers, persistent volumes, health checks, environment variables, and secrets, supporting both development workflows with hot-reload and production deployments with resource limits and logging.

## Instructions

- When defining services, specify `image` for pre-built containers or `build` for Dockerfiles, set `depends_on` with `condition: service_healthy` to prevent race conditions, and use `restart: unless-stopped` for production resilience.
- When configuring networking, use the default bridge network for simple setups (services reach each other by name) or custom networks to isolate service groups (frontend, backend, database).
- When managing data, use named volumes for persistent data (databases, uploads), bind mounts for development source code, and `tmpfs` for scratch data.
- When handling secrets, use `secrets` or `env_file` with `.gitignore` rather than inline `environment` values, and use variable substitution with defaults (`${DB_HOST:-localhost}`).
- When setting up development, use Compose Watch for file sync and auto-rebuild, `profiles` for optional services (monitoring, debug tools), and `compose.override.yml` for dev-specific customization.
- When preparing for production, set `deploy.resources.limits` for CPU and memory caps, configure logging drivers with rotation, use multi-stage builds, and pin image tags to specific versions.

## Examples

### Example 1: Set up a full-stack development environment

**User request:** "Create a Docker Compose setup for a Node.js app with PostgreSQL and Redis"

**Actions:**
1. Define `app`, `postgres`, and `redis` services with health checks
2. Configure bind mounts for source code and named volumes for database data
3. Set up Compose Watch for hot-reload on file changes
4. Add `.env` file for database credentials with `env_file` reference

**Output:** A development environment where all services start with `docker compose up`, code changes hot-reload, and database data persists.

### Example 2: Configure a production-ready multi-service deployment

**User request:** "Prepare a Docker Compose file for production with Nginx, API, and database"

**Actions:**
1. Define services with pinned image tags, health checks, and `restart: unless-stopped`
2. Set `deploy.resources.limits` for CPU and memory on each service
3. Configure Nginx as reverse proxy with TLS termination and upstream load balancing
4. Use Docker secrets for database passwords and API keys

**Output:** A production compose file with resource limits, health checks, TLS, secrets management, and automatic restart.

## Guidelines

- Use health checks on every database and message queue service to prevent race conditions with `depends_on`.
- Use named volumes for persistent data and bind mounts only for development source code.
- Never put secrets in `environment`; use `secrets` or `env_file` with `.gitignore`.
- Set `restart: unless-stopped` in production so services recover from crashes automatically.
- Use `profiles` for optional services like monitoring and debug tools to avoid bloating the default stack.
- Pin image tags (`postgres:16.2-alpine`, never `postgres:latest`) for reproducible builds.
- Set resource limits with `deploy.resources.limits` to prevent one service from starving others.
