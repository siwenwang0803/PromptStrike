#!/bin/bash

# RedForge Enhanced Helm Deployment Verification
# Handles environments with and without Docker daemon
# Provides comprehensive testing with graceful fallbacks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
REPO_URL="https://siwenwang0803.github.io/RedForge"
CHART_NAME="redforge-sidecar"
CHART_VERSION="0.2.0"
RELEASE_NAME="psguard"
NAMESPACE="redforge-test"
OPENAI_API_KEY="${OPENAI_API_KEY:-sk-test-key-for-deployment}"

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🎯 $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to track test results
track_test() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    case "$status" in
        "PASS")
            TESTS_PASSED=$((TESTS_PASSED + 1))
            echo -e "${GREEN}✅ $test_name: PASSED${NC} - $details"
            ;;
        "FAIL")
            TESTS_FAILED=$((TESTS_FAILED + 1))
            echo -e "${RED}❌ $test_name: FAILED${NC} - $details"
            ;;
        "SKIP")
            TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
            echo -e "${YELLOW}⚠️  $test_name: SKIPPED${NC} - $details"
            ;;
    esac
}

# Function to check Docker availability
check_docker() {
    if docker ps >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker daemon is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Docker daemon is not running or not available${NC}"
        echo -e "${YELLOW}   This is normal in CI environments or when Docker Desktop is not started${NC}"
        return 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_section "环境检查 / Environment Check"
    
    local all_good=true
    
    # Check core tools
    for tool in helm kubectl; do
        if command -v $tool &> /dev/null; then
            track_test "Tool: $tool" "PASS" "Found at $(command -v $tool)"
        else
            track_test "Tool: $tool" "FAIL" "Not found"
            all_good=false
        fi
    done
    
    # Check Docker
    if check_docker; then
        track_test "Docker availability" "PASS" "Docker daemon running"
        export DOCKER_AVAILABLE=true
    else
        track_test "Docker availability" "SKIP" "Docker daemon not running"
        export DOCKER_AVAILABLE=false
    fi
    
    # Check cluster tools
    for tool in kind minikube; do
        if command -v $tool &> /dev/null; then
            track_test "Tool: $tool" "PASS" "Found at $(command -v $tool)"
        else
            track_test "Tool: $tool" "SKIP" "Not found"
        fi
    done
    
    # Check AWS tools
    if command -v aws &> /dev/null && command -v eksctl &> /dev/null; then
        if aws sts get-caller-identity &> /dev/null; then
            track_test "AWS tools" "PASS" "AWS CLI and eksctl available with valid credentials"
            export AWS_AVAILABLE=true
        else
            track_test "AWS tools" "SKIP" "AWS tools found but credentials not configured"
            export AWS_AVAILABLE=false
        fi
    else
        track_test "AWS tools" "SKIP" "AWS CLI or eksctl not found"
        export AWS_AVAILABLE=false
    fi
    
    return 0
}

# Function to test Helm repository
test_helm_repository() {
    print_section "Helm 仓库测试 / Helm Repository Test"
    
    # Remove existing repo
    helm repo remove redforge 2>/dev/null || true
    
    # Add repository
    if helm repo add redforge "$REPO_URL" >/dev/null 2>&1; then
        track_test "Helm repo add" "PASS" "Repository added successfully"
    else
        track_test "Helm repo add" "FAIL" "Failed to add repository"
        return 1
    fi
    
    # Update repository
    if helm repo update >/dev/null 2>&1; then
        track_test "Helm repo update" "PASS" "Repository updated successfully"
    else
        track_test "Helm repo update" "FAIL" "Failed to update repository"
        return 1
    fi
    
    # Search for chart
    if helm search repo $CHART_NAME >/dev/null 2>&1; then
        track_test "Chart search" "PASS" "Chart found in repository"
    else
        track_test "Chart search" "FAIL" "Chart not found"
        return 1
    fi
    
    # Inspect chart
    if helm show chart redforge/$CHART_NAME >/dev/null 2>&1; then
        track_test "Chart inspection" "PASS" "Chart metadata accessible"
    else
        track_test "Chart inspection" "FAIL" "Chart metadata not accessible"
        return 1
    fi
    
    # Test template rendering (dry-run)
    if helm template test redforge/$CHART_NAME \
        --set openai.apiKey="test-key" \
        --namespace $NAMESPACE >/dev/null 2>&1; then
        track_test "Template rendering" "PASS" "Chart templates render correctly"
    else
        track_test "Template rendering" "FAIL" "Chart template rendering failed"
        return 1
    fi
    
    return 0
}

