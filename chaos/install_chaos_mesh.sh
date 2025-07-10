#!/bin/bash
# Install Chaos Mesh for RedForge Chaos Testing
# 目标：验证 data_corruption 和 protocol_violation 场景下系统韧性

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎯 Installing Chaos Mesh for RedForge Chaos Testing${NC}"
echo "==============================================="

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
        exit 1
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Kubernetes cluster not accessible. Please check your kubeconfig.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ kubectl is available and cluster is accessible${NC}"
}

# Function to install Chaos Mesh
install_chaos_mesh() {
    echo -e "${YELLOW}📦 Installing Chaos Mesh...${NC}"
    
    # Method 1: Using Helm (recommended)
    if command -v helm &> /dev/null; then
        echo -e "${GREEN}🎯 Installing Chaos Mesh using Helm...${NC}"
        
        # Add Chaos Mesh repository
        helm repo add chaos-mesh https://charts.chaos-mesh.org
        helm repo update
        
        # Install Chaos Mesh
        helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-mesh --create-namespace \
            --set chaosDaemon.runtime=containerd \
            --set chaosDaemon.socketPath=/run/containerd/containerd.sock \
            --set dashboard.securityMode=false \
            --wait --timeout=300s
        
        echo -e "${GREEN}✅ Chaos Mesh installed successfully via Helm${NC}"
    else
        # Method 2: Using kubectl directly
        echo -e "${YELLOW}📦 Installing Chaos Mesh using kubectl...${NC}"
        
        # Create namespace
        kubectl create namespace chaos-mesh || echo "Namespace chaos-mesh already exists"
        
        # Install Chaos Mesh CRDs and components
        kubectl apply -f https://raw.githubusercontent.com/chaos-mesh/chaos-mesh/master/manifests/crd.yaml
        kubectl apply -f https://raw.githubusercontent.com/chaos-mesh/chaos-mesh/master/manifests/rbac.yaml
        kubectl apply -f https://raw.githubusercontent.com/chaos-mesh/chaos-mesh/master/manifests/chaos-mesh.yaml
        
        # Wait for deployment to be ready
        kubectl wait --for=condition=Available --timeout=300s deployment/chaos-controller-manager -n chaos-mesh
        kubectl wait --for=condition=Available --timeout=300s deployment/chaos-dashboard -n chaos-mesh
        
        echo -e "${GREEN}✅ Chaos Mesh installed successfully via kubectl${NC}"
    fi
}

# Function to verify installation
verify_installation() {
    echo -e "${YELLOW}🔍 Verifying Chaos Mesh installation...${NC}"
    
    # Check pods
    echo "Checking Chaos Mesh pods:"
    kubectl get pods -n chaos-mesh
    
    # Check services
    echo -e "\nChecking Chaos Mesh services:"
    kubectl get svc -n chaos-mesh
    
    # Check CRDs
    echo -e "\nChecking Chaos Mesh CRDs:"
    kubectl get crd | grep chaos-mesh.org
    
    # Verify controller is running
    if kubectl get pods -n chaos-mesh -l app.kubernetes.io/name=chaos-mesh -o jsonpath='{.items[0].status.phase}' | grep -q "Running"; then
        echo -e "${GREEN}✅ Chaos Mesh controller is running${NC}"
    else
        echo -e "${RED}❌ Chaos Mesh controller is not running${NC}"
        return 1
    fi
    
    # Check dashboard
    if kubectl get pods -n chaos-mesh -l app.kubernetes.io/name=chaos-dashboard -o jsonpath='{.items[0].status.phase}' | grep -q "Running"; then
        echo -e "${GREEN}✅ Chaos Mesh dashboard is running${NC}"
    else
        echo -e "${RED}❌ Chaos Mesh dashboard is not running${NC}"
        return 1
    fi
}

# Function to set up dashboard access
setup_dashboard() {
    echo -e "${YELLOW}🖥️  Setting up Chaos Mesh dashboard access...${NC}"
    
    # Port forward to dashboard
    echo "To access Chaos Mesh dashboard, run:"
    echo "kubectl port-forward -n chaos-mesh svc/chaos-dashboard 2333:2333"
    echo "Then open http://localhost:2333 in your browser"
    
    # Create service account for dashboard access (if needed)
    cat <<EOF > /tmp/chaos-mesh-sa.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: chaos-mesh-dashboard
  namespace: chaos-mesh
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: chaos-mesh-dashboard
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints", "nodes"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["chaos-mesh.org"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: chaos-mesh-dashboard
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: chaos-mesh-dashboard
subjects:
- kind: ServiceAccount
  name: chaos-mesh-dashboard
  namespace: chaos-mesh
EOF
    
    kubectl apply -f /tmp/chaos-mesh-sa.yaml
    rm /tmp/chaos-mesh-sa.yaml
    
    echo -e "${GREEN}✅ Dashboard access configured${NC}"
}

# Function to create test target namespace
create_test_namespace() {
    echo -e "${YELLOW}🎯 Creating test namespace for RedForge...${NC}"
    
    # Create namespace if it doesn't exist
    kubectl create namespace redforge-test || echo "Namespace redforge-test already exists"
    
    # Add chaos-mesh annotation to enable chaos injection
    kubectl annotate namespace redforge-test chaos-mesh.org/inject=enabled --overwrite
    
    echo -e "${GREEN}✅ Test namespace created and configured${NC}"
}

# Function to install chaos testing tools
install_chaos_tools() {
    echo -e "${YELLOW}🛠️  Installing additional chaos testing tools...${NC}"
    
    # Install stress-ng for resource stress testing
    cat <<EOF > /tmp/stress-ng-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stress-ng
  namespace: redforge-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: stress-ng
  template:
    metadata:
      labels:
        app: stress-ng
    spec:
      containers:
      - name: stress-ng
        image: polinux/stress-ng:latest
        command: ["sleep", "infinity"]
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "512Mi"
            cpu: "500m"
EOF
    
    kubectl apply -f /tmp/stress-ng-deployment.yaml
    rm /tmp/stress-ng-deployment.yaml
    
    echo -e "${GREEN}✅ Chaos testing tools installed${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}🚀 Starting Chaos Mesh installation for RedForge...${NC}"
    
    check_kubectl
    install_chaos_mesh
    verify_installation
    setup_dashboard
    create_test_namespace
    install_chaos_tools
    
    echo -e "${GREEN}🎉 Chaos Mesh installation completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Access dashboard: kubectl port-forward -n chaos-mesh svc/chaos-dashboard 2333:2333"
    echo "2. Run chaos tests: python -m pytest tests/chaos/ -m 'data_corruption or protocol_violation'"
    echo "3. Monitor sidecar logs: kubectl logs -l app=psguard -c guardrail-sidecar"
    echo ""
    echo "Available chaos scenarios:"
    echo "- Data corruption: IOChaos, data corruption attacks"
    echo "- Protocol violation: NetworkChaos, malformed packets"
    echo "- Network delay: NetworkChaos with latency"
    echo "- Pod failure: PodChaos with pod kill"
}

# Run main function
main "$@"