---
name: kubernetes
description: "Manages containerized application orchestration using Kubernetes (K8s). Use when user asks to: deploy an application to Kubernetes, scale pods up or down, configure a Kubernetes service or ingress, debug a crashing or stuck pod, set up namespaces and RBAC, manage ConfigMaps and Secrets, apply or roll back a deployment, or connect a local Docker image with Minikube."
license: Apache-2.0
compatibility:
- any
metadata:
  author: SharpSkills
  version: 1.0.0
  category: devops
  tags: [kubernetes, k8s, containers, orchestration, devops, cloud-native, pods, deployments]
trace_id: a79bbc02d9c2
generated_at: '2026-02-28T22:43:27'
generator: sharpskill-v1.0 (legacy)
---

# Kubernetes Skill

## Quick Start

```bash
# Install kubectl (macOS)
brew install kubectl

# Verify cluster connection
kubectl cluster-info

# Deploy a containerized app
kubectl create deployment hello-app --image=gcr.io/google-samples/hello-app:1.0

# Expose it via a LoadBalancer service
kubectl expose deployment hello-app --type=LoadBalancer --port=8080

# Check running pods
kubectl get pods

# Scale to 3 replicas
kubectl scale deployment hello-app --replicas=3

# Check service external IP
kubectl get service hello-app
```

## When to Use

Use this skill when asked to:
- Deploy, update, or roll back an application on Kubernetes
- Scale pods or configure autoscaling (HPA/VPA)
- Debug pods that are crashing, pending, or stuck in Terminating
- Configure Services (ClusterIP, NodePort, LoadBalancer) or Ingress rules
- Manage namespaces, RBAC roles, and service accounts
- Create or consume ConfigMaps and Secrets in pods
- Use local Docker images inside Minikube without a registry
- Set resource requests, limits, liveness, and readiness probes
- Run one-off jobs or CronJobs in the cluster
- Migrate from Docker Compose to Kubernetes manifests

## Core Patterns

### Pattern 1: Production Deployment Manifest (Source: official)

A full Deployment with resource limits, health probes, and rolling-update strategy — the minimum viable production spec.

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: production
  labels:
    app: my-app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0          # zero-downtime rollout
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-app
          image: my-registry/my-app:1.2.3   # pin exact tag, never :latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: my-app-secrets
                  key: db-password
---
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: production
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
```

```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/my-app -n production
```

### Pattern 2: Service Types — ClusterIP vs NodePort vs LoadBalancer vs Ingress (Source: official)

```yaml
# ClusterIP — internal only (default; use for inter-service communication)
apiVersion: v1
kind: Service
metadata:
  name: backend-svc
spec:
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP

---
# NodePort — exposes on each node's IP; use for dev/testing only
apiVersion: v1
kind: Service
metadata:
  name: backend-nodeport
spec:
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080        # 30000–32767 range
  type: NodePort

---
# LoadBalancer — provisions cloud LB; use for production external traffic
apiVersion: v1
kind: Service
metadata:
  name: backend-lb
spec:
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 8080
  type: LoadBalancer

---
# Ingress — HTTP routing, TLS termination; preferred over raw LoadBalancer
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend-svc
                port:
                  number: 80
  tls:
    - hosts:
        - myapp.example.com
      secretName: myapp-tls-secret
```

### Pattern 3: ConfigMaps and Secrets (Source: official)

```bash
# Create a ConfigMap from a file or literals
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=info \
  --from-literal=MAX_CONNECTIONS=100

# Create a Secret (values are base64-encoded automatically)
kubectl create secret generic app-secrets \
  --from-literal=db-password=s3cr3t \
  --from-literal=api-key=abc123

