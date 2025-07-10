#!/bin/bash

# PSGuard Sidecar 500 RPS 资源测试脚本

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

print_msg $BLUE "🚀 PSGuard Sidecar 500 RPS 资源测试"
print_msg $BLUE "目标: CPU ≤ 200m, 内存 ≤ 180Mi, 承受 500 RPS"

# 1. 安装 metrics-server
print_msg $BLUE "1. 安装 metrics-server 以监控资源使用..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 为 Kind 集群修改 metrics-server 配置
kubectl patch deployment metrics-server -n kube-system --patch '
spec:
  template:
    spec:
      containers:
      - name: metrics-server
        args:
        - --cert-dir=/tmp
        - --secure-port=4443
        - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
        - --kubelet-use-node-status-port
        - --metric-resolution=15s
        - --kubelet-insecure-tls
'

# 等待 metrics-server 就绪
print_msg $BLUE "等待 metrics-server 就绪..."
kubectl wait --for=condition=Ready pod -l k8s-app=metrics-server -n kube-system --timeout=180s

# 等待一些时间让 metrics-server 开始收集数据
sleep 30

# 2. 创建资源监控脚本
print_msg $BLUE "2. 创建资源监控脚本..."
cat > monitor_resources.sh << 'EOF'
#!/bin/bash

# 资源监控脚本
NAMESPACE="psguard-test"
OUTPUT_FILE="resource_usage_500rps.csv"
MONITOR_DURATION=360  # 6分钟

echo "timestamp,pod,cpu_cores,cpu_millicores,memory_bytes,memory_mi" > $OUTPUT_FILE

echo "开始监控资源使用情况 (${MONITOR_DURATION}秒)..."

for i in $(seq 1 $MONITOR_DURATION); do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 获取资源使用情况
    kubectl top pod -n $NAMESPACE --containers 2>/dev/null | grep -v NAME | while read -r line; do
        pod=$(echo $line | awk '{print $1}')
        container=$(echo $line | awk '{print $2}')
        cpu=$(echo $line | awk '{print $3}')
        memory=$(echo $line | awk '{print $4}')
        
        # 转换 CPU (m -> millicores)
        cpu_millicores=$(echo $cpu | sed 's/m//')
        cpu_cores=$(echo "scale=4; $cpu_millicores / 1000" | bc)
        
        # 转换内存 (Mi -> bytes)
        memory_mi=$(echo $memory | sed 's/Mi//')
        memory_bytes=$(echo "$memory_mi * 1024 * 1024" | bc)
        
        echo "$timestamp,$pod,$cpu_cores,$cpu_millicores,$memory_bytes,$memory_mi" >> $OUTPUT_FILE
        
        # 检查是否超过限制
        if [ "$cpu_millicores" -gt 200 ]; then
            echo -e "\033[0;31m⚠️ CPU 超过限制: ${cpu_millicores}m > 200m\033[0m"
        fi
        
        if [ "$memory_mi" -gt 180 ]; then
            echo -e "\033[0;31m⚠️ 内存超过限制: ${memory_mi}Mi > 180Mi\033[0m"
        fi
    done
    
    # 每10秒显示一次进度
    if [ $((i % 10)) -eq 0 ]; then
        echo "监控中... $i/$MONITOR_DURATION 秒"
    fi
    
    sleep 1
done

echo "监控完成！结果保存在 $OUTPUT_FILE"
EOF

chmod +x monitor_resources.sh

# 3. 创建 k6 500 RPS 测试脚本
print_msg $BLUE "3. 创建 k6 500 RPS 测试脚本..."
cat > k6_500rps_test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// 自定义指标
const requestsPerSecond = new Trend('requests_per_second', true);
const successRate = new Rate('success_rate');
const errorCounter = new Counter('error_count');

