"""
RAG Engine — LlamaIndex + ChromaDB + Ollama.
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
from llama_index.core.node_parser import SentenceSplitter
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
    Retrieval-Augmented Generation engine using local infrastructure only.
    - LLM: Ollama (local)
    - Embeddings: Ollama nomic-embed-text (local)
    - Vector Store: ChromaDB (local persistent)
    """

    def __init__(self):
        self._index: Optional[VectorStoreIndex] = None
        self._chroma_client = None
        self._collection = None
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

            # Initialize ChromaDB (persistent local storage)
            self._chroma_client = chromadb.PersistentClient(path=str(CHROMADB_DIR))
            self._collection = self._chroma_client.get_or_create_collection(
                name=CHROMA_COLLECTION,
                metadata={"description": "Legal documents for privacy-first auditing"}
            )

            # Create vector store and index
            vector_store = ChromaVectorStore(chroma_collection=self._collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
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

    def add_document(self, doc_id: str, user_id: str, text: str, filename: str) -> int:
        """
        Add a document to the vector store.
        Returns the number of chunks created.
        """
        if not self._initialized:
            self.initialize()

        # Create LlamaIndex document with metadata
        document = Document(
            text=text,
            metadata={
                "app_doc_id": doc_id,
                "user_id": user_id,
                "filename": filename,
                "source": "local_upload",
            }
        )

        # Parse into nodes and add to index
        parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        nodes = parser.get_nodes_from_documents([document])

        # Add app_doc_id and user_id to each node's metadata for filtering
        for node in nodes:
            node.metadata["app_doc_id"] = doc_id
            node.metadata["user_id"] = user_id

        self._index.insert_nodes(nodes)

        logger.info(f"Added document '{filename}' ({doc_id}) — {len(nodes)} chunks indexed.")
        return len(nodes)

    def query(self, question: str, user_id: str, doc_ids: list[str] = None, top_k: int = 5) -> dict:
        """
        Query the RAG pipeline. Returns answer with source citations.
        All inference happens locally via Ollama.
        """
        if not self._initialized:
            self.initialize()

        # Build query engine with user_id metadata filtering
        filters = [ExactMatchFilter(key="user_id", value=user_id)]
        
        # If a specific doc is requested, filter by app_doc_id (not doc_id which LlamaIndex overwrites)
        if doc_ids and len(doc_ids) == 1:
            filters.append(ExactMatchFilter(key="app_doc_id", value=doc_ids[0]))

        metadata_filters = MetadataFilters(filters=filters)

        logger.info(f"RAG query with filters: {[f'{f.key}={f.value}' for f in filters]}")

        query_engine = self._index.as_query_engine(
            similarity_top_k=top_k,
            response_mode="tree_summarize",
            filters=metadata_filters,
            streaming=False,
        )

        # Execute query
        response = query_engine.query(question)

        logger.info(f"RAG response source_nodes count: {len(response.source_nodes) if response.source_nodes else 0}")

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
                })

        answer = str(response).strip()
        if not answer or answer.lower() == "empty response":
            answer = "I couldn't find relevant information in this document. This may happen if the document was uploaded before the latest update. Please try re-uploading the document and asking again."

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(
                sum(s["score"] for s in sources if s["score"]) / len(sources), 3
            ) if sources else None,
        }

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

    def get_document_count(self) -> int:
        """Get total number of vectors in the store."""
        if self._collection:
            return self._collection.count()
        return 0


# Singleton instance
rag_engine = RAGEngine()
