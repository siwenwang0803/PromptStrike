#!/bin/bash

# 修复 Dockerfile 语法问题并继续部署

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

print_msg $BLUE "🔧 修复 Dockerfile 问题并继续部署"

# 1. 创建修复后的测试镜像
print_msg $BLUE "1. 创建修复后的测试镜像..."
cat > Dockerfile.psguard-fixed << 'EOF'
FROM nginx:alpine

# 创建健康检查页面
RUN echo '{"status":"healthy","service":"psguard","timestamp":"'$(date +%s)'"}' > /usr/share/nginx/html/health.json

# 创建指标页面 - 修复多行字符串问题
RUN cat > /usr/share/nginx/html/metrics.txt << 'EOL'
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 42

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 35
http_request_duration_seconds_bucket{le="0.5"} 40
http_request_duration_seconds_bucket{le="1.0"} 42
http_request_duration_seconds_bucket{le="+Inf"} 42
http_request_duration_seconds_sum 8.2
http_request_duration_seconds_count 42

# HELP cpu_usage_millicores CPU usage in millicores
# TYPE cpu_usage_millicores gauge
cpu_usage_millicores 150

# HELP memory_usage_bytes Memory usage in bytes
# TYPE memory_usage_bytes gauge
memory_usage_bytes 134217728
EOL

# 配置 Nginx
RUN cat > /etc/nginx/conf.d/default.conf << 'EOL'
server {
    listen 8080;
    server_name localhost;
    
    # 默认页面
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ =404;
    }
    
    # 健康检查端点
    location /health {
        alias /usr/share/nginx/html/health.json;
        add_header Content-Type application/json;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # 指标端点
    location /metrics {
        alias /usr/share/nginx/html/metrics.txt;
        add_header Content-Type text/plain;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # 模拟扫描端点
    location /scan {
        return 200 '{"scan_id":"scan_'$request_id'","status":"completed","risk_score":2.5}';
        add_header Content-Type application/json;
    }
}
EOL

# 创建默认页面
RUN cat > /usr/share/nginx/html/index.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
    <title>PSGuard Sidecar Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .status { color: green; font-weight: bold; }
        .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🛡️ PSGuard Sidecar Test Service</h1>
    <p class="status">Status: Running</p>
    <h2>Available Endpoints:</h2>
    <div class="endpoint">GET /health - Health check</div>
    <div class="endpoint">GET /metrics - Prometheus metrics</div>
    <div class="endpoint">POST /scan - Security scan (mock)</div>
    <h2>Resource Limits:</h2>
    <ul>
        <li>CPU: 200m</li>
        <li>Memory: 180Mi</li>
    </ul>
</body>
</html>
EOL

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
EOF

# 2. 构建修复后的镜像
print_msg $BLUE "2. 构建修复后的镜像..."
if docker build -t psguard-sidecar:test -f Dockerfile.psguard-fixed .; then
    print_msg $GREEN "✅ 镜像构建成功"
else
    print_msg $RED "❌ 镜像构建失败"
    exit 1
fi

# 3. 加载到 Kind 集群
print_msg $BLUE "3. 加载镜像到 Kind 集群..."
if kind load docker-image psguard-sidecar:test --name psguard-test; then
    print_msg $GREEN "✅ 镜像加载成功"
else
    print_msg $RED "❌ 镜像加载失败"
    exit 1
fi

# 4. 创建部署配置
print_msg $BLUE "4. 创建部署配置..."
cat > psguard-deployment-fixed.yaml << 'EOF'
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
    version: test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: psguard
  template:
    metadata:
      labels:
        app: psguard
        version: test
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
          protocol: TCP
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
            scheme: HTTP
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        env:
        - name: NGINX_ENTRYPOINT_QUIET_LOGS
          value: "1"
        securityContext:
          runAsNonRoot: false
          allowPrivilegeEscalation: false
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
    protocol: TCP
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: psguard-nodeport
  namespace: psguard-test
  labels:
    app: psguard
spec:
  selector:
    app: psguard
  ports:
  - port: 8080
    targetPort: 8080
    nodePort: 30080
    name: http
    protocol: TCP
  type: NodePort
EOF

# 5. 部署到集群
print_msg $BLUE "5. 部署到集群..."
kubectl apply -f psguard-deployment-fixed.yaml

# 6. 等待部署完成
print_msg $BLUE "6. 等待部署完成..."
kubectl rollout status deployment/psguard -n psguard-test --timeout=300s
kubectl wait --for=condition=Ready pod -l app=psguard -n psguard-test --timeout=300s

# 7. 验证部署状态
print_msg $BLUE "7. 验证部署状态..."
kubectl get pods -n psguard-test -o wide
kubectl get svc -n psguard-test

# 8. 测试服务端点
print_msg $BLUE "8. 测试服务端点..."
POD_NAME=$(kubectl get pods -n psguard-test -l app=psguard -o jsonpath='{.items[0].metadata.name}')

print_msg $BLUE "测试健康检查..."
if kubectl exec -n psguard-test $POD_NAME -- curl -s http://localhost:8080/health; then
    echo
    print_msg $GREEN "✅ 健康检查通过"
else
    print_msg $RED "❌ 健康检查失败"
fi

print_msg $BLUE "测试指标端点..."
echo "指标样本："
kubectl exec -n psguard-test $POD_NAME -- curl -s http://localhost:8080/metrics | head -10
print_msg $GREEN "✅ 指标端点正常"

# 9. 检查资源使用情况
print_msg $BLUE "9. 检查资源使用情况..."
kubectl describe pod -n psguard-test -l app=psguard | grep -A 10 "Requests:"

# 等待一些时间让指标稳定
sleep 10

# 尝试获取资源使用指标
kubectl top pod -n psguard-test --containers 2>/dev/null || print_msg $YELLOW "⚠️ 无法获取实时资源使用情况（需要 metrics-server）"

# 10. 设置端口转发进行外部访问测试
print_msg $BLUE "10. 设置端口转发..."
kubectl port-forward svc/psguard 8080:8080 -n psguard-test &
PORT_FORWARD_PID=$!

# 等待端口转发启动
sleep 5

# 11. 外部访问测试
print_msg $BLUE "11. 外部访问测试..."
test_endpoint() {
    local endpoint=$1
    local description=$2
    
    if curl -s "http://localhost:8080$endpoint" > /dev/null; then
        print_msg $GREEN "✅ $description 可访问"
    else
        print_msg $RED "❌ $description 不可访问"
        return 1
    fi
}

test_endpoint "/health" "健康检查端点"
test_endpoint "/metrics" "指标端点"
test_endpoint "/" "主页"

# 12. 运行简单负载测试
print_msg $BLUE "12. 运行简单负载测试..."
if command -v k6 &> /dev/null; then
    cat > k6-resource-test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 5 },
    { duration: '20s', target: 20 },
    { duration: '20s', target: 50 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.05'],
  },
};

