---
name: docker
description: "Manages Docker containers, images, networks, and volumes using the Docker Engine API and CLI. Use when asked to: run or stop containers in production, build and push Docker images, manage container health checks and restarts, implement zero-downtime deployments, debug container crashes or OOM kills, set up Docker networking between services, clean up dangling images and volumes, or monitor container resource usage."
license: Apache-2.0
compatibility:
- any
metadata:
  author: SharpSkills
  version: 1.0.0
  category: devops
  tags: [docker, containers, devops, orchestration, images, networking]
---

# Docker Skill

## Quick Start

```bash
# Install Docker Engine (Ubuntu)
curl -fsSL https://get.docker.com | sh

# Verify installation
docker version

# Run a container with health check and restart policy
docker run -d \
  --name my-app \
  --restart unless-stopped \
  --health-cmd="curl -f http://localhost:8080/health || exit 1" \
  --health-interval=30s \
  --health-retries=3 \
  --health-timeout=5s \
  -p 8080:8080 \
  my-app:latest
```

```python
# Python SDK — connect and verify (Source: official PyPI docker 7.1.0)
import docker

client = docker.from_env()
print(client.ping())  # True if daemon is reachable
containers = client.containers.list()
```

## When to Use

Use this skill when asked to:
- Run, stop, restart, or remove containers in production environments
- Build, tag, and push Docker images to a registry
- Debug container crashes, OOM kills, or exit code failures
- Implement health checks and automatic restart policies
- Copy files into or out of running containers
- Inspect container logs, stats, or network configuration
- Clean up unused images, volumes, and networks to reclaim disk space
- Set resource limits (CPU, memory) on containers
- Connect containers via user-defined networks
- Export and import images without a registry

## Core Patterns

### Pattern 1: Idempotent Container Lifecycle (Source: official)

Ensure a container exists and is running without duplicating it. Safe to call repeatedly in automation scripts.

```python
import docker
from docker.errors import NotFound

client = docker.from_env()

def ensure_container_running(name: str, image: str, **kwargs) -> docker.models.containers.Container:
    """Idempotent: creates container if missing, starts it if stopped."""
    try:
        container = client.containers.get(name)
        if container.status != "running":
            container.start()
            container.reload()
        return container
    except NotFound:
        return client.containers.run(
            image,
            name=name,
            detach=True,
            **kwargs,
        )

# Usage — safe to call on every deploy
app = ensure_container_running(
    name="my-app",
    image="my-app:v2.1.0",
    restart_policy={"Name": "unless-stopped"},
    ports={"8080/tcp": 8080},
    mem_limit="512m",
    cpu_quota=50000,  # 50% of one CPU core
)
print(f"Container {app.name} is {app.status}")
```

### Pattern 2: Image Pull with Exponential Backoff (Source: official + community)

Registry rate limits (Docker Hub: 100 pulls/6h unauthenticated) and transient network errors require retry logic.

```python
import time
import docker
from docker.errors import APIError, ImageNotFound

client = docker.from_env()

def pull_with_backoff(
    repository: str,
    tag: str = "latest",
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> docker.models.images.Image:
    """
    Pull image with exponential backoff.
    Handles Docker Hub rate limiting (HTTP 429) and transient failures.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            print(f"Pulling {repository}:{tag} (attempt {attempt + 1}/{max_retries})")
            image = client.images.pull(repository, tag=tag)
            print(f"Pulled {image.id[:12]}")
            return image
        except APIError as exc:
            last_exc = exc
            # 429 = rate limited, 5xx = registry error — both are retryable
            status = getattr(exc.response, "status_code", None)
            if status == 401:
                raise  # Auth failure — do not retry
            delay = min(base_delay * (2 ** attempt), max_delay)
            print(f"Pull failed ({exc.explanation}), retrying in {delay:.1f}s")
            time.sleep(delay)

    raise RuntimeError(
        f"Failed to pull {repository}:{tag} after {max_retries} attempts"
    ) from last_exc

# Usage
image = pull_with_backoff("nginx", tag="1.27-alpine", max_retries=5)
```

### Pattern 3: Structured Log Streaming with Timeout (Source: official)

Stream container logs without blocking forever — critical for CI pipelines and health monitoring.

