#!/bin/bash

# 等待 Docker 完全启动的脚本

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

print_msg $BLUE "⏳ 等待 Docker 完全启动..."

# 检查 Docker Desktop 是否在运行
check_docker_desktop() {
    if pgrep -f "Docker Desktop" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# 等待 Docker Desktop 启动
wait_for_docker_desktop() {
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if check_docker_desktop; then
            print_msg $GREEN "✅ Docker Desktop 进程已启动"
            break
        else
            print_msg $YELLOW "⏳ 等待 Docker Desktop 启动... ($attempt/$max_attempts)"
            sleep 2
            ((attempt++))
        fi
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_msg $RED "❌ Docker Desktop 启动超时"
        return 1
    fi
}

# 等待 Docker 服务响应
wait_for_docker_service() {
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker version &> /dev/null; then
            print_msg $GREEN "✅ Docker 服务响应正常"
            return 0
        else
            print_msg $YELLOW "⏳ 等待 Docker 服务响应... ($attempt/$max_attempts)"
            sleep 5
            ((attempt++))
        fi
    done
    
    print_msg $RED "❌ Docker 服务响应超时"
    return 1
}

# 检查 Docker 资源
check_docker_resources() {
    print_msg $BLUE "📊 检查 Docker 资源配置..."
    
    # 检查 Docker 信息
    docker info | grep -E "(CPUs|Total Memory|Server Version)" 2>/dev/null || {
        print_msg $YELLOW "⚠️ 无法获取 Docker 资源信息"
        return 1
    }
    
    # 检查可用空间
    docker system df 2>/dev/null || {
        print_msg $YELLOW "⚠️ 无法获取 Docker 磁盘使用情况"
        return 1
    }
    
    print_msg $GREEN "✅ Docker 资源检查完成"
}

# 主要流程
main() {
    # 1. 检查 Docker Desktop 是否需要启动
    if ! check_docker_desktop; then
        print_msg $YELLOW "启动 Docker Desktop..."
        open -a "Docker Desktop"
        sleep 5
    fi
    
    # 2. 等待 Docker Desktop 启动
    if ! wait_for_docker_desktop; then
        print_msg $RED "请手动启动 Docker Desktop 应用程序"
        exit 1
    fi
    
    # 3. 等待 Docker 服务响应
    if ! wait_for_docker_service; then
        print_msg $RED "Docker 服务无法正常响应"
        print_msg $YELLOW "建议操作："
        print_msg $YELLOW "1. 重启 Docker Desktop"
        print_msg $YELLOW "2. 检查 Docker Desktop 设置中的资源分配"
        print_msg $YELLOW "3. 确保有足够的磁盘空间"
        exit 1
    fi
    
    # 4. 检查 Docker 资源
    check_docker_resources
    
    print_msg $GREEN "🎉 Docker 已完全启动并准备就绪！"
    print_msg $BLUE "现在可以运行："
    print_msg $BLUE "  ./diagnose_kind_issue.sh   # 重新诊断"
    print_msg $BLUE "  ./test-sidecar-local.sh    # 本地测试"
}

main "$@"