#!/bin/bash

# PSGuard Sidecar 资源开销测试脚本
# 目标：确保 Sidecar 容器 CPU ≤ 200m，内存 ≤ 180Mi，承受 500 RPS

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
CLUSTER_NAME="psguard-test"
NAMESPACE="psguard-test"
RELEASE_NAME="psguard"
CHART_PATH="./charts/psguard"
MONITORING_NS="monitoring"
TEST_DURATION="15m"
TARGET_RPS=500
CPU_LIMIT="200m"
MEMORY_LIMIT="180Mi"

# 函数：打印带颜色的消息
print_msg() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 函数：检查依赖
check_dependencies() {
    print_msg $BLUE "🔍 检查依赖..."
    
    # 检查 kubectl
    if ! command -v kubectl &> /dev/null; then
        print_msg $RED "❌ kubectl 未安装"
        exit 1
    fi
    
    # 检查 helm
    if ! command -v helm &> /dev/null; then
        print_msg $RED "❌ helm 未安装"
        exit 1
    fi
    
    # 检查 kind
    if ! command -v kind &> /dev/null; then
        print_msg $RED "❌ kind 未安装"
        exit 1
    fi
    
    # 检查 k6
    if ! command -v k6 &> /dev/null; then
        print_msg $RED "❌ k6 未安装"
        exit 1
    fi
    
    print_msg $GREEN "✅ 所有依赖已安装"
}

# 函数：创建 Kind 集群
create_cluster() {
    print_msg $BLUE "🚀 创建 Kind 集群..."
    
    # 检查集群是否已存在
    if kind get clusters | grep -q "$CLUSTER_NAME"; then
        print_msg $YELLOW "⚠️ 集群 $CLUSTER_NAME 已存在，删除后重新创建..."
        kind delete cluster --name "$CLUSTER_NAME"
    fi
    
    # 创建集群配置
    cat > kind-config.yaml << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 3000
    hostPort: 3000
    protocol: TCP
  - containerPort: 9090
    hostPort: 9090
    protocol: TCP
- role: worker
- role: worker
EOF
    
    kind create cluster --name "$CLUSTER_NAME" --config kind-config.yaml
    kubectl cluster-info --context "kind-$CLUSTER_NAME"
    
    print_msg $GREEN "✅ Kind 集群创建完成"
}

# 函数：部署监控组件
deploy_monitoring() {
    print_msg $BLUE "📊 部署监控组件..."
    
    # 创建监控命名空间
    kubectl create namespace "$MONITORING_NS" --dry-run=client -o yaml | kubectl apply -f -
    
    # 部署 Prometheus
    print_msg $BLUE "部署 Prometheus..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace "$MONITORING_NS" \
        --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
        --set prometheus.prometheusSpec.scrapeInterval=15s \
        --set prometheus.prometheusSpec.evaluationInterval=15s \
        --set grafana.adminPassword=admin \
        --set grafana.service.type=NodePort \
        --set prometheus.service.type=NodePort \
        --wait
    
    # 应用自定义 Prometheus 配置
    kubectl create configmap prometheus-config \
        --from-file=./monitoring/prometheus.yml \
        --namespace "$MONITORING_NS" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # 应用告警规则
    kubectl create configmap alert-rules \
        --from-file=./monitoring/alert_rules.yml \
        --namespace "$MONITORING_NS" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_msg $GREEN "✅ 监控组件部署完成"
}

# 函数：部署 PSGuard Sidecar
deploy_psguard() {
    print_msg $BLUE "🛡️ 部署 PSGuard Sidecar..."
    
    # 创建命名空间
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # 部署 PSGuard
    helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
        --namespace "$NAMESPACE" \
        --set image.tag=dev \
        --set resources.limits.cpu="$CPU_LIMIT" \
        --set resources.limits.memory="$MEMORY_LIMIT" \
        --set autoscaling.enabled=true \
        --set autoscaling.maxReplicas=5 \
        --set monitoring.enabled=true \
        --wait
    
    # 等待 Pod 就绪
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=psguard -n "$NAMESPACE" --timeout=300s
    
    print_msg $GREEN "✅ PSGuard Sidecar 部署完成"
}

