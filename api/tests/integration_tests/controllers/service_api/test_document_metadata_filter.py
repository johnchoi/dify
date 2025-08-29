import json
import uuid
from datetime import datetime
from unittest import mock

import pytest

from models.dataset import Dataset, Document


class TestDocumentMetadataFilterServiceAPI:
    """Service API 元数据过滤功能集成测试"""

    @pytest.fixture
    def mock_dataset(self):
        """创建模拟数据集"""
        dataset = Dataset()
        dataset.id = str(uuid.uuid4())
        dataset.tenant_id = str(uuid.uuid4())
        dataset.name = "Test Dataset"
        dataset.created_at = datetime.utcnow()
        return dataset

    @pytest.fixture 
    def mock_documents_with_metadata(self, mock_dataset):
        """创建带有元数据的模拟文档"""
        documents = []
        
        # 文档1：技术文档
        doc1 = Document()
        doc1.id = str(uuid.uuid4())
        doc1.dataset_id = mock_dataset.id
        doc1.tenant_id = mock_dataset.tenant_id
        doc1.name = "技术文档1.pdf"
        doc1.doc_metadata = {
            "author": "张三",
            "category": "技术",
            "word_count": 1500,
            "tags": ["AI", "机器学习"]
        }
        doc1.created_at = datetime.utcnow()
        documents.append(doc1)
        
        # 文档2：产品文档
        doc2 = Document()
        doc2.id = str(uuid.uuid4())
        doc2.dataset_id = mock_dataset.id
        doc2.tenant_id = mock_dataset.tenant_id
        doc2.name = "产品文档1.docx"
        doc2.doc_metadata = {
            "author": "李四",
            "category": "产品",
            "word_count": 2000,
            "tags": ["产品设计", "用户体验"]
        }
        doc2.created_at = datetime.utcnow()
        documents.append(doc2)
        
        # 文档3：设计文档
        doc3 = Document()
        doc3.id = str(uuid.uuid4())
        doc3.dataset_id = mock_dataset.id
        doc3.tenant_id = mock_dataset.tenant_id
        doc3.name = "设计文档1.pdf"
        doc3.doc_metadata = {
            "author": "王五",
            "category": "设计",
            "word_count": 800,
            "tags": ["UI设计", "视觉"]
        }
        doc3.created_at = datetime.utcnow()
        documents.append(doc3)
        
        return documents

    def test_get_documents_without_metadata_filter(self, test_client, mock_dataset, mock_documents_with_metadata):
        """测试不带元数据过滤的API调用（向后兼容性）"""
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            # 模拟数据库查询
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            # 模拟分页查询
            mock_paginated = mock.Mock()
            mock_paginated.items = mock_documents_with_metadata
            mock_paginated.total = len(mock_documents_with_metadata)
            mock_db.paginate.return_value = mock_paginated
            
            # API调用
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            # 验证响应格式
            assert 'data' in data
            assert 'total' in data
            assert 'page' in data
            assert 'limit' in data
            assert len(data['data']) == 3

    def test_get_documents_with_exact_match_filter(self, test_client, mock_dataset, mock_documents_with_metadata):
        """测试精确匹配过滤"""
        metadata_filter = json.dumps({"author": "张三"})
        
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            # 模拟过滤后的结果（只有张三的文档）
            filtered_docs = [doc for doc in mock_documents_with_metadata 
                           if doc.doc_metadata.get("author") == "张三"]
            
            mock_paginated = mock.Mock()
            mock_paginated.items = filtered_docs
            mock_paginated.total = len(filtered_docs)
            mock_db.paginate.return_value = mock_paginated
            
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                query_string={'metadata_filter': metadata_filter},
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['total'] == 1

    def test_get_documents_with_in_operator_filter(self, test_client, mock_dataset, mock_documents_with_metadata):
        """测试in操作符过滤"""
        metadata_filter = json.dumps({"category": {"in": ["技术", "产品"]}})
        
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            # 模拟过滤后的结果（技术和产品文档）
            filtered_docs = [doc for doc in mock_documents_with_metadata 
                           if doc.doc_metadata.get("category") in ["技术", "产品"]]
            
            mock_paginated = mock.Mock()
            mock_paginated.items = filtered_docs
            mock_paginated.total = len(filtered_docs)
            mock_db.paginate.return_value = mock_paginated
            
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                query_string={'metadata_filter': metadata_filter},
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['total'] == 2

    def test_get_documents_with_numeric_range_filter(self, test_client, mock_dataset, mock_documents_with_metadata):
        """测试数值范围过滤"""
        metadata_filter = json.dumps({"word_count": {"gt": 1000}})
        
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            # 模拟过滤后的结果（字数大于1000的文档）
            filtered_docs = [doc for doc in mock_documents_with_metadata 
                           if doc.doc_metadata.get("word_count", 0) > 1000]
            
            mock_paginated = mock.Mock()
            mock_paginated.items = filtered_docs
            mock_paginated.total = len(filtered_docs)
            mock_db.paginate.return_value = mock_paginated
            
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                query_string={'metadata_filter': metadata_filter},
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['total'] == 2  # 张三(1500)和李四(2000)的文档

    def test_get_documents_with_contains_filter(self, test_client, mock_dataset, mock_documents_with_metadata):
        """测试contains操作符过滤"""
        metadata_filter = json.dumps({"tags": {"contains": "AI"}})
        
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            # 模拟过滤后的结果（标签包含"AI"的文档）
            filtered_docs = [doc for doc in mock_documents_with_metadata 
                           if "AI" in doc.doc_metadata.get("tags", [])]
            
            mock_paginated = mock.Mock()
            mock_paginated.items = filtered_docs
            mock_paginated.total = len(filtered_docs)
            mock_db.paginate.return_value = mock_paginated
            
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                query_string={'metadata_filter': metadata_filter},
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['total'] == 1

    def test_get_documents_with_complex_filter(self, test_client, mock_dataset, mock_documents_with_metadata):
        """测试复杂过滤条件"""
        metadata_filter = json.dumps({
            "category": {"in": ["技术", "产品"]},
            "word_count": {"gte": 1500}
        })
        
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            # 模拟过滤后的结果
            filtered_docs = [doc for doc in mock_documents_with_metadata 
                           if (doc.doc_metadata.get("category") in ["技术", "产品"] and 
                               doc.doc_metadata.get("word_count", 0) >= 1500)]
            
            mock_paginated = mock.Mock()
            mock_paginated.items = filtered_docs
            mock_paginated.total = len(filtered_docs)
            mock_db.paginate.return_value = mock_paginated
            
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                query_string={'metadata_filter': metadata_filter},
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['total'] == 2  # 张三和李四的文档

    def test_get_documents_with_pagination_and_filter(self, test_client, mock_dataset, mock_documents_with_metadata):
        """测试分页功能与元数据过滤的结合"""
        metadata_filter = json.dumps({"category": {"in": ["技术", "产品"]}})
        
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            filtered_docs = [doc for doc in mock_documents_with_metadata 
                           if doc.doc_metadata.get("category") in ["技术", "产品"]]
            
            mock_paginated = mock.Mock()
            mock_paginated.items = filtered_docs[:1]  # 每页1个
            mock_paginated.total = len(filtered_docs)  # 总共2个
            mock_db.paginate.return_value = mock_paginated
            
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                query_string={
                    'metadata_filter': metadata_filter,
                    'page': 1,
                    'limit': 1
                },
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['total'] == 2
            assert data['page'] == 1
            assert data['limit'] == 1
            assert len(data['data']) == 1

    def test_get_documents_dataset_not_found(self, test_client):
        """测试数据集不存在的情况"""
        non_existent_dataset_id = str(uuid.uuid4())
        
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = None
            
            response = test_client.get(
                f'/v1/datasets/{non_existent_dataset_id}/documents',
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 404

    def test_get_documents_invalid_json_filter(self, test_client, mock_dataset):
        """测试无效JSON格式过滤条件"""
        invalid_filter = '{"author": "张三", "invalid": }'
        
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                query_string={'metadata_filter': invalid_filter},
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'Invalid JSON format in metadata filter' in str(data)

    def test_get_documents_unsupported_operator(self, test_client, mock_dataset):
        """测试不支持的操作符"""
        unsupported_filter = json.dumps({"field": {"regex": ".*pattern.*"}})
        
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                query_string={'metadata_filter': unsupported_filter},
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'Invalid metadata filter conditions' in str(data)

    def test_get_documents_empty_in_operator(self, test_client, mock_dataset):
        """测试空的in操作符值"""
        empty_in_filter = json.dumps({"category": {"in": []}})
        
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                query_string={'metadata_filter': empty_in_filter},
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'Invalid metadata filter conditions' in str(data)

    def test_get_documents_metadata_response_format(self, test_client, mock_dataset, mock_documents_with_metadata):
        """测试元数据响应格式正确性"""
        with mock.patch('controllers.service_api.dataset.document.db') as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dataset
            
            mock_paginated = mock.Mock()
            mock_paginated.items = mock_documents_with_metadata
            mock_paginated.total = len(mock_documents_with_metadata)
            mock_db.paginate.return_value = mock_paginated
            
            response = test_client.get(
                f'/v1/datasets/{mock_dataset.id}/documents',
                headers={'Authorization': 'Bearer test-api-key'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            # 验证每个文档都包含doc_metadata字段
            for doc in data['data']:
                assert 'doc_metadata' in doc
                # 注意：实际的marshal过程会通过doc_metadata_details属性返回结构化格式
                # 这里我们主要验证字段存在