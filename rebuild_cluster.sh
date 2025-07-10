#!/bin/bash

# 重建 Kind 集群并部署 PSGuard

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

print_msg $BLUE "🔧 重建 Kind 集群"

# 1. 完全清理环境
print_msg $BLUE "1. 完全清理环境..."
kind delete cluster --name psguard-test 2>/dev/null || true
kind delete cluster --name psguard-test-simple 2>/dev/null || true
kind delete cluster --name psguard-test-optimized 2>/dev/null || true

# 清理 Docker 容器
docker ps -a | grep kind | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

# 2. 验证 Docker 状态
print_msg $BLUE "2. 验证 Docker 状态..."
if ! docker info &> /dev/null; then
    print_msg $RED "❌ Docker 无法响应"
    print_msg $YELLOW "请确保 Docker Desktop 正在运行"
    exit 1
fi

print_msg $GREEN "✅ Docker 状态正常"

# 3. 创建简化的 Kind 配置
print_msg $BLUE "3. 创建简化的 Kind 配置..."
cat > kind-minimal-config.yaml << 'EOF'
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
        max-pods: "30"
        kube-reserved: "cpu=200m,memory=300Mi"
  extraPortMappings:
  - containerPort: 80
    hostPort: 8080
    protocol: TCP
  - containerPort: 443
    hostPort: 8443
    protocol: TCP
  - containerPort: 30000
    hostPort: 3000
    protocol: TCP
  - containerPort: 30090
    hostPort: 9090
    protocol: TCP
EOF

# 4. 创建集群（增加详细输出）
print_msg $BLUE "4. 创建 Kind 集群..."
print_msg $YELLOW "这可能需要 3-5 分钟，请耐心等待..."

if kind create cluster --name psguard-test --config kind-minimal-config.yaml --wait 300s --verbosity 1; then
    print_msg $GREEN "✅ Kind 集群创建成功"
else
    print_msg $RED "❌ Kind 集群创建失败"
    print_msg $BLUE "尝试创建最小化集群..."
    
    # 尝试最基本的集群配置
    if kind create cluster --name psguard-test --wait 300s; then
        print_msg $GREEN "✅ 最小化集群创建成功"
    else
        print_msg $RED "❌ 集群创建完全失败"
        print_msg $YELLOW "建议使用本地 Docker 测试："
        print_msg $YELLOW "  ./test-sidecar-local.sh"
        exit 1
    fi
fi

# 5. 验证集群连接
print_msg $BLUE "5. 验证集群连接..."
if kubectl cluster-info &> /dev/null; then
    print_msg $GREEN "✅ kubectl 可以连接到集群"
    kubectl get nodes
else
    print_msg $RED "❌ kubectl 无法连接到集群"
    
    # 尝试手动设置上下文
    print_msg $BLUE "尝试设置 kubectl 上下文..."
    kubectl config use-context kind-psguard-test
    
    if kubectl cluster-info &> /dev/null; then
        print_msg $GREEN "✅ 上下文设置成功"
    else
        print_msg $RED "❌ 仍然无法连接"
        exit 1
    fi
fi

# 6. 等待集群完全就绪
print_msg $BLUE "6. 等待集群完全就绪..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# 7. 创建测试镜像
print_msg $BLUE "7. 创建测试镜像..."
cat > Dockerfile.psguard << 'EOF'
FROM nginx:alpine

# 创建健康检查页面
RUN echo '{"status":"healthy","service":"psguard"}' > /usr/share/nginx/html/health.json

# 创建指标页面
RUN echo 'http_requests_total{method="GET",status="200"} 1
http_request_duration_seconds_bucket{le="0.1"} 1
cpu_usage_millicores 150
memory_usage_bytes 134217728' > /usr/share/nginx/html/metrics.txt

# 配置 Nginx
RUN cat > /etc/nginx/conf.d/default.conf << 'EOL'
server {
    listen 8080;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
    
    location /health {
        alias /usr/share/nginx/html/health.json;
        add_header Content-Type application/json;
    }
    
    location /metrics {
        alias /usr/share/nginx/html/metrics.txt;
        add_header Content-Type text/plain;
    }
}
EOL

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
EOF

# 构建镜像
docker build -t psguard-sidecar:test -f Dockerfile.psguard .

# 加载到 Kind 集群
kind load docker-image psguard-sidecar:test --name psguard-test