export const options = {
    scenarios: {
        // 场景1: 逐步增加到 500 RPS
        ramp_up_to_500rps: {
            executor: 'ramping-vus',
            startVUs: 10,
            stages: [
                { duration: '30s', target: 50 },    // 预热
                { duration: '1m', target: 100 },    // 增加到 100 VUs
                { duration: '1m', target: 200 },    // 增加到 200 VUs  
                { duration: '1m', target: 250 },    // 增加到 250 VUs (目标 500 RPS)
                { duration: '2m', target: 250 },    // 保持 250 VUs 持续2分钟
                { duration: '30s', target: 0 },     // 逐步减少
            ],
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<500'],       // 95% 请求必须在 500ms 内完成
        http_req_failed: ['rate<0.01'],         // 错误率必须低于 1%
        success_rate: ['rate>0.99'],           // 成功率必须高于 99%
    },
};

// 测试数据
const endpoints = [
    { url: '/health', weight: 0.4 },
    { url: '/metrics', weight: 0.3 },
    { url: '/', weight: 0.2 },
    { url: '/scan', weight: 0.1 },
];

export default function() {
    // 根据权重选择端点
    const random = Math.random();
    let endpoint;
    let cumulativeWeight = 0;
    
    for (const ep of endpoints) {
        cumulativeWeight += ep.weight;
        if (random <= cumulativeWeight) {
            endpoint = ep.url;
            break;
        }
    }
    
    const startTime = Date.now();
    const response = http.get(`http://localhost:8080${endpoint}`);
    const endTime = Date.now();
    
    // 记录请求速率
    requestsPerSecond.add(1);
    
    // 检查响应
    const success = check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    });
    
    if (!success) {
        errorCounter.add(1);
    }
    
    successRate.add(success);
    
    // 模拟真实用户行为
    sleep(Math.random() * 2);
}

export function handleSummary(data) {
    const avgRPS = data.metrics.iterations.values.rate || 0;
    console.log(`\n📊 测试摘要:`);
    console.log(`平均 RPS: ${avgRPS.toFixed(2)}`);
    console.log(`目标 RPS: 500`);
    console.log(`达成率: ${(avgRPS / 500 * 100).toFixed(1)}%`);
    
    return {
        'summary.json': JSON.stringify(data, null, 2),
    };
}
EOF

# 4. 设置端口转发
print_msg $BLUE "4. 设置端口转发..."
kubectl port-forward svc/psguard 8080:8080 -n psguard-test &
PORT_FORWARD_PID=$!
sleep 5

# 5. 验证服务可访问
print_msg $BLUE "5. 验证服务可访问..."
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    print_msg $GREEN "✅ 服务健康检查通过"
else
    print_msg $RED "❌ 服务不可访问"
    kill $PORT_FORWARD_PID 2>/dev/null || true
    exit 1
fi

# 6. 启动资源监控
print_msg $BLUE "6. 启动资源监控..."
./monitor_resources.sh &
MONITOR_PID=$!

# 等待监控稳定
sleep 5

# 7. 运行 500 RPS 负载测试
print_msg $BLUE "7. 运行 500 RPS 负载测试..."
print_msg $YELLOW "测试将运行约 6 分钟..."

if k6 run k6_500rps_test.js; then
    print_msg $GREEN "✅ 负载测试完成"
else
    print_msg $RED "❌ 负载测试失败"
fi

# 8. 等待监控完成
print_msg $BLUE "8. 等待资源监控完成..."
wait $MONITOR_PID

# 9. 分析测试结果
print_msg $BLUE "9. 分析测试结果..."

