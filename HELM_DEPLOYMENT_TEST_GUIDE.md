# 🎯 PromptStrike Helm 一键部署验证指南

## 📋 概述 / Overview

This guide provides comprehensive testing for Helm one-command deployment across multiple Kubernetes environments, ensuring the script exits with code 0 upon successful verification.

**目标**: 验证 Helm 在 Kind 和 EKS 上的一键部署，脚本自动退出码为 0

## 🚀 快速开始 / Quick Start

### 基本测试 / Basic Testing
```bash
# 运行所有可用环境的测试 / Run tests on all available environments
./scripts/comprehensive_helm_test.sh

# 仅本地环境测试 (Kind + Minikube) / Local environments only
./scripts/comprehensive_helm_test.sh local

# 单独测试 Kind / Test Kind only
./scripts/comprehensive_helm_test.sh kind
```

### 高级测试 / Advanced Testing
```bash
# 包含 EKS 测试 (注意: 会产生 AWS 费用!) / Include EKS tests (WARNING: AWS costs!)
RUN_EKS_TESTS=true ./scripts/comprehensive_helm_test.sh

# 仅测试 EKS / Test EKS only
RUN_EKS_TESTS=true ./scripts/comprehensive_helm_test.sh eks
```

## 🛠️ 环境准备 / Environment Setup

### 必需工具 / Required Tools

```bash
# 核心工具 / Core tools
helm >= 3.0
kubectl >= 1.20
```

### Kind 环境 / Kind Environment
```bash
# 安装 Kind / Install Kind
# On macOS
brew install kind

# On Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### Minikube 环境 / Minikube Environment
```bash
# 安装 Minikube / Install Minikube
# On macOS
brew install minikube

# On Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

### EKS 环境 / EKS Environment
```bash
# 安装 AWS CLI / Install AWS CLI
pip install awscli

# 安装 eksctl / Install eksctl
# On macOS
brew tap weaveworks/tap
brew install weaveworks/tap/eksctl

# On Linux
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# 配置 AWS 凭证 / Configure AWS credentials
aws configure
```

## 📝 测试脚本详解 / Test Scripts Explanation

### 1. 综合测试脚本 / Comprehensive Test Script
**文件**: `scripts/comprehensive_helm_test.sh`

**功能**:
- 检查所有环境的前置条件
- 测试 Helm 仓库访问性
- 运行多环境部署测试
- 生成详细测试报告

**使用方法**:
```bash
./scripts/comprehensive_helm_test.sh [test_mode]
```

### 2. Kind/EKS 部署测试 / Kind/EKS Deployment Test
**文件**: `scripts/verify_helm_deployment.sh`

**功能**:
- Kind 集群创建和部署测试
- EKS 集群创建和部署测试
- Helm 升级/回滚测试
- Sidecar 功能验证

**使用方法**:
```bash
# Kind 测试 / Kind testing
./scripts/verify_helm_deployment.sh --kind-only

# EKS 测试 / EKS testing
./scripts/verify_helm_deployment.sh --eks-only

# 不清理集群 / Don't cleanup clusters
./scripts/verify_helm_deployment.sh --no-cleanup
```

### 3. Minikube 部署测试 / Minikube Deployment Test
**文件**: `scripts/test_minikube_deployment.sh`

**功能**:
- Minikube 集群启动和配置
- 特性测试 (Ingress, Dashboard, Metrics)
- 负载均衡测试
- 端口转发测试

**使用方法**:
```bash
# 基本测试 / Basic testing
./scripts/test_minikube_deployment.sh

# 测试后停止集群 / Stop cluster after testing
./scripts/test_minikube_deployment.sh --cleanup-cluster
```

## 🎯 测试覆盖范围 / Test Coverage

### 功能测试 / Functional Tests
- ✅ Helm 仓库添加和更新
- ✅ Chart 搜索和检查
- ✅ 一键部署命令
- ✅ Pod 启动和就绪检查
- ✅ 服务端点可访问性
- ✅ ConfigMap 和 Secret 应用

### 安全测试 / Security Tests
- ✅ 非 root 用户运行
- ✅ 权限限制检查
- ✅ 只读文件系统
- ✅ 网络策略执行
- ✅ 密钥访问控制
- ✅ 资源限制

### 性能测试 / Performance Tests
- ✅ 基准性能测试
- ✅ 内存消耗监控
- ✅ CPU 利用率监控
- ✅ 并发请求处理
- ✅ 负载均衡测试

### Helm 操作测试 / Helm Operations Tests
- ✅ helm install - 一键部署
- ✅ helm upgrade - Chart 升级
- ✅ helm rollback - 版本回滚
- ✅ helm uninstall - 清理卸载
- ✅ helm status - 状态检查

### Sidecar 功能测试 / Sidecar Functionality Tests
- ✅ 请求拦截日志
- ✅ 健康状态端点
- ✅ 指标收集端点
- ✅ 资源使用监控
- ✅ 错误处理验证

## 📊 测试结果解析 / Test Results Interpretation

### 退出码 / Exit Codes
- `0`: 所有测试通过 / All tests passed
- `1`: 部分测试失败 / Some tests failed
- `2`: 重大测试失败 / Major test failures