# 函数：运行资源基准测试
run_baseline_test() {
    print_msg $BLUE "📈 运行资源基准测试..."
    
    # 获取 Pod 名称
    POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=psguard -o jsonpath='{.items[0].metadata.name}')
    
    # 检查初始资源使用情况
    print_msg $BLUE "检查初始资源使用情况..."
    kubectl top pod "$POD_NAME" -n "$NAMESPACE" --containers
    
    # 运行健康检查
    print_msg $BLUE "运行健康检查..."
    kubectl exec -n "$NAMESPACE" "$POD_NAME" -- curl -s http://localhost:8080/health
    
    # 运行指标检查
    print_msg $BLUE "检查指标端点..."
    kubectl exec -n "$NAMESPACE" "$POD_NAME" -- curl -s http://localhost:8080/metrics | head -20
    
    print_msg $GREEN "✅ 基准测试完成"
}

# 函数：运行 k6 负载测试
run_load_test() {
    print_msg $BLUE "🚀 运行 k6 负载测试..."
    
    # 获取服务地址
    SERVICE_URL="http://$(kubectl get svc "$RELEASE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}'):8080"
    
    # 在集群内运行 k6
    kubectl run k6-test \
        --image=grafana/k6:latest \
        --rm -i --restart=Never \
        --namespace "$NAMESPACE" \
        --env="PSGUARD_SERVICE=$SERVICE_URL" \
        -- run - < ./load-tests/k6-sidecar-test.js &
    
    K6_PID=$!
    print_msg $BLUE "k6 测试启动，PID: $K6_PID"
    
    # 监控资源使用情况
    print_msg $BLUE "监控资源使用情况..."
    for i in {1..30}; do
        echo "=== 监控轮次 $i/30 ==="
        kubectl top pod -n "$NAMESPACE" --containers
        
        # 检查是否超过限制
        CPU_USAGE=$(kubectl top pod "$POD_NAME" -n "$NAMESPACE" --containers | grep psguard | awk '{print $3}' | sed 's/m//')
        MEMORY_USAGE=$(kubectl top pod "$POD_NAME" -n "$NAMESPACE" --containers | grep psguard | awk '{print $4}' | sed 's/Mi//')
        
        if [ "$CPU_USAGE" -gt 200 ]; then
            print_msg $RED "⚠️ CPU 使用率超过限制: ${CPU_USAGE}m > 200m"
        fi
        
        if [ "$MEMORY_USAGE" -gt 180 ]; then
            print_msg $RED "⚠️ 内存使用率超过限制: ${MEMORY_USAGE}Mi > 180Mi"
        fi
        
        sleep 30
    done
    
    # 等待 k6 测试完成
    wait $K6_PID
    
    print_msg $GREEN "✅ 负载测试完成"
}

# 函数：收集测试结果
collect_results() {
    print_msg $BLUE "📋 收集测试结果..."
    
    # 创建结果目录
    mkdir -p test-results
    
    # 获取资源使用情况
    kubectl top pod -n "$NAMESPACE" --containers > test-results/resource-usage.txt
    
    # 获取 Pod 描述
    kubectl describe pod -n "$NAMESPACE" -l app.kubernetes.io/name=psguard > test-results/pod-description.txt
    
    # 获取日志
    kubectl logs -n "$NAMESPACE" -l app.kubernetes.io/name=psguard > test-results/pod-logs.txt
    
    # 获取事件
    kubectl get events -n "$NAMESPACE" > test-results/events.txt
    
    # 获取指标
    POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=psguard -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -n "$NAMESPACE" "$POD_NAME" -- curl -s http://localhost:8080/metrics > test-results/metrics.txt
    
    # 生成总结报告
    cat > test-results/test-summary.md << EOF
# PSGuard Sidecar 资源开销测试报告

## 测试目标
- CPU 使用率 ≤ 200m
- 内存使用率 ≤ 180Mi  
- 承受 500 RPS 负载
- 测试时长: $TEST_DURATION

## 测试环境
- 集群: $CLUSTER_NAME
- 命名空间: $NAMESPACE
- 发布名称: $RELEASE_NAME
- 测试时间: $(date)

## 资源配置
- CPU 限制: $CPU_LIMIT
- 内存限制: $MEMORY_LIMIT
- 副本数: 1-5 (自动扩缩容)

## 监控指标
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## 测试结果
详细结果请查看:
- resource-usage.txt - 资源使用情况
- pod-description.txt - Pod 详细信息
- pod-logs.txt - Pod 日志
- events.txt - 集群事件
- metrics.txt - 应用指标

## 验证步骤
1. 检查 resource-usage.txt 中的 CPU 和内存使用情况
2. 查看 Grafana 仪表板确认指标符合预期
3. 确认没有触发资源告警
4. 验证 500 RPS 目标达成情况
EOF
    
    print_msg $GREEN "✅ 测试结果已收集到 test-results/ 目录"
}

