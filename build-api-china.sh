#!/bin/bash

# Dify API 容器构建脚本 - 中国网络优化版本
# 使用国内镜像源加速构建过程

set -e

echo "🚀 开始构建 Dify API 容器（中国网络优化版本）..."

# 设置构建参数
IMAGE_NAME=${1:-"dify-api"}
TAG=${2:-"latest"}
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "📦 镜像名称: ${FULL_IMAGE_NAME}"
echo "🔧 构建目录: ./api"

# 进入 API 目录
cd api

# 检查是否存在中国优化版本的 Dockerfile
DOCKERFILE="Dockerfile"
if [ -f "Dockerfile.china" ]; then
    echo "🇨🇳 发现中国网络优化版本的 Dockerfile，使用该版本构建..."
    DOCKERFILE="Dockerfile.china"
fi

# 使用 Docker buildx 进行优化构建
echo "🏗️ 开始构建镜像..."
echo "📄 使用 Dockerfile: $DOCKERFILE"

docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --progress=plain \
  -f "$DOCKERFILE" \
  -t "${FULL_IMAGE_NAME}" \
  .

echo "✅ 构建完成！"
echo "🎯 镜像标签: ${FULL_IMAGE_NAME}"
echo ""
echo "📋 优化说明："
echo "  ✓ 使用阿里云 Debian 镜像源"
echo "  ✓ 使用清华大学 PyPI 镜像源"
echo "  ✓ 配置 apt 网络超时和重试"
echo "  ✓ 优化 uv 包管理器网络设置"
echo ""
echo "🚀 运行容器："
echo "docker run -d --name dify-api -p 5001:5001 ${FULL_IMAGE_NAME}"

cd ..
