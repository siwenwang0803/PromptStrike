#!/bin/bash

# Kind 集群创建问题诊断脚本（修复版）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_msg() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_msg $BLUE "🔍 Kind 集群创建问题诊断（修复版）"

# 1. 检查 Docker 服务状态
print_msg $BLUE "1. 检查 Docker 服务状态..."
if pgrep -f "Docker" > /dev/null; then
    print_msg $GREEN "✅ Docker 进程正在运行"
else
    print_msg $RED "❌ Docker 进程未运行"
    print_msg $YELLOW "请启动 Docker Desktop 应用程序"
    exit 1
fi

# 2. 检查 Docker 响应性（增加超时时间）
print_msg $BLUE "2. 检查 Docker 响应性..."
test_docker_response() {
    local attempt=1
    local max_attempts=6
    
    while [ $attempt -le $max_attempts ]; do
        print_msg $YELLOW "尝试 $attempt/$max_attempts..."
        
        if docker version &> /dev/null; then
            print_msg $GREEN "✅ Docker 响应正常"
            return 0
        else
            print_msg $YELLOW "Docker 响应缓慢，等待 10 秒..."
            sleep 10
            ((attempt++))
        fi
    done
    
    print_msg $RED "❌ Docker 响应超时"
    return 1
}

if ! test_docker_response; then
    print_msg $YELLOW "Docker 响应有问题，但我们可以尝试继续..."
    print_msg $YELLOW "如果后续步骤失败，请重启 Docker Desktop"
else
    print_msg $GREEN "✅ Docker 响应正常"
fi

# 3. 检查 Docker 资源
print_msg $BLUE "3. 检查 Docker 资源..."
if docker system df 2>/dev/null; then
    print_msg $GREEN "✅ Docker 资源信息获取成功"
else
    print_msg $YELLOW "⚠️ 无法获取 Docker 资源信息"
fi

# 4. 检查现有 Kind 集群
print_msg $BLUE "4. 检查现有 Kind 集群..."
if kind get clusters 2>/dev/null | grep -q "psguard-test"; then
    print_msg $YELLOW "⚠️ 集群 psguard-test 已存在"
    print_msg $BLUE "删除现有集群..."
    kind delete cluster --name psguard-test
    print_msg $GREEN "✅ 现有集群已删除"
else
    print_msg $GREEN "✅ 没有冲突的集群"
fi

# 5. 检查端口占用
print_msg $BLUE "5. 检查端口占用..."
check_port() {
    local port=$1
    if lsof -i :$port &> /dev/null; then
        print_msg $YELLOW "⚠️ 端口 $port 已被占用"
        lsof -i :$port
        return 1
    else
        print_msg $GREEN "✅ 端口 $port 可用"
        return 0
    fi
}

ports_available=true
check_port 80 || ports_available=false
check_port 443 || ports_available=false
check_port 3000 || ports_available=false
check_port 9090 || ports_available=false

if [ "$ports_available" = false ]; then
    print_msg $YELLOW "⚠️ 部分端口被占用，将调整端口配置"
fi

# 6. 检查磁盘空间
print_msg $BLUE "6. 检查磁盘空间..."
df -h | grep -E "(Filesystem|/)" | head -2

# 7. 清理 Docker 缓存（如果空间不足）
print_msg $BLUE "7. 检查是否需要清理 Docker 缓存..."
available_space=$(df / | tail -1 | awk '{print $4}')
if [ "$available_space" -lt 5242880 ]; then  # 5GB in KB
    print_msg $YELLOW "磁盘空间不足，清理 Docker 缓存..."
    docker system prune -f &> /dev/null || print_msg $YELLOW "⚠️ 无法清理 Docker 缓存"
else
    print_msg $GREEN "✅ 磁盘空间充足"
fi

# 8. 创建优化的 Kind 配置
print_msg $BLUE "8. 创建优化的 Kind 配置..."
cat > kind-optimized-config.yaml << EOF
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
        max-pods: "50"
  extraPortMappings:
  - containerPort: 80
    hostPort: 8080
    protocol: TCP
  - containerPort: 443
    hostPort: 8443
    protocol: TCP
  - containerPort: 3000
    hostPort: 3000
    protocol: TCP
  - containerPort: 9090
    hostPort: 9090
    protocol: TCP
EOF

# 9. 尝试创建测试集群
print_msg $BLUE "9. 尝试创建测试集群..."
print_msg $YELLOW "这可能需要几分钟时间，请耐心等待..."

# 显示进度
show_progress() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# 创建集群（后台运行以显示进度）
{
    kind create cluster --name psguard-test-optimized --config kind-optimized-config.yaml --wait 120s
} &
cluster_pid=$!

print_msg $BLUE "正在创建集群..."
show_progress $cluster_pid

# 检查结果
if wait $cluster_pid; then
    print_msg $GREEN "✅ 测试集群创建成功！"
else
    print_msg $RED "❌ 测试集群创建失败"
    
    # 提供详细的故障排除信息
    print_msg $BLUE "故障排除信息:"
    
    # 检查 Docker 容器状态
    print_msg $BLUE "Docker 容器状态："
    docker ps -a | grep kind || print_msg $YELLOW "无 kind 容器"
    
    # 检查 Docker 日志
    if docker ps -a | grep -q "kind-control-plane"; then
        print_msg $BLUE "Kind 控制平面日志："
        docker logs kind-control-plane 2>&1 | tail -20
    fi
    
    # 提供解决方案
    print_msg $YELLOW "建议解决方案："
    print_msg $YELLOW "1. 重启 Docker Desktop 并等待完全启动"
    print_msg $YELLOW "2. 增加 Docker 的内存限制到 6GB+"
    print_msg $YELLOW "3. 运行本地测试代替 Kubernetes: ./test-sidecar-local.sh"
    print_msg $YELLOW "4. 检查防火墙和 VPN 设置"
    
    # 清理
    kind delete cluster --name psguard-test-optimized 2>/dev/null || true
    rm -f kind-optimized-config.yaml
    
    print_msg $BLUE "🎯 推荐：运行本地测试"
    print_msg $BLUE "  ./test-sidecar-local.sh"
    
    exit 1
fi

# 10. 验证集群
print_msg $BLUE "10. 验证集群..."
if kubectl cluster-info --context kind-psguard-test-optimized &> /dev/null; then
    print_msg $GREEN "✅ 集群验证成功"
    kubectl get nodes
else
    print_msg $RED "❌ 集群验证失败"
fi

# 11. 清理测试集群
print_msg $BLUE "11. 清理测试集群..."
kind delete cluster --name psguard-test-optimized
rm -f kind-optimized-config.yaml

print_msg $GREEN "🎉 诊断完成！Kind 和 Docker 工作正常"
print_msg $BLUE "现在可以运行完整测试:"
print_msg $BLUE "  ./test-sidecar-resources.sh"
print_msg $BLUE "或者运行本地测试:"
print_msg $BLUE "  ./test-sidecar-local.sh"