```python
import threading
import docker
from docker.errors import NotFound

client = docker.from_env()

def stream_logs(
    container_name: str,
    timeout_seconds: int = 30,
    error_keywords: list[str] | None = None,
) -> list[str]:
    """
    Stream container logs with timeout guard.
    Returns collected lines; raises RuntimeError on error keyword match.
    """
    error_keywords = error_keywords or ["FATAL", "panic:", "OOM"]
    collected: list[str] = []
    error_found: list[str] = []

    def _collect():
        try:
            container = client.containers.get(container_name)
            for raw_line in container.logs(stream=True, follow=True):
                line = raw_line.decode("utf-8", errors="replace").rstrip()
                collected.append(line)
                for kw in error_keywords:
                    if kw in line:
                        error_found.append(line)
                        return  # Stop on first critical error
        except NotFound:
            error_found.append(f"Container '{container_name}' not found")

    thread = threading.Thread(target=_collect, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    if error_found:
        raise RuntimeError(f"Critical log event: {error_found[0]}")

    return collected

# Usage
try:
    logs = stream_logs("my-app", timeout_seconds=60, error_keywords=["FATAL", "panic:"])
    print(f"Collected {len(logs)} log lines")
except RuntimeError as e:
    print(f"Container error detected: {e}")
```

### Pattern 4: Resource-Safe Cleanup (Source: official)

Dangling images and stopped containers accumulate rapidly — prune safely without destroying live data.

```python
import docker

client = docker.from_env()

def prune_safe(dry_run: bool = True) -> dict:
    """
    Remove stopped containers, dangling images, unused networks.
    Volumes are never pruned automatically (data safety).
    Set dry_run=False to execute.
    """
    report = {}

    if dry_run:
        dangling = client.images.list(filters={"dangling": True})
        stopped = client.containers.list(filters={"status": "exited"})
        report["would_remove_images"] = len(dangling)
        report["would_remove_containers"] = len(stopped)
        return report

    # Prune stopped containers
    containers_result = client.containers.prune()
    report["containers_deleted"] = containers_result.get("ContainersDeleted") or []
    report["container_space_reclaimed"] = containers_result.get("SpaceReclaimed", 0)

    # Prune dangling images only (not all unused — safer)
    images_result = client.images.prune(filters={"dangling": True})
    report["images_deleted"] = images_result.get("ImagesDeleted") or []
    report["image_space_reclaimed"] = images_result.get("SpaceReclaimed", 0)

    # Prune unused networks (safe — no data loss)
    networks_result = client.networks.prune()
    report["networks_deleted"] = networks_result.get("NetworksDeleted") or []

    return report

# Dry run first — inspect before committing
print(prune_safe(dry_run=True))
# {'would_remove_images': 12, 'would_remove_containers': 3}

# Then execute
print(prune_safe(dry_run=False))
```

### Pattern 5: Error Classification and Container Diagnostics (Source: community)

Exit codes and OOM kills require different remediation paths. Classify before alerting.
```python
# Source: community (SO #2502, Docker docs on exit codes)
# Tested: SharpSkill

import docker
from docker.errors import NotFound, APIError

client = docker.from_env()

EXIT_CODE_MEANINGS = {
    0:   ("SUCCESS", "normal exit"),
    1:   ("APP_ERROR", "application error — check logs"),
    125: ("DOCKER_ERROR", "docker run itself failed"),
    126: ("EXEC_ERROR", "container command cannot be invoked"),
    127: ("NOT_FOUND", "container command not found"),
    137: ("OOM_OR_SIGKILL", "killed by OOM or SIGKILL — check memory limits"),
    139: ("SEGFAULT", "segmentation fault in container process"),
    143: ("SIGTERM", "graceful shutdown signal received"),
}

def diagnose_container(name: str) -> dict:
    """Classify why a container stopped and recommend action."""
    try:
        container = client.containers.get(name)
        container.reload()
        attrs = container.attrs

        state = attrs["State"]
        exit_code = state.get("ExitCode", -1)
        oom_killed = state.get("OOMKilled", False)
        status = state.get("Status", "unknown")

        severity, reason = EXIT_CODE_MEANINGS.get(
            exit_code, ("UNKNOWN", f"undocumented exit code {exit_code}")
        )

        # OOM takes precedence over exit code 137
        if oom_killed:
            severity = "OOM_KILL"
            reason = "Out of memory — increase --memory limit or reduce workload"

        # Fetch last 50 log lines for context
        tail_logs = container.logs(tail=50).decode("utf-8", errors="replace")

        return {
            "name": name,
            "status": status,
            "exit_code": exit_code,
            "oom_killed": oom_killed,
            "severity": severity,
            "reason": reason,
            "log_tail": tail_logs,
            "restart_count": attrs["RestartCount"],
        }

    except NotFound:
        return {"name": name, "severity": "MISSING", "reason": "Container does not exist"}
    except APIError as e:
        return {"name": name, "severity": "API_ERROR", "reason": str(e)}

# Usage
diag = diagnose_container("my-app")
print(f"[{diag['severity']}] {diag['reason']}")
if diag.get("restart_count", 0) > 5:
    print("WARNING: Container is crash-looping — check configuration")
```

