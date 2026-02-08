"""
Embedding Service - Generate vector embeddings for text

Supports multiple embedding providers:
- OpenAI (text-embedding-3-large/small)
- Sentence Transformers (local, free)
- Ollama (local)
"""

import asyncio
from typing import List, Optional, Union
from abc import ABC, abstractmethod

from config.settings import settings


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension"""
        pass


class OpenAIEmbedding(BaseEmbeddingProvider):
    """OpenAI embedding provider"""
    
    def __init__(self):
        from openai import AsyncOpenAI
        
        api_key = settings.openai_key
        if not api_key:
            raise ValueError("OpenAI API key not configured (OPENAI_API_KEY or OPEN_AI)")
        
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = settings.OPENAI_EMBEDDING_MODEL
        
        # Dimension mapping for OpenAI models
        self._dimensions = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
        }
    
    @property
    def dimension(self) -> int:
        return self._dimensions.get(self._model, 3072)
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text using OpenAI"""
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings


class SentenceTransformersEmbedding(BaseEmbeddingProvider):
    """Sentence Transformers embedding provider (local, free)"""
    
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
        
        self._model_name = settings.SENTENCE_TRANSFORMERS_MODEL
        self._model = SentenceTransformer(self._model_name)
        self._dimension = self._model.get_sentence_embedding_dimension()
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using Sentence Transformers"""
        # Run in thread pool since ST is synchronous
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._model.encode(text, normalize_embeddings=True).tolist()
        )
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(texts, normalize_embeddings=True).tolist()
        )
        return embeddings


class OllamaEmbedding(BaseEmbeddingProvider):
    """Ollama embedding provider (local)"""
    
    def __init__(self):
        import httpx
        
        self._base_url = settings.OLLAMA_BASE_URL
        self._model = settings.OLLAMA_EMBED_MODEL
        self._client = httpx.AsyncClient(timeout=60.0)
        
        # Default dimension for nomic-embed-text
        self._dimension = 768
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        response = await self._client.post(
            f"{self._base_url}/api/embeddings",
            json={"model": self._model, "prompt": text}
        )
        response.raise_for_status()
        return response.json()["embedding"]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (sequential for Ollama)"""
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings


class EmbeddingService:
    """
    Unified embedding service that supports multiple providers.
    
    Usage:
        service = EmbeddingService()
        embedding = await service.embed("comfortable office chair")
        embeddings = await service.embed_batch(["text1", "text2"])
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize embedding service.
        
        Args:
            provider: Override provider from settings ('openai', 'sentence_transformers', 'ollama')
        """
        self._provider_name = provider or settings.EMBEDDING_PROVIDER
        self._provider: Optional[BaseEmbeddingProvider] = None
    
    def _get_provider(self) -> BaseEmbeddingProvider:
        """Lazy initialization of embedding provider"""
        if self._provider is None:
            if self._provider_name == "openai":
                self._provider = OpenAIEmbedding()
            elif self._provider_name == "sentence_transformers":
                self._provider = SentenceTransformersEmbedding()
            elif self._provider_name == "ollama":
                self._provider = OllamaEmbedding()
            else:
                raise ValueError(f"Unknown embedding provider: {self._provider_name}")
        return self._provider
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension for current provider"""
        return self._get_provider().dimension
    
    @property
    def provider_name(self) -> str:
        """Get current provider name"""
        return self._provider_name
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        provider = self._get_provider()
        return await provider.embed(text)
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        provider = self._get_provider()
        return await provider.embed_batch(texts)
    
    def create_product_text(
        self,
        name: str,
        brand: str,
        category: str,
        description: str,
        price: float,
        rating: float = 0,
        num_reviews: int = 0,
        review_texts: list = None,
    ) -> str:
        """
        Create optimized text representation of a product for embedding.
        
        Args:
            name: Product name
            brand: Brand name
            category: Product category
            description: Product description
            price: Product price
            rating: Product rating
            num_reviews: Number of reviews
            review_texts: List of review comment strings
            
        Returns:
            Formatted text for embedding
        """
        # Include key attributes in a natural language format
        # This helps semantic search understand product context
        parts = [
            f"{name}",
            f"Brand: {brand}",
            f"Category: {category}",
            f"Description: {description}",
            f"Price: ${price:.2f}",
        ]
        
        if rating > 0:
            parts.append(f"Rating: {rating:.1f}/5 stars")
        
        if num_reviews > 0:
            parts.append(f"Customer reviews: {num_reviews} reviews")
        
        if review_texts:
            parts.append("Customer feedback: " + " | ".join(review_texts[:10]))
        
        return " | ".join(parts)
    
    def create_query_text(self, query: str, context: Optional[str] = None) -> str:
        """
        Format a search query for embedding.
        
        Args:
            query: User's search query
            context: Optional context (e.g., "looking for gifts", "budget-friendly")
            
        Returns:
            Formatted query text
        """
        if context:
            return f"{query} ({context})"
        return query


# Singleton instance for easy import
embedding_service = EmbeddingService()
