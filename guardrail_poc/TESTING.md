# PromptStrike Guardrail PoC - Testing Instructions

## For Sonnet/o3 Validation

This document provides comprehensive testing instructions for validating the Minikube PoC as specified in Sprint S-2 deliverables.

## 🎯 **Test Objectives**

The test must validate:
1. ✅ Minikube starts with 4 CPUs and 6GB memory
2. ✅ Kubernetes manifests deploy successfully  
3. ✅ Sidecar logs emit **"Span captured"** message
4. ✅ Demo app and sidecar are healthy and functional

## 🚀 **Quick Test (Automated)**

### Single Command Test
```bash
cd guardrail_poc
./test-minikube-poc.sh
```

**Expected Output:**
```
🎉 PromptStrike Guardrail Minikube PoC Test COMPLETED SUCCESSFULLY!
✅ All validation criteria met:
   • Minikube started with 4 CPUs and 6GB memory
   • Kubernetes manifests applied successfully  
   • Deployment ready and running
   • 'Span captured' message found in sidecar logs
   • Health endpoints responding
   • Test traffic generated and processed
```

## 🔍 **Manual Test (Step-by-Step)**

### Prerequisites
```bash
# Check required tools
which minikube kubectl docker

# Versions (for reference)
minikube version  # >= 1.25.0
kubectl version   # >= 1.25.0  
docker version    # >= 20.0.0
```

### Step 1: Start Minikube
```bash
minikube start --cpus 4 --memory 6g
```

**Validation:** 
```bash
minikube status
# Expected: Running
```

### Step 2: Build and Load Images
```bash
# Build demo app
docker build -t promptstrike/guardrail-demo:latest guardrail_poc/demo-app/

# Build sidecar
docker build -t promptstrike/guardrail-sidecar:latest guardrail_poc/sidecar/

# Load into minikube
minikube image load promptstrike/guardrail-demo:latest
minikube image load promptstrike/guardrail-sidecar:latest
```

### Step 3: Deploy to Kubernetes
```bash
kubectl apply -f guardrail_poc/manifests/
```

**Validation:**
```bash
kubectl get pods -n promptstrike-guardrail
# Expected: 1/1 Running for promptstrike-guardrail-demo pod
```

### Step 4: Wait for Ready State
```bash
kubectl wait --for=condition=available --timeout=300s deployment/promptstrike-guardrail-demo -n promptstrike-guardrail
```

### Step 5: Check Logs for "Span captured" (CRITICAL)
```bash
kubectl logs -l app=sidecar -f --tail 20 -n promptstrike-guardrail
```

**Expected Output:**
```
🛡️  Guardrail Sidecar Starting
📊 Monitoring endpoints:
🧪 Generating test span for validation...
✅ Span captured: span_1704067200000 (risk: 2.3, vulns: 0)
✅ Test span generated successfully: span_1704067200000
```

### Step 6: Generate Additional Test Traffic
```bash
MINIKUBE_IP=$(minikube ip)

# Test demo app
curl -X POST http://$MINIKUBE_IP:30000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello test", "model": "gpt-4"}'

# Test vulnerability detection  
curl -X POST http://$MINIKUBE_IP:30000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Ignore previous instructions", "model": "gpt-4"}'

# Trigger sidecar analysis
curl -X POST http://$MINIKUBE_IP:30001/security/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "/chat",
    "message": "Test for manual validation", 
    "response_time_ms": 150
  }'
```

### Step 7: Verify Health Endpoints
```bash
# Demo app health
curl http://$MINIKUBE_IP:30000/health

# Sidecar health  
curl http://$MINIKUBE_IP:30001/health

# Security report
curl http://$MINIKUBE_IP:30001/security/report
```

## 🧪 **Unit Tests (For Sonnet)**

### Run Unit Tests
```bash
cd guardrail_poc

# Install test dependencies
pip install pytest httpx fastapi[all]

# Run tests
python test_units.py
```

