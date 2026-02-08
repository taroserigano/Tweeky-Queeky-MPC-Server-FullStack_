"""
Product Service - Core product operations

Handles all product-related business logic including CRUD, search, and recommendations.
Used by both REST API endpoints and MCP tools.
"""

import re
from typing import Optional, List, Dict, Any
from bson import ObjectId

from models.product import Product, Review


class ProductService:
    """Service class for product operations"""
    
    @staticmethod
    def _cap_limit(limit: int, max_limit: int = 50) -> int:
        """Cap the limit to prevent excessive queries"""
        return max(1, min(limit, max_limit))
    
    @staticmethod
    def product_to_summary(product: Product) -> Dict[str, Any]:
        """Convert product to summary dict (for listings)"""
        return {
            "id": str(product.id),
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "price": product.price,
            "rating": product.rating,
            "num_reviews": product.num_reviews,
            "count_in_stock": product.count_in_stock,
            "image": product.image,
        }
    
    @staticmethod
    def product_to_detail(product: Product) -> Dict[str, Any]:
        """Convert product to detailed dict (for single product view)"""
        return {
            **ProductService.product_to_summary(product),
            "description": product.description,
            "detailed_description": product.detailed_description,
            "specifications": product.specifications,
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        }
    
    @staticmethod
    def review_to_dict(review: Review) -> Dict[str, Any]:
        """Convert review to dict"""
        return {
            "id": str(review.id),
            "name": review.name,
            "rating": review.rating,
            "comment": review.comment,
            "user": str(review.user),
            "created_at": review.created_at.isoformat() if review.created_at else None,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # READ OPERATIONS
    # ──────────────────────────────────────────────────────────────────────────

    async def list_products(
        self,
        limit: int = 10,
        skip: int = 0,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "-created_at",
    ) -> List[Dict[str, Any]]:
        """
        List products with optional filters and pagination.
        
        Args:
            limit: Maximum products to return (1-50)
            skip: Number of products to skip (pagination)
            category: Filter by category
            min_price: Minimum price filter
            max_price: Maximum price filter
            sort_by: Sort field (prefix with - for descending)
            
        Returns:
            List of product summary dicts
        """
        limit = self._cap_limit(limit)
        
        query: Dict[str, Any] = {}
        if category:
            query["category"] = {"$regex": f"^{re.escape(category)}$", "$options": "i"}
        if min_price is not None or max_price is not None:
            price_query: Dict[str, Any] = {}
            if min_price is not None:
                price_query["$gte"] = min_price
            if max_price is not None:
                price_query["$lte"] = max_price
            query["price"] = price_query
        
        products = await Product.find(query).sort(sort_by).skip(skip).limit(limit).to_list()
        return [self.product_to_summary(p) for p in products]

    async def get_product(self, product_id: str, include_reviews: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a single product by ID.
        
        Args:
            product_id: The product's ObjectId string
            include_reviews: Whether to fetch linked reviews
            
        Returns:
            Product detail dict or None if not found
        """
        try:
            oid = ObjectId(product_id)
        except Exception:
            raise ValueError(f"Invalid product ID format: {product_id}")
        
        product = await Product.get(oid, fetch_links=include_reviews)
        if not product:
            return None
        
        result = self.product_to_detail(product)
        
        if include_reviews and product.reviews:
            result["reviews"] = [self.review_to_dict(r) for r in product.reviews]
        
        return result

    async def search_products(
        self,
        query: str,
        limit: int = 10,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search products by text in name, brand, or category (regex-based).
        
        Args:
            query: Search text
            limit: Maximum results
            fields: Fields to search (default: name, brand, category)
            
        Returns:
            List of matching product summaries
        """
        limit = self._cap_limit(limit)
        fields = fields or ["name", "brand", "category"]
        
        escaped_query = re.escape(query)
        search_pattern = {"$regex": escaped_query, "$options": "i"}
        
        mongo_query = {"$or": [{field: search_pattern} for field in fields]}
        
        products = await Product.find(mongo_query).limit(limit).to_list()
        return [self.product_to_summary(p) for p in products]

    async def get_top_products(
        self,
        limit: int = 5,
        sort_by: str = "rating",
    ) -> List[Dict[str, Any]]:
        """
        Get top products by rating or review count.
        
        Args:
            limit: Number of products to return
            sort_by: 'rating' or 'reviews'
            
        Returns:
            List of top product summaries
        """
        limit = self._cap_limit(limit, max_limit=20)
        
        if sort_by == "reviews":
            sort_field = "-numReviews"
        else:
            sort_field = "-rating"
        
        products = await Product.find().sort(sort_field).limit(limit).to_list()
        return [self.product_to_summary(p) for p in products]

    async def get_product_reviews(self, product_id: str) -> List[Dict[str, Any]]:
        """
        Get all reviews for a product.
        
        Args:
            product_id: The product's ObjectId string
            
        Returns:
            List of review dicts
        """
        try:
            oid = ObjectId(product_id)
        except Exception:
            raise ValueError(f"Invalid product ID format: {product_id}")
        
        product = await Product.get(oid, fetch_links=True)
        if not product:
            raise ValueError("Product not found")
        
        return [self.review_to_dict(r) for r in (product.reviews or [])]

    async def get_products_by_ids(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple products by their IDs.
        
        Args:
            product_ids: List of product ObjectId strings
            
        Returns:
            List of product summaries (in same order as input, missing products skipped)
        """
        results = []
        for pid in product_ids:
            try:
                oid = ObjectId(pid)
                product = await Product.get(oid)
                if product:
                    results.append(self.product_to_summary(product))
            except Exception:
                continue
        return results

    async def get_all_products_raw(self) -> List[Product]:
        """
        Get all products as raw Beanie documents.
        Used internally for bulk operations like indexing.
        
        Returns:
            List of Product documents
        """
        return await Product.find().to_list()

    # ──────────────────────────────────────────────────────────────────────────
    # COMPARISON & ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    async def compare_products(self, product_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple products side by side.
        
        Args:
            product_ids: List of 2-5 product IDs to compare
            
        Returns:
            Comparison data with products and insights
        """
        if len(product_ids) < 2:
            raise ValueError("Provide at least 2 product IDs to compare")
        
        product_ids = product_ids[:5]  # Max 5 products
        
        products = []
        for pid in product_ids:
            try:
                p = await Product.get(ObjectId(pid))
                if p:
                    products.append(p)
            except Exception:
                continue
        
        if len(products) < 2:
            raise ValueError("Could not find enough products to compare")
        
        comparison = [self.product_to_summary(p) for p in products]
        
        prices = [c["price"] for c in comparison]
        ratings = [c["rating"] for c in comparison]
        
        return {
            "products": comparison,
            "insights": {
                "lowest_price": min(prices),
                "highest_price": max(prices),
                "highest_rated": max(ratings),
                "best_value_id": comparison[prices.index(min(prices))]["id"],
                "top_rated_id": comparison[ratings.index(max(ratings))]["id"],
            },
        }


# Singleton instance for easy import
product_service = ProductService()
