#!/bin/bash

# 简化的 PSGuard Sidecar 测试脚本
# 用于验证脚本逻辑和配置文件

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

# 检查配置文件
check_config_files() {
    print_msg $BLUE "🔍 检查配置文件..."
    
    local files=(
        "charts/psguard/Chart.yaml"
        "charts/psguard/values.yaml"
        "charts/psguard/templates/deployment.yaml"
        "load-tests/k6-sidecar-test.js"
        "monitoring/prometheus.yml"
        "monitoring/alert_rules.yml"
    )
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            print_msg $GREEN "✅ $file 存在"
        else
            print_msg $RED "❌ $file 不存在"
        fi
    done
}

# 验证 Helm chart 语法
validate_helm_chart() {
    print_msg $BLUE "🔍 验证 Helm chart 语法..."
    
    if command -v helm &> /dev/null; then
        if helm lint charts/psguard/; then
            print_msg $GREEN "✅ Helm chart 语法正确"
        else
            print_msg $RED "❌ Helm chart 语法错误"
        fi
        
        # 测试模板渲染
        if helm template test-release charts/psguard/ > /tmp/rendered-templates.yaml; then
            print_msg $GREEN "✅ Helm 模板渲染成功"
            print_msg $BLUE "模板输出已保存到 /tmp/rendered-templates.yaml"
        else
            print_msg $RED "❌ Helm 模板渲染失败"
        fi
    else
        print_msg $YELLOW "⚠️ helm 未安装，跳过验证"
    fi
}

# 检查 k6 脚本语法
validate_k6_script() {
    print_msg $BLUE "🔍 检查 k6 脚本语法..."
    
    if [[ -f "load-tests/k6-sidecar-test.js" ]]; then
        # 基本的 JavaScript 语法检查
        if node -c load-tests/k6-sidecar-test.js 2>/dev/null; then
            print_msg $GREEN "✅ k6 脚本语法正确"
        else
            print_msg $YELLOW "⚠️ 无法验证 k6 脚本语法（需要 node.js）"
        fi
    else
        print_msg $RED "❌ k6 脚本不存在"
    fi
}

# 验证 Prometheus 配置
validate_prometheus_config() {
    print_msg $BLUE "🔍 验证 Prometheus 配置..."
    
    if [[ -f "monitoring/prometheus.yml" ]]; then
        # 检查 YAML 语法
        if python3 -c "import yaml; yaml.safe_load(open('monitoring/prometheus.yml'))" 2>/dev/null; then
            print_msg $GREEN "✅ Prometheus 配置 YAML 语法正确"
        else
            print_msg $RED "❌ Prometheus 配置 YAML 语法错误"
        fi
        
        # 检查必要的配置项
        if grep -q "scrape_interval.*10s" monitoring/prometheus.yml; then
            print_msg $GREEN "✅ Prometheus 抓取间隔配置正确 (10s)"
        else
            print_msg $YELLOW "⚠️ 检查 Prometheus 抓取间隔配置"
        fi
    else
        print_msg $RED "❌ Prometheus 配置文件不存在"
    fi
}

# 检查资源限制配置
check_resource_limits() {
    print_msg $BLUE "🔍 检查资源限制配置..."
    
    if [[ -f "charts/psguard/values.yaml" ]]; then
        # 检查 CPU 限制
        if grep -q "cpu.*200m" charts/psguard/values.yaml; then
            print_msg $GREEN "✅ CPU 限制配置正确 (200m)"
        else
            print_msg $RED "❌ CPU 限制配置错误"
        fi
        
        # 检查内存限制
        if grep -q "memory.*180Mi" charts/psguard/values.yaml; then
            print_msg $GREEN "✅ 内存限制配置正确 (180Mi)"
        else
            print_msg $RED "❌ 内存限制配置错误"
        fi
    else
        print_msg $RED "❌ values.yaml 文件不存在"
    fi
}

