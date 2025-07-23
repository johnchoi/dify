#!/bin/bash

# Dify NLTK 数据离线准备脚本
# 用于在构建时预先下载 NLTK 数据，避免构建时的网络问题

set -e

echo "🚀 开始准备 NLTK 离线数据包..."

# 创建临时工作目录
WORK_DIR="/tmp/nltk_offline"
NLTK_DATA_DIR="${WORK_DIR}/nltk_data"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$WORK_DIR"
mkdir -p "$NLTK_DATA_DIR"

echo "📁 工作目录: $WORK_DIR"
echo "📂 NLTK 数据目录: $NLTK_DATA_DIR"

# 切换到工作目录
cd "$WORK_DIR"

# 创建虚拟环境
echo "🐍 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装 NLTK
echo "📦 安装 NLTK..."
pip install --timeout=60 -i https://pypi.tuna.tsinghua.edu.cn/simple nltk

# 设置 NLTK 数据路径
export NLTK_DATA="$NLTK_DATA_DIR"

echo "⬇️  下载 NLTK 数据包..."

# 下载所需的数据包
python3 << 'EOF'
import nltk
import ssl
import socket
import time
import os
from pathlib import Path

# 配置网络设置
socket.setdefaulttimeout(60)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 设置 NLTK 数据路径
nltk_data_dir = os.environ.get('NLTK_DATA', '/tmp/nltk_offline/nltk_data')
nltk.data.path = [nltk_data_dir]

packages = ['punkt', 'averaged_perceptron_tagger', 'stopwords']

print("开始下载 NLTK 数据包...")
for package in packages:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"下载 {package} (尝试 {attempt + 1}/{max_retries})")
            success = nltk.download(package, download_dir=nltk_data_dir, quiet=False)
            if success:
                print(f"✅ {package} 下载成功")
                break
            else:
                print(f"❌ {package} 下载失败")
        except Exception as e:
            print(f"错误: {e}")
            if attempt < max_retries - 1:
                print(f"等待 {2 ** attempt} 秒后重试...")
                time.sleep(2 ** attempt)
    else:
        print(f"⚠️  {package} 下载失败，跳过")

print("NLTK 数据下载完成")
EOF

# 验证下载的数据
echo "🔍 验证下载的数据..."
find "$NLTK_DATA_DIR" -type f -name "*.zip" -o -name "*.pickle" -o -name "*.txt" | head -10

# 创建压缩包
echo "📦 创建 NLTK 数据压缩包..."
cd "$NLTK_DATA_DIR"
tar -czf "$SCRIPT_DIR/nltk_data.tar.gz" .

# 清理临时文件
echo "🧹 清理临时文件..."
cd /
rm -rf "$WORK_DIR"

echo "✅ NLTK 离线数据包准备完成!"
echo "📄 数据包位置: $SCRIPT_DIR/nltk_data.tar.gz"

# 显示数据包大小
if [ -f "$SCRIPT_DIR/nltk_data.tar.gz" ]; then
    size=$(du -h "$SCRIPT_DIR/nltk_data.tar.gz" | cut -f1)
    echo "📊 数据包大小: $size"
else
    echo "❌ 数据包创建失败"
    exit 1
fi