# Function to simulate cluster deployment
simulate_cluster_deployment() {
    local cluster_type="$1"
    
    print_section "${cluster_type} 部署模拟 / ${cluster_type} Deployment Simulation"
    
    echo -e "${YELLOW}🎭 Running deployment simulation (Docker not available)${NC}"
    
    # Simulate helm install with template rendering (client-side only)
    echo -e "${YELLOW}📋 Testing Helm template rendering (install simulation)...${NC}"
    if helm template $RELEASE_NAME redforge/$CHART_NAME \
        --namespace $NAMESPACE \
        --set openai.apiKey="$OPENAI_API_KEY" \
        --set image.tag="latest" \
        --set resources.limits.memory="256Mi" \
        --set resources.requests.memory="128Mi" >/dev/null 2>&1; then
        track_test "${cluster_type} deployment simulation" "PASS" "Helm template rendering completed successfully"
    else
        track_test "${cluster_type} deployment simulation" "FAIL" "Helm template rendering failed"
        return 1
    fi
    
    # Simulate upgrade with template rendering
    echo -e "${YELLOW}📋 Testing Helm template rendering (upgrade simulation)...${NC}"
    if helm template $RELEASE_NAME-upgrade redforge/$CHART_NAME \
        --namespace $NAMESPACE \
        --set openai.apiKey="$OPENAI_API_KEY" \
        --set image.tag="latest" \
        --set resources.limits.memory="512Mi" \
        --set replicaCount=2 >/dev/null 2>&1; then
        track_test "${cluster_type} upgrade simulation" "PASS" "Helm upgrade simulation completed"
    else
        track_test "${cluster_type} upgrade simulation" "FAIL" "Helm upgrade simulation failed"
        return 1
    fi
    
    # Test values validation
    echo -e "${YELLOW}📋 Testing values validation...${NC}"
    if helm template test-validation redforge/$CHART_NAME \
        --set openai.apiKey="test-key" \
        --set image.tag="v1.0.0" \
        --set replicaCount=3 \
        --set resources.limits.cpu="500m" \
        --set resources.limits.memory="1Gi" \
        --set ingress.enabled=true \
        --namespace $NAMESPACE >/dev/null 2>&1; then
        track_test "${cluster_type} values validation" "PASS" "Complex values validated successfully"
    else
        track_test "${cluster_type} values validation" "FAIL" "Values validation failed"
        return 1
    fi
    
    return 0
}

# Function to test real cluster deployment
test_real_cluster_deployment() {
    local cluster_type="$1"
    local create_cluster_cmd="$2"
    local cleanup_cluster_cmd="$3"
    
    print_section "${cluster_type} 真实部署测试 / ${cluster_type} Real Deployment Test"
    
    echo -e "${YELLOW}🚀 Creating ${cluster_type} cluster...${NC}"
    if eval "$create_cluster_cmd" >/dev/null 2>&1; then
        track_test "${cluster_type} cluster creation" "PASS" "Cluster created successfully"
    else
        track_test "${cluster_type} cluster creation" "FAIL" "Cluster creation failed"
        return 1
    fi
    
    # Deploy with Helm
    echo -e "${YELLOW}📦 Deploying to ${cluster_type}...${NC}"
    if helm install $RELEASE_NAME redforge/$CHART_NAME \
        --namespace $NAMESPACE \
        --create-namespace \
        --set openai.apiKey="$OPENAI_API_KEY" \
        --set image.tag="latest" \
        --wait --timeout=300s >/dev/null 2>&1; then
        track_test "${cluster_type} deployment" "PASS" "Helm deployment successful"
    else
        track_test "${cluster_type} deployment" "FAIL" "Helm deployment failed"
        eval "$cleanup_cluster_cmd" >/dev/null 2>&1 || true
        return 1
    fi
    
    # Verify deployment
    if kubectl get pods -n $NAMESPACE | grep -q "Running"; then
        track_test "${cluster_type} pod verification" "PASS" "Pods are running"
    else
        track_test "${cluster_type} pod verification" "FAIL" "Pods not running"
    fi
    
    # Test upgrade
    if helm upgrade $RELEASE_NAME redforge/$CHART_NAME \
        --namespace $NAMESPACE \
        --set replicaCount=2 \
        --wait --timeout=180s >/dev/null 2>&1; then
        track_test "${cluster_type} upgrade" "PASS" "Helm upgrade successful"
    else
        track_test "${cluster_type} upgrade" "FAIL" "Helm upgrade failed"
    fi
    
    # Cleanup
    helm uninstall $RELEASE_NAME -n $NAMESPACE >/dev/null 2>&1 || true
    kubectl delete namespace $NAMESPACE >/dev/null 2>&1 || true
    eval "$cleanup_cluster_cmd" >/dev/null 2>&1 || true
    
    return 0
}

# Function to test Kind deployment
test_kind_deployment() {
    if ! command -v kind &> /dev/null; then
        track_test "Kind deployment" "SKIP" "Kind tool not available"
        return 0
    fi
    
    if [ "$DOCKER_AVAILABLE" = "true" ]; then
        test_real_cluster_deployment "Kind" \
            "kind create cluster --name psguard-test-kind" \
            "kind delete cluster --name psguard-test-kind"
    else
        simulate_cluster_deployment "Kind"
    fi
}

# Function to test Minikube deployment
test_minikube_deployment() {
    if ! command -v minikube &> /dev/null; then
        track_test "Minikube deployment" "SKIP" "Minikube tool not available"
        return 0
    fi
    
    if [ "$DOCKER_AVAILABLE" = "true" ]; then
        test_real_cluster_deployment "Minikube" \
            "minikube start --driver=docker --cpus=2 --memory=2048" \
            "minikube delete"
    else
        simulate_cluster_deployment "Minikube"
    fi
}

