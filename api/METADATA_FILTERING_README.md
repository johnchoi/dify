# 元数据过滤功能扩展

## 概述

本次实现了方案二：暴露现有的元数据过滤功能，使 `/datasets/{dataset_id}/retrieve` 接口支持更强大的元数据过滤能力。

## 🎯 新增功能

### 1. 新增API参数

在原有接口基础上，新增了以下参数：

- `metadata_filtering_mode`: 元数据过滤模式
- `metadata_filtering_conditions`: 元数据过滤条件  
- `metadata_model_config`: 元数据模型配置（自动模式需要）

### 2. 支持的过滤模式

#### `disabled` - 禁用模式
不进行任何元数据过滤，使用原有的检索逻辑。

#### `manual` - 手动模式  
由用户手动指定过滤条件，支持复杂的条件组合。

#### `automatic` - 自动模式
使用LLM自动从查询中提取元数据过滤条件。

## 📝 API使用说明

### 基本请求格式

```http
POST /console/api/datasets/{dataset_id}/retrieve
Content-Type: application/json

{
  "query": "查询文本",
  "retrieval_model": {
    "search_method": "semantic_search",
    "top_k": 10,
    "score_threshold_enabled": true,
    "score_threshold": 0.7
  },
  "metadata_filtering_mode": "manual",
  "metadata_filtering_conditions": {
    "logical_operator": "and",
    "conditions": [
      {
        "name": "category",
        "comparison_operator": "is", 
        "value": "AI"
      }
    ]
  }
}
```

### 支持的比较操作符

#### 字符串操作
- `contains`: 包含
- `not contains`: 不包含
- `start with`: 以...开头
- `end with`: 以...结尾
- `is`: 等于
- `is not`: 不等于
- `empty`: 为空
- `not empty`: 不为空

#### 数值操作  
- `=`: 等于
- `≠`: 不等于
- `>`: 大于
- `<`: 小于
- `≥`: 大于等于
- `≤`: 小于等于

#### 时间操作
- `before`: 早于
- `after`: 晚于

### 逻辑操作符
- `and`: 所有条件都必须满足
- `or`: 任一条件满足即可

## 🔧 实现细节

### 修改的文件

1. **`api/controllers/console/datasets/hit_testing_base.py`**
   - 扩展 `parse_args()` 方法，增加元数据过滤参数
   - 修改 `perform_hit_testing()` 方法，传递新参数

2. **`api/services/hit_testing_service.py`**  
   - 扩展 `retrieve()` 方法签名，支持新参数
   - 增强 `hit_testing_args_check()` 参数验证
   - 优化元数据过滤逻辑处理

3. **`api/fields/dataset_fields.py`**
   - 添加元数据过滤相关的字段定义
   - 扩展 `dataset_retrieval_model_fields`

### 核心逻辑

1. **参数优先级**: API传入的参数 > retrieval_model中的参数 > 数据集默认配置
2. **过滤策略**: 先在PostgreSQL层面过滤文档ID，再传递给向量数据库  
3. **兼容性**: 完全向后兼容，不影响现有功能

## 🚀 使用示例

### 示例1: 手动模式基本过滤

```json
{
  "query": "机器学习算法", 
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
```

### 示例2: 自动模式智能过滤

```json
{
  "query": "找到2024年发布的关于深度学习的文档",
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
```

### 示例3: 复杂条件组合

```json
{
  "query": "自然语言处理技术",
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
      }
    ]
  }
}
```

## ⚠️ 注意事项

1. **元数据字段**: 过滤的字段名必须与数据集中实际的元数据字段匹配
2. **数据类型**: 数值比较时确保value为数值类型，字符串比较时确保为字符串类型
3. **性能**: 复杂的过滤条件可能影响查询性能，建议合理设置top_k值
4. **权限**: 需要有相应的数据集访问权限

## 🔄 向后兼容性

- 所有新增参数都是可选的
- 不传入新参数时，行为与之前完全一致
- 现有的API调用方式保持不变

## 🧪 测试

运行测试示例：

```bash
cd api
python test_metadata_filtering.py
```

## 📈 后续扩展

当前实现为方案二，后续可以继续实现：
- 方案一：支持向量数据库原生元数据过滤
- 性能优化：缓存过滤结果
- 更多操作符：正则表达式匹配等 
