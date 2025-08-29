import pytest
from unittest.mock import Mock
from werkzeug.exceptions import BadRequest

from core.dataset.metadata_filter_parser import MetadataFilterParser


class TestMetadataFilterParser:
    """MetadataFilterParser 类的单元测试"""

    def test_parse_empty_filter_string(self):
        """测试空字符串解析"""
        result = MetadataFilterParser.parse_filter_string("")
        assert result == {}

    def test_parse_none_filter_string(self):
        """测试None值解析"""
        result = MetadataFilterParser.parse_filter_string(None)
        assert result == {}

    def test_parse_valid_json_filter_string(self):
        """测试有效JSON字符串解析"""
        filter_str = '{"author": "张三", "category": "技术"}'
        result = MetadataFilterParser.parse_filter_string(filter_str)
        expected = {"author": "张三", "category": "技术"}
        assert result == expected

    def test_parse_complex_json_filter_string(self):
        """测试复杂JSON字符串解析"""
        filter_str = '{"author": "张三", "category": {"in": ["技术", "产品"]}, "word_count": {"gt": 1000}}'
        result = MetadataFilterParser.parse_filter_string(filter_str)
        expected = {
            "author": "张三",
            "category": {"in": ["技术", "产品"]},
            "word_count": {"gt": 1000}
        }
        assert result == expected

    def test_parse_invalid_json_format(self):
        """测试无效JSON格式"""
        filter_str = '{"author": "张三", "invalid": }'
        with pytest.raises(BadRequest) as exc_info:
            MetadataFilterParser.parse_filter_string(filter_str)
        assert "Invalid JSON format in metadata filter" in str(exc_info.value)

    def test_parse_non_dict_json(self):
        """测试非字典JSON"""
        filter_str = '["author", "category"]'
        with pytest.raises(BadRequest) as exc_info:
            MetadataFilterParser.parse_filter_string(filter_str)
        assert "Filter must be a JSON object" in str(exc_info.value)


class TestMetadataFilterValidation:
    """MetadataFilterParser 验证功能的单元测试"""

    def test_validate_empty_filter(self):
        """测试空过滤条件验证"""
        errors = MetadataFilterParser.validate_filter_conditions({})
        assert errors == []

    def test_validate_simple_exact_match(self):
        """测试简单精确匹配验证"""
        filter_dict = {"author": "张三", "category": "技术"}
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert errors == []

    def test_validate_supported_operators(self):
        """测试支持的操作符验证"""
        filter_dict = {
            "field1": {"in": ["value1", "value2"]},
            "field2": {"gt": 100},
            "field3": {"gte": 50},
            "field4": {"lt": 200},
            "field5": {"lte": 150},
            "field6": {"contains": "text"}
        }
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert errors == []

    def test_validate_unsupported_operator(self):
        """测试不支持的操作符"""
        filter_dict = {"field": {"regex": ".*pattern.*"}}
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert len(errors) == 1
        assert "Unsupported operator: regex" in errors[0]

    def test_validate_in_operator_with_valid_list(self):
        """测试in操作符的有效列表值"""
        filter_dict = {"category": {"in": ["技术", "产品", "设计"]}}
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert errors == []

    def test_validate_in_operator_with_invalid_value(self):
        """测试in操作符的无效值"""
        filter_dict = {"category": {"in": "not_a_list"}}
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert len(errors) == 1
        assert "Value for 'in' operator must be a list" in errors[0]

    def test_validate_in_operator_with_empty_list(self):
        """测试in操作符的空列表"""
        filter_dict = {"category": {"in": []}}
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert len(errors) == 1
        assert "Value for 'in' operator cannot be empty list" in errors[0]

    def test_validate_numeric_operators_with_valid_values(self):
        """测试数值操作符的有效值"""
        filter_dict = {
            "count1": {"gt": 100},
            "count2": {"gte": "50"},
            "count3": {"lt": 3.14},
            "count4": {"lte": 200}
        }
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert errors == []

    def test_validate_numeric_operators_with_invalid_values(self):
        """测试数值操作符的无效值"""
        filter_dict = {"count": {"gt": ["not_a_number"]}}
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert len(errors) == 1
        assert "Value for 'gt' operator must be number or string" in errors[0]

    def test_validate_contains_operator_with_valid_value(self):
        """测试contains操作符的有效值"""
        filter_dict = {
            "tags": {"contains": "AI"},
            "score": {"contains": 100},
            "rate": {"contains": 3.5}
        }
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert errors == []

    def test_validate_contains_operator_with_invalid_value(self):
        """测试contains操作符的无效值"""
        filter_dict = {"tags": {"contains": ["invalid_list"]}}
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert len(errors) == 1
        assert "Value for 'contains' operator must be string or number" in errors[0]

    def test_validate_multiple_errors(self):
        """测试多个验证错误"""
        filter_dict = {
            "field1": {"invalid_op": "value"},
            "field2": {"in": []},
            "field3": {"gt": ["invalid"]}
        }
        errors = MetadataFilterParser.validate_filter_conditions(filter_dict)
        assert len(errors) == 3
        assert any("Unsupported operator: invalid_op" in error for error in errors)
        assert any("Value for 'in' operator cannot be empty list" in error for error in errors)
        assert any("Value for 'gt' operator must be number or string" in error for error in errors)

    def test_validate_non_dict_filter(self):
        """测试非字典类型的过滤条件"""
        errors = MetadataFilterParser.validate_filter_conditions("not_a_dict")
        assert len(errors) == 1
        assert "Filter must be a dictionary" in errors[0]


