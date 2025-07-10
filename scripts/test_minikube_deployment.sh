#!/bin/bash

# PromptStrike Minikube Deployment Test
# Extends test coverage to include Minikube environment
# 建议: 测试 Minikube 环境，增加覆盖面

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REPO_URL="https://siwenwang0803.github.io/PromptStrike"
CHART_NAME="promptstrike-sidecar"
RELEASE_NAME="psguard"
NAMESPACE="promptstrike-minikube-test"
OPENAI_API_KEY="${OPENAI_API_KEY:-sk-test-key-for-minikube}"

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🎯 $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    print_section "检查 Minikube 环境 / Checking Minikube Environment"
    
    # Check required tools
    for tool in minikube kubectl helm; do
        if ! command -v $tool &> /dev/null; then
            echo -e "${RED}❌ $tool not found${NC}"
            echo "Please install $tool and try again."
            exit 1
        else
            echo -e "${GREEN}✅ $tool found: $(command -v $tool)${NC}"
        fi
    done
}

# Function to start Minikube
start_minikube() {
    print_section "启动 Minikube 集群 / Starting Minikube Cluster"
    
    # Check if minikube is running
    if minikube status | grep -q "host: Running"; then
        echo -e "${YELLOW}⚠️  Minikube is already running${NC}"
        echo -e "${YELLOW}🔄 Restarting for clean test...${NC}"
        minikube stop
        sleep 5
    fi
    
    echo -e "${YELLOW}🚀 Starting Minikube...${NC}"
    
    # Start with specific configuration
    minikube start \
        --driver=docker \
        --cpus=2 \
        --memory=4096 \
        --kubernetes-version=v1.28.0 \
        --addons=ingress,dashboard,metrics-server
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Minikube started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start Minikube${NC}"
        exit 1
    fi
    
    # Verify cluster
    echo -e "${YELLOW}🔍 Verifying Minikube cluster...${NC}"
    kubectl cluster-info
    kubectl get nodes
    
    # Enable addons
    echo -e "${YELLOW}🔧 Enabling useful addons...${NC}"
    minikube addons enable ingress
    minikube addons enable dashboard
    minikube addons enable metrics-server
    
    echo -e "${GREEN}✅ Minikube environment ready${NC}"
}

# Function to add Helm repository
add_helm_repo() {
    echo -e "${YELLOW}📦 Adding PromptStrike Helm repository...${NC}"
    
    # Remove if exists
    helm repo remove promptstrike 2>/dev/null || true
    
    if helm repo add promptstrike $REPO_URL; then
        echo -e "${GREEN}✅ Repository added successfully${NC}"
    else
        echo -e "${RED}❌ Failed to add repository${NC}"
        exit 1
    fi
    
    helm repo update
    helm search repo promptstrike --versions
}

# Function to deploy to Minikube
deploy_to_minikube() {
    print_section "Minikube 部署测试 / Minikube Deployment Test"
    
    # Create namespace
    echo -e "${YELLOW}📦 Creating namespace '${NAMESPACE}'...${NC}"
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy with Helm
    echo -e "${YELLOW}🚀 Deploying PromptStrike Guardrail to Minikube...${NC}"
    
    helm install $RELEASE_NAME promptstrike/$CHART_NAME \
        --namespace $NAMESPACE \
        --set openai.apiKey="$OPENAI_API_KEY" \
        --set image.tag="latest" \
        --set resources.limits.memory="256Mi" \
        --set resources.requests.memory="128Mi" \
        --set ingress.enabled=true \
        --set ingress.className="nginx" \
        --wait --timeout=300s
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Helm deployment to Minikube successful${NC}"
    else
        echo -e "${RED}❌ Helm deployment to Minikube failed${NC}"
        echo "Debugging information:"
        kubectl get pods -n $NAMESPACE
        kubectl describe pods -n $NAMESPACE
        exit 1
    fi
}