# 8. 创建简单的部署配置
print_msg $BLUE "8. 创建简单的部署配置..."
cat > psguard-deployment.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: psguard-test
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: psguard
  namespace: psguard-test
  labels:
    app: psguard
spec:
  replicas: 1
  selector:
    matchLabels:
      app: psguard
  template:
    metadata:
      labels:
        app: psguard
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: psguard
        image: psguard-sidecar:test
        imagePullPolicy: Never
        ports:
        - containerPort: 8080
          name: http
        resources:
          limits:
            cpu: 200m
            memory: 180Mi
          requests:
            cpu: 100m
            memory: 128Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: psguard
  namespace: psguard-test
  labels:
    app: psguard
spec:
  selector:
    app: psguard
  ports:
  - port: 8080
    targetPort: 8080
    name: http
  type: ClusterIP
EOF

# 9. 部署 PSGuard
print_msg $BLUE "9. 部署 PSGuard..."
kubectl apply -f psguard-deployment.yaml

# 10. 等待部署完成
print_msg $BLUE "10. 等待部署完成..."
kubectl wait --for=condition=Available deployment/psguard -n psguard-test --timeout=300s
kubectl wait --for=condition=Ready pod -l app=psguard -n psguard-test --timeout=300s

# 11. 验证部署
print_msg $BLUE "11. 验证部署..."
kubectl get pods -n psguard-test -o wide
kubectl get svc -n psguard-test

# 12. 测试服务
print_msg $BLUE "12. 测试服务..."
POD_NAME=$(kubectl get pods -n psguard-test -l app=psguard -o jsonpath='{.items[0].metadata.name}')

print_msg $BLUE "测试健康检查..."
if kubectl exec -n psguard-test $POD_NAME -- curl -s http://localhost:8080/health; then
    print_msg $GREEN "✅ 健康检查通过"
else
    print_msg $RED "❌ 健康检查失败"
fi

print_msg $BLUE "测试指标端点..."
if kubectl exec -n psguard-test $POD_NAME -- curl -s http://localhost:8080/metrics | head -5; then
    print_msg $GREEN "✅ 指标端点正常"
else
    print_msg $RED "❌ 指标端点异常"
fi

# 13. 检查资源使用情况
print_msg $BLUE "13. 检查资源使用情况..."
kubectl top pod -n psguard-test --containers 2>/dev/null || print_msg $YELLOW "⚠️ 无法获取资源使用情况（metrics-server 未安装）"

# 14. 设置端口转发用于测试
print_msg $BLUE "14. 设置端口转发..."
kubectl port-forward svc/psguard 8080:8080 -n psguard-test &
PORT_FORWARD_PID=$!

# 等待端口转发启动
sleep 5

# 15. 本地连接测试
print_msg $BLUE "15. 本地连接测试..."
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    print_msg $GREEN "✅ 服务可通过端口转发访问"
else
    print_msg $RED "❌ 服务无法通过端口转发访问"
fi

# 16. 运行简单的负载测试
print_msg $BLUE "16. 运行简单的负载测试..."
if command -v k6 &> /dev/null; then
    cat > k6-simple-test.js << 'EOF'
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

export default function() {
  const response = http.get('http://localhost:8080/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
  });
}
EOF

    k6 run k6-simple-test.js
    rm k6-simple-test.js
else
    print_msg $YELLOW "⚠️ k6 未安装，跳过负载测试"
fi

# 17. 清理
print_msg $BLUE "17. 清理..."
kill $PORT_FORWARD_PID 2>/dev/null || true
rm -f kind-minimal-config.yaml Dockerfile.psguard psguard-deployment.yaml

print_msg $GREEN "🎉 集群重建和部署完成！"
print_msg $BLUE "PSGuard 现在运行在以下环境："
print_msg $BLUE "  集群: kind-psguard-test"
print_msg $BLUE "  命名空间: psguard-test"
print_msg $BLUE "  资源限制: CPU 200m, 内存 180Mi"

print_msg $BLUE "下一步可以："
print_msg $BLUE "1. 运行完整的资源测试"
print_msg $BLUE "2. 监控资源使用情况"
print_msg $BLUE "3. 进行压力测试"

print_msg $BLUE "集群将保持运行。使用以下命令清理："
print_msg $BLUE "  kind delete cluster --name psguard-test"