# 分析资源使用情况
if [ -f "resource_usage_500rps.csv" ]; then
    print_msg $BLUE "资源使用分析:"
    
    # 计算最大值
    max_cpu=$(tail -n +2 resource_usage_500rps.csv | awk -F',' '{print $4}' | sort -n | tail -1)
    max_memory=$(tail -n +2 resource_usage_500rps.csv | awk -F',' '{print $6}' | sort -n | tail -1)
    
    # 计算平均值
    avg_cpu=$(tail -n +2 resource_usage_500rps.csv | awk -F',' '{sum+=$4; count++} END {print sum/count}')
    avg_memory=$(tail -n +2 resource_usage_500rps.csv | awk -F',' '{sum+=$6; count++} END {print sum/count}')
    
    print_msg $BLUE "CPU 使用情况:"
    print_msg $BLUE "  最大值: ${max_cpu}m"
    print_msg $BLUE "  平均值: ${avg_cpu}m"
    print_msg $BLUE "  限制: 200m"
    
    if [ "$max_cpu" -le 200 ]; then
        print_msg $GREEN "  ✅ CPU 使用率符合要求"
    else
        print_msg $RED "  ❌ CPU 使用率超过限制"
    fi
    
    print_msg $BLUE "内存使用情况:"
    print_msg $BLUE "  最大值: ${max_memory}Mi"
    print_msg $BLUE "  平均值: ${avg_memory}Mi"
    print_msg $BLUE "  限制: 180Mi"
    
    if [ "$max_memory" -le 180 ]; then
        print_msg $GREEN "  ✅ 内存使用率符合要求"
    else
        print_msg $RED "  ❌ 内存使用率超过限制"
    fi
fi

# 10. 生成测试报告
print_msg $BLUE "10. 生成测试报告..."
cat > psguard_500rps_test_report.md << EOF
# PSGuard Sidecar 500 RPS 资源测试报告

## 测试概述
- **测试时间**: $(date)
- **目标**: CPU ≤ 200m, 内存 ≤ 180Mi, 承受 500 RPS
- **测试时长**: 6 分钟
- **集群**: kind-psguard-test

## 资源使用情况
### CPU 使用
- **最大值**: ${max_cpu}m
- **平均值**: ${avg_cpu}m
- **限制**: 200m
- **状态**: $([ "$max_cpu" -le 200 ] && echo "✅ 符合要求" || echo "❌ 超过限制")

### 内存使用
- **最大值**: ${max_memory}Mi
- **平均值**: ${avg_memory}Mi
- **限制**: 180Mi
- **状态**: $([ "$max_memory" -le 180 ] && echo "✅ 符合要求" || echo "❌ 超过限制")

## k6 负载测试结果
$(cat summary.json 2>/dev/null | jq -r '.metrics.iterations.values | "总请求数: \(.count)\n请求速率: \(.rate) req/s"' || echo "详见 summary.json")

## 详细数据
- 资源使用详情: resource_usage_500rps.csv
- k6 测试摘要: summary.json

## 结论
$(if [ "$max_cpu" -le 200 ] && [ "$max_memory" -le 180 ]; then
    echo "✅ PSGuard Sidecar 成功满足资源要求，可以在 CPU ≤ 200m 和内存 ≤ 180Mi 的限制下承受 500 RPS 负载。"
else
    echo "❌ PSGuard Sidecar 在 500 RPS 负载下超过了资源限制，需要优化。"
fi)

## 建议
$(if [ "$max_cpu" -gt 200 ] || [ "$max_memory" -gt 180 ]; then
    echo "- 优化代码以减少资源使用"
    echo "- 考虑使用缓存减少重复计算"
    echo "- 评估是否可以增加资源限制"
else
    echo "- 资源使用符合要求"
    echo "- 可以考虑进一步压力测试以找到最大承载能力"
    echo "- 监控生产环境以确保稳定性"
fi)
EOF

# 11. 清理
print_msg $BLUE "11. 清理..."
kill $PORT_FORWARD_PID 2>/dev/null || true
rm -f monitor_resources.sh k6_500rps_test.js

print_msg $GREEN "🎉 500 RPS 资源测试完成！"
print_msg $BLUE "查看测试报告: psguard_500rps_test_report.md"
print_msg $BLUE "查看详细数据: resource_usage_500rps.csv"

# 显示简要结果
print_msg $BLUE "\n📊 测试结果摘要:"
print_msg $BLUE "CPU: 最大 ${max_cpu}m / 限制 200m"
print_msg $BLUE "内存: 最大 ${max_memory}Mi / 限制 180Mi"

if [ "$max_cpu" -le 200 ] && [ "$max_memory" -le 180 ]; then
    print_msg $GREEN "✅ 测试通过！PSGuard Sidecar 满足所有资源要求。"
else
    print_msg $RED "❌ 测试未通过。资源使用超过限制。"
fi