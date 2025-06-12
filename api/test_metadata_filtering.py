#!/usr/bin/env python3
"""
测试元数据过滤功能的示例
使用 /datasets/{dataset_id}/retrieve 接口
"""

import json

# 示例1：手动模式 - 基本元数据过滤


def test_manual_metadata_filtering():
    """测试手动模式的元数据过滤"""

    payload = {
        "query": "机器学习算法",
        "retrieval_model": {
            "search_method": "semantic_search",
            "top_k": 10,
            "score_threshold_enabled": True,
            "score_threshold": 0.7,
            "reranking_enable": False
        },
        # 新增的元数据过滤参数
        "metadata_filtering_mode": "manual",
        "metadata_filtering_conditions": {
            "logical_operator": "and",
            "conditions": [
                {
                    "name": "category",
                    "comparison_operator": "is",
                    "value": "AI"
                },
                {
                    "name": "publish_date",
                    "comparison_operator": "after",
                    "value": "2023-01-01"
                }
            ]
        }
    }

    print("示例1 - 手动模式元数据过滤:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload

# 示例2：自动模式 - 使用LLM自动提取元数据过滤条件


def test_automatic_metadata_filtering():
    """测试自动模式的元数据过滤"""

    payload = {
        "query": "找到2024年发布的关于深度学习的文档",
        "retrieval_model": {
            "search_method": "semantic_search",
            "top_k": 5,
            "score_threshold_enabled": True,
            "score_threshold": 0.6
        },
        # 自动模式需要模型配置
        "metadata_filtering_mode": "automatic",
        "metadata_model_config": {
            "provider": "openai",
            "name": "gpt-3.5-turbo",
            "mode": "chat",
            "completion_params": {
                "temperature": 0.0
            }
        }
    }

    print("\n示例2 - 自动模式元数据过滤:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload

# 示例3：复杂的元数据过滤条件


def test_complex_metadata_filtering():
    """测试复杂的元数据过滤条件"""

    payload = {
        "query": "自然语言处理技术",
        "retrieval_model": {
            "search_method": "hybrid_search",
            "top_k": 15,
            "score_threshold_enabled": True,
            "score_threshold": 0.5,
            "reranking_enable": True,
            "reranking_mode": "reranking_model",
            "reranking_model": {
                "reranking_provider_name": "cohere",
                "reranking_model_name": "rerank-english-v2.0"
            }
        },
        "metadata_filtering_mode": "manual",
        "metadata_filtering_conditions": {
            "logical_operator": "or",
            "conditions": [
                {
                    "name": "tags",
                    "comparison_operator": "contains",
                    "value": "NLP"
                },
                {
                    "name": "difficulty_level",
                    "comparison_operator": "=",
                    "value": "intermediate"
                },
                {
                    "name": "word_count",
                    "comparison_operator": ">",
                    "value": 1000
                },
                {
                    "name": "author",
                    "comparison_operator": "start with",
                    "value": "Dr."
                }
            ]
        }
    }

    print("\n示例3 - 复杂元数据过滤条件:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload

# 示例4：禁用元数据过滤


def test_disabled_metadata_filtering():
    """测试禁用元数据过滤"""

    payload = {
        "query": "人工智能发展历史",
        "retrieval_model": {
            "search_method": "semantic_search",
            "top_k": 8,
            "score_threshold_enabled": False
        },
        "metadata_filtering_mode": "disabled"
    }

    print("\n示例4 - 禁用元数据过滤:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


if __name__ == "__main__":
    print("=== Dify 元数据过滤功能测试示例 ===\n")

    # 运行所有测试示例
    test_manual_metadata_filtering()
    test_automatic_metadata_filtering()
    test_complex_metadata_filtering()
    test_disabled_metadata_filtering()

    print("\n=== 使用说明 ===")
    print("1. 替换 {dataset_id} 为实际的数据集ID")
    print("2. 根据实际环境调整服务器地址")
    print("3. 确保有相应的权限访问数据集")
    print("4. 元数据字段名需要与数据集中实际的元数据字段匹配")
    print("\n支持的比较操作符:")
    print("- 字符串: contains, not contains, start with, end with, is, is not, empty, not empty")
    print("- 数值: =, ≠, >, <, ≥, ≤")
    print("- 时间: before, after")
