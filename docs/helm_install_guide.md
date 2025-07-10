# RedForge Guardrail Pilot-0 Installation Guide

This guide provides step-by-step instructions for installing RedForge Guardrail using Helm for Pilot-0 customers, ensuring PCI-DSS and NIST compliance.

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

### Step 2: Add RedForge Helm Repository

```bash
helm repo add redforge https://siwenwang0803.github.io/RedForge
helm repo update
```

### Step 3: Create a Namespace (Optional)

```bash
kubectl create namespace redforge-pilot
kubectl config set-context --current --namespace=redforge-pilot
```

### Step 4: Configure Your API Keys

```bash
kubectl create secret generic my-openai-api-key --from-literal=api-key="sk-your-openai-api-key-here" -n redforge-pilot
```

### Step 5: Install RedForge Guardrail

```bash
helm install guardrail redforge/redforge-guardrail \
  --namespace redforge-pilot \
  --set guardrail.secrets.openaiApiKey=true \
  --set guardrail.secrets.openaiSecretName=my-openai-api-key \
  --set guardrail.secrets.openaiSecretKey=api-key \
  --set guardrail.samplingRate=0.05 \
  --set guardrail.tokenGuard.threshold=4000
```

**Alternative (DOD Command):**
```bash
helm install guardrail redforge/redforge-guardrail -n rf --set openai.apiKey=$OPENAI_API_KEY
```

### Step 6: Verify Installation

```bash
kubectl get deployments -l app.kubernetes.io/name=redforge-guardrail
kubectl get pods -l app.kubernetes.io/name=redforge-guardrail
```

**Expected Output:**
```
NAME                                READY   UP-TO-DATE   AVAILABLE   AGE
redforge-guardrail   1/1     1            1           2m
```

### Step 7: Run Validation Script

```bash
./scripts/verify_helm_repository.sh
```

### Step 8: Access Metrics Dashboard

```bash
kubectl port-forward service/redforge-guardrail-metrics 9090:9090 -n redforge-pilot
```

Open: http://localhost:9090/metrics

### Step 9: Verify Configuration

```bash
kubectl get configmap redforge-guardrail-config -n redforge-pilot -o yaml
```

## Screenshots and Verification Points

### Expected Pod Status

```
NAME                                                    READY   STATUS    RESTARTS   AGE
redforge-guardrail-xxx-yyy   2/2     Running   0          5m
```

### Expected Services

```bash
kubectl get services -l app.kubernetes.io/name=redforge-guardrail -n redforge-pilot
```

```
NAME                                             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
redforge-guardrail    ClusterIP   10.96.x.x      <none>        8080/TCP   5m
redforge-guardrail-metrics ClusterIP 10.96.x.x <none>        9090/TCP   5m
```

### Expected Log Messages

```bash
kubectl logs -l app.kubernetes.io/name=redforge-guardrail -c guardrail-sidecar -n redforge-pilot
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
  name: redforge-reports
  namespace: redforge-pilot
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

helm upgrade guardrail redforge/redforge-guardrail \
  --namespace redforge-pilot \
  --reuse-values \
  --set guardrail.reportPVC.enabled=true \
  --set guardrail.reportPVC.claimName=redforge-reports
```

### Configure Custom OTEL Endpoint

```bash
helm upgrade guardrail redforge/redforge-guardrail \
  --namespace redforge-pilot \
  --reuse-values \
  --set guardrail.otelExporter.url="http://your-otel-collector:4317"
```

## Troubleshooting

### Common Issues

**Pod Stuck in Pending:**
```bash
kubectl describe pods -l app.kubernetes.io/name=redforge-guardrail -n redforge-pilot
```

**Sidecar Failing:**
```bash
kubectl logs -l app.kubernetes.io/name=redforge-guardrail -c guardrail-sidecar -n redforge-pilot
```

**Metrics Not Responding:**
```bash
kubectl exec $POD_NAME -c guardrail-sidecar -n redforge-pilot -- wget -q -O - http://localhost:9090/metrics
```

## Getting Support

- **Slack:** #redforge-pilot-support
- **Email:** pilot-support@redforge.dev
- **Office Hours:** Tuesdays 2PM PST