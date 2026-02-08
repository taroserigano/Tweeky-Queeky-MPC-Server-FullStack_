"""
RAG Service - Retrieval Augmented Generation

This module provides semantic search, embeddings, and retrieval capabilities
for AI-powered product discovery and question answering.

Uses LangChain ecosystem for production-grade RAG:
- langchain-openai for embeddings
- langchain-pinecone for vector store
- LangChain chains for Q&A
"""

# LangChain-based RAG (recommended)
from rag_service.langchain_rag import (
    ProductVectorStore,
    ProductRAGChain,
    get_vector_store,
    get_rag_chain,
    get_embeddings,
    index_all_products,
    index_single_product,
)

# Legacy custom implementation (kept for reference)
from rag_service.embeddings import EmbeddingService, embedding_service
from rag_service.vector_store import PineconeStore, pinecone_store
from rag_service.retriever import RAGRetriever, rag_retriever
from rag_service.indexer import ProductIndexer, product_indexer

__all__ = [
    # LangChain RAG (primary)
    "ProductVectorStore",
    "ProductRAGChain",
    "get_vector_store",
    "get_rag_chain",
    "get_embeddings",
    "index_all_products",
    "index_single_product",
    # Legacy (reference)
    "EmbeddingService",
    "embedding_service",
    "PineconeStore", 
    "pinecone_store",
    "RAGRetriever",
    "rag_retriever",
    "ProductIndexer",
    "product_indexer",
]