# Function to test EKS deployment
test_eks_deployment() {
    if [ "$AWS_AVAILABLE" != "true" ]; then
        track_test "EKS deployment" "SKIP" "AWS tools not available or not configured"
        return 0
    fi
    
    if [ "${RUN_EKS_TESTS:-false}" = "true" ]; then
        test_real_cluster_deployment "EKS" \
            "eksctl create cluster --name psguard-test-eks --region us-west-2 --node-type t3.small --nodes 1" \
            "eksctl delete cluster --name psguard-test-eks --region us-west-2"
    else
        track_test "EKS deployment" "SKIP" "EKS tests disabled (set RUN_EKS_TESTS=true to enable)"
    fi
}

# Function to test Helm operations comprehensively
test_helm_operations() {
    print_section "Helm 操作综合测试 / Comprehensive Helm Operations Test"
    
    # Test various Helm commands with dry-run
    local operations=(
        "helm show values redforge/$CHART_NAME"
        "helm show readme redforge/$CHART_NAME"
        "helm show all redforge/$CHART_NAME"
        "helm pull redforge/$CHART_NAME --version $CHART_VERSION --untar"
    )
    
    for operation in "${operations[@]}"; do
        local op_name=$(echo "$operation" | cut -d' ' -f2)
        if eval "$operation >/dev/null 2>&1"; then
            track_test "Helm $op_name" "PASS" "Command executed successfully"
        else
            track_test "Helm $op_name" "FAIL" "Command failed"
        fi
    done
    
    # Clean up pulled chart
    rm -rf $CHART_NAME 2>/dev/null || true
}

# Function to generate comprehensive report
generate_report() {
    print_section "测试报告 / Test Report"
    
    local total_tests=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))
    
    echo -e "${BLUE}📊 测试统计 / Test Statistics:${NC}"
    echo "  Total tests: $total_tests"
    echo -e "  Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "  Failed: ${RED}$TESTS_FAILED${NC}"
    echo -e "  Skipped: ${YELLOW}$TESTS_SKIPPED${NC}"
    
    if [ $total_tests -gt 0 ]; then
        local success_rate=$(( (TESTS_PASSED * 100) / total_tests ))
        echo "  Success rate: ${success_rate}%"
    fi
    
    echo ""
    echo -e "${BLUE}🎯 环境状态 / Environment Status:${NC}"
    echo -e "  Docker: $([ "$DOCKER_AVAILABLE" = "true" ] && echo "${GREEN}Available${NC}" || echo "${YELLOW}Not Available${NC}")"
    echo -e "  AWS: $([ "$AWS_AVAILABLE" = "true" ] && echo "${GREEN}Available${NC}" || echo "${YELLOW}Not Available${NC}")"
    
    echo ""
    if [ $TESTS_FAILED -eq 0 ]; then
        if [ "$DOCKER_AVAILABLE" = "true" ]; then
            echo -e "${GREEN}🎉 ALL TESTS PASSED - Full deployment capability verified!${NC}"
        else
            echo -e "${GREEN}🎉 ALL AVAILABLE TESTS PASSED - Helm operations verified!${NC}"
            echo -e "${YELLOW}💡 To test full deployment, start Docker and run again${NC}"
        fi
        echo -e "${GREEN}✅ Exit code: 0${NC}"
        return 0
    else
        echo -e "${RED}❌ SOME TESTS FAILED - Review failed tests above${NC}"
        echo -e "${RED}🛠️  Address issues before proceeding${NC}"
        return 1
    fi
}

# Main execution function
main() {
    print_section "RedForge Helm 部署验证增强版 / Enhanced Helm Deployment Verification"
    
    echo "Configuration:"
    echo "- Repository: $REPO_URL"
    echo "- Chart: $CHART_NAME:$CHART_VERSION"
    echo "- Test mode: Enhanced (with Docker detection)"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Test Helm repository (always available)
    test_helm_repository
    
    # Test cluster deployments (Docker-dependent)
    test_kind_deployment
    test_minikube_deployment
    test_eks_deployment
    
    # Test Helm operations comprehensively
    test_helm_operations
    
    # Clean up Helm repo
    helm repo remove redforge 2>/dev/null || true
    
    # Generate final report
    generate_report
}

# Handle script arguments
case "${1:-}" in
    --help)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help         Show this help"
        echo ""
        echo "Environment variables:"
        echo "  OPENAI_API_KEY  API key for testing (default: sk-test-key-for-deployment)"
        echo "  RUN_EKS_TESTS   Enable EKS testing (default: false)"
        echo ""
        echo "Features:"
        echo "  - Automatically detects Docker availability"
        echo "  - Runs real deployments when Docker is available"
        echo "  - Falls back to simulation mode when Docker is not available"
        echo "  - Comprehensive Helm operations testing"
        echo "  - Detailed reporting with environment status"
        exit 0
        ;;
esac

# Execute main function
main

# Return appropriate exit code
exit $?