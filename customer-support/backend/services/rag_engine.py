"""
RAG Engine — LlamaIndex + ChromaDB + Ollama.
Provides retrieval-augmented generation for company knowledge bases.
Everything runs locally. Zero data exfiltration.
"""
import logging
from typing import Optional

import chromadb
from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings,
    StorageContext,
)
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.core.node_parser import SentenceSplitter, HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.retrievers import AutoMergingRetriever, QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

from config import (
    OLLAMA_BASE_URL,
    LLM_MODEL,
    EMBED_MODEL,
    LLM_TEMPERATURE,
    LLM_REQUEST_TIMEOUT,
    CHROMADB_DIR,
    CHROMA_COLLECTION,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for company knowledge bases.
    - LLM: Ollama (local)
    - Embeddings: Ollama nomic-embed-text (local)
    - Vector Store: ChromaDB (local persistent)
    """

    def __init__(self):
        self._index: Optional[VectorStoreIndex] = None
        self._chroma_client = None
        self._collection = None
        self._node_parser = None
        self._initialized = False

    def initialize(self):
        """Initialize the RAG engine with local models."""
        if self._initialized:
            return

        logger.info(f"Initializing RAG Engine — LLM: {LLM_MODEL}, Embeddings: {EMBED_MODEL}")

        try:
            # Configure Ollama LLM (runs locally)
            llm = Ollama(
                model=LLM_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=LLM_TEMPERATURE,
                request_timeout=LLM_REQUEST_TIMEOUT,
            )

            # Configure Ollama Embeddings (runs locally)
            embed_model = OllamaEmbedding(
                model_name=EMBED_MODEL,
                base_url=OLLAMA_BASE_URL,
            )

            # Set global settings
            Settings.llm = llm
            Settings.embed_model = embed_model
            Settings.chunk_size = CHUNK_SIZE
            Settings.chunk_overlap = CHUNK_OVERLAP

            # 1. Advanced Hierarchical Node Parser
            self._node_parser = HierarchicalNodeParser.from_defaults(
                chunk_sizes=[2048, 512, 128]
            )

            # Metadata extraction now done via direct LLM calls in add_document()

            # Initialize ChromaDB (persistent local storage)
            self._chroma_client = chromadb.PersistentClient(path=str(CHROMADB_DIR))
            self._collection = self._chroma_client.get_or_create_collection(
                name=CHROMA_COLLECTION,
                metadata={"description": "Company knowledge bases for customer support training"}
            )

            # Create vector store and index
            vector_store = ChromaVectorStore(chroma_collection=self._collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Load index from vector store
            self._index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                storage_context=storage_context,
            )

            self._initialized = True
            logger.info("RAG Engine initialized successfully — all local, all private.")

        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {e}")
            logger.warning("Make sure Ollama is running: `ollama serve`")
            logger.warning(f"Make sure models are pulled: `ollama pull {LLM_MODEL}` and `ollama pull {EMBED_MODEL}`")
            raise

    def add_document(self, doc_id: str, user_id: str, kb_id: str,
                     text: str, filename: str, progress_callback=None) -> int:
        """
        Add a document to the vector store with KB isolation.
        Returns the number of chunks created.
        progress_callback: optional callable(int) that receives progress 0-100.
        """
        if not self._initialized:
            self.initialize()

        # Create LlamaIndex document with metadata for multi-tenant filtering
        document = Document(
            text=text,
            metadata={
                "app_doc_id": doc_id,
                "user_id": user_id,
                "kb_id": kb_id,
                "filename": filename,
                "source": "kb_upload",
            }
        )

        # Step 1: Hierarchical chunking (Small-to-Big)
        nodes = self._node_parser.get_nodes_from_documents([document])
        leaf_nodes = get_leaf_nodes(nodes)

        if progress_callback:
            progress_callback(25)

        # Step 5: Manual sync metadata extraction (keywords + summary)
        # LlamaIndex's Ollama client uses async httpx internally, which breaks
        # in the Kafka worker. We call Ollama's REST API directly via requests.
        import requests as http_requests
        total = len(leaf_nodes)
        for i, node in enumerate(leaf_nodes):
            try:
                text_snippet = node.text[:2000]

                # Extract keywords via direct Ollama API call
                kw_resp = http_requests.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": LLM_MODEL,
                        "prompt": f"Extract 5 important keywords from this text. "
                                  f"Return ONLY the keywords separated by commas, nothing else.\n\n"
                                  f"Text: {text_snippet}",
                        "stream": False
                    },
                    timeout=120
                )
                node.metadata["keywords"] = kw_resp.json().get("response", "").strip()

                # Extract summary via direct Ollama API call
                sum_resp = http_requests.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": LLM_MODEL,
                        "prompt": f"Summarize this text in 1-2 sentences. Return ONLY the summary.\n\n"
                                  f"Text: {text_snippet}",
                        "stream": False
                    },
                    timeout=120
                )
                node.metadata["section_summary"] = sum_resp.json().get("response", "").strip()

                # Report progress: metadata phase is 25% to 85%
                if progress_callback:
                    pct = 25 + int((i + 1) / total * 60)
                    progress_callback(pct)

                logger.info(f"  Metadata extracted for chunk {i+1}/{total}")
            except Exception as e:
                logger.warning(f"  Metadata extraction failed for chunk {i+1}/{total}: {e}")

        # Ensure isolation metadata propagates to each leaf node
        for node in leaf_nodes:
            node.metadata["app_doc_id"] = doc_id
            node.metadata["user_id"] = user_id
            node.metadata["kb_id"] = kb_id
            node.excluded_llm_metadata_keys = ["user_id", "kb_id", "app_doc_id"]
            node.excluded_embed_metadata_keys = ["user_id", "kb_id", "app_doc_id"]

        if progress_callback:
            progress_callback(90)

        self._index.insert_nodes(leaf_nodes)

        logger.info(f"Added KB document '{filename}' ({doc_id}) to KB {kb_id} — {len(leaf_nodes)} leaf nodes indexed.")
        return len(leaf_nodes)

    def query(self, question: str, user_id: str, kb_id: str = None,
              doc_id: str = None, top_k: int = 5) -> dict:
        """
        Query the RAG pipeline. Returns answer with source citations.
        Filtered by user_id, optionally by kb_id, and strictly by doc_id.
        """
        if not self._initialized:
            self.initialize()

        # Build metadata filters for tenant isolation
        filters = [ExactMatchFilter(key="user_id", value=user_id)]
        if kb_id:
            filters.append(ExactMatchFilter(key="kb_id", value=kb_id))
        if doc_id:
            filters.append(ExactMatchFilter(key="app_doc_id", value=doc_id))

        metadata_filters = MetadataFilters(filters=filters)
        logger.info(f"RAG Query: '{question}' | Filters: {filters}")

        # Point 1: Base retriever
        base_retriever = self._index.as_retriever(
            similarity_top_k=top_k * 2,
            filters=metadata_filters,
        )

        # Point 4: Hybrid Search (BM25)
        # Note: In a production app, we'd persist the BM25 index. 
        # For this MVP, we create a temporary BM25 retriever from the top-K nodes for speed.
        all_nodes = base_retriever.retrieve(question)
        logger.info(f"Retrieved {len(all_nodes)} nodes from vector store with filters.")
        
        if not all_nodes:
            # Try a broad search without doc_id if specific search fails (for debugging)
            logger.warning(f"No nodes found for doc_id {doc_id}. Checking if nodes exist at all for this user/kb...")
            debug_filters = MetadataFilters(filters=[ExactMatchFilter(key="user_id", value=user_id)])
            debug_retriever = self._index.as_retriever(similarity_top_k=5, filters=debug_filters)
            debug_nodes = debug_retriever.retrieve(question)
            logger.info(f"Broad search found {len(debug_nodes)} nodes.")

            return {
                "answer": "I couldn't find relevant information in the knowledge base. Please ensure documents have been uploaded and indexed.",
                "sources": []
            }
            
        actual_nodes = [n.node for n in all_nodes]
        bm25_retriever = BM25Retriever.from_defaults(nodes=actual_nodes, similarity_top_k=top_k)

        # Fusion
        fusion_retriever = QueryFusionRetriever(
            [base_retriever, bm25_retriever],
            similarity_top_k=top_k,
            num_queries=1,  # set to 1 to avoid query generation overhead for now
            mode="reciprocal_rerank",
            use_async=False,
        )

        # Point 2: LLM Reranking (Local Ollama)
        reranker = LLMRerank(choice_batch_size=5, top_n=3)

        query_engine = RetrieverQueryEngine.from_args(
            retriever=fusion_retriever,
            node_postprocessors=[reranker],
            response_mode="tree_summarize",
            streaming=False,
        )

        # Execute query
        response = query_engine.query(question)

        logger.info(f"RAG response source_nodes count: "
                     f"{len(response.source_nodes) if response.source_nodes else 0}")

        # Extract source references
        sources = []
        if response.source_nodes:
            for i, node in enumerate(response.source_nodes):
                sources.append({
                    "chunk_id": i + 1,
                    "text": node.text[:300] + "..." if len(node.text) > 300 else node.text,
                    "score": round(node.score, 3) if node.score else None,
                    "filename": node.metadata.get("filename", "Unknown"),
                    "doc_id": node.metadata.get("app_doc_id", ""),
                    "kb_id": node.metadata.get("kb_id", ""),
                })

        answer = str(response).strip()
        if not answer or answer.lower() == "empty response":
            answer = ("I couldn't find relevant information in the knowledge base. "
                      "Please ensure documents have been uploaded and indexed.")

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(
                sum(s["score"] for s in sources if s["score"]) / len(sources), 3
            ) if sources else None,
        }

    def get_context(self, question: str, user_id: str, kb_id: str = None, doc_id: str = None, top_k: int = 5) -> str:
        """
        Only retrieve context, without generating a final LLM answer.
        Used by the LangGraph agent for injecting context into its own prompts.
        """
        if not self._initialized:
            self.initialize()

        filters = [ExactMatchFilter(key="user_id", value=user_id)]
        if kb_id:
            filters.append(ExactMatchFilter(key="kb_id", value=kb_id))
        if doc_id:
            filters.append(ExactMatchFilter(key="app_doc_id", value=doc_id))

        metadata_filters = MetadataFilters(filters=filters)

        # 1. Base Retriever
        base_retriever = self._index.as_retriever(
            similarity_top_k=top_k * 2,
            filters=metadata_filters,
        )

        # 4. Hybrid (BM25)
        all_nodes = base_retriever.retrieve(question)
        if not all_nodes:
            return "No relevant company knowledge found."
            
        actual_nodes = [n.node for n in all_nodes]
        bm25_retriever = BM25Retriever.from_defaults(nodes=actual_nodes, similarity_top_k=top_k)

        # Fusion
        fusion_retriever = QueryFusionRetriever(
            [base_retriever, bm25_retriever],
            similarity_top_k=top_k,
            num_queries=1,
            mode="reciprocal_rerank",
            use_async=False,
        )

        # 2. Reranking
        reranker = LLMRerank(choice_batch_size=5, top_n=top_k)
        
        # Retrieve and process
        nodes = fusion_retriever.retrieve(question)
        nodes = reranker.postprocess_nodes(nodes, query_str=question)

        context_parts = []
        for i, node in enumerate(nodes):
            source = node.metadata.get("filename", "Unknown")
            context_parts.append(f"[Source: {source}]\n{node.text}")

        return "\n\n---\n\n".join(context_parts)

    def delete_document(self, doc_id: str):
        """Remove a document's vectors from ChromaDB."""
        if self._collection:
            try:
                results = self._collection.get(where={"app_doc_id": doc_id})
                if results and results["ids"]:
                    self._collection.delete(ids=results["ids"])
                    logger.info(f"Removed {len(results['ids'])} vectors for document {doc_id}")
            except Exception as e:
                logger.warning(f"Could not delete vectors for {doc_id}: {e}")

    def delete_kb_documents(self, kb_id: str):
        """Remove all vectors for a knowledge base."""
        if self._collection:
            try:
                results = self._collection.get(where={"kb_id": kb_id})
                if results and results["ids"]:
                    self._collection.delete(ids=results["ids"])
                    logger.info(f"Removed {len(results['ids'])} vectors for KB {kb_id}")
            except Exception as e:
                logger.warning(f"Could not delete vectors for KB {kb_id}: {e}")

    def get_document_count(self) -> int:
        """Get total number of vectors in the store."""
        if self._collection:
            return self._collection.count()
        return 0


# Singleton instance
rag_engine = RAGEngine()
