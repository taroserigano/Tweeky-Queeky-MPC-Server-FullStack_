"""
Pinecone Vector Store - Vector database operations

Handles all interactions with Pinecone for storing and querying product embeddings.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from config.settings import settings


@dataclass
class SearchResult:
    """Represents a single search result from Pinecone"""
    id: str
    score: float
    metadata: Dict[str, Any]


class PineconeStore:
    """
    Pinecone vector store client.
    
    Handles:
    - Index creation/verification
    - Upserting product embeddings
    - Semantic similarity search
    - Metadata filtering
    
    Usage:
        store = PineconeStore()
        await store.initialize()
        await store.upsert_products(products_with_embeddings)
        results = await store.search(query_embedding, top_k=10)
    """
    
    def __init__(self):
        self._pc = None
        self._index = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Pinecone client and verify/create index"""
        if self._initialized:
            return
        
        try:
            from pinecone import Pinecone, ServerlessSpec
        except ImportError:
            raise ImportError(
                "pinecone not installed. "
                "Run: pip install pinecone"
            )
        
        api_key = settings.PINECONE_API_KEY
        if not api_key:
            raise ValueError("PINECONE_API_KEY not configured")
        
        # Initialize Pinecone client
        self._pc = Pinecone(api_key=api_key)
        
        # Check if index exists, create if not
        index_name = settings.PINECONE_INDEX
        existing_indexes = [idx.name for idx in self._pc.list_indexes()]
        
        if index_name not in existing_indexes:
            print(f"Creating Pinecone index: {index_name}")
            self._pc.create_index(
                name=index_name,
                dimension=settings.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=settings.PINECONE_CLOUD,
                    region=settings.PINECONE_REGION,
                )
            )
            # Wait for index to be ready
            await asyncio.sleep(5)
        
        self._index = self._pc.Index(index_name)
        self._initialized = True
        print(f"Pinecone initialized: index={index_name}, namespace={settings.PINECONE_NAMESPACE}")
    
    async def upsert(
        self,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None,
        batch_size: int = 100,
    ) -> int:
        """
        Upsert vectors to Pinecone.
        
        Args:
            vectors: List of dicts with 'id', 'values', and optional 'metadata'
            namespace: Pinecone namespace (default from settings)
            batch_size: Number of vectors per batch
            
        Returns:
            Number of vectors upserted
        """
        await self.initialize()
        
        namespace = namespace or settings.PINECONE_NAMESPACE
        total_upserted = 0
        
        # Process in batches
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            
            # Run upsert in thread pool (pinecone client is sync)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda b=batch: self._index.upsert(vectors=b, namespace=namespace)
            )
            total_upserted += len(batch)
            print(f"Upserted batch {i // batch_size + 1}: {len(batch)} vectors")
        
        return total_upserted
    
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[SearchResult]:
        """
        Search for similar vectors in Pinecone.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            namespace: Pinecone namespace
            filter: Metadata filter (e.g., {"category": "Electronics"})
            include_metadata: Whether to return metadata
            
        Returns:
            List of SearchResult objects with id, score, and metadata
        """
        await self.initialize()
        
        namespace = namespace or settings.PINECONE_NAMESPACE
        
        # Run query in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter,
                include_metadata=include_metadata,
            )
        )
        
        results = []
        for match in response.matches:
            results.append(SearchResult(
                id=match.id,
                score=match.score,
                metadata=match.metadata or {},
            ))
        
        return results
    
    async def delete(
        self,
        ids: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        delete_all: bool = False,
        filter: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Delete vectors from Pinecone.
        
        Args:
            ids: List of vector IDs to delete
            namespace: Pinecone namespace
            delete_all: Delete all vectors in namespace
            filter: Metadata filter for selective deletion
        """
        await self.initialize()
        
        namespace = namespace or settings.PINECONE_NAMESPACE
        
        loop = asyncio.get_event_loop()
        
        if delete_all:
            await loop.run_in_executor(
                None,
                lambda: self._index.delete(delete_all=True, namespace=namespace)
            )
        elif ids:
            await loop.run_in_executor(
                None,
                lambda: self._index.delete(ids=ids, namespace=namespace)
            )
        elif filter:
            await loop.run_in_executor(
                None,
                lambda: self._index.delete(filter=filter, namespace=namespace)
            )
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Dict with index stats including vector count
        """
        await self.initialize()
        
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(
            None,
            lambda: self._index.describe_index_stats()
        )
        
        return {
            "dimension": stats.dimension,
            "total_vector_count": stats.total_vector_count,
            "namespaces": {
                ns: {"vector_count": data.vector_count}
                for ns, data in (stats.namespaces or {}).items()
            },
        }
    
    async def fetch(
        self,
        ids: List[str],
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch vectors by ID.
        
        Args:
            ids: List of vector IDs to fetch
            namespace: Pinecone namespace
            
        Returns:
            Dict mapping IDs to vector data
        """
        await self.initialize()
        
        namespace = namespace or settings.PINECONE_NAMESPACE
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._index.fetch(ids=ids, namespace=namespace)
        )
        
        return {
            id: {
                "values": vec.values,
                "metadata": vec.metadata,
            }
            for id, vec in (response.vectors or {}).items()
        }


# Singleton instance
pinecone_store = PineconeStore()