# Inspect
kubectl get configmap app-config -o yaml
kubectl get secret app-secrets -o yaml
```

```yaml
# Consume ConfigMap as env vars and Secret as volume
spec:
  containers:
    - name: my-app
      image: my-app:1.0.0
      envFrom:
        - configMapRef:
            name: app-config       # injects LOG_LEVEL, MAX_CONNECTIONS
      volumeMounts:
        - name: secret-vol
          mountPath: /etc/secrets
          readOnly: true
  volumes:
    - name: secret-vol
      secret:
        secretName: app-secrets    # files: db-password, api-key
```

### Pattern 4: Horizontal Pod Autoscaler (Source: official)

```yaml
# hpa.yaml — scale between 2 and 10 pods based on CPU
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

```bash
kubectl apply -f hpa.yaml
kubectl get hpa my-app-hpa --watch
```

### Pattern 5: Use Local Docker Images in Minikube (Source: community)
# Source: community (Stack Overflow — 688 votes)
# Tested: SharpSkill

The most common Minikube pitfall: `ErrImagePull` when using locally-built images.

```bash
# Point your shell's Docker daemon AT Minikube's Docker daemon
eval $(minikube docker-env)

# Now build — the image lands inside Minikube, not your host
docker build -t my-local-app:dev .

# Deploy with imagePullPolicy: Never so Kubernetes won't hit a registry
kubectl run my-local-app \
  --image=my-local-app:dev \
  --image-pull-policy=Never

# Or in a manifest:
# imagePullPolicy: Never   <-- critical line
```

```bash
# Undo the docker-env when done
eval $(minikube docker-env --unset)
```

### Pattern 6: Rollout Management and Rollback (Source: official)

```bash
# Update image (triggers rolling update)
kubectl set image deployment/my-app my-app=my-registry/my-app:1.3.0 -n production

# Watch rollout progress
kubectl rollout status deployment/my-app -n production

# View rollout history
kubectl rollout history deployment/my-app -n production

# Rollback to previous revision
kubectl rollout undo deployment/my-app -n production

# Rollback to a specific revision
kubectl rollout undo deployment/my-app --to-revision=2 -n production
```

### Pattern 7: Debugging Pods (Source: community)
# Source: community (Stack Overflow — multiple high-vote questions)
# Tested: SharpSkill

```bash
# Check pod status and events
kubectl get pods -n <namespace>
kubectl describe pod <pod-name> -n <namespace>    # events section is key

# Stream logs (add --previous for last crashed container)
kubectl logs <pod-name> -n <namespace> --follow
kubectl logs <pod-name> -n <namespace> --previous

# Open a shell inside a running container
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Pods stuck in Terminating — force delete (last resort)
kubectl delete pod <pod-name> -n <namespace> --grace-period=0 --force

# Run a temporary debug container in the cluster
kubectl run debug-shell --rm -it \
  --image=busybox \
  --restart=Never \
  -- /bin/sh
```

### Pattern 8: RBAC — Namespace-Scoped Role (Source: official)

```yaml
# role.yaml — read-only access to pods and logs in "staging"
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: staging
  name: pod-reader
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader-binding
  namespace: staging
subjects:
  - kind: User
    name: jane
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl apply -f role.yaml
# Verify what a user can do
kubectl auth can-i list pods --namespace=staging --as=jane
```

## Production Notes

**1. Never use `latest` image tag in production**
Using `:latest` makes deployments non-deterministic — nodes may cache different versions. Pin to an immutable digest or semantic version tag (e.g., `my-app:1.2.3` or `my-app@sha256:abc…`). Source: GitHub Issues (kubernetes/kubernetes)

**2. Always set resource `requests` AND `limits`**
Without `requests`, the scheduler cannot make placement decisions; pods land on overloaded nodes. Without `limits`, a runaway process OOM-kills its neighbors. Set both on every container. Source: SO community, Kubernetes official docs

**3. `kubectl apply` vs `kubectl create` — use `apply` for everything declarative**
`kubectl create` fails if the resource already exists. `kubectl apply` is idempotent and diff-aware — it's the right tool for GitOps and CI/CD pipelines. Use `create` only for imperative one-shots (e.g., `kubectl create secret`). Source: SO (484 votes)

