"""
测试 /datasets/{dataset_id}/retrieve 接口的元数据返回功能
"""

import pytest
from flask import Flask

from models.dataset import Dataset, Document, DatasetMetadata, DatasetMetadataBinding


@pytest.fixture
def setup_dataset_with_metadata(setup_account, setup_app):
    """创建包含元数据的测试数据集"""
    from extensions.ext_database import db
    from models.model import App
    
    # 创建测试数据集
    dataset = Dataset(
        id="test-dataset-123",
        tenant_id=setup_account.current_tenant_id,
        name="测试数据集",
        provider="vendor",
        permission="only_me",
        data_source_type="upload_file",
        indexing_technique="high_quality",
        created_by=setup_account.id,
        built_in_field_enabled=True
    )
    db.session.add(dataset)
    
    # 创建元数据字段定义
    metadata1 = DatasetMetadata(
        id="meta-1",
        dataset_id=dataset.id,
        name="author",
        type="string",
        created_by=setup_account.id
    )
    metadata2 = DatasetMetadata(
        id="meta-2", 
        dataset_id=dataset.id,
        name="tags",
        type="array",
        created_by=setup_account.id
    )
    metadata3 = DatasetMetadata(
        id="meta-3",
        dataset_id=dataset.id, 
        name="priority",
        type="number",
        created_by=setup_account.id
    )
    db.session.add_all([metadata1, metadata2, metadata3])
    
    # 创建测试文档
    document = Document(
        id="test-doc-123",
        tenant_id=setup_account.current_tenant_id,
        dataset_id=dataset.id,
        position=1,
        data_source_type="upload_file",
        name="测试文档.pdf",
        doc_type="pdf",
        doc_metadata={
            "author": "张三",
            "tags": ["AI", "技术", "重要"],
            "priority": 1,
            "nested_data": {
                "category": "技术文档",
                "confidential": false
            }
        },
        created_by=setup_account.id,
        indexing_status="completed"
    )
    db.session.add(document)
    
    # 创建元数据绑定关系
    bindings = [
        DatasetMetadataBinding(
            dataset_id=dataset.id,
            document_id=document.id,
            metadata_id=metadata1.id
        ),
        DatasetMetadataBinding(
            dataset_id=dataset.id,
            document_id=document.id,
            metadata_id=metadata2.id
        ),
        DatasetMetadataBinding(
            dataset_id=dataset.id,
            document_id=document.id,
            metadata_id=metadata3.id
        )
    ]
    db.session.add_all(bindings)
    
    db.session.commit()
    
    return {
        "dataset": dataset,
        "document": document,
        "metadata_fields": [metadata1, metadata2, metadata3]
    }