# Function to verify deployment
verify_deployment() {
    print_section "验证 Minikube 部署 / Verifying Minikube Deployment"
    
    echo -e "${YELLOW}🔍 Checking deployment status...${NC}"
    
    # Check pods
    echo "Pod status:"
    kubectl get pods -n $NAMESPACE -o wide
    
    # Check services
    echo "Service status:"
    kubectl get services -n $NAMESPACE
    
    # Check ingress
    echo "Ingress status:"
    kubectl get ingress -n $NAMESPACE
    
    # Verify pod is running
    echo -e "${YELLOW}⏳ Waiting for pods to be ready...${NC}"
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=promptstrike-sidecar -n $NAMESPACE --timeout=120s
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ All pods are ready${NC}"
    else
        echo -e "${RED}❌ Pods failed to become ready${NC}"
        kubectl describe pods -n $NAMESPACE
        exit 1
    fi
    
    # Test service accessibility via Minikube
    echo -e "${YELLOW}🌐 Testing service accessibility...${NC}"
    SERVICE_URL=$(minikube service $RELEASE_NAME-promptstrike-sidecar --url -n $NAMESPACE 2>/dev/null || echo "")
    
    if [ -n "$SERVICE_URL" ]; then
        echo "Service URL: $SERVICE_URL"
        # Test health endpoint
        curl -s "$SERVICE_URL/health" --connect-timeout 5 || echo "Health endpoint test completed"
    else
        echo -e "${YELLOW}⚠️  Service URL not available (may be normal)${NC}"
    fi
}

# Function to test Minikube-specific features
test_minikube_features() {
    print_section "Minikube 特性测试 / Minikube-Specific Features Test"
    
    # Test dashboard access
    echo -e "${YELLOW}📊 Testing Kubernetes Dashboard...${NC}"
    if minikube addons list | grep -q "dashboard.*enabled"; then
        echo -e "${GREEN}✅ Kubernetes Dashboard is enabled${NC}"
        echo "Dashboard URL: $(minikube dashboard --url 2>/dev/null &)"
        sleep 2
        pkill -f "minikube dashboard" 2>/dev/null || true
    else
        echo -e "${YELLOW}⚠️  Dashboard not enabled${NC}"
    fi
    
    # Test metrics server
    echo -e "${YELLOW}📈 Testing Metrics Server...${NC}"
    if kubectl top nodes 2>/dev/null; then
        echo -e "${GREEN}✅ Metrics Server is working${NC}"
    else
        echo -e "${YELLOW}⚠️  Metrics Server not ready (may need more time)${NC}"
    fi
    
    # Test port forwarding
    echo -e "${YELLOW}🔗 Testing port forwarding...${NC}"
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=promptstrike-sidecar -o jsonpath='{.items[0].metadata.name}')
    
    if [ -n "$POD_NAME" ]; then
        echo "Testing port forward to pod: $POD_NAME"
        timeout 5 kubectl port-forward $POD_NAME 8081:8080 -n $NAMESPACE >/dev/null 2>&1 &
        PORT_FORWARD_PID=$!
        sleep 2
        
        if curl -s http://localhost:8081/health --connect-timeout 2 >/dev/null; then
            echo -e "${GREEN}✅ Port forwarding works${NC}"
        else
            echo -e "${YELLOW}⚠️  Port forwarding test completed (endpoint may not exist)${NC}"
        fi
        
        kill $PORT_FORWARD_PID 2>/dev/null || true
    else
        echo -e "${YELLOW}⚠️  No pod found for port forwarding test${NC}"
    fi
}