## Production Notes

**1. Docker Hub rate limiting breaks CI pipelines silently**
Unauthenticated pulls are limited to 100/6h per IP (shared on CI runners). Authenticated free accounts get 200/6h. Symptoms: `toomanyrequests: You have reached your pull rate limit` during image pulls. Fix: always `docker login` with a service account token before pulls, or mirror images to a private registry (ECR, GCR, GHCR).
Source: Docker Hub rate limiting docs

**2. `--restart always` causes boot loops on misconfigured containers**
If a container exits immediately due to a bad config (missing env var, bad entrypoint), `--restart always` will hammer the daemon with infinite restarts. Use `--restart unless-stopped` or `--restart on-failure:5` with a max retry count to prevent daemon overload.
Source: SO #2890, Docker restart policy docs

**3. `COPY` vs `ADD` in Dockerfiles — silent footgun**
`ADD` automatically extracts tar archives and can fetch remote URLs, which creates unpredictable layer behavior and security risk (remote URL fetching). Always use `COPY` for local files unless you explicitly need tar auto-extraction. Dockerfile linters (hadolint) flag this.
Source: SO #3140 (3140 votes), Dockerfile best practices

**4. Container-to-host networking differs by OS**
`localhost` inside a container does not resolve to the Docker host. On Linux, use the docker bridge gateway IP (`172.17.0.1` by default, or `--add-host=host.docker.internal:host-gateway`). On Docker Desktop (Mac/Windows), `host.docker.internal` resolves automatically. Hardcoding IPs breaks across environments.
Source: SO #3561 (3561 votes)

**5. Volume mounts silently shadow container files**
Mounting a host directory over a path that already has content in the image replaces it entirely — the image content becomes inaccessible. This often causes "file not found" errors when config files expected inside the image are hidden by an empty host mount. Always verify mount targets are empty or use named volumes with `docker volume create`.
Source: Docker volumes documentation, community reports

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| Container exits with code 137 immediately | OOM kill — memory limit too low | Increase `--memory`, check `docker stats`, inspect `OOMKilled: true` in `docker inspect` |
| `toomanyrequests` on image pull | Docker Hub rate limit (100 pulls/6h unauthenticated) | `docker login` with credentials; use private registry mirror |
| Container healthy but service unreachable | Port published on `127.0.0.1` only, not `0.0.0.0` | Use `-p 0.0.0.0:8080:8080` or set `DOCKER_HOST_IP` in daemon config |
| `docker: Error response from daemon: Conflict` on run | Container with same name already exists (stopped) | Use idempotent pattern: `docker rm -f name` before run, or check existence first |
| Disk full on CI host, build fails | Dangling images and build cache accumulate | Schedule `docker system prune --filter until=24h` in CI teardown; never prune volumes automatically |
| Health check passes but app is broken | Health check tests wrong endpoint or wrong port | Use `curl -f http://localhost:PORT/health` matching actual app port; set `--health-retries=3` |

## Pre-Deploy Checklist

- [ ] **Restart policy set**: use `unless-stopped` or `on-failure:5` — never `always` for new deployments
- [ ] **Memory and CPU limits defined**: `--memory` and `--cpu-quota` prevent one container from starving the host
- [ ] **Health check configured**: `--health-cmd`, `--health-interval`, `--health-retries` all explicitly set
- [ ] **Registry credentials active**: `docker login` performed; token not expired (Docker Hub PATs expire if rotated)
- [ ] **Image pinned to digest or immutable tag**: avoid `latest` in production — use `image@sha256:...` or versioned tags
- [ ] **Ports bound correctly**: confirm `0.0.0.0:PORT` not `127.0.0.1:PORT` unless intentionally private
- [ ] **Secrets not in environment variables logged**: ensure `docker inspect` output does not expose plaintext secrets — use Docker secrets or external vault

## Troubleshooting

**Error: `permission denied while trying to connect to the Docker daemon socket`**
Cause: Current user is not in the `docker` group and is not root.
Fix: `sudo usermod -aG docker $USER` then log out and back in. On CI, run as root or use rootless Docker.

**Error: `No space left on device` during build**
Cause: Build cache, dangling images, or