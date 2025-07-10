#!/bin/bash

# 修复环境变量并安装依赖
echo "🔧 修复环境变量并安装 kind 和 k6"

# 重新设置环境变量
export PWD="/Users/siwenwang/RedForge"
cd "$PWD"

# 验证环境
echo "当前目录: $(pwd)"
echo "PWD 变量: $PWD"

# 检查 homebrew 是否正常
echo "检查 homebrew..."
if command -v brew &> /dev/null; then
    echo "✅ Homebrew 已安装"
else
    echo "❌ Homebrew 未安装，请先安装 Homebrew"
    exit 1
fi

# 尝试修复 homebrew 环境
echo "修复 homebrew 环境..."
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || eval "$(/usr/local/bin/brew shellenv)" 2>/dev/null

# 重新设置 PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 安装 kind
echo "安装 kind..."
if ! command -v kind &> /dev/null; then
    brew install kind
    echo "✅ kind 安装完成"
else
    echo "✅ kind 已安装"
fi

# 验证 kind 版本
kind --version

# 安装 k6
echo "安装 k6..."
if ! command -v k6 &> /dev/null; then
    brew install k6
    echo "✅ k6 安装完成"
else
    echo "✅ k6 已安装"
fi

# 验证 k6 版本
k6 --version

# 检查 Docker 是否运行
echo "检查 Docker..."
if docker info &> /dev/null; then
    echo "✅ Docker 正在运行"
else
    echo "⚠️ Docker 未运行，请启动 Docker Desktop"
    echo "kind 需要 Docker 来创建 Kubernetes 集群"
fi

echo "🎉 依赖安装完成！现在可以运行:"
echo "  ./test-sidecar-resources.sh"