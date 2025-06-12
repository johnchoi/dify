import logging
import time
from typing import Any

from core.app.app_config.entities import ModelConfig
from core.model_runtime.entities import LLMMode
from core.rag.datasource.retrieval_service import RetrievalService
from core.rag.models.document import Document
from core.rag.retrieval.dataset_retrieval import DatasetRetrieval
from core.rag.retrieval.retrieval_methods import RetrievalMethod
from extensions.ext_database import db
from models.account import Account
from models.dataset import Dataset, DatasetQuery

default_retrieval_model = {
    "search_method": RetrievalMethod.SEMANTIC_SEARCH.value,
    "reranking_enable": False,
    "reranking_model": {"reranking_provider_name": "", "reranking_model_name": ""},
    "top_k": 2,
    "score_threshold_enabled": False,
}


class HitTestingService:
    @classmethod
    def retrieve(
        cls,
        dataset: Dataset,
        query: str,
        account: Account,
        retrieval_model: Any,  # FIXME drop this any
        external_retrieval_model: dict,
        metadata_filtering_mode: str = None,
        metadata_filtering_conditions: dict = None,
        metadata_model_config: dict = None,
        limit: int = 10,
    ) -> dict:
        start = time.perf_counter()

        # get retrieval model config
        retrieval_model_config = dataset.retrieval_model if dataset.retrieval_model else {}
        if retrieval_model:
            retrieval_model_config = {
                'search_method': retrieval_model.get('search_method', retrieval_model_config.get('search_method')),
                'reranking_enable': retrieval_model.get('reranking_enable',
                                                        retrieval_model_config.get('reranking_enable')),
                'reranking_model': retrieval_model.get('reranking_model', retrieval_model_config.get('reranking_model')),
                'reranking_mode': retrieval_model.get('reranking_mode', retrieval_model_config.get('reranking_mode')),
                'top_k': retrieval_model.get('top_k', retrieval_model_config.get('top_k')),
                'score_threshold_enabled': retrieval_model.get('score_threshold_enabled',
                                                               retrieval_model_config.get('score_threshold_enabled', False)),
                'score_threshold': retrieval_model.get('score_threshold',
                                                       retrieval_model_config.get('score_threshold')),
            }

        if external_retrieval_model:
            retrieval_model_config['search_method'] = 'hybrid_search'

        # 处理传入的元数据过滤参数，优先使用API传入的参数
        if metadata_filtering_mode is not None:
            retrieval_model_config["metadata_filtering_mode"] = metadata_filtering_mode
        if metadata_filtering_conditions is not None:
            retrieval_model_config["metadata_filtering_conditions"] = metadata_filtering_conditions
        if metadata_model_config is not None:
            retrieval_model_config["metadata_model_config"] = metadata_model_config

        document_ids_filter = None
        metadata_filtering_conditions = retrieval_model_config.get(
            "metadata_filtering_conditions", {})
        if metadata_filtering_conditions:
            dataset_retrieval = DatasetRetrieval()

            from core.app.app_config.entities import MetadataFilteringCondition

            metadata_filtering_conditions = MetadataFilteringCondition(
                **metadata_filtering_conditions)

            metadata_filter_document_ids, metadata_condition = dataset_retrieval.get_metadata_filter_condition(
                dataset_ids=[dataset.id],
                query=query,
                metadata_filtering_mode=retrieval_model_config.get(
                    "metadata_filtering_mode", "manual"),
                metadata_filtering_conditions=metadata_filtering_conditions,
                inputs={},
                tenant_id=dataset.tenant_id,
                user_id=account.id,
                metadata_model_config=ModelConfig(
                    **retrieval_model_config["metadata_model_config"])
                if retrieval_model_config.get("metadata_model_config")
                else ModelConfig(provider="", name="", mode=LLMMode.CHAT, completion_params={}),
            )
            if metadata_filter_document_ids:
                document_ids_filter = metadata_filter_document_ids.get(
                    dataset.id, [])
            if metadata_condition and not document_ids_filter:
                return cls.compact_retrieve_response(query, [])
        all_documents = RetrievalService.retrieve(
            retrieval_method=retrieval_model_config.get(
                "search_method", "semantic_search"),
            dataset_id=dataset.id,
            query=query,
            top_k=retrieval_model_config.get("top_k", 2),
            score_threshold=retrieval_model_config.get("score_threshold", 0.0)
            if retrieval_model_config["score_threshold_enabled"]
            else 0.0,
            reranking_model=retrieval_model_config.get("reranking_model", None)
            if retrieval_model_config["reranking_enable"]
            else None,
            reranking_mode=retrieval_model_config.get(
                "reranking_mode") or "reranking_model",
            weights=retrieval_model_config.get("weights", None),
            document_ids_filter=document_ids_filter,
        )

        end = time.perf_counter()
        logging.debug(f"Hit testing retrieve in {end - start:0.4f} seconds")

        dataset_query = DatasetQuery(
            dataset_id=dataset.id, content=query, source="hit_testing", created_by_role="account", created_by=account.id
        )

        db.session.add(dataset_query)
        db.session.commit()

        # type: ignore
        return cls.compact_retrieve_response(query, all_documents)

    @classmethod
    def external_retrieve(
        cls,
        dataset: Dataset,
        query: str,
        account: Account,
        external_retrieval_model: dict,
        metadata_filtering_conditions: dict,
    ) -> dict:
        if dataset.provider != "external":
            return {
                "query": {"content": query},
                "records": [],
            }

        start = time.perf_counter()

        all_documents = RetrievalService.external_retrieve(
            dataset_id=dataset.id,
            query=cls.escape_query_for_search(query),
            external_retrieval_model=external_retrieval_model,
            metadata_filtering_conditions=metadata_filtering_conditions,
        )

        end = time.perf_counter()
        logging.debug(
            f"External knowledge hit testing retrieve in {end - start:0.4f} seconds")

        dataset_query = DatasetQuery(
            dataset_id=dataset.id, content=query, source="hit_testing", created_by_role="account", created_by=account.id
        )

        db.session.add(dataset_query)
        db.session.commit()

        return dict(cls.compact_external_retrieve_response(dataset, query, all_documents))

    @classmethod
    def compact_retrieve_response(cls, query: str, documents: list[Document]) -> dict[Any, Any]:
        records = RetrievalService.format_retrieval_documents(documents)

        return {
            "query": {
                "content": query,
            },
            "records": [record.model_dump() for record in records],
        }

    @classmethod
    def compact_external_retrieve_response(cls, dataset: Dataset, query: str, documents: list) -> dict[Any, Any]:
        records = []
        if dataset.provider == "external":
            for document in documents:
                record = {
                    "content": document.get("content", None),
                    "title": document.get("title", None),
                    "score": document.get("score", None),
                    "metadata": document.get("metadata", None),
                }
                records.append(record)
            return {
                "query": {"content": query},
                "records": records,
            }
        return {"query": {"content": query}, "records": []}

    @classmethod
    def hit_testing_args_check(cls, args):
        query = args["query"]

        if not query or len(query) > 250:
            raise ValueError(
                "Query is required and cannot exceed 250 characters")

        # 验证元数据过滤模式
        metadata_filtering_mode = args.get("metadata_filtering_mode")
        if metadata_filtering_mode and metadata_filtering_mode not in ["disabled", "automatic", "manual"]:
            raise ValueError(
                "metadata_filtering_mode must be one of: disabled, automatic, manual")

        # 验证元数据过滤条件
        metadata_filtering_conditions = args.get(
            "metadata_filtering_conditions")
        if metadata_filtering_conditions:
            if not isinstance(metadata_filtering_conditions, dict):
                raise ValueError(
                    "metadata_filtering_conditions must be a dictionary")

            logical_operator = metadata_filtering_conditions.get(
                "logical_operator")
            if logical_operator and logical_operator not in ["and", "or"]:
                raise ValueError("logical_operator must be 'and' or 'or'")

            conditions = metadata_filtering_conditions.get("conditions")
            if conditions and not isinstance(conditions, list):
                raise ValueError("conditions must be a list")

            # 验证每个条件
            if conditions:
                valid_operators = [
                    "contains", "not contains", "start with", "end with",
                    "is", "is not", "empty", "not empty",
                    "=", "≠", ">", "<", "≥", "≤", "before", "after"
                ]
                for condition in conditions:
                    if not isinstance(condition, dict):
                        raise ValueError("Each condition must be a dictionary")
                    if "name" not in condition or "comparison_operator" not in condition:
                        raise ValueError(
                            "Each condition must have 'name' and 'comparison_operator'")
                    if condition["comparison_operator"] not in valid_operators:
                        raise ValueError(
                            f"comparison_operator must be one of: {', '.join(valid_operators)}")

        # 验证元数据模型配置
        metadata_model_config = args.get("metadata_model_config")
        if metadata_model_config:
            if not isinstance(metadata_model_config, dict):
                raise ValueError("metadata_model_config must be a dictionary")
            # 如果指定了自动模式，则需要模型配置
            if metadata_filtering_mode == "automatic" and not metadata_model_config:
                raise ValueError(
                    "metadata_model_config is required when metadata_filtering_mode is 'automatic'")

    @staticmethod
    def escape_query_for_search(query: str) -> str:
        return query.replace('"', '\\"')