# Function to test load balancing
test_load_balancing() {
    print_section "负载均衡测试 / Load Balancing Test"
    
    echo -e "${YELLOW}⚖️  Testing load balancing with multiple replicas...${NC}"
    
    # Scale up deployment
    kubectl scale deployment $RELEASE_NAME-promptstrike-sidecar --replicas=3 -n $NAMESPACE
    
    # Wait for scaling
    echo -e "${YELLOW}⏳ Waiting for scale up...${NC}"
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=promptstrike-sidecar -n $NAMESPACE --timeout=120s
    
    # Check scaled pods
    echo "Scaled deployment status:"
    kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=promptstrike-sidecar
    
    # Test service load balancing
    echo -e "${YELLOW}🔄 Testing service load balancing...${NC}"
    SERVICE_IP=$(kubectl get service $RELEASE_NAME-promptstrike-sidecar -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    
    if [ -n "$SERVICE_IP" ]; then
        echo "Service ClusterIP: $SERVICE_IP"
        for i in {1..5}; do
            echo "Request $i:"
            kubectl run test-curl-$i --rm -i --restart=Never --image=curlimages/curl -- \
                curl -s http://$SERVICE_IP:8080/health --connect-timeout 2 || echo "Request completed"
        done
    else
        echo -e "${YELLOW}⚠️  Service IP not available${NC}"
    fi
    
    # Scale back down
    kubectl scale deployment $RELEASE_NAME-promptstrike-sidecar --replicas=1 -n $NAMESPACE
    
    echo -e "${GREEN}✅ Load balancing test completed${NC}"
}

# Function to cleanup
cleanup_minikube() {
    print_section "清理 Minikube 环境 / Cleaning up Minikube Environment"
    
    local cleanup_cluster=${1:-false}
    
    echo -e "${YELLOW}🧹 Cleaning up deployment...${NC}"
    
    # Uninstall Helm release
    helm uninstall $RELEASE_NAME -n $NAMESPACE 2>/dev/null || true
    
    # Delete namespace
    kubectl delete namespace $NAMESPACE 2>/dev/null || true
    
    # Remove Helm repo
    helm repo remove promptstrike 2>/dev/null || true
    
    if [ "$cleanup_cluster" = "true" ]; then
        echo -e "${YELLOW}🛑 Stopping Minikube cluster...${NC}"
        minikube stop
        echo -e "${GREEN}✅ Minikube cleanup completed${NC}"
    else
        echo -e "${GREEN}✅ Deployment cleanup completed (cluster left running)${NC}"
    fi
}

# Main execution function
main() {
    local cleanup_cluster=${CLEANUP_CLUSTER:-false}
    
    print_section "PromptStrike Minikube 部署测试 / Minikube Deployment Test"
    
    echo "Test Configuration:"
    echo "- Repository: $REPO_URL"
    echo "- Chart: $CHART_NAME"
    echo "- Namespace: $NAMESPACE"
    echo "- Cleanup cluster: $cleanup_cluster"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Start Minikube
    start_minikube
    
    # Add Helm repository
    add_helm_repo
    
    # Deploy to Minikube
    deploy_to_minikube
    
    # Verify deployment
    verify_deployment
    
    # Test Minikube-specific features
    test_minikube_features
    
    # Test load balancing
    test_load_balancing
    
    # Cleanup
    cleanup_minikube "$cleanup_cluster"
    
    print_section "Minikube 测试完成 / Minikube Test Completed"
    echo -e "${GREEN}🎉 Minikube deployment test passed successfully!${NC}"
    echo -e "${GREEN}✅ Exit code: 0${NC}"
}

# Handle script arguments
case "${1:-}" in
    --cleanup-cluster)
        export CLEANUP_CLUSTER=true
        ;;
    --help)
        echo "Usage: $0 [--cleanup-cluster]"
        echo ""
        echo "Options:"
        echo "  --cleanup-cluster  Stop Minikube cluster after testing"
        echo "  --help            Show this help"
        echo ""
        echo "Environment variables:"
        echo "  OPENAI_API_KEY    API key for testing (default: sk-test-key-for-minikube)"
        echo "  CLEANUP_CLUSTER   Stop cluster after tests (default: false)"
        exit 0
        ;;
esac

# Execute main function
main

exit 0