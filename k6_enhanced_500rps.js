import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend, Gauge } from 'k6/metrics';

// 自定义指标
const requestsPerSecond = new Trend('requests_per_second');
const successRate = new Rate('success_rate');
const errorCounter = new Counter('error_count');
const responseTime = new Trend('response_time_custom');
const activeConnections = new Gauge('active_connections');

export const options = {
    scenarios: {
        // 激进测试：真正达到 500 RPS
        target_500rps: {
            executor: 'constant-arrival-rate',
            rate: 500,  // 精确 500 RPS
            timeUnit: '1s',
            duration: '5m',  // 5分钟持续测试
            preAllocatedVUs: 50,
            maxVUs: 200,
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<1000'],     // 95% 请求必须在 1s 内完成
        http_req_failed: ['rate<0.02'],        // 错误率必须低于 2%
        success_rate: ['rate>0.98'],          // 成功率必须高于 98%
        response_time_custom: ['p(90)<500'],   // 90% 响应时间 < 500ms
    },
};

// 测试端点配置
const endpoints = [
    { url: '/health', weight: 0.5, expectedStatus: 200 },
    { url: '/metrics', weight: 0.3, expectedStatus: 200 },
    { url: '/', weight: 0.15, expectedStatus: 200 },
    { url: '/scan', weight: 0.05, expectedStatus: 200 },
];

let requestCount = 0;

export default function() {
    requestCount++;
    
    // 根据权重选择端点
    const random = Math.random();
    let endpoint = endpoints[0];
    let cumulativeWeight = 0;
    
    for (const ep of endpoints) {
        cumulativeWeight += ep.weight;
        if (random <= cumulativeWeight) {
            endpoint = ep;
            break;
        }
    }
    
    const startTime = Date.now();
    
    // 执行请求
    const response = http.get(`http://localhost:8080${endpoint.url}`, {
        timeout: '10s',
        headers: {
            'User-Agent': 'k6-load-test/1.0',
            'Accept': 'application/json,text/plain,*/*',
        },
    });
    
    const endTime = Date.now();
    const responseTime_ms = endTime - startTime;
    
    // 记录指标
    requestsPerSecond.add(1);
    responseTime.add(responseTime_ms);
    activeConnections.add(__VU);
    
    // 验证响应
    const success = check(response, {
        [`${endpoint.url} status is ${endpoint.expectedStatus}`]: (r) => r.status === endpoint.expectedStatus,
        [`${endpoint.url} response time < 2000ms`]: (r) => r.timings.duration < 2000,
        [`${endpoint.url} body not empty`]: (r) => r.body && r.body.length > 0,
    });
    
    if (!success) {
        errorCounter.add(1);
        console.error(`Request failed: ${endpoint.url}, Status: ${response.status}, Time: ${responseTime_ms}ms`);
    }
    
    successRate.add(success);
    
    // 每1000个请求报告一次进度
    if (requestCount % 1000 === 0) {
        console.log(`Progress: ${requestCount} requests completed, Current RPS target: 500`);
    }
    
    // 无需 sleep - 使用 constant-arrival-rate 控制速率
}

export function handleSummary(data) {
    const avgRPS = data.metrics.iterations.values.rate || 0;
    const totalRequests = data.metrics.iterations.values.count || 0;
    const errorRate = data.metrics.http_req_failed.values.rate || 0;
    const avgResponseTime = data.metrics.http_req_duration.values.avg || 0;
    
    console.log(`\n📊 详细测试结果:`);
    console.log(`总请求数: ${totalRequests}`);
    console.log(`平均 RPS: ${avgRPS.toFixed(2)}`);
    console.log(`目标 RPS: 500`);
    console.log(`达成率: ${(avgRPS / 500 * 100).toFixed(1)}%`);
    console.log(`错误率: ${(errorRate * 100).toFixed(2)}%`);
    console.log(`平均响应时间: ${avgResponseTime.toFixed(2)}ms`);
    console.log(`95% 响应时间: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms`);
    
    // 性能评级
    let grade = 'F';
    if (avgRPS >= 450 && errorRate < 0.01) grade = 'A';
    else if (avgRPS >= 400 && errorRate < 0.02) grade = 'B';
    else if (avgRPS >= 300 && errorRate < 0.05) grade = 'C';
    else if (avgRPS >= 200 && errorRate < 0.1) grade = 'D';
    
    console.log(`性能评级: ${grade}`);
    
    return {
        'enhanced_summary.json': JSON.stringify(data, null, 2),
        'performance_report.txt': `
PSGuard Sidecar 500 RPS 测试报告
=====================================
测试时间: ${new Date().toISOString()}
目标 RPS: 500
实际 RPS: ${avgRPS.toFixed(2)}
达成率: ${(avgRPS / 500 * 100).toFixed(1)}%
错误率: ${(errorRate * 100).toFixed(2)}%
性能评级: ${grade}

详细指标:
- 总请求数: ${totalRequests}
- 平均响应时间: ${avgResponseTime.toFixed(2)}ms
- 95% 响应时间: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms
- 最大响应时间: ${data.metrics.http_req_duration.values.max.toFixed(2)}ms

阈值检查:
- http_req_duration p(95)<1000ms: ${data.metrics.http_req_duration.thresholds['p(95)<1000'].ok ? 'PASS' : 'FAIL'}
- http_req_failed rate<0.02: ${data.metrics.http_req_failed.thresholds['rate<0.02'].ok ? 'PASS' : 'FAIL'}
- success_rate rate>0.98: ${data.metrics.success_rate.thresholds['rate>0.98'].ok ? 'PASS' : 'FAIL'}
`,
    };
}