class TestHitTestingMetadata:
    """测试命中测试接口的元数据返回功能"""
    
    def test_document_metadata_details_property(self, setup_dataset_with_metadata):
        """测试 Document 模型的 doc_metadata_details 属性"""
        document = setup_dataset_with_metadata["document"]
        
        # 获取元数据详情
        metadata_details = document.doc_metadata_details
        
        # 验证基本结构
        assert metadata_details is not None
        assert isinstance(metadata_details, list)
        
        # 验证包含预期的字段数量（3个自定义字段 + 内置字段）
        assert len(metadata_details) >= 3
        
        # 验证每个元数据项的结构
        for metadata_item in metadata_details:
            assert "id" in metadata_item
            assert "name" in metadata_item 
            assert "type" in metadata_item
            assert "value" in metadata_item
            
    def test_metadata_data_types(self, setup_dataset_with_metadata):
        """测试不同数据类型的元数据处理"""
        document = setup_dataset_with_metadata["document"]
        metadata_details = document.doc_metadata_details
        
        # 验证字符串类型
        author_meta = next((m for m in metadata_details if m["name"] == "author"), None)
        assert author_meta is not None
        assert author_meta["type"] == "string"
        assert author_meta["value"] == "张三"
        
        # 验证数组类型 
        tags_meta = next((m for m in metadata_details if m["name"] == "tags"), None)
        assert tags_meta is not None
        assert tags_meta["type"] == "array"
        assert tags_meta["value"] == ["AI", "技术", "重要"]
        
        # 验证数值类型
        priority_meta = next((m for m in metadata_details if m["name"] == "priority"), None)
        assert priority_meta is not None
        assert priority_meta["type"] == "number"
        assert priority_meta["value"] == 1
        
    def test_built_in_fields_included(self, setup_dataset_with_metadata):
        """测试内置字段是否包含在元数据中"""
        document = setup_dataset_with_metadata["document"]
        metadata_details = document.doc_metadata_details
        
        # 查找内置字段
        built_in_names = [m["name"] for m in metadata_details]
        
        # 验证应该包含一些内置字段
        expected_built_in_fields = ["document_name", "uploader", "upload_date", "last_update_date", "source"]
        found_built_in_fields = [name for name in expected_built_in_fields if name in built_in_names]
        
        # 至少应该有一些内置字段
        assert len(found_built_in_fields) > 0
        
    def test_empty_metadata_handling(self, setup_account, setup_app):
        """测试空元数据情况下的处理"""
        from extensions.ext_database import db
        
        # 创建没有元数据的文档
        dataset = Dataset(
            id="test-dataset-empty",
            tenant_id=setup_account.current_tenant_id,
            name="空数据集",
            provider="vendor",
            permission="only_me",
            data_source_type="upload_file",
            created_by=setup_account.id,
            built_in_field_enabled=False
        )
        
        document = Document(
            id="test-doc-empty",
            tenant_id=setup_account.current_tenant_id,
            dataset_id=dataset.id,
            position=1,
            data_source_type="upload_file",
            name="空文档.txt",
            doc_metadata=None,  # 空元数据
            created_by=setup_account.id,
            indexing_status="completed"
        )
        
        db.session.add_all([dataset, document])
        db.session.commit()
        
        # 验证空元数据处理
        metadata_details = document.doc_metadata_details
        assert metadata_details == []  # 修复后返回空数组而不是 None
        
        # 清理
        db.session.delete(document)
        db.session.delete(dataset)
        db.session.commit()
        
    def test_unicode_and_special_characters(self, setup_account, setup_app):
        """测试Unicode和特殊字符的处理"""
        from extensions.ext_database import db
        
        # 创建包含特殊字符的测试数据
        dataset = Dataset(
            id="test-dataset-unicode",
            tenant_id=setup_account.current_tenant_id,
            name="Unicode测试",
            provider="vendor",
            permission="only_me",
            data_source_type="upload_file",
            created_by=setup_account.id
        )
        
        # 创建元数据字段
        metadata_field = DatasetMetadata(
            id="meta-unicode",
            dataset_id=dataset.id,
            name="special_text",
            type="string",
            created_by=setup_account.id
        )
        
        # 创建包含特殊字符的文档
        document = Document(
            id="test-doc-unicode",
            tenant_id=setup_account.current_tenant_id,
            dataset_id=dataset.id,
            position=1,
            data_source_type="upload_file",
            name="特殊字符文档.pdf",
            doc_metadata={
                "special_text": "测试文本 🚀 \"引号\" 'apostrophe' & < > 特殊字符",
                "emoji_text": "😀🎉🔥💻",
                "mixed_lang": "English 中文 日本語 العربية"
            },
            created_by=setup_account.id,
            indexing_status="completed"
        )
        
        binding = DatasetMetadataBinding(
            dataset_id=dataset.id,
            document_id=document.id,
            metadata_id=metadata_field.id
        )
        
        db.session.add_all([dataset, metadata_field, document, binding])
        db.session.commit()
        
        # 验证特殊字符处理
        metadata_details = document.doc_metadata_details
        assert metadata_details is not None
        
        special_meta = next((m for m in metadata_details if m["name"] == "special_text"), None)
        assert special_meta is not None
        assert "🚀" in special_meta["value"]
        assert "\"引号\"" in special_meta["value"]
        
        # 清理
        db.session.delete(binding)
        db.session.delete(document)
        db.session.delete(metadata_field)
        db.session.delete(dataset)
        db.session.commit()


class TestHitTestingFieldsSerialization:
    """测试命中测试字段序列化"""
    
    def test_document_fields_structure(self):
        """测试 document_fields 的结构"""
        from fields.hit_testing_fields import document_fields
        
        # 验证必要字段存在
        required_fields = ["id", "data_source_type", "name", "doc_type", "doc_metadata"]
        for field_name in required_fields:
            assert field_name in document_fields
            
        # 验证 doc_metadata 字段类型
        from flask_restx import fields
        assert isinstance(document_fields["doc_metadata"], fields.Raw)
        
    def test_hit_testing_record_fields_structure(self):
        """测试完整的记录字段结构"""
        from fields.hit_testing_fields import hit_testing_record_fields, segment_fields
        
        # 验证记录包含段落
        assert "segment" in hit_testing_record_fields
        
        # 验证段落包含文档
        assert "document" in segment_fields
        
    def test_metadata_serialization_format(self, setup_dataset_with_metadata):
        """测试元数据序列化格式是否符合预期"""
        from flask_restx import fields
        from fields.hit_testing_fields import document_fields
        
        document = setup_dataset_with_metadata["document"]
        
        # 模拟序列化过程
        doc_metadata_field = document_fields["doc_metadata"]
        
        # 获取实际的元数据
        actual_metadata = document.doc_metadata_details
        
        # 验证数据结构符合需求
        if actual_metadata:
            for metadata_item in actual_metadata:
                # 验证每个字段都符合预期结构
                assert isinstance(metadata_item, dict)
                assert "id" in metadata_item
                assert "name" in metadata_item
                assert "type" in metadata_item
                assert "value" in metadata_item