# PSGuard Sidecar 资源开销测试指南

## 🎯 测试目标

确保 PSGuard Sidecar 容器满足以下资源要求：
- **CPU 使用率**: ≤ 200m
- **内存使用率**: ≤ 180Mi
- **性能目标**: 承受 500 RPS 负载
- **监控精度**: Prometheus 抓取间隔 ≤ 15s

## 📋 测试环境

### 依赖要求
- `kubectl` - Kubernetes 命令行工具
- `helm` - Kubernetes 包管理器
- `kind` - Kubernetes 本地开发环境
- `k6` - 现代负载测试工具

### 集群配置
- **节点数量**: 1 控制节点 + 2 工作节点
- **资源分配**: 每节点 2 CPU, 4GB 内存
- **网络**: 本地端口转发支持监控访问

## 🚀 快速开始

### 1. 运行完整测试
```bash
./test-sidecar-resources.sh
```

### 2. 仅清理环境
```bash
./test-sidecar-resources.sh cleanup
```

### 3. 验证测试结果
```bash
./test-sidecar-resources.sh verify
```

### 4. 收集测试数据
```bash
./test-sidecar-resources.sh collect
```

## 📊 监控与告警

### Prometheus 指标
- `container_cpu_usage_seconds_total{container="psguard"}` - CPU 使用率
- `container_memory_working_set_bytes{container="psguard"}` - 内存使用量
- `container_network_receive_bytes_total{container="psguard"}` - 网络接收流量
- `container_network_transmit_bytes_total{container="psguard"}` - 网络发送流量
- `container_fs_io_time_seconds_total{container="psguard"}` - 磁盘 I/O 时间

### 告警规则
- **CPU 告警**: 使用率 > 200m 持续 1 分钟
- **内存告警**: 使用量 > 180Mi 持续 1 分钟
- **网络告警**: 流量 > 10MB/s 持续 2 分钟
- **磁盘告警**: I/O 使用率 > 80% 持续 2 分钟

### 访问地址
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **PSGuard Service**: http://localhost:8080 (集群内)

## 🔧 测试配置

### Helm Values 优化
```yaml
resources:
  limits:
    cpu: 200m
    memory: 180Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### K6 负载测试场景
1. **渐增负载**: 10 → 250 VUs (目标 500 RPS)
2. **恒定负载**: 250 VUs 持续 5 分钟
3. **峰值测试**: 500 VUs 持续 30 秒

### 性能阈值
- **响应时间**: 95% 请求 < 500ms
- **错误率**: < 1%
- **成功率**: > 99%

## 📈 结果分析

### 1. 资源使用情况
检查 `test-results/resource-usage.txt`:
```
NAME                CPU(cores)   MEMORY(bytes)
psguard-xxx         150m         120Mi
```

### 2. 性能指标
检查 `test-results/metrics.txt`:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",status="200"} 15000

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 12000
http_request_duration_seconds_bucket{le="0.5"} 14800
```

### 3. 告警状态
检查 Grafana 告警面板:
- 🟢 **正常**: 所有指标在阈值内
- 🟡 **警告**: 单个指标超过阈值
- 🔴 **严重**: 多个指标超过阈值或服务不可用

## 🐛 故障排除

### 常见问题

#### 1. CPU/内存超标
**症状**: 资源使用率超过 200m/180Mi
**解决方案**:
```bash
# 检查 Pod 日志
kubectl logs -n psguard-test -l app.kubernetes.io/name=psguard

# 检查资源限制
kubectl describe pod -n psguard-test -l app.kubernetes.io/name=psguard

# 优化配置
helm upgrade psguard ./charts/psguard \
  --set resources.limits.cpu=150m \
  --set resources.limits.memory=128Mi
```

#### 2. k6 测试失败
**症状**: k6 无法连接到服务
**解决方案**:
```bash
# 检查服务状态
kubectl get svc -n psguard-test

# 检查端口转发
kubectl port-forward svc/psguard 8080:8080 -n psguard-test

# 验证服务可访问性
curl http://localhost:8080/health
```

#### 3. Prometheus 无数据
**症状**: Grafana 仪表板显示 "No data"
**解决方案**:
```bash
# 检查 ServiceMonitor
kubectl get servicemonitor -n monitoring

# 检查 Prometheus 配置
kubectl get configmap prometheus-config -n monitoring -o yaml

# 验证目标发现
# 访问 http://localhost:9090/targets
```

#### 4. Grafana 告警不触发
**症状**: 超过阈值但没有告警
**解决方案**:
```bash
# 检查告警规则
kubectl get configmap alert-rules -n monitoring -o yaml

# 验证规则语法
# 访问 http://localhost:9090/rules

# 检查 Alertmanager 状态
kubectl get pods -n monitoring -l app.kubernetes.io/name=alertmanager
```

## 📚 补充资源

### 优化建议
1. **CPU 优化**:
   - 使用异步 I/O
   - 优化正则表达式
   - 实现请求缓存

2. **内存优化**:
   - 限制缓存大小
   - 使用内存池
   - 定期垃圾回收

3. **网络优化**:
   - 启用 HTTP/2
   - 实现连接池
   - 压缩响应数据

### 扩展测试
1. **长时间稳定性测试**:
   ```bash
   k6 run --duration 2h load-tests/k6-sidecar-test.js
   ```

2. **多模型并发测试**:
   ```javascript
   const models = ['gpt-4', 'gpt-3.5-turbo', 'claude-3-sonnet'];
   // 针对不同模型的负载测试
   ```

3. **内存泄漏检测**:
   ```bash
   # 监控内存使用趋势
   kubectl top pod -n psguard-test --watch
   ```

### 相关文档
- [Kubernetes 资源管理](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Prometheus 监控最佳实践](https://prometheus.io/docs/practices/naming/)
- [k6 负载测试指南](https://k6.io/docs/testing-guides/)
- [Grafana 告警配置](https://grafana.com/docs/grafana/latest/alerting/)

## 🎉 测试完成标准

测试通过需要满足以下所有条件:
- ✅ CPU 使用率 ≤ 200m (平均值)
- ✅ 内存使用率 ≤ 180Mi (平均值)
- ✅ 成功处理 500 RPS 负载
- ✅ 95% 响应时间 < 500ms
- ✅ 错误率 < 1%
- ✅ 无资源相关告警触发
- ✅ 服务连续运行 15 分钟无崩溃

满足以上条件即可认为 PSGuard Sidecar 达到生产部署要求。