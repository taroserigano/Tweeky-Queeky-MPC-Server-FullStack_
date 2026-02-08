"""
User History Tracking - Tools for personalization

Tracks user behavior for personalized recommendations:
- Purchase history
- Browsing history
- Product interactions
- Preferences
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from collections import defaultdict, Counter

from config.settings import settings
from config.database import get_sync_db  # Use singleton connection pool


def _get_sync_db():
    """Get synchronous MongoDB connection (reuses connection pool)."""
    return get_sync_db()


def _product_to_dict(product: dict) -> dict:
    """Convert MongoDB product to dict."""
    oid = product.get("_id")
    fallback_sku = f"SKU-{str(oid).upper()}" if oid else ""
    return {
        "id": str(product.get("_id", "")),
        "sku": product.get("sku") or fallback_sku,
        "name": product.get("name", ""),
        "brand": product.get("brand", ""),
        "category": product.get("category", ""),
        "description": product.get("description", ""),
        "detailed_description": product.get("detailedDescription", ""),
        "specifications": product.get("specifications", {}),
        "price": product.get("price", 0),
        "rating": product.get("rating", 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# USER HISTORY TRACKING
# ─────────────────────────────────────────────────────────────────────────────

def get_user_purchase_history(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's past purchases."""
    db = _get_sync_db()
    
    try:
        user_oid = ObjectId(user_id)
    except:
        return []
    
    # Get user's orders
    orders = list(
        db.orders.find({"user": user_oid})
        .sort("createdAt", -1)
        .limit(limit)
    )
    
    if not orders:
        return []
    
    # Extract products from orders
    purchased_products = []
    for order in orders:
        for item in order.get("orderItems", []):
            product_id = item.get("product")
            if product_id:
                product = db.products.find_one({"_id": product_id})
                if product:
                    purchased_products.append({
                        **_product_to_dict(product),
                        "order_date": order.get("createdAt"),
                        "quantity": item.get("qty", 1),
                        "price_paid": item.get("price", 0),
                    })
    
    return purchased_products


def get_user_preferences_from_history(user_id: str) -> Dict[str, Any]:
    """Analyze user's purchase history to extract preferences."""
    purchases = get_user_purchase_history(user_id, limit=50)
    
    if not purchases:
        return {
            "favorite_categories": [],
            "favorite_brands": [],
            "avg_price_range": {"min": 0, "max": 1000},
            "total_purchases": 0,
        }
    
    # Analyze categories
    categories = Counter([p["category"] for p in purchases if p.get("category")])
    favorite_categories = [cat for cat, _ in categories.most_common(3)]
    
    # Analyze brands
    brands = Counter([p["brand"] for p in purchases if p.get("brand")])
    favorite_brands = [brand for brand, _ in brands.most_common(3)]
    
    # Analyze price range
    prices = [p["price_paid"] for p in purchases if p.get("price_paid", 0) > 0]
    if prices:
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
    else:
        avg_price = min_price = max_price = 0
    
    return {
        "favorite_categories": favorite_categories,
        "favorite_brands": favorite_brands,
        "avg_price_range": {
            "min": min_price,
            "max": max_price,
            "average": avg_price,
        },
        "total_purchases": len(purchases),
        "recent_purchases": purchases[:5],
    }


def get_trending_products(category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Get trending products based on recent orders."""
    db = _get_sync_db()
    
    # Get orders from last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_orders = list(
        db.orders.find({"createdAt": {"$gte": thirty_days_ago}})
    )
    
    # Count product purchases
    product_counts = defaultdict(int)
    for order in recent_orders:
        for item in order.get("orderItems", []):
            product_id = str(item.get("product", ""))
            if product_id:
                product_counts[product_id] += item.get("qty", 1)
    
    # Get top products
    top_product_ids = [pid for pid, _ in sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:limit * 2]]
    
    # Fetch product details
    products = []
    for pid_str in top_product_ids:
        try:
            pid = ObjectId(pid_str)
            product = db.products.find_one({"_id": pid})
            if product:
                if category and product.get("category", "").lower() != category.lower():
                    continue
                products.append({
                    **_product_to_dict(product),
                    "purchase_count": product_counts[pid_str],
                })
                if len(products) >= limit:
                    break
        except:
            continue
    
    return products


def get_similar_products_by_category(product_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get products in the same category as the given product."""
    db = _get_sync_db()
    
    try:
        product = db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            return []
        
        category = product.get("category", "")
        if not category:
            return []
        
        # Find similar products in same category
        similar = list(
            db.products.find({
                "_id": {"$ne": ObjectId(product_id)},
                "category": category,
                "rating": {"$gte": 3.5},  # Only good products
            })
            .sort("rating", -1)
            .limit(limit)
        )
        
        return [_product_to_dict(p) for p in similar]
    except:
        return []


def get_products_frequently_bought_together(product_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get products frequently purchased with this product."""
    db = _get_sync_db()
    
    try:
        pid = ObjectId(product_id)
    except:
        return []
    
    # Find orders containing this product
    orders_with_product = list(
        db.orders.find({
            "orderItems.product": pid
        })
    )
    
    # Count co-purchased products
    copurchased_counts = defaultdict(int)
    for order in orders_with_product:
        for item in order.get("orderItems", []):
            item_product_id = item.get("product")
            if item_product_id and item_product_id != pid:
                copurchased_counts[str(item_product_id)] += 1
    
    # Get top co-purchased products
    top_products = []
    for pid_str, count in sorted(copurchased_counts.items(), key=lambda x: x[1], reverse=True)[:limit]:
        try:
            product = db.products.find_one({"_id": ObjectId(pid_str)})
            if product:
                top_products.append({
                    **_product_to_dict(product),
                    "copurchase_count": count,
                })
        except:
            continue
    
    return top_products


def get_best_deals(category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Get products with best value (high rating, good price)."""
    db = _get_sync_db()
    
    query = {
        "rating": {"$gte": 4.0},
        "countInStock": {"$gt": 0},
    }
    
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    
    products = list(
        db.products.find(query)
        .sort([("rating", -1), ("price", 1)])
        .limit(limit)
    )
    
    return [_product_to_dict(p) for p in products]


def get_new_arrivals(category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Get newest products in catalog."""
    db = _get_sync_db()
    
    query = {"countInStock": {"$gt": 0}}
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    
    products = list(
        db.products.find(query)
        .sort("createdAt", -1)
        .limit(limit)
    )
    
    return [_product_to_dict(p) for p in products]
