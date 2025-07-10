#!/bin/bash

# 本地 PSGuard Sidecar 资源测试（无需 Kubernetes）
# 使用 Docker 容器直接测试资源使用情况

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

# 配置
CONTAINER_NAME="psguard-test"
CPU_LIMIT="200m"
MEMORY_LIMIT="180Mi"
TARGET_RPS=500
TEST_DURATION="300" # 5分钟

print_msg $BLUE "🎯 PSGuard Sidecar 本地资源测试"
print_msg $BLUE "目标: CPU ≤ $CPU_LIMIT, 内存 ≤ $MEMORY_LIMIT, 承受 $TARGET_RPS RPS"

# 1. 检查依赖
print_msg $BLUE "1. 检查依赖..."
check_dependency() {
    local cmd=$1
    if command -v $cmd &> /dev/null; then
        print_msg $GREEN "✅ $cmd 已安装"
    else
        print_msg $RED "❌ $cmd 未安装"
        exit 1
    fi
}

check_dependency docker
check_dependency k6

# 2. 清理现有容器
print_msg $BLUE "2. 清理现有容器..."
if docker ps -a | grep -q $CONTAINER_NAME; then
    docker stop $CONTAINER_NAME &> /dev/null || true
    docker rm $CONTAINER_NAME &> /dev/null || true
    print_msg $GREEN "✅ 清理完成"
fi

# 3. 创建简化的 PSGuard 服务
print_msg $BLUE "3. 创建简化的 PSGuard 服务..."
cat > psguard-server.py << 'EOF'
#!/usr/bin/env python3
import json
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import psutil
import os

class PSGuardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'status': 'healthy', 'timestamp': time.time()}
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            
            # 获取系统指标
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            metrics = f"""# HELP cpu_usage_percent CPU usage percentage
# TYPE cpu_usage_percent gauge
cpu_usage_percent {cpu_percent}

# HELP memory_usage_bytes Memory usage in bytes
# TYPE memory_usage_bytes gauge
memory_usage_bytes {memory.used}

# HELP memory_usage_percent Memory usage percentage
# TYPE memory_usage_percent gauge
memory_usage_percent {memory.percent}

# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total {{method="GET",status="200"}} {getattr(self.server, 'request_count', 0)}

# HELP http_requests_per_second Current RPS
# TYPE http_requests_per_second gauge
http_requests_per_second {getattr(self.server, 'current_rps', 0)}
"""
            self.wfile.write(metrics.encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/scan':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                
                # 模拟扫描处理
                scan_time = random.uniform(0.1, 0.5)  # 100-500ms
                time.sleep(scan_time)
                
                # 更新请求计数
                if not hasattr(self.server, 'request_count'):
                    self.server.request_count = 0
                self.server.request_count += 1
                
                # 模拟响应
                response = {
                    'scan_id': f'scan_{int(time.time())}_{random.randint(1000, 9999)}',
                    'model': data.get('model', 'unknown'),
                    'prompt': data.get('prompt', ''),
                    'vulnerability_detected': random.choice([True, False]),
                    'risk_score': random.uniform(0.1, 10.0),
                    'scan_time_ms': int(scan_time * 1000),
                    'timestamp': time.time()
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = {'error': str(e)}
                self.wfile.write(json.dumps(error_response).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # 禁用默认日志

# RPS 监控线程
def monitor_rps(server):
    last_count = 0
    while True:
        time.sleep(1)
        current_count = getattr(server, 'request_count', 0)
        server.current_rps = current_count - last_count
        last_count = current_count

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), PSGuardHandler)
    server.request_count = 0
    server.current_rps = 0
    
    # 启动 RPS 监控
    monitor_thread = threading.Thread(target=monitor_rps, args=(server,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    print('PSGuard server starting on port 8080...')
    server.serve_forever()
EOF

# 4. 创建 Dockerfile
print_msg $BLUE "4. 创建 Dockerfile..."
cat > Dockerfile.psguard << 'EOF'
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip install psutil

# 复制服务文件
COPY psguard-server.py /app/psguard-server.py
WORKDIR /app

# 设置用户
RUN useradd -m -u 1000 psguard
USER psguard

# 暴露端口
EXPOSE 8080

# 启动服务
CMD ["python3", "psguard-server.py"]
EOF

# 5. 构建镜像
print_msg $BLUE "5. 构建 Docker 镜像..."
docker build -t psguard-test:latest -f Dockerfile.psguard .

# 6. 运行容器（带资源限制）
print_msg $BLUE "6. 运行容器（资源限制: CPU=$CPU_LIMIT, 内存=$MEMORY_LIMIT）..."
docker run -d \
    --name $CONTAINER_NAME \
    --cpus="0.2" \
    --memory="180m" \
    -p 8080:8080 \
    psguard-test:latest

# 等待服务启动
print_msg $BLUE "等待服务启动..."
sleep 5

# 7. 健康检查
print_msg $BLUE "7. 健康检查..."
if curl -s http://localhost:8080/health > /dev/null; then
    print_msg $GREEN "✅ 服务健康检查通过"
else
    print_msg $RED "❌ 服务健康检查失败"
    exit 1
fi

# 8. 创建 k6 测试脚本
print_msg $BLUE "8. 创建 k6 负载测试..."
cat > k6-local-test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },   // 逐步增加到 50 VUs
    { duration: '1m', target: 100 },   // 增加到 100 VUs
    { duration: '2m', target: 250 },   // 增加到 250 VUs (目标 500 RPS)
    { duration: '2m', target: 250 },   // 保持 250 VUs
    { duration: '30s', target: 0 },    // 逐步减少
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% 请求 < 500ms
    http_req_failed: ['rate<0.01'],    // 错误率 < 1%
  },
};