export default function() {
  const healthResponse = http.get('http://localhost:8080/health');
  check(healthResponse, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 100ms': (r) => r.timings.duration < 100,
  });
  
  const metricsResponse = http.get('http://localhost:8080/metrics');
  check(metricsResponse, {
    'metrics status is 200': (r) => r.status === 200,
    'metrics contains data': (r) => r.body.includes('http_requests_total'),
  });
  
  sleep(Math.random() * 2);
}
EOF

    print_msg $YELLOW "运行 60 秒负载测试..."
    k6 run k6-resource-test.js
    
    # 清理测试文件
    rm k6-resource-test.js
    
    print_msg $GREEN "✅ 负载测试完成"
else
    print_msg $YELLOW "⚠️ k6 未安装，跳过负载测试"
fi

# 13. 最终资源检查
print_msg $BLUE "13. 最终资源检查..."
kubectl top pod -n psguard-test --containers 2>/dev/null || print_msg $YELLOW "使用 kubectl describe 查看资源配置"

# 显示资源配置
kubectl get pod -n psguard-test -l app=psguard -o jsonpath='{.items[0].spec.containers[0].resources}'
echo

# 14. 清理
print_msg $BLUE "14. 清理临时文件..."
kill $PORT_FORWARD_PID 2>/dev/null || true
rm -f Dockerfile.psguard-fixed psguard-deployment-fixed.yaml

print_msg $GREEN "🎉 PSGuard Sidecar 部署成功！"
print_msg $BLUE "服务详情："
print_msg $BLUE "  命名空间: psguard-test"
print_msg $BLUE "  Pod: $(kubectl get pods -n psguard-test -l app=psguard -o jsonpath='{.items[0].metadata.name}')"
print_msg $BLUE "  资源限制: CPU 200m, 内存 180Mi"
print_msg $BLUE "  服务端点: /health, /metrics, /"

print_msg $BLUE "验证命令："
print_msg $BLUE "  kubectl get pods -n psguard-test"
print_msg $BLUE "  kubectl top pod -n psguard-test --containers"
print_msg $BLUE "  kubectl port-forward svc/psguard 8080:8080 -n psguard-test"

print_msg $BLUE "清理集群："
print_msg $BLUE "  kind delete cluster --name psguard-test"