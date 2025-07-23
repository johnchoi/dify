#!/usr/bin/env python3
"""
NLTK 数据下载脚本 - 针对中国网络环境优化
支持重试和超时机制，提高下载成功率
"""

import ssl
import socket
import time
from pathlib import Path
import os
import sys


def configure_ssl_and_proxy():
    """配置 SSL 和代理设置"""
    # 创建不验证 SSL 证书的上下文（在网络受限环境中有用）
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # 设置默认超时
    socket.setdefaulttimeout(30)

    return ssl_context


def download_with_retry(package_name, max_retries=5, base_delay=2):
    """
    使用重试机制下载 NLTK 包

    Args:
        package_name: NLTK 包名称
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
    """
    import nltk

    for attempt in range(max_retries + 1):
        try:
            print(
                f"📦 尝试下载 {package_name} (尝试 {attempt + 1}/{max_retries + 1})")

            # 设置下载目录
            nltk_data_dir = Path.home() / "nltk_data"
            nltk_data_dir.mkdir(exist_ok=True)
            nltk.data.path.append(str(nltk_data_dir))

            # 尝试下载
            success = nltk.download(package_name, quiet=False, force=False)

            if success:
                print(f"✅ {package_name} 下载成功!")
                return True
            else:
                print(f"❌ {package_name} 下载失败")

        except Exception as e:
            print(f"⚠️  下载 {package_name} 时出错: {str(e)}")

        if attempt < max_retries:
            delay = base_delay * (2 ** attempt)  # 指数退避
            print(f"⏰ 等待 {delay} 秒后重试...")
            time.sleep(delay)

    print(f"❌ {package_name} 下载失败，已达到最大重试次数")
    return False


def download_nltk_packages():
    """下载所需的 NLTK 包"""
    # 配置网络设置
    ssl_context = configure_ssl_and_proxy()

    try:
        import nltk
        print("🚀 开始下载 NLTK 数据包...")

        # 需要下载的包列表
        packages = [
            'punkt',  # 分词器
            'averaged_perceptron_tagger',  # 词性标注器
            'stopwords',  # 停用词（某些功能可能需要）
        ]

        success_count = 0
        total_count = len(packages)

        for package in packages:
            if download_with_retry(package):
                success_count += 1

        print(f"\n📊 下载统计: {success_count}/{total_count} 包下载成功")

        if success_count == total_count:
            print("🎉 所有 NLTK 数据包下载完成!")
            return True
        else:
            print("⚠️  部分包下载失败，但可能不影响基本功能")
            return success_count > 0

    except ImportError:
        print("❌ 无法导入 nltk，请确保已安装")
        return False
    except Exception as e:
        print(f"❌ 下载过程中发生未知错误: {str(e)}")
        return False


def verify_nltk_data():
    """验证 NLTK 数据是否可用"""
    try:
        import nltk

        print("🔍 验证 NLTK 数据...")

        # 验证 punkt
        try:
            nltk.data.find('tokenizers/punkt')
            print("✅ punkt 数据包可用")
        except LookupError:
            print("❌ punkt 数据包不可用")
            return False

        # 验证 averaged_perceptron_tagger
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
            print("✅ averaged_perceptron_tagger 数据包可用")
        except LookupError:
            print("❌ averaged_perceptron_tagger 数据包不可用")
            return False

        print("🎉 所有必需的 NLTK 数据包验证通过!")
        return True

    except Exception as e:
        print(f"❌ 验证过程中发生错误: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("🌟 NLTK 数据下载工具 - 中国网络优化版")
    print("=" * 50)

    # 设置环境变量以优化网络访问
    os.environ.setdefault('NLTK_DATA_TIMEOUT', '30')

    start_time = time.time()

    # 下载数据包
    download_success = download_nltk_packages()

    if download_success:
        # 验证数据包
        verify_success = verify_nltk_data()

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n⏱️  总耗时: {duration:.2f} 秒")

        if verify_success:
            print("🎊 NLTK 数据下载和验证完成!")
            sys.exit(0)
        else:
            print("❌ NLTK 数据验证失败")
            sys.exit(1)
    else:
        print("❌ NLTK 数据下载失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