# 函数：验证结果
verify_results() {
    print_msg $BLUE "🔍 验证测试结果..."
    
    # 检查资源使用情况
    if [ -f "test-results/resource-usage.txt" ]; then
        CPU_USAGE=$(cat test-results/resource-usage.txt | grep psguard | awk '{print $3}' | sed 's/m//')
        MEMORY_USAGE=$(cat test-results/resource-usage.txt | grep psguard | awk '{print $4}' | sed 's/Mi//')
        
        echo "最终资源使用情况:"
        echo "CPU: ${CPU_USAGE}m / ${CPU_LIMIT}"
        echo "Memory: ${MEMORY_USAGE}Mi / ${MEMORY_LIMIT}"
        
        # 验证 CPU
        if [ "$CPU_USAGE" -le 200 ]; then
            print_msg $GREEN "✅ CPU 使用率符合要求 (${CPU_USAGE}m ≤ 200m)"
        else
            print_msg $RED "❌ CPU 使用率超过限制 (${CPU_USAGE}m > 200m)"
        fi
        
        # 验证内存
        if [ "$MEMORY_USAGE" -le 180 ]; then
            print_msg $GREEN "✅ 内存使用率符合要求 (${MEMORY_USAGE}Mi ≤ 180Mi)"
        else
            print_msg $RED "❌ 内存使用率超过限制 (${MEMORY_USAGE}Mi > 180Mi)"
        fi
    fi
    
    # 检查 Pod 状态
    if kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=psguard -o jsonpath='{.items[0].status.phase}' | grep -q "Running"; then
        print_msg $GREEN "✅ Pod 运行状态正常"
    else
        print_msg $RED "❌ Pod 运行状态异常"
    fi
    
    print_msg $GREEN "✅ 结果验证完成"
}

# 函数：清理资源
cleanup() {
    print_msg $BLUE "🧹 清理测试资源..."
    
    # 删除 Helm 发布
    helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" || true
    
    # 删除命名空间
    kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
    kubectl delete namespace "$MONITORING_NS" --ignore-not-found=true
    
    # 删除集群（可选）
    read -p "是否删除 Kind 集群? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kind delete cluster --name "$CLUSTER_NAME"
        print_msg $GREEN "✅ 集群已删除"
    fi
    
    # 清理临时文件
    rm -f kind-config.yaml
    
    print_msg $GREEN "✅ 清理完成"
}

# 主函数
main() {
    print_msg $BLUE "🎯 开始 PSGuard Sidecar 资源开销测试"
    print_msg $BLUE "目标: CPU ≤ $CPU_LIMIT, 内存 ≤ $MEMORY_LIMIT, 承受 $TARGET_RPS RPS"
    
    # 检查参数
    case "${1:-}" in
        "cleanup")
            cleanup
            exit 0
            ;;
        "verify")
            verify_results
            exit 0
            ;;
        "collect")
            collect_results
            exit 0
            ;;
    esac
    
    # 执行测试流程
    check_dependencies
    create_cluster
    deploy_monitoring
    deploy_psguard
    run_baseline_test
    run_load_test
    collect_results
    verify_results
    
    print_msg $GREEN "🎉 测试完成！"
    print_msg $BLUE "查看详细结果: ./test-results/test-summary.md"
    print_msg $BLUE "Grafana 仪表板: http://localhost:3000 (admin/admin)"
    print_msg $BLUE "Prometheus: http://localhost:9090"
    
    # 询问是否保持集群运行
    read -p "保持集群运行以便进一步分析? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_msg $BLUE "集群将继续运行，使用 '$0 cleanup' 清理资源"
    else
        cleanup
    fi
}

# 捕获退出信号
trap cleanup EXIT

# 运行主函数
main "$@"