class TestQueryConditionBuilding:
    """查询条件构建功能的单元测试"""

    @pytest.fixture
    def mock_query(self):
        """创建模拟查询对象"""
        return Mock()

    def test_build_empty_filter_conditions(self, mock_query):
        """测试空过滤条件的查询构建"""
        result = MetadataFilterParser.build_query_conditions(mock_query, {})
        assert result == mock_query

    def test_build_exact_match_conditions(self, mock_query):
        """测试精确匹配条件的查询构建"""
        filter_dict = {"author": "张三", "category": "技术"}
        
        # Mock filter方法链
        mock_query.filter.return_value = mock_query
        
        result = MetadataFilterParser.build_query_conditions(mock_query, filter_dict)
        
        # 验证filter方法被调用
        assert mock_query.filter.called
        assert result == mock_query

    def test_build_in_operator_conditions(self, mock_query):
        """测试in操作符条件的查询构建"""
        filter_dict = {"category": {"in": ["技术", "产品"]}}
        
        # Mock filter方法链
        mock_query.filter.return_value = mock_query
        
        result = MetadataFilterParser.build_query_conditions(mock_query, filter_dict)
        
        # 验证filter方法被调用
        assert mock_query.filter.called
        assert result == mock_query

    def test_build_numeric_conditions(self, mock_query):
        """测试数值比较条件的查询构建"""
        filter_dict = {
            "count1": {"gt": 100},
            "count2": {"gte": 50},
            "count3": {"lt": 200},
            "count4": {"lte": 150}
        }
        
        # Mock filter方法链
        mock_query.filter.return_value = mock_query
        
        result = MetadataFilterParser.build_query_conditions(mock_query, filter_dict)
        
        # 验证filter方法被调用
        assert mock_query.filter.called
        assert result == mock_query

    def test_build_contains_conditions(self, mock_query):
        """测试contains操作符条件的查询构建"""
        filter_dict = {"tags": {"contains": "AI"}}
        
        # Mock filter方法链
        mock_query.filter.return_value = mock_query
        
        result = MetadataFilterParser.build_query_conditions(mock_query, filter_dict)
        
        # 验证filter方法被调用
        assert mock_query.filter.called
        assert result == mock_query

    def test_build_mixed_conditions(self, mock_query):
        """测试混合条件的查询构建"""
        filter_dict = {
            "author": "张三",
            "category": {"in": ["技术", "产品"]},
            "word_count": {"gt": 1000},
            "tags": {"contains": "AI"}
        }
        
        # Mock filter方法链
        mock_query.filter.return_value = mock_query
        
        result = MetadataFilterParser.build_query_conditions(mock_query, filter_dict)
        
        # 验证filter方法被调用
        assert mock_query.filter.called
        assert result == mock_query

    def test_build_conditions_with_invalid_field(self, mock_query):
        """测试包含无效字段的条件构建（应该跳过错误条件）"""
        filter_dict = {
            "valid_field": "valid_value",
            "invalid_field": {"invalid_op": "value"}
        }
        
        # Mock filter方法链
        mock_query.filter.return_value = mock_query
        
        # 不应该抛出异常，而是跳过无效条件
        result = MetadataFilterParser.build_query_conditions(mock_query, filter_dict)
        assert result == mock_query


class TestOperatorValueValidation:
    """操作符值验证的单元测试"""

    def test_validate_operator_value_in_valid(self):
        """测试in操作符的有效值验证"""
        error = MetadataFilterParser._validate_operator_value("in", ["value1", "value2"])
        assert error == ""

    def test_validate_operator_value_in_invalid_type(self):
        """测试in操作符的无效类型验证"""
        error = MetadataFilterParser._validate_operator_value("in", "not_a_list")
        assert "Value for 'in' operator must be a list" in error

    def test_validate_operator_value_in_empty_list(self):
        """测试in操作符的空列表验证"""
        error = MetadataFilterParser._validate_operator_value("in", [])
        assert "Value for 'in' operator cannot be empty list" in error

    @pytest.mark.parametrize("operator", ["gt", "gte", "lt", "lte"])
    def test_validate_operator_value_numeric_valid(self, operator):
        """测试数值操作符的有效值验证"""
        error = MetadataFilterParser._validate_operator_value(operator, 100)
        assert error == ""
        
        error = MetadataFilterParser._validate_operator_value(operator, 3.14)
        assert error == ""
        
        error = MetadataFilterParser._validate_operator_value(operator, "100")
        assert error == ""

    @pytest.mark.parametrize("operator", ["gt", "gte", "lt", "lte"])
    def test_validate_operator_value_numeric_invalid(self, operator):
        """测试数值操作符的无效值验证"""
        error = MetadataFilterParser._validate_operator_value(operator, ["not_a_number"])
        assert f"Value for '{operator}' operator must be number or string" in error

    def test_validate_operator_value_contains_valid(self):
        """测试contains操作符的有效值验证"""
        error = MetadataFilterParser._validate_operator_value("contains", "text")
        assert error == ""
        
        error = MetadataFilterParser._validate_operator_value("contains", 123)
        assert error == ""
        
        error = MetadataFilterParser._validate_operator_value("contains", 3.14)
        assert error == ""

    def test_validate_operator_value_contains_invalid(self):
        """测试contains操作符的无效值验证"""
        error = MetadataFilterParser._validate_operator_value("contains", ["invalid_list"])
        assert "Value for 'contains' operator must be string or number" in error


class TestSupportedOperators:
    """支持的操作符常量测试"""

    def test_supported_operators_constant(self):
        """测试支持的操作符常量"""
        expected_operators = ["in", "gt", "gte", "lt", "lte", "contains"]
        assert MetadataFilterParser.SUPPORTED_OPERATORS == expected_operators

    def test_all_operators_are_strings(self):
        """测试所有操作符都是字符串"""
        for operator in MetadataFilterParser.SUPPORTED_OPERATORS:
            assert isinstance(operator, str)
            assert len(operator) > 0