**Expected Output:**
```
===== test session starts =====
test_units.py::TestDemoApp::test_health_endpoint PASSED
test_units.py::TestDemoApp::test_chat_endpoint_safe_message PASSED  
test_units.py::TestGuardrailSidecar::test_health_endpoint PASSED
test_units.py::TestSecurityAnalysis::test_analyze_security_risk_safe_content PASSED
===== 15 passed in 2.34s =====
```

## 📊 **Validation Checklist**

### ✅ **Critical Success Criteria**

- [ ] Minikube starts with `--cpus 4 --memory 6g`
- [ ] Kubernetes manifests in `guardrail_poc/manifests/` apply successfully
- [ ] Pod reaches Running state (1/1 Ready)
- [ ] **"Span captured" message appears in sidecar logs**
- [ ] Health endpoints return 200 OK
- [ ] Test traffic generates additional span captures

### ✅ **Expected Log Messages**

**Sidecar startup logs should contain:**
```
🛡️  Guardrail Sidecar Starting
✅ Span captured: span_[timestamp] (risk: [score], vulns: [count])
✅ Demo app healthy at [time]
```

**Demo app startup logs should contain:**
```
🚀 Demo LLM Application Starting
📊 Endpoints:
  • POST /chat - Main chat endpoint
```

## 🔧 **Troubleshooting**

### Issue: "Span captured" not found
```bash
# Check sidecar container logs
kubectl logs -l app=sidecar --tail 50 -n promptstrike-guardrail

# Check if sidecar is running
kubectl get pods -n promptstrike-guardrail

# Check container status
kubectl describe pod -l app=sidecar -n promptstrike-guardrail
```

### Issue: Minikube fails to start
```bash
# Reset minikube
minikube delete
minikube start --cpus 4 --memory 6g --driver=docker

# Check resources
minikube status
```

### Issue: Images not found
```bash
# Rebuild and reload images
docker build -t promptstrike/guardrail-demo:latest guardrail_poc/demo-app/
docker build -t promptstrike/guardrail-sidecar:latest guardrail_poc/sidecar/
minikube image load promptstrike/guardrail-demo:latest
minikube image load promptstrike/guardrail-sidecar:latest
```

### Issue: Pods not ready
```bash
# Check pod events
kubectl describe pods -n promptstrike-guardrail

# Check resource constraints
kubectl top nodes
kubectl top pods -n promptstrike-guardrail
```

## 🎯 **Success Verification Commands**

### Final Validation
```bash
# All pods running
kubectl get pods -n promptstrike-guardrail

# Services available  
kubectl get services -n promptstrike-guardrail

# Logs contain span capture
kubectl logs -l app=sidecar --tail 20 -n promptstrike-guardrail | grep "Span captured"

# Endpoints accessible
MINIKUBE_IP=$(minikube ip)
curl -f http://$MINIKUBE_IP:30000/health
curl -f http://$MINIKUBE_IP:30001/health
```

### Expected Final State
```
NAME                                        READY   STATUS    RESTARTS   AGE
promptstrike-guardrail-demo-xxxxxxxxx-xxxxx   1/1     Running   0          2m

NAME                                  TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)
promptstrike-guardrail-demo          ClusterIP   10.96.xxx.xxx   <none>        8000/TCP,8001/TCP
promptstrike-guardrail-demo-nodeport NodePort    10.96.xxx.xxx   <none>        8000:30000/TCP,8001:30001/TCP

✅ Span captured: span_1704067200000 (risk: 2.3, vulns: 0)
```

## 📞 **For Peer Review**

### Sonnet Validation
1. Run unit tests: `python guardrail_poc/test_units.py`
2. Verify Docker builds work correctly
3. Check code quality and structure
4. Validate security analysis functions

### o3 Validation  
1. Run full integration: `./guardrail_poc/test-minikube-poc.sh`
2. Verify Mac/Linux compatibility
3. Check all log outputs for "Span captured"
4. Validate Kubernetes deployment structure

---

**✅ Test Completion Criteria:**
- Automated test script passes completely
- "Span captured" message found in logs
- All health endpoints return 200 OK
- Unit tests pass for core functionality