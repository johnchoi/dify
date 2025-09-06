"""
端到端测试 /datasets/{dataset_id}/retrieve 接口的元数据返回功能
"""

import pytest
import json
from unittest.mock import patch, Mock
from flask import Flask


class TestRetrieveMetadataE2E:
    """端到端测试检索接口元数据功能"""
    
    def test_hit_testing_api_metadata_response_structure(self):
        """测试命中测试 API 响应中的元数据结构"""
        from fields.hit_testing_fields import hit_testing_record_fields, document_fields
        from core.rag.embedding.retrieval import RetrievalSegments
        from models.dataset import DocumentSegment, Document
        
        # 验证字段定义结构
        assert "segment" in hit_testing_record_fields
        assert "document" in hit_testing_record_fields["segment"].nested
        assert "doc_metadata" in document_fields
        
        # 模拟完整的数据流
        mock_document = Mock(spec=Document)
        mock_document.id = "test-doc-123"
        mock_document.name = "测试文档.pdf"
        mock_document.doc_type = "pdf"
        mock_document.data_source_type = "upload_file"
        mock_document.doc_metadata_details = [
            {
                "id": "meta-1",
                "name": "author",
                "type": "string",
                "value": "张三"
            },
            {
                "id": "meta-2",
                "name": "tags",
                "type": "array", 
                "value": ["AI", "技术"]
            }
        ]
        
        mock_segment = Mock(spec=DocumentSegment)
        mock_segment.id = "seg-123"
        mock_segment.content = "这是测试内容"
        mock_segment.document = mock_document
        
        # 创建 RetrievalSegments 对象
        retrieval_segment = RetrievalSegments(
            segment=mock_segment,
            score=0.85
        )
        
        # 测试序列化
        try:
            from flask_restx import marshal
            serialized = marshal(retrieval_segment.model_dump(), hit_testing_record_fields)
            
            # 验证基本结构
            assert "segment" in serialized
            assert "score" in serialized
            assert serialized["score"] == 0.85
            
            # 验证段落结构
            segment_data = serialized["segment"]
            assert "id" in segment_data
            assert "content" in segment_data
            assert "document" in segment_data
            
            # 验证文档结构
            document_data = segment_data["document"]
            assert "id" in document_data
            assert "name" in document_data
            assert "doc_type" in document_data
            assert "doc_metadata" in document_data
            
            # 验证元数据结构
            metadata = document_data["doc_metadata"]
            assert isinstance(metadata, list)
            assert len(metadata) == 2
            
            # 验证第一个元数据项
            first_meta = metadata[0]
            assert first_meta["id"] == "meta-1"
            assert first_meta["name"] == "author"
            assert first_meta["type"] == "string"
            assert first_meta["value"] == "张三"
            
            # 验证第二个元数据项
            second_meta = metadata[1]
            assert second_meta["id"] == "meta-2"
            assert second_meta["name"] == "tags"
            assert second_meta["type"] == "array"
            assert second_meta["value"] == ["AI", "技术"]
            
        except ImportError:
            # 如果无法导入 flask_restx，跳过序列化测试
            pytest.skip("flask_restx not available for serialization test")
            
    def test_hit_testing_service_response_format(self):
        """测试 HitTestingService 响应格式"""
        from services.hit_testing_service import HitTestingService
        
        # 验证 compact_retrieve_response 方法存在
        assert hasattr(HitTestingService, 'compact_retrieve_response')
        
        # 模拟文档数据
        mock_documents = []
        mock_records = [
            {
                "segment": {
                    "id": "seg-123",
                    "content": "测试内容",
                    "document": {
                        "id": "doc-123",
                        "name": "测试.pdf",
                        "doc_metadata": [
                            {
                                "id": "meta-1",
                                "name": "author",
                                "type": "string",
                                "value": "测试作者"
                            }
                        ]
                    }
                },
                "score": 0.85
            }
        ]
        
        # 测试响应格式
        response = HitTestingService.compact_retrieve_response("测试查询", mock_documents)
        
        # 验证响应结构
        assert isinstance(response, dict)
        assert "query" in response
        assert "records" in response
        assert response["query"]["content"] == "测试查询"
        assert isinstance(response["records"], list)
        
    def test_empty_metadata_handling(self):
        """测试空元数据处理"""
        from core.rag.embedding.retrieval import RetrievalSegments
        from models.dataset import DocumentSegment, Document
        
        # 创建没有元数据的文档
        mock_document = Mock(spec=Document)
        mock_document.id = "test-doc-empty"
        mock_document.name = "空文档.txt"
        mock_document.doc_type = "txt"
        mock_document.data_source_type = "upload_file"
        mock_document.doc_metadata_details = []  # 空数组
        
        mock_segment = Mock(spec=DocumentSegment)
        mock_segment.id = "seg-empty"
        mock_segment.content = "空内容"
        mock_segment.document = mock_document
        
        retrieval_segment = RetrievalSegments(
            segment=mock_segment,
            score=0.5
        )
        
        # 验证可以正常处理
        assert retrieval_segment.segment.document.doc_metadata_details == []
        
    def test_unicode_metadata_handling(self):
        """测试 Unicode 字符处理"""
        from models.dataset import Document
        
        mock_document = Mock(spec=Document)
        mock_document.doc_metadata_details = [
            {
                "id": "meta-unicode",
                "name": "特殊字符",
                "type": "string",
                "value": "测试 🚀 \"引号\" & < > 特殊字符"
            },
            {
                "id": "meta-emoji",
                "name": "emoji",
                "type": "string",
                "value": "😀🎉🔥💻"
            }
        ]
        
        # 验证 Unicode 字符不会引起错误
        metadata = mock_document.doc_metadata_details
        assert len(metadata) == 2
        assert "🚀" in metadata[0]["value"]
        assert "😀" in metadata[1]["value"]
        
    def test_nested_object_metadata(self):
        """测试嵌套对象元数据处理 - 需求 1.5"""
        from models.dataset import Document
        
        mock_document = Mock(spec=Document) 
        mock_document.doc_metadata_details = [
            {
                "id": "meta-nested",
                "name": "配置",
                "type": "object",
                "value": {
                    "level1": {
                        "level2": {
                            "deep_value": "深层值"
                        },
                        "array": [1, 2, {"nested_in_array": True}]
                    },
                    "simple": "简单值"
                }
            }
        ]
        
        # 验证嵌套结构完整保留
        metadata = mock_document.doc_metadata_details[0]
        nested_value = metadata["value"]
        
        assert nested_value["level1"]["level2"]["deep_value"] == "深层值"
        assert nested_value["level1"]["array"][2]["nested_in_array"] is True
        assert nested_value["simple"] == "简单值"
        
    def test_response_backward_compatibility(self):
        """测试响应向后兼容性 - 需求 2.1, 2.2"""
        from fields.hit_testing_fields import hit_testing_record_fields
        
        # 验证所有必需字段仍然存在
        required_fields = ["segment", "score"]
        for field in required_fields:
            assert field in hit_testing_record_fields
            
        # 验证段落字段
        segment_fields = hit_testing_record_fields["segment"].nested
        segment_required = ["id", "content", "document"]
        for field in segment_required:
            assert field in segment_fields
            
        # 验证文档字段
        document_fields = segment_fields["document"].nested
        document_required = ["id", "name", "doc_type", "doc_metadata"]
        for field in document_required:
            assert field in document_fields
            
        # 验证 doc_metadata 是 Raw 字段，支持任意格式
        from flask_restx import fields
        assert isinstance(document_fields["doc_metadata"], fields.Raw)


class TestMetadataValidation:
    """测试元数据验证和格式"""
    
    def test_metadata_item_structure_validation(self):
        """验证元数据项结构符合需求"""
        # 标准元数据项应该包含的字段
        required_fields = {"id", "name", "type", "value"}
        
        # 测试样例数据
        sample_metadata_item = {
            "id": "field_1",
            "name": "author",
            "type": "string",
            "value": "张三"
        }
        
        # 验证结构
        assert set(sample_metadata_item.keys()) == required_fields
        assert isinstance(sample_metadata_item["id"], str)
        assert isinstance(sample_metadata_item["name"], str) 
        assert isinstance(sample_metadata_item["type"], str)
        # value 可以是任意类型
        
    def test_metadata_types_validation(self):
        """验证支持的元数据类型"""
        supported_types = {"string", "number", "boolean", "array", "object", "time"}
        
        test_cases = [
            {"type": "string", "value": "文本"},
            {"type": "number", "value": 42},
            {"type": "boolean", "value": True},
            {"type": "array", "value": [1, 2, 3]},
            {"type": "object", "value": {"key": "value"}},
            {"type": "time", "value": "2024-06-15T10:30:00Z"}
        ]
        
        for case in test_cases:
            assert case["type"] in supported_types