export default function() {
  const payload = {
    model: 'gpt-4',
    prompt: 'Test security scan',
    max_tokens: 100,
  };
  
  const response = http.post('http://localhost:8080/scan', JSON.stringify(payload), {
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  sleep(Math.random() * 2);
}
EOF

# 9. 运行负载测试
print_msg $BLUE "9. 运行负载测试 (目标: 500 RPS)..."
print_msg $YELLOW "测试将运行约 6 分钟..."

# 启动监控
monitor_resources() {
    local logfile="resource-monitor.log"
    echo "timestamp,cpu_percent,memory_mb,memory_percent" > $logfile
    
    while true; do
        local stats=$(docker stats $CONTAINER_NAME --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | tail -1)
        local cpu=$(echo $stats | awk '{print $1}' | sed 's/%//')
        local memory=$(echo $stats | awk '{print $2}' | sed 's/MiB.*//')
        local mem_percent=$(echo $stats | awk '{print $3}' | sed 's/%//')
        
        echo "$(date '+%Y-%m-%d %H:%M:%S'),$cpu,$memory,$mem_percent" >> $logfile
        
        # 检查是否超过限制
        if (( $(echo "$cpu > 20" | bc -l) )); then
            print_msg $RED "⚠️ CPU 使用率: ${cpu}% (> 20%)"
        fi
        
        if (( $(echo "$memory > 180" | bc -l) )); then
            print_msg $RED "⚠️ 内存使用率: ${memory}MB (> 180MB)"
        fi
        
        sleep 5
    done
}

# 后台启动资源监控
monitor_resources &
MONITOR_PID=$!

# 运行 k6 测试
k6 run k6-local-test.js

# 停止监控
kill $MONITOR_PID 2>/dev/null || true

# 10. 收集结果
print_msg $BLUE "10. 收集测试结果..."

# 获取最终资源使用情况
docker stats $CONTAINER_NAME --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" > final-stats.txt

# 获取服务指标
curl -s http://localhost:8080/metrics > final-metrics.txt

# 获取容器日志
docker logs $CONTAINER_NAME > container-logs.txt

# 11. 生成报告
print_msg $BLUE "11. 生成测试报告..."
cat > sidecar-test-results.md << EOF
# PSGuard Sidecar 本地资源测试结果

## 测试配置
- CPU 限制: $CPU_LIMIT (0.2 核心)
- 内存限制: $MEMORY_LIMIT (180MB)
- 目标 RPS: $TARGET_RPS
- 测试时长: 6 分钟

## 资源使用情况
\`\`\`
$(cat final-stats.txt)
\`\`\`

## 服务指标
\`\`\`
$(tail -20 final-metrics.txt)
\`\`\`

## 文件说明
- resource-monitor.log: 详细的资源使用监控
- final-stats.txt: 最终资源统计
- final-metrics.txt: 服务指标
- container-logs.txt: 容器日志

## 测试结论
查看 resource-monitor.log 确认：
- CPU 使用率是否保持在 20% 以下
- 内存使用率是否保持在 180MB 以下
- 是否成功处理了目标 RPS 负载

## 验证命令
\`\`\`bash
# 查看详细监控日志
tail -f resource-monitor.log

# 查看容器状态
docker stats $CONTAINER_NAME
\`\`\`
EOF

# 12. 清理
print_msg $BLUE "12. 清理测试环境..."
docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME
docker rmi psguard-test:latest

# 清理临时文件
rm -f psguard-server.py Dockerfile.psguard k6-local-test.js

print_msg $GREEN "✅ 测试完成！"
print_msg $BLUE "查看结果: sidecar-test-results.md"
print_msg $BLUE "详细监控: resource-monitor.log"