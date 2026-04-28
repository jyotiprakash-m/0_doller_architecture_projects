from llama_index.core.vector_stores.types import MetadataFilters, ExactMatchFilter, MetadataFilter, FilterOperator, FilterCondition
f1 = MetadataFilter(key="app_doc_id", value=["doc1", "doc2"], operator=FilterOperator.IN)
filters = MetadataFilters(filters=[f1])
print(filters)
