# PromptStrike Guardrail Pilot-0 Installation Guide

This guide provides step-by-step instructions for installing PromptStrike Guardrail using Helm for Pilot-0 customers, ensuring PCI-DSS and NIST compliance.

## Prerequisites

- Kubernetes cluster (v1.19+)
- Helm 3.2.0+
- kubectl configured to access your cluster
- Admin access to the target namespace

## Installation Steps

### Step 1: Prepare Your Environment

```bash
kubectl cluster-info
helm version
```

### Step 2: Add PromptStrike Helm Repository

```bash
helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike
helm repo update
```

### Step 3: Create a Namespace (Optional)

```bash
kubectl create namespace promptstrike-pilot
kubectl config set-context --current --namespace=promptstrike-pilot
```

### Step 4: Configure Your API Keys

```bash
kubectl create secret generic my-openai-api-key --from-literal=api-key="sk-your-openai-api-key-here" -n promptstrike-pilot
```

### Step 5: Install PromptStrike Guardrail

```bash
helm install guardrail promptstrike/promptstrike-guardrail \
  --namespace promptstrike-pilot \
  --set guardrail.secrets.openaiApiKey=true \
  --set guardrail.secrets.openaiSecretName=my-openai-api-key \
  --set guardrail.secrets.openaiSecretKey=api-key \
  --set guardrail.samplingRate=0.05 \
  --set guardrail.tokenGuard.threshold=4000
```

**Alternative (DOD Command):**
```bash
helm install guardrail promptstrike/promptstrike-guardrail -n ps --set openai.apiKey=$OPENAI_API_KEY
```

### Step 6: Verify Installation

```bash
kubectl get deployments -l app.kubernetes.io/name=promptstrike-guardrail
kubectl get pods -l app.kubernetes.io/name=promptstrike-guardrail
```

**Expected Output:**
```
NAME                                READY   UP-TO-DATE   AVAILABLE   AGE
promptstrike-guardrail   1/1     1            1           2m
```

### Step 7: Run Validation Script

```bash
./scripts/verify_helm_repository.sh
```

### Step 8: Access Metrics Dashboard

```bash
kubectl port-forward service/promptstrike-guardrail-metrics 9090:9090 -n promptstrike-pilot
```

Open: http://localhost:9090/metrics

### Step 9: Verify Configuration

```bash
kubectl get configmap promptstrike-guardrail-config -n promptstrike-pilot -o yaml
```

## Screenshots and Verification Points

### Expected Pod Status

```
NAME                                                    READY   STATUS    RESTARTS   AGE
promptstrike-guardrail-xxx-yyy   2/2     Running   0          5m
```

### Expected Services

```bash
kubectl get services -l app.kubernetes.io/name=promptstrike-guardrail -n promptstrike-pilot
```

```
NAME                                             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
promptstrike-guardrail    ClusterIP   10.96.x.x      <none>        8080/TCP   5m
promptstrike-guardrail-metrics ClusterIP 10.96.x.x <none>        9090/TCP   5m
```

### Expected Log Messages

```bash
kubectl logs -l app.kubernetes.io/name=promptstrike-guardrail -c guardrail-sidecar -n promptstrike-pilot
```

**Look for:**

- ✅ "Guardrail service started"
- ✅ "Token guard initialized with threshold: 4000"
- ✅ "OTEL exporter configured"
- ✅ "Metrics server listening on :9090"

## Advanced Configuration

### Enable Persistent Reports

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: promptstrike-reports
  namespace: promptstrike-pilot
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

helm upgrade guardrail promptstrike/promptstrike-guardrail \
  --namespace promptstrike-pilot \
  --reuse-values \
  --set guardrail.reportPVC.enabled=true \
  --set guardrail.reportPVC.claimName=promptstrike-reports
```

### Configure Custom OTEL Endpoint

```bash
helm upgrade guardrail promptstrike/promptstrike-guardrail \
  --namespace promptstrike-pilot \
  --reuse-values \
  --set guardrail.otelExporter.url="http://your-otel-collector:4317"
```

## Troubleshooting

### Common Issues

**Pod Stuck in Pending:**
```bash
kubectl describe pods -l app.kubernetes.io/name=promptstrike-guardrail -n promptstrike-pilot
```

**Sidecar Failing:**
```bash
kubectl logs -l app.kubernetes.io/name=promptstrike-guardrail -c guardrail-sidecar -n promptstrike-pilot
```

**Metrics Not Responding:**
```bash
kubectl exec $POD_NAME -c guardrail-sidecar -n promptstrike-pilot -- wget -q -O - http://localhost:9090/metrics
```

## Getting Support

- **Slack:** #promptstrike-pilot-support
- **Email:** pilot-support@promptstrike.dev
- **Office Hours:** Tuesdays 2PM PST