"""
Product Indexer - Index products into Pinecone

Handles the initial indexing and incremental updates of product embeddings.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.settings import settings
from rag_service.embeddings import EmbeddingService
from rag_service.vector_store import PineconeStore
from services.product_service import product_service
from models.product import Product

# Create local instances to avoid circular imports
_embedding_svc: Optional[EmbeddingService] = None
_pinecone_svc: Optional[PineconeStore] = None


def _get_embedding_service() -> EmbeddingService:
    global _embedding_svc
    if _embedding_svc is None:
        _embedding_svc = EmbeddingService()
    return _embedding_svc


def _get_pinecone_store() -> PineconeStore:
    global _pinecone_svc
    if _pinecone_svc is None:
        _pinecone_svc = PineconeStore()
    return _pinecone_svc


class ProductIndexer:
    """
    Product Indexer for RAG.
    
    Handles:
    - Full reindexing of all products
    - Incremental indexing of new/updated products
    - Index maintenance (deletion, stats)
    
    Usage:
        indexer = ProductIndexer()
        stats = await indexer.index_all_products()
        await indexer.index_product(product_id)
        await indexer.remove_product(product_id)
    """
    
    def __init__(
        self,
        embedding_svc: Optional[EmbeddingService] = None,
        vector_store: Optional[PineconeStore] = None,
    ):
        self._embeddings = embedding_svc or _get_embedding_service()
        self._store = vector_store or _get_pinecone_store()
    
    def _product_to_metadata(self, product: Product) -> Dict[str, Any]:
        """
        Convert product to Pinecone metadata.
        
        Note: Pinecone metadata values must be string, number, boolean, or list.
        """
        return {
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "price": float(product.price),
            "rating": float(product.rating),
            "num_reviews": int(product.num_reviews),
            "count_in_stock": int(product.count_in_stock),
            "image": product.image,
            "indexed_at": datetime.utcnow().isoformat(),
        }
    
    def _product_to_text(self, product: Product) -> str:
        """Convert product to text for embedding"""
        return self._embeddings.create_product_text(
            name=product.name,
            brand=product.brand,
            category=product.category,
            description=product.description,
            price=product.price,
            rating=product.rating,
        )
    
    async def index_all_products(
        self,
        batch_size: int = 50,
        clear_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Index all products from MongoDB to Pinecone.
        
        Args:
            batch_size: Number of products to process per batch
            clear_existing: Whether to clear existing vectors first
            
        Returns:
            Indexing statistics
        """
        start_time = datetime.utcnow()
        
        # Clear existing if requested
        if clear_existing:
            print("Clearing existing product embeddings...")
            await self._store.delete(delete_all=True)
        
        # Get all products
        products = await product_service.get_all_products_raw()
        total_products = len(products)
        
        if total_products == 0:
            return {
                "status": "completed",
                "total_products": 0,
                "indexed": 0,
                "errors": 0,
                "duration_seconds": 0,
            }
        
        print(f"Indexing {total_products} products...")
        
        indexed = 0
        errors = 0
        
        # Process in batches
        for i in range(0, total_products, batch_size):
            batch = products[i:i + batch_size]
            
            # Generate texts for embedding
            texts = [self._product_to_text(p) for p in batch]
            
            try:
                # Generate embeddings
                embeddings = await self._embeddings.embed_batch(texts)
                
                # Prepare vectors for Pinecone
                vectors = []
                for product, embedding in zip(batch, embeddings):
                    vectors.append({
                        "id": str(product.id),
                        "values": embedding,
                        "metadata": self._product_to_metadata(product),
                    })
                
                # Upsert to Pinecone
                await self._store.upsert(vectors)
                indexed += len(vectors)
                
                print(f"Indexed batch {i // batch_size + 1}/{(total_products + batch_size - 1) // batch_size}: {len(vectors)} products")
                
            except Exception as e:
                print(f"Error indexing batch {i // batch_size + 1}: {e}")
                errors += len(batch)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "status": "completed",
            "total_products": total_products,
            "indexed": indexed,
            "errors": errors,
            "duration_seconds": round(duration, 2),
            "products_per_second": round(indexed / duration, 2) if duration > 0 else 0,
        }
    
    async def index_product(self, product_id: str) -> Dict[str, Any]:
        """
        Index or update a single product.
        
        Args:
            product_id: Product ID to index
            
        Returns:
            Indexing result
        """
        from bson import ObjectId
        
        try:
            oid = ObjectId(product_id)
        except Exception:
            raise ValueError(f"Invalid product ID: {product_id}")
        
        product = await Product.get(oid)
        if not product:
            raise ValueError(f"Product not found: {product_id}")
        
        # Generate embedding
        text = self._product_to_text(product)
        embedding = await self._embeddings.embed(text)
        
        # Prepare vector
        vector = {
            "id": str(product.id),
            "values": embedding,
            "metadata": self._product_to_metadata(product),
        }
        
        # Upsert to Pinecone
        await self._store.upsert([vector])
        
        return {
            "status": "indexed",
            "product_id": product_id,
            "product_name": product.name,
        }
    
    async def index_products_batch(self, product_ids: List[str]) -> Dict[str, Any]:
        """
        Index multiple products by ID.
        
        Args:
            product_ids: List of product IDs to index
            
        Returns:
            Batch indexing result
        """
        from bson import ObjectId
        
        indexed = 0
        errors = 0
        error_details = []
        
        products = []
        for pid in product_ids:
            try:
                oid = ObjectId(pid)
                product = await Product.get(oid)
                if product:
                    products.append(product)
                else:
                    errors += 1
                    error_details.append({"id": pid, "error": "Not found"})
            except Exception as e:
                errors += 1
                error_details.append({"id": pid, "error": str(e)})
        
        if products:
            # Generate embeddings
            texts = [self._product_to_text(p) for p in products]
            embeddings = await self._embeddings.embed_batch(texts)
            
            # Prepare vectors
            vectors = []
            for product, embedding in zip(products, embeddings):
                vectors.append({
                    "id": str(product.id),
                    "values": embedding,
                    "metadata": self._product_to_metadata(product),
                })
            
            # Upsert to Pinecone
            await self._store.upsert(vectors)
            indexed = len(vectors)
        
        return {
            "status": "completed",
            "requested": len(product_ids),
            "indexed": indexed,
            "errors": errors,
            "error_details": error_details if error_details else None,
        }
    
    async def remove_product(self, product_id: str) -> Dict[str, Any]:
        """
        Remove a product from the vector index.
        
        Args:
            product_id: Product ID to remove
            
        Returns:
            Removal result
        """
        await self._store.delete(ids=[product_id])
        
        return {
            "status": "removed",
            "product_id": product_id,
        }
    
    async def remove_products_batch(self, product_ids: List[str]) -> Dict[str, Any]:
        """
        Remove multiple products from the vector index.
        
        Args:
            product_ids: List of product IDs to remove
            
        Returns:
            Batch removal result
        """
        await self._store.delete(ids=product_ids)
        
        return {
            "status": "removed",
            "count": len(product_ids),
        }
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get indexing statistics.
        
        Returns:
            Index stats including vector count
        """
        # Get Pinecone stats
        pinecone_stats = await self._store.get_stats()
        
        # Get MongoDB product count
        products = await product_service.get_all_products_raw()
        mongo_count = len(products)
        
        # Get indexed count for our namespace
        namespace = settings.PINECONE_NAMESPACE
        indexed_count = pinecone_stats.get("namespaces", {}).get(namespace, {}).get("vector_count", 0)
        
        return {
            "mongodb_products": mongo_count,
            "indexed_products": indexed_count,
            "sync_status": "synced" if mongo_count == indexed_count else "out_of_sync",
            "missing_from_index": mongo_count - indexed_count,
            "pinecone_stats": pinecone_stats,
        }
    
    async def sync_index(self) -> Dict[str, Any]:
        """
        Sync index with MongoDB - add missing, remove orphaned.
        
        Returns:
            Sync results
        """
        # Get all product IDs from MongoDB
        products = await product_service.get_all_products_raw()
        mongo_ids = {str(p.id) for p in products}
        
        # Get all indexed IDs from Pinecone (by fetching stats)
        # Note: Pinecone doesn't have a list all IDs feature, so we'd need to
        # re-index missing products. For a full sync, use index_all_products.
        
        # For now, just ensure all MongoDB products are indexed
        result = await self.index_all_products(clear_existing=False)
        
        return {
            "status": "synced",
            "mongo_products": len(mongo_ids),
            "indexing_result": result,
        }


# Singleton instance
product_indexer = ProductIndexer()
