#!/bin/bash

# Dify NLTK 数据管理脚本
# 支持准备离线数据包、验证数据完整性等功能

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NLTK_DATA_ARCHIVE="$SCRIPT_DIR/api/docker/nltk_data.tar.gz"

show_help() {
    cat << EOF
🌟 Dify NLTK 数据管理工具

用法: $0 [选项]

选项:
    prepare     准备离线 NLTK 数据包
    verify      验证 NLTK 数据包
    build       使用优化配置构建 API 镜像
    test        测试 NLTK 功能
    clean       清理临时文件
    help        显示此帮助信息

示例:
    $0 prepare          # 准备离线数据包
    $0 verify           # 验证数据包完整性
    $0 build            # 构建优化的 API 镜像
    $0 test             # 测试 NLTK 功能

EOF
}

prepare_offline_data() {
    echo "🚀 准备 NLTK 离线数据包..."

    if [ -f "$SCRIPT_DIR/api/docker/prepare_nltk_offline.sh" ]; then
        cd "$SCRIPT_DIR"
        bash api/docker/prepare_nltk_offline.sh

        if [ -f "$NLTK_DATA_ARCHIVE" ]; then
            echo "✅ NLTK 离线数据包准备完成!"
            echo "📄 位置: $NLTK_DATA_ARCHIVE"
            du -h "$NLTK_DATA_ARCHIVE"
        else
            echo "❌ 数据包准备失败"
            exit 1
        fi
    else
        echo "❌ 未找到准备脚本: api/docker/prepare_nltk_offline.sh"
        exit 1
    fi
}

verify_data_package() {
    echo "🔍 验证 NLTK 数据包..."

    if [ ! -f "$NLTK_DATA_ARCHIVE" ]; then
        echo "❌ 未找到 NLTK 数据包: $NLTK_DATA_ARCHIVE"
        echo "💡 请先运行: $0 prepare"
        exit 1
    fi

    echo "📦 数据包信息:"
    ls -lh "$NLTK_DATA_ARCHIVE"

    echo "📋 数据包内容:"
    tar -tzf "$NLTK_DATA_ARCHIVE" | head -20

    echo "✅ 数据包验证完成"
}

build_optimized_image() {
    echo "🏗️ 构建优化的 API 镜像..."

    if [ -f "$SCRIPT_DIR/build-api-china.sh" ]; then
        cd "$SCRIPT_DIR"
        ./build-api-china.sh "$@"
    else
        echo "❌ 未找到构建脚本: build-api-china.sh"
        exit 1
    fi
}

test_nltk_functionality() {
    echo "🧪 测试 NLTK 功能..."

    # 创建测试脚本
    cat > /tmp/test_nltk.py << 'EOF'
import nltk
import sys
import os

def test_nltk():
    print("🔍 测试 NLTK 功能...")

    # 测试 punkt
    try:
        nltk.data.find('tokenizers/punkt')
        print("✅ punkt 数据包可用")

        # 测试分词功能
        from nltk.tokenize import sent_tokenize, word_tokenize
        text = "Hello world. This is a test sentence."
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        print(f"✅ 分词功能正常: {len(sentences)} 句子, {len(words)} 词")

    except Exception as e:
        print(f"❌ punkt 测试失败: {e}")
        return False

    # 测试 averaged_perceptron_tagger
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger')
        print("✅ averaged_perceptron_tagger 数据包可用")

        # 测试词性标注功能
        from nltk import pos_tag
        from nltk.tokenize import word_tokenize
        words = word_tokenize("This is a test")
        tagged = pos_tag(words)
        print(f"✅ 词性标注功能正常: {tagged}")

    except Exception as e:
        print(f"❌ 词性标注测试失败: {e}")
        return False

    print("🎉 所有 NLTK 功能测试通过!")
    return True

if __name__ == "__main__":
    success = test_nltk()
    sys.exit(0 if success else 1)
EOF

    # 运行测试
    if command -v python3 >/dev/null 2>&1; then
        python3 /tmp/test_nltk.py
    else
        echo "❌ 未找到 Python3，无法运行测试"
        exit 1
    fi

    # 清理测试文件
    rm -f /tmp/test_nltk.py
}

clean_temp_files() {
    echo "🧹 清理临时文件..."

    # 清理可能的临时文件
    rm -rf /tmp/nltk_offline
    rm -f /tmp/test_nltk.py
    rm -f /tmp/download_nltk_data.py

    echo "✅ 清理完成"
}

main() {
    case "${1:-help}" in
        prepare)
            prepare_offline_data
            ;;
        verify)
            verify_data_package
            ;;
        build)
            shift
            build_optimized_image "$@"
            ;;
        test)
            test_nltk_functionality
            ;;
        clean)
            clean_temp_files
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "❌ 未知选项: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