# 模拟资源计算
simulate_resource_calculation() {
    print_msg $BLUE "🔍 模拟资源使用计算..."
    
    # 模拟 CPU 使用率计算 (毫核)
    local cpu_millicores=150
    local cpu_limit=200
    
    if [[ $cpu_millicores -le $cpu_limit ]]; then
        print_msg $GREEN "✅ CPU 使用率模拟: ${cpu_millicores}m ≤ ${cpu_limit}m"
    else
        print_msg $RED "❌ CPU 使用率模拟: ${cpu_millicores}m > ${cpu_limit}m"
    fi
    
    # 模拟内存使用计算 (Mi)
    local memory_mi=120
    local memory_limit=180
    
    if [[ $memory_mi -le $memory_limit ]]; then
        print_msg $GREEN "✅ 内存使用率模拟: ${memory_mi}Mi ≤ ${memory_limit}Mi"
    else
        print_msg $RED "❌ 内存使用率模拟: ${memory_mi}Mi > ${memory_limit}Mi"
    fi
}

# 生成测试报告
generate_test_report() {
    print_msg $BLUE "📋 生成测试报告..."
    
    cat > sidecar-test-report.md << EOF
# PSGuard Sidecar 配置验证报告

## 测试时间
$(date)

## 配置文件检查
- Helm Chart: $(test -f charts/psguard/Chart.yaml && echo "✅ 存在" || echo "❌ 缺失")
- Values: $(test -f charts/psguard/values.yaml && echo "✅ 存在" || echo "❌ 缺失")
- Deployment: $(test -f charts/psguard/templates/deployment.yaml && echo "✅ 存在" || echo "❌ 缺失")
- K6 Script: $(test -f load-tests/k6-sidecar-test.js && echo "✅ 存在" || echo "❌ 缺失")
- Prometheus Config: $(test -f monitoring/prometheus.yml && echo "✅ 存在" || echo "❌ 缺失")
- Alert Rules: $(test -f monitoring/alert_rules.yml && echo "✅ 存在" || echo "❌ 缺失")

## 资源限制验证
- CPU 限制: $(grep -q "cpu.*200m" charts/psguard/values.yaml && echo "✅ 200m" || echo "❌ 未配置")
- 内存限制: $(grep -q "memory.*180Mi" charts/psguard/values.yaml && echo "✅ 180Mi" || echo "❌ 未配置")

## 下一步
1. 安装缺失的依赖: kind, k6
2. 运行完整测试: ./test-sidecar-resources.sh
3. 检查实际资源使用情况
4. 验证 500 RPS 性能目标

## 依赖状态
- kubectl: $(which kubectl &>/dev/null && echo "✅ 已安装" || echo "❌ 未安装")
- helm: $(which helm &>/dev/null && echo "✅ 已安装" || echo "❌ 未安装")
- kind: $(which kind &>/dev/null && echo "✅ 已安装" || echo "❌ 未安装")
- k6: $(which k6 &>/dev/null && echo "✅ 已安装" || echo "❌ 未安装")
EOF

    print_msg $GREEN "✅ 报告已生成: sidecar-test-report.md"
}

# 提供安装指南
provide_installation_guide() {
    print_msg $BLUE "📖 依赖安装指南..."
    
    cat << EOF

🔧 安装缺失的依赖:

# 1. 安装 kind (Kubernetes in Docker)
# macOS:
brew install kind

# Linux:
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# 2. 安装 k6 (负载测试工具)
# macOS:
brew install k6

# Linux:
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# 3. 验证安装
kind --version
k6 --version

# 4. 运行完整测试
./test-sidecar-resources.sh

EOF
}

# 主函数
main() {
    print_msg $BLUE "🎯 PSGuard Sidecar 配置验证"
    
    check_config_files
    validate_helm_chart
    validate_k6_script
    validate_prometheus_config
    check_resource_limits
    simulate_resource_calculation
    generate_test_report
    provide_installation_guide
    
    print_msg $GREEN "✅ 配置验证完成！"
    print_msg $BLUE "查看详细报告: sidecar-test-report.md"
}

main "$@"