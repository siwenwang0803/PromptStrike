/**
 * k6 压力测试脚本 - PromptStrike Sidecar
 * 目标：测试 500 RPS 下的资源使用情况
 * 期望：CPU ≤ 200m，内存 ≤ 180Mi
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// 自定义指标
const requestDuration = new Trend('request_duration', true);
const successRate = new Rate('success_rate');
const errorCounter = new Counter('error_count');

// 测试配置
export const options = {
  scenarios: {
    // 场景1：逐步增加负载到 500 RPS
    ramp_up: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '30s', target: 50 },   // 0-50 VUs over 30s
        { duration: '1m', target: 100 },   // 50-100 VUs over 1m
        { duration: '2m', target: 200 },   // 100-200 VUs over 2m
        { duration: '3m', target: 250 },   // 200-250 VUs over 3m (target 500 RPS)
        { duration: '2m', target: 250 },   // Hold at 250 VUs
        { duration: '30s', target: 0 },    // Ramp down
      ],
    },
    
    // 场景2：恒定高负载测试
    constant_load: {
      executor: 'constant-vus',
      vus: 250,
      duration: '5m',
      startTime: '8m',
    },
    
    // 场景3：峰值负载测试
    spike_test: {
      executor: 'ramping-vus',
      startTime: '13m',
      stages: [
        { duration: '10s', target: 500 },   // Spike to 500 VUs (1000 RPS)
        { duration: '30s', target: 500 },   // Hold spike
        { duration: '10s', target: 250 },   // Return to normal
      ],
    },
  },
  
  thresholds: {
    http_req_duration: ['p(95)<500'],       // 95% of requests must be below 500ms
    http_req_failed: ['rate<0.01'],         // Error rate must be below 1%
    success_rate: ['rate>0.99'],           // Success rate must be above 99%
    request_duration: ['p(99)<1000'],      // 99% of requests below 1s
  },
};

// 测试数据
const testPayloads = [
  {
    model: 'gpt-4',
    prompt: 'Hello, world!',
    max_tokens: 100,
  },
  {
    model: 'gpt-3.5-turbo',
    prompt: 'Explain quantum computing in simple terms.',
    max_tokens: 200,
  },
  {
    model: 'claude-3-sonnet',
    prompt: 'Write a short story about AI.',
    max_tokens: 300,
  },
  {
    model: 'gpt-4',
    prompt: 'Analyze the security implications of this code: function authenticate(user) { return user.isValid; }',
    max_tokens: 150,
  },
];

// 获取服务地址
const PSGUARD_SERVICE = __ENV.PSGUARD_SERVICE || 'http://psguard:8080';

export default function() {
  const startTime = Date.now();
  
  // 随机选择测试负载
  const payload = testPayloads[Math.floor(Math.random() * testPayloads.length)];
  
  // 构造请求
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Test-Scenario': 'load-test',
    },
    timeout: '30s',
  };
  
  // 发送扫描请求
  const scanResponse = http.post(`${PSGUARD_SERVICE}/scan`, JSON.stringify(payload), params);
  
  // 记录请求时长
  const duration = Date.now() - startTime;
  requestDuration.add(duration);
  
  // 检查响应
  const scanSuccess = check(scanResponse, {
    'scan request successful': (r) => r.status === 200,
    'scan response has data': (r) => r.json() && r.json().scan_id,
    'scan response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  if (!scanSuccess) {
    errorCounter.add(1);
    console.log(`Scan failed: ${scanResponse.status} - ${scanResponse.body}`);
  }
  
  successRate.add(scanSuccess);
  
  // 检查健康端点
  const healthResponse = http.get(`${PSGUARD_SERVICE}/health`);
  const healthSuccess = check(healthResponse, {
    'health endpoint accessible': (r) => r.status === 200,
    'health response time < 100ms': (r) => r.timings.duration < 100,
  });
  
  if (!healthSuccess) {
    console.log(`Health check failed: ${healthResponse.status}`);
  }
  
  // 检查指标端点
  const metricsResponse = http.get(`${PSGUARD_SERVICE}/metrics`);
  const metricsSuccess = check(metricsResponse, {
    'metrics endpoint accessible': (r) => r.status === 200,
    'metrics contain CPU data': (r) => r.body.includes('cpu_usage'),
    'metrics contain memory data': (r) => r.body.includes('memory_usage'),
  });
  
  if (!metricsSuccess) {
    console.log(`Metrics check failed: ${metricsResponse.status}`);
  }
  
  // 模拟真实用户行为：请求间隔
  sleep(Math.random() * 2); // 0-2秒随机间隔
}

// 测试生命周期钩子
export function setup() {
  console.log('🚀 Starting PSGuard Sidecar Load Test');
  console.log(`Target: ${PSGUARD_SERVICE}`);
  console.log('Objectives:');
  console.log('  - CPU usage ≤ 200m');
  console.log('  - Memory usage ≤ 180Mi');
  console.log('  - Handle 500 RPS');
  console.log('  - 95% requests < 500ms');
  console.log('  - Error rate < 1%');
  
  // 预热请求
  const warmupResponse = http.get(`${PSGUARD_SERVICE}/health`);
  if (warmupResponse.status !== 200) {
    console.error('❌ Service not ready for testing');
    throw new Error('Service health check failed');
  }
  
  console.log('✅ Service ready for testing');
  return { startTime: Date.now() };
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`\n📊 Test completed in ${duration.toFixed(1)}s`);
  console.log('🔍 Check Grafana dashboard for resource usage metrics');
  console.log('📈 Expected metrics:');
  console.log('  - container_cpu_usage_seconds_total{container="psguard"}');
  console.log('  - container_memory_working_set_bytes{container="psguard"}');
  console.log('  - container_network_receive_bytes_total{container="psguard"}');
  console.log('  - container_fs_io_time_seconds_total{container="psguard"}');
}