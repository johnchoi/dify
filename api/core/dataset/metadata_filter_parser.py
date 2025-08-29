import json
import logging
from json import JSONDecodeError
from typing import Any, Dict, List, Union

from sqlalchemy import and_, func, or_
from sqlalchemy.exc import DataError
from werkzeug.exceptions import BadRequest

from models.dataset import Document

logger = logging.getLogger(__name__)


class MetadataFilterParser:
    """
    元数据过滤器解析器，用于解析和构建数据集文档的元数据过滤查询。
    
    支持的操作符：
    - 精确匹配: {"field": "value"}
    - 多值匹配: {"field": {"in": ["value1", "value2"]}}
    - 数值比较: {"field": {"gt": 100}}, {"field": {"gte": 100}}, {"field": {"lt": 100}}, {"field": {"lte": 100}}
    - 数组包含: {"field": {"contains": "value"}}
    """
    
    SUPPORTED_OPERATORS = ["in", "gt", "gte", "lt", "lte", "contains"]
    
    @staticmethod
    def parse_filter_string(filter_str: str) -> Dict[str, Any]:
        """
        解析JSON格式的过滤条件字符串。
        
        Args:
            filter_str: JSON格式的过滤条件字符串
            
        Returns:
            解析后的过滤条件字典
            
        Raises:
            BadRequest: 当JSON格式错误时
        """
        if not filter_str:
            return {}
            
        try:
            filter_dict = json.loads(filter_str)
            if not isinstance(filter_dict, dict):
                raise BadRequest("Filter must be a JSON object")
            return filter_dict
        except JSONDecodeError as e:
            logger.warning(f"Invalid JSON in metadata filter: {filter_str}, error: {e}")
            raise BadRequest(f"Invalid JSON format in metadata filter: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error parsing metadata filter: {filter_str}, error: {e}")
            raise BadRequest(f"Failed to parse metadata filter: {str(e)}")
    
    @staticmethod
    def validate_filter_conditions(filter_dict: Dict[str, Any]) -> List[str]:
        """
        验证过滤条件格式和操作符有效性。
        
        Args:
            filter_dict: 过滤条件字典
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not isinstance(filter_dict, dict):
            errors.append("Filter must be a dictionary")
            return errors
            
        for field, condition in filter_dict.items():
            if not isinstance(field, str):
                errors.append(f"Field name must be string, got: {type(field).__name__}")
                continue
                
            # 检查是否是直接值（精确匹配）
            if not isinstance(condition, dict):
                continue
                
            # 检查操作符条件
            if isinstance(condition, dict):
                for operator, value in condition.items():
                    if operator not in MetadataFilterParser.SUPPORTED_OPERATORS:
                        errors.append(f"Unsupported operator: {operator}. Supported operators: {MetadataFilterParser.SUPPORTED_OPERATORS}")
                        continue
                        
                    # 验证操作符特定的值
                    validation_error = MetadataFilterParser._validate_operator_value(operator, value)
                    if validation_error:
                        errors.append(f"Field '{field}', operator '{operator}': {validation_error}")
        
        return errors
    
    @staticmethod
    def _validate_operator_value(operator: str, value: Any) -> str:
        """
        验证操作符特定的值格式。
        
        Args:
            operator: 操作符名称
            value: 操作符对应的值
            
        Returns:
            错误信息，空字符串表示验证通过
        """
        if operator == "in":
            if not isinstance(value, list):
                return "Value for 'in' operator must be a list"
            if len(value) == 0:
                return "Value for 'in' operator cannot be empty list"
        elif operator in ["gt", "gte", "lt", "lte"]:
            if not isinstance(value, (int, float, str)):
                return f"Value for '{operator}' operator must be number or string"
        elif operator == "contains":
            if not isinstance(value, (str, int, float)):
                return "Value for 'contains' operator must be string or number"
        
        return ""
    
    @staticmethod
    def build_query_conditions(query, filter_dict: Dict[str, Any]):
        """
        根据过滤条件构建SQLAlchemy查询条件。
        
        Args:
            query: 基础SQLAlchemy查询对象
            filter_dict: 过滤条件字典
            
        Returns:
            添加了过滤条件的查询对象
            
        Raises:
            BadRequest: 当构建查询失败时
        """
        if not filter_dict:
            return query
            
        conditions = []
        
        for field, condition in filter_dict.items():
            try:
                field_conditions = MetadataFilterParser._build_field_conditions(field, condition)
                if field_conditions is not None:
                    conditions.extend(field_conditions)
            except Exception as e:
                logger.warning(f"Failed to build condition for field '{field}': {e}")
                # 跳过无效条件，不中断整个查询
                continue
        
        # 使用AND逻辑组合所有条件
        if conditions:
            query = query.filter(and_(*conditions))
            
        return query
    
    @staticmethod
    def _build_field_conditions(field: str, condition: Any) -> List[Any]:
        """
        为单个字段构建查询条件。
        
        Args:
            field: 字段名
            condition: 字段的过滤条件
            
        Returns:
            字段的查询条件列表
        """
        conditions = []
        
        # 精确匹配
        if not isinstance(condition, dict):
            conditions.append(Document.doc_metadata[field] == condition)
            return conditions
        
        # 操作符条件
        for operator, value in condition.items():
            try:
                field_condition = MetadataFilterParser._build_operator_condition(field, operator, value)
                if field_condition is not None:
                    conditions.append(field_condition)
            except Exception as e:
                logger.warning(f"Failed to build condition for field '{field}', operator '{operator}': {e}")
                continue
        
        return conditions
    
    @staticmethod
    def _build_operator_condition(field: str, operator: str, value: Any):
        """
        为单个操作符构建查询条件。
        
        Args:
            field: 字段名
            operator: 操作符
            value: 操作符值
            
        Returns:
            查询条件对象
        """
        if operator == "in":
            # 多值匹配：使用OR条件组合
            or_conditions = []
            for v in value:
                or_conditions.append(Document.doc_metadata[field].astext == str(v))
            return or_(*or_conditions)
        
        elif operator == "gt":
            return MetadataFilterParser._build_numeric_condition(field, ">", value)
        elif operator == "gte":
            return MetadataFilterParser._build_numeric_condition(field, ">=", value)
        elif operator == "lt":
            return MetadataFilterParser._build_numeric_condition(field, "<", value)
        elif operator == "lte":
            return MetadataFilterParser._build_numeric_condition(field, "<=", value)
        
        elif operator == "contains":
            # 数组元素包含查询：展开JSONB数组并进行精确匹配
            return func.jsonb_array_elements_text(Document.doc_metadata[field]) == str(value)
        
        else:
            logger.warning(f"Unsupported operator: {operator}")
            return None
    
    @staticmethod
    def _build_numeric_condition(field: str, operator: str, value: Any):
        """
        构建数值比较条件，包含错误处理。
        
        Args:
            field: 字段名
            operator: 比较操作符 (>, >=, <, <=)
            value: 比较值
            
        Returns:
            数值比较查询条件
        """
        try:
            # 尝试数值转换和比较
            from sqlalchemy import Integer
            field_value = Document.doc_metadata[field].astext.cast(Integer)
            
            if operator == ">":
                return field_value > int(value)
            elif operator == ">=":
                return field_value >= int(value)
            elif operator == "<":
                return field_value < int(value)
            elif operator == "<=":
                return field_value <= int(value)
            else:
                return None
                
        except (ValueError, DataError) as e:
            logger.warning(f"Failed to build numeric condition for field '{field}': {e}")
            # 类型转换失败时返回None，调用方会跳过该条件
            return None