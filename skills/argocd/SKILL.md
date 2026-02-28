---
name: argocd
description: "Deploy and manage Kubernetes applications with Argo CD GitOps. Use when asked to: install Argo CD, create Argo CD Applications, sync deployments, configure auto-sync, manage Argo CD with CLI, set up ApplicationSets, troubleshoot Argo CD sync errors, or implement GitOps workflows."
license: Apache-2.0
compatibility:
  - kubernetes >= 1.25
  - kubectl
  - argocd-cli >= 2.8
metadata:
  author: SharpSkills
  version: 1.1.0
  category: devops
  tags: [argocd, gitops, kubernetes, deployment, continuous-delivery, helm, kustomize]
trace_id: 08c13a732497
generated_at: '2026-02-28T22:43:16'
generator: sharpskill-v1.0 (legacy)
---

# Argo CD

Argo CD is a declarative GitOps continuous delivery tool for Kubernetes. It monitors Git repos and automatically syncs cluster state to match the desired state defined in Git.

## Installation

```bash
# Install Argo CD in Kubernetes cluster
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Install CLI (macOS)
brew install argocd

# Install CLI (Linux)
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd && sudo mv argocd /usr/local/bin/

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## When to Use
- "Deploy app to Kubernetes with Argo CD"
- "Set up GitOps with Argo CD"
- "Create an Argo CD Application"
- "Configure auto-sync in Argo CD"
- "Fix Argo CD OutOfSync / sync failed"
- "Set up Argo CD ApplicationSet for multiple clusters"

## Core Patterns

### Pattern 1: Create an Application (YAML)

```yaml
# apps/myapp.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io  # Delete resources on app delete
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/myapp-config
    targetRevision: main
    path: kubernetes/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true       # Delete resources removed from Git
      selfHeal: true    # Revert manual cluster changes
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

```bash
kubectl apply -f apps/myapp.yaml
```

### Pattern 2: CLI — Login and Manage Apps

```bash
# Login (port-forward first or use LoadBalancer)
kubectl port-forward svc/argocd-server -n argocd 8080:443
argocd login localhost:8080 --username admin --password <password> --insecure

# List applications
argocd app list

# Get app status
argocd app get myapp

# Manual sync
argocd app sync myapp

# Sync with specific revision
argocd app sync myapp --revision v1.2.3

# Wait for sync to complete
argocd app wait myapp --sync

# Rollback to previous version
argocd app history myapp
argocd app rollback myapp <revision-id>
```

### Pattern 3: Helm-Based Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: prometheus
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://prometheus-community.github.io/helm-charts
    chart: kube-prometheus-stack
    targetRevision: 55.5.0
    helm:
      releaseName: prometheus
      values: |
        grafana:
          enabled: true
          adminPassword: "{{ .Values.grafana.password }}"
        alertmanager:
          enabled: true
        prometheus:
          prometheusSpec:
            retention: 30d
            storageSpec:
              volumeClaimTemplate:
                spec:
                  storageClassName: fast
                  resources:
                    requests:
                      storage: 50Gi
  destination:
    server: https://kubernetes.default.svc
    namespace: monitoring
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true  # Required for CRDs with large annotations
```

### Pattern 4: ApplicationSet — Deploy to Multiple Clusters

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp-clusters
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - cluster: staging
            url: https://staging.k8s.example.com
            env: staging
          - cluster: production
            url: https://prod.k8s.example.com
            env: production
  template:
    metadata:
      name: 'myapp-{{cluster}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/myapp-config
        targetRevision: main
        path: 'kubernetes/overlays/{{env}}'
      destination:
        server: '{{url}}'
        namespace: myapp
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

### Pattern 5: Private Repo and RBAC

```bash
# Add private GitHub repo (HTTPS with token)
argocd repo add https://github.com/myorg/private-config \
  --username myuser \
  --password ghp_yourtoken

# Add private repo (SSH)
argocd repo add git@github.com:myorg/private-config.git \
  --ssh-private-key-path ~/.ssh/id_rsa

# Create project with restricted source repos and destinations
argocd proj create myproject \
  --description "Production apps" \
  --src https://github.com/myorg/* \
  --dest https://kubernetes.default.svc,production
```

## Production Notes

1. **`selfHeal: true` prevents drift** — Without it, manual `kubectl apply` changes persist until next Git commit syncs. Enable selfHeal in production to enforce GitOps.
2. **`prune: true` deletes orphaned resources** — Resources removed from Git manifests are deleted from the cluster. Disable during migrations to avoid accidental deletion.
3. **`ServerSideApply=true` for CRDs** — Prometheus and similar operators create resources with large annotations that exceed client-side apply limits. Use server-side apply.
4. **Health checks before auto-sync** — Argo CD won't auto-sync if the app is in a degraded health state. Fix health probes on deployments before enabling auto-sync.

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| App stuck `OutOfSync` after sync | Mutation webhooks modify resources post-apply | Add `ignoreDifferences` for the modified fields |
| `ComparisonError: failed to get cluster info` | kubeconfig or cluster URL wrong | Check `argocd cluster list`; re-add cluster |
| Sync fails with `Too long annotation` | CRD annotations exceed 262144 bytes | Enable `ServerSideApply=true` in syncOptions |
| Resources deleted unexpectedly | `prune: true` with resources not in Git | Add `argocd.argoproj.io/managed-by` label or disable prune |
| `permission denied` accessing private repo | Token expired or missing repo permission | Re-add repo with fresh token: `argocd repo add ...` |
| Helm values not applied | Wrong `helm.values` indent in Application YAML | Validate YAML indentation; use `helm template` locally first |

## Pre-Deploy Checklist
- [ ] `argocd app get <name>` shows `Synced` and `Healthy` before going live
- [ ] `prune: true` tested on staging before enabling in production
- [ ] `selfHeal: true` confirmed for production (prevents cluster drift)
- [ ] Private repo credentials added via `argocd repo add` (not hardcoded)
- [ ] RBAC projects configured to restrict which repos/namespaces each team can access
- [ ] Notifications configured (Slack/email) for sync failures

## Resources
- Docs: https://argo-cd.readthedocs.io/
- GitHub: https://github.com/argoproj/argo-cd
- ApplicationSet: https://argo-cd.readthedocs.io/en/stable/user-guide/application-set/
