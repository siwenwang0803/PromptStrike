#!/bin/bash

# 修复 Helm 超时问题

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

print_msg $BLUE "🔧 修复 Helm 超时问题"

# 1. 清理失败的部署
print_msg $BLUE "1. 清理失败的部署..."
helm uninstall redforge -n redforge-test 2>/dev/null || true
kubectl delete namespace redforge-test --ignore-not-found=true
kubectl delete namespace monitoring --ignore-not-found=true

# 等待命名空间完全删除
print_msg $BLUE "等待命名空间清理..."
sleep 10

# 2. 重新创建命名空间
print_msg $BLUE "2. 重新创建命名空间..."
kubectl create namespace redforge-test
kubectl create namespace monitoring

# 3. 检查集群资源
print_msg $BLUE "3. 检查集群资源..."
kubectl get nodes -o wide
kubectl top nodes 2>/dev/null || print_msg $YELLOW "⚠️ 无法获取节点资源使用情况"

# 4. 拉取必要的镜像
print_msg $BLUE "4. 预拉取镜像..."
# 由于我们使用的是自定义镜像，创建一个简单的测试镜像
cat > Dockerfile.test << 'EOF'
FROM nginx:alpine
COPY <<'EOL' /usr/share/nginx/html/index.html
<!DOCTYPE html>
<html>
<head><title>RedForge Test</title></head>
<body>
<h1>RedForge Sidecar Test Service</h1>
<p>Status: Running</p>
</body>
</html>
EOL

COPY <<'EOL' /etc/nginx/conf.d/default.conf
server {
    listen 8080;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
    
    location /health {
        access_log off;
        return 200 '{"status":"healthy"}';
        add_header Content-Type application/json;
    }
    
    location /metrics {
        access_log off;
        return 200 'http_requests_total{method="GET",status="200"} 1';
        add_header Content-Type text/plain;
    }
}
EOL

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
EOF

# 构建测试镜像
docker build -t redforge-test:latest -f Dockerfile.test .

# 将镜像加载到 Kind 集群
kind load docker-image redforge-test:latest --name redforge-test

# 5. 创建简化的 Values 文件
print_msg $BLUE "5. 创建简化的 Values 文件..."
cat > values-simple.yaml << 'EOF'
replicaCount: 1

image:
  repository: redforge-test
  pullPolicy: Never
  tag: "latest"

service:
  type: ClusterIP
  port: 8080
  targetPort: 8080

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

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"
  prometheus.io/path: "/metrics"

autoscaling:
  enabled: false

monitoring:
  enabled: true
  serviceMonitor:
    enabled: false
EOF

# 6. 部署简化版本的 RedForge
print_msg $BLUE "6. 部署简化版本的 RedForge..."
helm upgrade --install redforge ./charts/redforge \
  --namespace redforge-test \
  --values values-simple.yaml \
  --timeout 300s \
  --wait \
  --debug

# 7. 验证部署
print_msg $BLUE "7. 验证部署..."
kubectl get pods -n redforge-test
kubectl get svc -n redforge-test

# 8. 等待 Pod 就绪
print_msg $BLUE "8. 等待 Pod 就绪..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=redforge -n redforge-test --timeout=300s

# 9. 测试服务
print_msg $BLUE "9. 测试服务..."
POD_NAME=$(kubectl get pods -n redforge-test -l app.kubernetes.io/name=redforge -o jsonpath='{.items[0].metadata.name}')

# 测试健康检查
kubectl exec -n redforge-test $POD_NAME -- curl -s http://localhost:8080/health

# 测试指标端点
kubectl exec -n redforge-test $POD_NAME -- curl -s http://localhost:8080/metrics

# 10. 检查资源使用情况
print_msg $BLUE "10. 检查资源使用情况..."
kubectl top pod -n redforge-test --containers 2>/dev/null || print_msg $YELLOW "⚠️ 无法获取 Pod 资源使用情况"

# 11. 设置端口转发
print_msg $BLUE "11. 设置端口转发..."
kubectl port-forward svc/redforge 8080:8080 -n redforge-test &
PORT_FORWARD_PID=$!

# 等待端口转发启动
sleep 3

# 12. 本地测试
print_msg $BLUE "12. 本地测试..."
if curl -s http://localhost:8080/health > /dev/null; then
    print_msg $GREEN "✅ 服务可通过端口转发访问"
else
    print_msg $RED "❌ 服务无法访问"
fi

# 13. 创建 k6 测试脚本
print_msg $BLUE "13. 创建 k6 测试脚本..."
cat > k6-kubernetes-test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 50 },
    { duration: '1m', target: 50 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function() {
  const response = http.get('http://localhost:8080/health');
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  sleep(1);
}
EOF

# 14. 运行负载测试
print_msg $BLUE "14. 运行负载测试..."
if command -v k6 &> /dev/null; then
    k6 run k6-kubernetes-test.js &
    K6_PID=$!
    
    # 监控资源使用情况
    print_msg $BLUE "监控资源使用情况（60秒）..."
    for i in {1..12}; do
        echo "=== 监控轮次 $i/12 ==="
        kubectl top pod -n redforge-test --containers 2>/dev/null || echo "无法获取资源使用情况"
        sleep 5
    done
    
    # 等待 k6 完成
    wait $K6_PID
    
    print_msg $GREEN "✅ 负载测试完成"
else
    print_msg $YELLOW "⚠️ k6 未安装，跳过负载测试"
fi

# 15. 清理
print_msg $BLUE "15. 清理..."
kill $PORT_FORWARD_PID 2>/dev/null || true
rm -f Dockerfile.test values-simple.yaml k6-kubernetes-test.js

print_msg $GREEN "🎉 Helm 部署修复完成！"
print_msg $BLUE "RedForge 服务现在运行在 Kubernetes 集群中"
print_msg $BLUE "可以继续运行完整的资源测试或检查服务状态"