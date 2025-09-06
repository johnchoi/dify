"""
测试 Document 模型的元数据相关功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from models.dataset import Document, Dataset, DatasetMetadata, DatasetMetadataBinding


class TestDocumentMetadata:
    """测试 Document 的元数据功能"""
    
    def test_doc_metadata_details_with_data(self):
        """测试有元数据时的返回"""
        # 创建 mock 对象
        document = Document()
        document.id = "test-doc-id"
        document.dataset_id = "test-dataset-id"
        document.doc_metadata = {
            "author": "张三",
            "tags": ["AI", "技术"],
            "priority": 1
        }
        
        # Mock 数据库查询结果
        mock_metadata1 = Mock()
        mock_metadata1.id = "meta-1"
        mock_metadata1.name = "author"
        mock_metadata1.type = "string"
        
        mock_metadata2 = Mock()
        mock_metadata2.id = "meta-2"
        mock_metadata2.name = "tags"
        mock_metadata2.type = "array"
        
        mock_metadata3 = Mock()
        mock_metadata3.id = "meta-3"
        mock_metadata3.name = "priority" 
        mock_metadata3.type = "number"
        
        mock_dataset = Mock()
        mock_dataset.built_in_field_enabled = False
        
        # Mock 数据库查询
        with patch('models.dataset.db.session') as mock_session:
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.where.return_value = mock_query
            mock_query.all.return_value = [mock_metadata1, mock_metadata2, mock_metadata3]
            
            # Mock dataset 属性
            with patch.object(document, 'dataset', mock_dataset):
                result = document.doc_metadata_details
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 3
        
        # 验证每个元数据项的结构
        author_meta = next((m for m in result if m["name"] == "author"), None)
        assert author_meta is not None
        assert author_meta["id"] == "meta-1"
        assert author_meta["name"] == "author"
        assert author_meta["type"] == "string"
        assert author_meta["value"] == "张三"
        
        tags_meta = next((m for m in result if m["name"] == "tags"), None)
        assert tags_meta is not None
        assert tags_meta["value"] == ["AI", "技术"]
        
        priority_meta = next((m for m in result if m["name"] == "priority"), None)
        assert priority_meta is not None
        assert priority_meta["value"] == 1
        
    def test_doc_metadata_details_empty_data(self):
        """测试空元数据时的返回 - 需求 1.3"""
        document = Document()
        document.id = "test-doc-id"
        document.dataset_id = "test-dataset-id"
        document.doc_metadata = None
        
        mock_dataset = Mock()
        mock_dataset.built_in_field_enabled = False
        
        # Mock dataset 属性
        with patch.object(document, 'dataset', mock_dataset):
            result = document.doc_metadata_details
        
        # 验证返回空数组而不是 None
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0
        
    def test_doc_metadata_details_with_built_in_fields(self):
        """测试包含内置字段的情况"""
        document = Document()
        document.id = "test-doc-id"
        document.dataset_id = "test-dataset-id"
        document.doc_metadata = {"author": "测试"}
        
        # Mock 自定义元数据查询
        mock_metadata = Mock()
        mock_metadata.id = "meta-1"
        mock_metadata.name = "author"
        mock_metadata.type = "string"
        
        # Mock built-in fields
        mock_built_in_fields = [
            {
                "id": "built-in",
                "name": "document_name",
                "type": "string", 
                "value": "测试文档.pdf"
            }
        ]
        
        mock_dataset = Mock()
        mock_dataset.built_in_field_enabled = True
        
        with patch('models.dataset.db.session') as mock_session:
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.where.return_value = mock_query
            mock_query.all.return_value = [mock_metadata]
            
            with patch.object(document, 'dataset', mock_dataset):
                with patch.object(document, 'get_built_in_fields', return_value=mock_built_in_fields):
                    result = document.doc_metadata_details
        
        # 验证结果包含自定义字段和内置字段
        assert isinstance(result, list)
        assert len(result) == 2
        
        # 验证自定义字段
        author_meta = next((m for m in result if m["name"] == "author"), None)
        assert author_meta is not None
        assert author_meta["value"] == "测试"
        
        # 验证内置字段
        doc_name_meta = next((m for m in result if m["name"] == "document_name"), None)
        assert doc_name_meta is not None
        assert doc_name_meta["value"] == "测试文档.pdf"
        
    def test_doc_metadata_details_no_built_in_fields_when_disabled(self):
        """测试禁用内置字段时不包含内置字段"""
        document = Document()
        document.id = "test-doc-id"
        document.dataset_id = "test-dataset-id"
        document.doc_metadata = None
        
        mock_dataset = Mock()
        mock_dataset.built_in_field_enabled = False
        
        with patch.object(document, 'dataset', mock_dataset):
            result = document.doc_metadata_details
        
        # 验证只返回空数组，没有内置字段
        assert isinstance(result, list)
        assert len(result) == 0
        
    def test_doc_metadata_details_data_type_preservation(self):
        """测试数据类型保持 - 需求 1.4"""
        document = Document()
        document.id = "test-doc-id"
        document.dataset_id = "test-dataset-id"
        document.doc_metadata = {
            "string_field": "文本值",
            "number_field": 42,
            "float_field": 3.14,
            "boolean_field": True,
            "array_field": [1, 2, 3],
            "object_field": {"nested": "value"}
        }
        
        # Mock 元数据定义
        mock_metadatas = []
        for i, (name, field_type) in enumerate([
            ("string_field", "string"),
            ("number_field", "number"), 
            ("float_field", "number"),
            ("boolean_field", "boolean"),
            ("array_field", "array"),
            ("object_field", "object")
        ]):
            mock_meta = Mock()
            mock_meta.id = f"meta-{i+1}"
            mock_meta.name = name
            mock_meta.type = field_type
            mock_metadatas.append(mock_meta)
        
        mock_dataset = Mock()
        mock_dataset.built_in_field_enabled = False
        
        with patch('models.dataset.db.session') as mock_session:
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.where.return_value = mock_query
            mock_query.all.return_value = mock_metadatas
            
            with patch.object(document, 'dataset', mock_dataset):
                result = document.doc_metadata_details
        
        # 验证数据类型保持原样
        assert len(result) == 6
        
        value_map = {item["name"]: item["value"] for item in result}
        
        assert value_map["string_field"] == "文本值"
        assert value_map["number_field"] == 42
        assert value_map["float_field"] == 3.14
        assert value_map["boolean_field"] is True
        assert value_map["array_field"] == [1, 2, 3]
        assert value_map["object_field"] == {"nested": "value"}
        
    def test_doc_metadata_details_missing_value_handling(self):
        """测试元数据定义存在但文档中缺少该字段的情况"""
        document = Document()
        document.id = "test-doc-id"
        document.dataset_id = "test-dataset-id"
        document.doc_metadata = {
            "existing_field": "存在的值"
        }
        
        # Mock 元数据定义包含不存在的字段
        mock_metadata1 = Mock()
        mock_metadata1.id = "meta-1"
        mock_metadata1.name = "existing_field"
        mock_metadata1.type = "string"
        
        mock_metadata2 = Mock()
        mock_metadata2.id = "meta-2"
        mock_metadata2.name = "missing_field"
        mock_metadata2.type = "string"
        
        mock_dataset = Mock()
        mock_dataset.built_in_field_enabled = False
        
        with patch('models.dataset.db.session') as mock_session:
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.where.return_value = mock_query
            mock_query.all.return_value = [mock_metadata1, mock_metadata2]
            
            with patch.object(document, 'dataset', mock_dataset):
                result = document.doc_metadata_details
        
        # 验证结果
        assert len(result) == 2
        
        existing_meta = next((m for m in result if m["name"] == "existing_field"), None)
        assert existing_meta is not None
        assert existing_meta["value"] == "存在的值"
        
        missing_meta = next((m for m in result if m["name"] == "missing_field"), None)
        assert missing_meta is not None
        assert missing_meta["value"] is None  # doc_metadata.get() 返回 None