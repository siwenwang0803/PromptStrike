# PSGuard Sidecar 500 RPS 资源测试报告

## 测试概述
- **测试时间**: Wed Jul  9 16:24:22 PDT 2025
- **目标**: CPU ≤ 200m, 内存 ≤ 180Mi, 承受 500 RPS
- **测试时长**: 6 分钟
- **集群**: kind-psguard-test

## 性能测试结果
### 负载测试
- **平均 RPS**: 169.79299983351896
- **总请求数**: 61315
- **错误率**: 0
- **RPS 达成**: FAIL
- **错误率控制**: PASS

### Pod 稳定性
- **Pod 状态**: Running
- **重启次数**: 0
- **稳定性**: PASS

## 资源配置
- **CPU 限制**: 200m
- **内存限制**: 180Mi
- **资源监控**: NO

## 测试数据文件
- k6 负载测试摘要: summary.json
- 资源监控日志: resource_usage_500rps.csv

## 结论
⚠️ PSGuard Sidecar 基本满足要求：Pod 运行稳定，但性能指标需要进一步优化。

## 建议
- 优化应用代码以提高性能
- 考虑调整资源配置
- 进行更详细的性能分析

---
测试环境: Kind Kubernetes cluster
测试工具: k6 load testing tool