**4. Ingress is almost always better than exposing a LoadBalancer per service**
Each `type: LoadBalancer` service provisions a separate cloud load balancer, incurring cost. A single Ingress controller (nginx, Traefik) with one LB routes all HTTP/S traffic by host and path. Source: SO (471 votes)

**5. Pods stuck in `Terminating` usually mean a finalizer or webhook is blocking**
Kubernetes sets a deletion timestamp and waits for finalizers to complete. If a webhook is unreachable or a finalizer is orphaned, the pod hangs. Fix: inspect finalizers with `kubectl get pod -o json` and remove the offending finalizer with a patch, then force-delete only as a last resort. Source: SO (582 votes)

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `ErrImagePull` / `ImagePullBackOff` | Image tag doesn't exist in registry, or registry credentials missing | Verify tag exists; create `imagePullSecret` and reference it in pod spec |
| Pod stuck in `Pending` | Insufficient cluster resources or no node matches node selector/taint | `kubectl describe pod` → Events; add nodes or fix tolerations/requests |
| Pod stuck in `Terminating` | Finalizer not cleared or admission webhook unreachable | Remove finalizer via `kubectl patch`; check webhook configs |
| `CrashLoopBackOff` | Container exits immediately (bad entrypoint, missing env var, OOM) | `kubectl logs --previous`; check exit code; verify env/secret mounts |
| `kubectl apply` returns 403 Forbidden | RBAC role missing `update`/`patch` verbs for resource | Add missing verbs to the Role/ClusterRole and re-apply |
| Ingress returns 404 for all paths | Ingress controller not installed or `ingressClassName` mismatch | Install nginx-ingress; match `ingressClassName` to controller's class |
| HPA stuck at minimum replicas | Metrics server not installed; no resource `requests` set | Install `metrics-server`; add CPU/memory `requests` to containers |

## Pre-Deploy Checklist

- [ ] Image tag is pinned (no `:latest`) and image exists in the target registry
- [ ] Resource `requests` and `limits` set on every container
- [ ] `livenessProbe` and `readinessProbe` configured with appropriate `initialDelaySeconds`
- [ ] Secrets stored as Kubernetes Secrets (not hardcoded in manifests or env literals in YAML committed to git)
- [ ] `RollingUpdate` strategy configured with `maxUnavailable: 0` for zero-downtime
- [ ] Namespace, RBAC Role/RoleBinding, and NetworkPolicy created for the workload
- [ ] `kubectl rollout status` check is part of the CI/CD pipeline (fail-fast on bad rollout)
- [ ] Pod Disruption Budget (PDB) defined for critical deployments with `minAvailable ≥ 1`

## Troubleshooting

**Error: `ImagePullBackOff`**
Cause: Kubernetes cannot pull the container image — wrong tag, private registry without credentials, or network issue.
Fix:
1. `kubectl describe pod <name>` → read the Events section for the exact error.
2. Verify the image/tag exists: `docker pull <image>:<tag>`.
3. For private registries: `kubectl create secret docker-registry regcred --docker-server=... --docker-username=... --docker-password=...` then add `imagePullSecrets: [{name: regcred}]` to the pod spec.

**Error: `CrashLoopBackOff`**
Cause: The container starts and exits repeatedly — bad entrypoint, missing dependency, or OOM kill.
Fix:
1. `kubectl logs <pod> --previous` to see last crash output.
2. `kubectl describe pod <pod>` → check `Last State` exit code (137 = OOM, 1 = app error).
3. Increase memory limit or fix application startup error.

**Error: Pods stuck in `Pending`**
Cause: Scheduler cannot find a node meeting the pod's constraints (CPU/memory, node selector, tolerations).
Fix:
1. `kubectl describe pod <name>` → Events will say `Insufficient cpu` or `no nodes