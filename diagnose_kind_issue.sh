#!/bin/bash

# Kind 集群创建问题诊断脚本

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

print_msg $BLUE "🔍 Kind 集群创建问题诊断"

# 1. 检查 Docker 服务状态
print_msg $BLUE "1. 检查 Docker 服务状态..."
if pgrep -f "Docker" > /dev/null; then
    print_msg $GREEN "✅ Docker 进程正在运行"
else
    print_msg $RED "❌ Docker 进程未运行"
    print_msg $YELLOW "请启动 Docker Desktop 应用程序"
    exit 1
fi

# 2. 检查 Docker 响应性
print_msg $BLUE "2. 检查 Docker 响应性..."
if timeout 10s docker version &> /dev/null; then
    print_msg $GREEN "✅ Docker 响应正常"
else
    print_msg $RED "❌ Docker 响应超时"
    print_msg $YELLOW "Docker 可能正在启动中，请等待或重启 Docker Desktop"
    exit 1
fi

# 3. 检查 Docker 资源
print_msg $BLUE "3. 检查 Docker 资源..."
docker system df 2>/dev/null || {
    print_msg $YELLOW "⚠️ 无法获取 Docker 资源信息"
}

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
    else
        print_msg $GREEN "✅ 端口 $port 可用"
    fi
}

check_port 80
check_port 443
check_port 3000
check_port 9090

# 6. 检查磁盘空间
print_msg $BLUE "6. 检查磁盘空间..."
df -h | grep -E "(Filesystem|/)"

# 7. 清理 Docker 缓存
print_msg $BLUE "7. 清理 Docker 缓存..."
docker system prune -f &> /dev/null || print_msg $YELLOW "⚠️ 无法清理 Docker 缓存"

# 8. 创建简化的 Kind 配置
print_msg $BLUE "8. 创建简化的 Kind 配置..."
cat > kind-simple-config.yaml << EOF
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
    hostPort: 8080
    protocol: TCP
  - containerPort: 443
    hostPort: 8443
    protocol: TCP
EOF

# 9. 尝试创建简化集群
print_msg $BLUE "9. 尝试创建简化集群..."
print_msg $YELLOW "这可能需要几分钟时间..."

# 设置超时
timeout 300s kind create cluster --name psguard-test-simple --config kind-simple-config.yaml --wait 60s || {
    print_msg $RED "❌ 简化集群创建失败"
    print_msg $BLUE "检查错误日志..."
    
    # 检查 Docker 日志
    if docker logs kind-control-plane 2>/dev/null | tail -20; then
        print_msg $BLUE "以上是 Docker 容器日志"
    fi
    
    # 提供手动解决方案
    print_msg $YELLOW "手动解决方案:"
    print_msg $YELLOW "1. 重启 Docker Desktop"
    print_msg $YELLOW "2. 增加 Docker 内存限制 (推荐 4GB+)"
    print_msg $YELLOW "3. 运行: docker system prune -a"
    print_msg $YELLOW "4. 检查防火墙设置"
    
    exit 1
}

print_msg $GREEN "✅ 简化集群创建成功！"

# 10. 验证集群
print_msg $BLUE "10. 验证集群..."
kubectl cluster-info --context kind-psguard-test-simple

# 11. 清理
print_msg $BLUE "11. 清理测试集群..."
kind delete cluster --name psguard-test-simple
rm -f kind-simple-config.yaml

print_msg $GREEN "🎉 诊断完成！Docker 和 Kind 工作正常"
print_msg $BLUE "现在可以运行完整测试: ./test-sidecar-resources.sh"