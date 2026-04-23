import os
import logging
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings
import chromadb

from config import OLLAMA_BASE_URL, LLM_MODEL, EMBED_MODEL, CHROMADB_DIR, DATA_DIR

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.is_initialized = False
        self.query_engine = None

    def initialize(self):
        """Initializes the LlamaIndex components using local Ollama and local ChromaDB"""
        try:
            logger.info(f"Initializing RAG Service with LLM: {LLM_MODEL}")
            
            # 1. Setup Local LLM and Embedding Model (Ollama)
            llm = Ollama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, request_timeout=300.0)
            embed_model = OllamaEmbedding(model_name=EMBED_MODEL, base_url=OLLAMA_BASE_URL)
            
            # Apply to global settings
            Settings.llm = llm
            Settings.embed_model = embed_model
            Settings.chunk_size = 1024
            Settings.chunk_overlap = 200

            # 2. Setup Local Vector DB (Chroma)
            db = chromadb.PersistentClient(path=str(CHROMADB_DIR))
            chroma_collection = db.get_or_create_collection("ghost_editor_docs")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            self.storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # 3. Create or load index (Empty for now until docs are added)
            self.index = VectorStoreIndex.from_vector_store(
                vector_store,
                embed_model=embed_model,
            )
            
            self.query_engine = self.index.as_query_engine()
            self.is_initialized = True
            logger.info("RAG Service initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG Service: {e}")
            self.is_initialized = False

    def query_docs(self, query: str) -> str:
        """Queries the indexed documentation"""
        if not self.is_initialized or not self.query_engine:
            return "RAG Engine is not initialized."
            
        logger.info(f"Querying local docs: {query}")
        response = self.query_engine.query(query)
        return str(response)

rag_service = RAGService()
