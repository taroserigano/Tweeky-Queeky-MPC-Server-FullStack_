"""
Catalog Service - Catalog-wide operations and analytics

Handles catalog statistics, category analysis, inventory management, and pricing insights.
Used by both REST API endpoints and MCP tools.
"""

from typing import Optional, List, Dict, Any
from bson import ObjectId

from models.product import Product, Review


class CatalogService:
    """Service class for catalog-wide operations"""

    # ──────────────────────────────────────────────────────────────────────────
    # CATALOG STATISTICS
    # ──────────────────────────────────────────────────────────────────────────

    async def get_catalog_stats(self) -> Dict[str, Any]:
        """
        Get overall catalog statistics.
        
        Returns:
            Dict with total products, reviews, and category counts
        """
        total_products = await Product.find().count()
        total_reviews = await Review.find().count()
        
        products = await Product.find().to_list()
        categories = list(set(p.category for p in products))
        
        category_counts: Dict[str, int] = {}
        for category in categories:
            category_counts[category] = sum(1 for p in products if p.category == category)
        
        return {
            "total_products": total_products,
            "total_reviews": total_reviews,
            "total_categories": len(categories),
            "categories": category_counts,
        }

    async def get_categories(self) -> List[str]:
        """
        Get list of all unique categories.
        
        Returns:
            List of category names
        """
        products = await Product.find().to_list()
        return sorted(list(set(p.category for p in products)))

    async def get_category_price_summary(self) -> List[Dict[str, Any]]:
        """
        Get price statistics per category.
        
        Returns:
            List of category summaries with min/max/avg price
        """
        products = await Product.find().to_list()
        
        by_cat: Dict[str, List[float]] = {}
        for p in products:
            by_cat.setdefault(p.category, []).append(p.price)
        
        summaries = []
        for cat, prices in by_cat.items():
            summaries.append({
                "category": cat,
                "count": len(prices),
                "min_price": round(min(prices), 2),
                "max_price": round(max(prices), 2),
                "avg_price": round(sum(prices) / len(prices), 2),
            })
        
        return sorted(summaries, key=lambda x: x["category"])

    # ──────────────────────────────────────────────────────────────────────────
    # INVENTORY MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────────

    async def get_low_stock_products(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """
        Get products with stock at or below threshold.
        
        Args:
            threshold: Stock level threshold (default 5)
            
        Returns:
            List of low-stock product details
        """
        products = await Product.find({"countInStock": {"$lte": threshold}}).to_list()
        
        return [
            {
                "id": str(p.id),
                "name": p.name,
                "brand": p.brand,
                "category": p.category,
                "count_in_stock": p.count_in_stock,
                "price": p.price,
            }
            for p in products
        ]

    async def get_out_of_stock_products(self) -> List[Dict[str, Any]]:
        """
        Get products with zero stock.
        
        Returns:
            List of out-of-stock product details
        """
        return await self.get_low_stock_products(threshold=0)

    async def get_inventory_value(self) -> Dict[str, Any]:
        """
        Calculate total inventory value (price * stock).
        
        Returns:
            Total value and breakdown by category
        """
        products = await Product.find().to_list()
        
        total = 0.0
        by_cat: Dict[str, float] = {}
        
        for p in products:
            value = p.price * p.count_in_stock
            total += value
            by_cat[p.category] = by_cat.get(p.category, 0.0) + value
        
        return {
            "total_inventory_value": round(total, 2),
            "by_category": {k: round(v, 2) for k, v in sorted(by_cat.items())},
        }

    # ──────────────────────────────────────────────────────────────────────────
    # PRICE ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    async def get_price_outliers(self, std_multiplier: float = 1.5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find products whose price deviates significantly from category average.
        
        Args:
            std_multiplier: How many standard deviations to consider an outlier
            
        Returns:
            Dict of outliers grouped by category
        """
        products = await Product.find().to_list()
        
        by_cat: Dict[str, List[Product]] = {}
        for p in products:
            by_cat.setdefault(p.category, []).append(p)
        
        outliers: Dict[str, List[Dict[str, Any]]] = {}
        
        for cat, items in by_cat.items():
            prices = [p.price for p in items]
            if len(prices) < 2:
                continue
            
            avg = sum(prices) / len(prices)
            variance = sum((x - avg) ** 2 for x in prices) / len(prices)
            std = variance ** 0.5
            
            if std == 0:
                continue
            
            for p in items:
                deviation = p.price - avg
                if abs(deviation) > std_multiplier * std:
                    outliers.setdefault(cat, []).append({
                        "id": str(p.id),
                        "name": p.name,
                        "price": p.price,
                        "category_avg": round(avg, 2),
                        "deviation": round(deviation, 2),
                        "is_above_avg": deviation > 0,
                    })
        
        return outliers

    async def get_price_distribution(self, bucket_size: float = 50.0) -> Dict[str, Any]:
        """
        Get price distribution across all products.
        
        Args:
            bucket_size: Size of each price bucket
            
        Returns:
            Distribution data with buckets and counts
        """
        products = await Product.find().to_list()
        if not products:
            return {"buckets": [], "total": 0}
        
        prices = [p.price for p in products]
        min_price = min(prices)
        max_price = max(prices)
        
        buckets: Dict[str, int] = {}
        for price in prices:
            bucket_start = int(price // bucket_size) * bucket_size
            bucket_label = f"${bucket_start:.0f}-${bucket_start + bucket_size:.0f}"
            buckets[bucket_label] = buckets.get(bucket_label, 0) + 1
        
        return {
            "buckets": [{"range": k, "count": v} for k, v in sorted(buckets.items())],
            "total": len(products),
            "min_price": round(min_price, 2),
            "max_price": round(max_price, 2),
            "avg_price": round(sum(prices) / len(prices), 2),
        }


# Singleton instance for easy import
catalog_service = CatalogService()