### 测试状态 / Test Status
- ✅ `PASS`: 测试通过
- ❌ `FAIL`: 测试失败
- ⚠️ `SKIP`: 测试跳过 (环境不可用)

### 成功率评估 / Success Rate Assessment
- `100%`: 生产就绪 / Production ready
- `90-99%`: 基本可用，需要修复少量问题 / Mostly ready, minor fixes needed
- `<90%`: 需要重大修复 / Major fixes required

## 🔧 故障排除 / Troubleshooting

### 常见问题 / Common Issues

#### 1. Kind 集群创建失败 / Kind Cluster Creation Failed
```bash
# 检查 Docker 状态 / Check Docker status
docker ps

# 清理现有集群 / Clean existing clusters
kind delete cluster --name psguard-kind-test

# 重新创建 / Recreate
kind create cluster --name psguard-kind-test
```

#### 2. EKS 部署失败 / EKS Deployment Failed
```bash
# 验证 AWS 凭证 / Verify AWS credentials
aws sts get-caller-identity

# 检查权限 / Check permissions
aws iam get-user

# 清理失败的集群 / Clean failed cluster
eksctl delete cluster --name psguard-eks-test --region us-west-2
```

#### 3. Helm 仓库访问失败 / Helm Repository Access Failed
```bash
# 检查网络连接 / Check network connectivity
curl -I https://siwenwang0803.github.io/PromptStrike

# 清理和重新添加仓库 / Clean and re-add repository
helm repo remove promptstrike
helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike
helm repo update
```

#### 4. Sidecar 无日志 / Sidecar No Logs
```bash
# 检查 Pod 状态 / Check pod status
kubectl get pods -n promptstrike-test

# 查看详细信息 / View detailed info
kubectl describe pod <pod-name> -n promptstrike-test

# 检查 values.yaml 配置 / Check values.yaml config
helm get values <release-name> -n promptstrike-test
```

### 调试命令 / Debug Commands

#### 集群状态检查 / Cluster Status Check
```bash
# 检查集群信息 / Check cluster info
kubectl cluster-info

# 检查节点状态 / Check node status
kubectl get nodes

# 检查系统 Pod / Check system pods
kubectl get pods -n kube-system
```

#### Helm 状态检查 / Helm Status Check
```bash
# 列出所有 Release / List all releases
helm list -A

# 检查 Release 状态 / Check release status
helm status <release-name> -n <namespace>

# 查看 Release 历史 / View release history
helm history <release-name> -n <namespace>
```

#### 网络诊断 / Network Diagnostics
```bash
# 测试服务连接 / Test service connectivity
kubectl run test-pod --rm -i --restart=Never --image=curlimages/curl -- \
  curl -v http://<service-name>.<namespace>.svc.cluster.local:8080/health

# 检查网络策略 / Check network policies
kubectl get networkpolicies -A

# 检查 Ingress / Check ingress
kubectl get ingress -A
```

## 📄 测试报告 / Test Reports

测试完成后，会生成详细的报告文件:
- 文件位置: `test_reports/helm_deployment_test_YYYYMMDD_HHMMSS.md`
- 包含内容: 测试统计、详细结果、环境信息、结论

## 🎉 成功标准 / Success Criteria

### 必须通过的测试 / Must-Pass Tests (P0)
- ✅ Helm 仓库访问
- ✅ Chart 搜索和检查
- ✅ 至少一个环境的成功部署
- ✅ Pod 启动和就绪
- ✅ 基本健康检查

### 建议通过的测试 / Should-Pass Tests (P1)
- ✅ 多环境部署
- ✅ Helm 升级/回滚
- ✅ Sidecar 功能验证
- ✅ 性能基准测试

### 可选测试 / Optional Tests (P2)
- ✅ EKS 部署 (需要 AWS 凭证)
- ✅ 负载均衡测试
- ✅ 高级网络功能

## 🚀 生产部署建议 / Production Deployment Recommendations

### 部署前检查 / Pre-Deployment Checklist
1. ✅ 运行完整测试套件
2. ✅ 验证目标环境兼容性
3. ✅ 准备 API 密钥和配置
4. ✅ 设置监控和告警
5. ✅ 准备回滚计划

### 生产部署命令 / Production Deployment Commands
```bash
# 添加 Helm 仓库 / Add Helm repository
helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike
helm repo update

# 生产环境部署 / Production deployment
helm install guardrail promptstrike/promptstrike-sidecar \
  --namespace promptstrike-production \
  --create-namespace \
  --set openai.apiKey="$OPENAI_API_KEY" \
  --set image.tag="0.1.0-alpha" \
  --set resources.limits.memory="512Mi" \
  --set resources.requests.memory="256Mi" \
  --set replicaCount=3 \
  --values production-values.yaml \
  --wait --timeout=600s

# 验证部署 / Verify deployment
helm status guardrail -n promptstrike-production
kubectl get pods -n promptstrike-production
```

---

**📝 注意**: 此测试套件确保 Helm 一键部署命令在各种 Kubernetes 环境中都能正常工作，并且脚本会返回正确的退出码以便自动化流水线使用。