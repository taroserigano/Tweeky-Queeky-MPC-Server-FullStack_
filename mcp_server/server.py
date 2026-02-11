import asyncio
import json
import os
from typing import Optional, List, Dict, Any

from beanie import init_beanie
from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from mcp.server.fastmcp import FastMCP
from openai import AsyncOpenAI

from models.product import Product, Review
from models.audit_log import AuditLog
from models.user import User
from models.order import Order

# Load .env from project root
load_dotenv()

mcp = FastMCP("Tweeky Queeky Shop MCP")

# OpenAI client (lazy init)
_openai_client: Optional[AsyncOpenAI] = None


def _get_openai() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPEN_AI")
        if not api_key:
            raise RuntimeError("OPEN_AI env var not set")
        _openai_client = AsyncOpenAI(api_key=api_key)
    return _openai_client

_db_initialized = False
_db_lock = asyncio.Lock()
_current_loop = None


def _cap_limit(limit: int) -> int:
    return max(1, min(limit, 50))


def _product_summary(product: Product) -> Dict[str, Any]:
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


def _product_detail(product: Product) -> Dict[str, Any]:
    return {
        **_product_summary(product),
        "description": product.description,
        "detailed_description": product.detailed_description,
        "specifications": product.specifications,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
    }


async def _ensure_db() -> None:
    global _db_initialized, _current_loop
    
    # Check if we're in a different event loop (e.g., new test)
    try:
        current = asyncio.get_running_loop()
    except RuntimeError:
        current = None
    
    if _db_initialized and _current_loop is current:
        return

    async with _db_lock:
        # Re-check inside lock
        try:
            current = asyncio.get_running_loop()
        except RuntimeError:
            current = None
            
        if _db_initialized and _current_loop is current:
            return

        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/tweekyqueeky")
        client = AsyncIOMotorClient(mongo_uri)
        await init_beanie(
            database=client.get_default_database(),
            document_models=[Product, Review, AuditLog, User, Order]
        )
        _db_initialized = True
        _current_loop = current


@mcp.tool()
async def list_products(
    limit: int = 10,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    List products with optional filters.
    """
    await _ensure_db()
    limit = _cap_limit(limit)

    query: Dict[str, Any] = {}
    if category:
        query["category"] = category
    if min_price is not None or max_price is not None:
        price_query: Dict[str, Any] = {}
        if min_price is not None:
            price_query["$gte"] = min_price
        if max_price is not None:
            price_query["$lte"] = max_price
        query["price"] = price_query

    products = await Product.find(query).limit(limit).to_list()
    return [_product_summary(product) for product in products]


@mcp.tool()
async def search_products(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search products by name, brand, or category.
    """
    import re
    await _ensure_db()
    limit = _cap_limit(limit)

    # Escape regex special characters for safe search
    escaped_query = re.escape(query)
    search = {"$regex": escaped_query, "$options": "i"}
    mongo_query = {
        "$or": [
            {"name": search},
            {"brand": search},
            {"category": search},
        ]
    }

    products = await Product.find(mongo_query).limit(limit).to_list()
    return [_product_summary(product) for product in products]


@mcp.tool()
async def get_product(product_id: str) -> Dict[str, Any]:
    """
    Get product details by id.
    """
    await _ensure_db()

    try:
        object_id = ObjectId(product_id)
    except Exception as exc:
        raise ValueError("Invalid product id") from exc

    product = await Product.get(object_id)
    if not product:
        raise ValueError("Product not found")

    return _product_detail(product)


@mcp.tool()
async def get_top_products(limit: int = 3) -> List[Dict[str, Any]]:
    """
    Get top-rated products.
    """
    await _ensure_db()
    limit = _cap_limit(limit)

    products = await Product.find().sort("-rating").limit(limit).to_list()
    return [_product_summary(product) for product in products]


@mcp.tool()
async def get_product_reviews(product_id: str) -> List[Dict[str, Any]]:
    """
    Get reviews for a product.
    """
    await _ensure_db()

    try:
        object_id = ObjectId(product_id)
    except Exception as exc:
        raise ValueError("Invalid product id") from exc

    product = await Product.get(object_id, fetch_links=True)
    if not product:
        raise ValueError("Product not found")

    reviews = []
    for review in product.reviews or []:
        reviews.append(
            {
                "id": str(review.id),
                "name": review.name,
                "rating": review.rating,
                "comment": review.comment,
                "user": str(review.user),
                "created_at": review.created_at.isoformat(),
            }
        )

    return reviews


@mcp.tool()
async def catalog_stats() -> Dict[str, Any]:
    """
    Return summary stats for the product catalog.
    """
    await _ensure_db()

    total_products = await Product.find().count()
    total_reviews = await Review.find().count()

    # Get distinct categories by fetching all products and extracting unique categories
    products = await Product.find().to_list()
    categories = list(set(p.category for p in products))
    category_counts: Dict[str, int] = {}
    for category in categories:
        category_counts[category] = await Product.find({"category": category}).count()

    return {
        "total_products": total_products,
        "total_reviews": total_reviews,
        "categories": category_counts,
    }


# ──────────────────────────────────────────────────────────────────────────────
# CATALOG INTELLIGENCE TOOLS
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def low_stock_report(threshold: int = 5) -> List[Dict[str, Any]]:
    """
    Get products with stock at or below the given threshold.
    Useful for inventory alerts.
    """
    await _ensure_db()
    # Use "countInStock" - the MongoDB field name (camelCase alias)
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


@mcp.tool()
async def price_outliers(std_multiplier: float = 1.5) -> Dict[str, Any]:
    """
    Find products whose price deviates significantly from category average.
    Returns outliers grouped by category.
    """
    await _ensure_db()
    products = await Product.find().to_list()

    # Group by category
    by_cat: Dict[str, List[Product]] = {}
    for p in products:
        by_cat.setdefault(p.category, []).append(p)

    outliers: Dict[str, List[Dict[str, Any]]] = {}
    for cat, items in by_cat.items():
        prices = [p.price for p in items]
        if len(prices) < 2:
            continue
        avg = sum(prices) / len(prices)
        std = (sum((x - avg) ** 2 for x in prices) / len(prices)) ** 0.5
        if std == 0:
            continue
        for p in items:
            if abs(p.price - avg) > std_multiplier * std:
                outliers.setdefault(cat, []).append(
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "price": p.price,
                        "category_avg": round(avg, 2),
                        "deviation": round(p.price - avg, 2),
                    }
                )
    return outliers


@mcp.tool()
async def category_price_summary() -> List[Dict[str, Any]]:
    """
    Return min/max/avg price and product count per category.
    """
    await _ensure_db()
    products = await Product.find().to_list()

    by_cat: Dict[str, List[float]] = {}
    for p in products:
        by_cat.setdefault(p.category, []).append(p.price)

    summaries = []
    for cat, prices in by_cat.items():
        summaries.append(
            {
                "category": cat,
                "count": len(prices),
                "min_price": round(min(prices), 2),
                "max_price": round(max(prices), 2),
                "avg_price": round(sum(prices) / len(prices), 2),
            }
        )
    return sorted(summaries, key=lambda x: x["category"])


@mcp.tool()
async def reviews_sentiment_summary(product_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Basic sentiment summary of reviews (positive/neutral/negative keyword counts).
    If product_id is given, analyzes that product's reviews; otherwise all reviews.
    """
    await _ensure_db()

    positive_words = {"great", "love", "excellent", "amazing", "good", "best", "perfect", "awesome", "fantastic", "happy"}
    negative_words = {"bad", "poor", "terrible", "worst", "hate", "broken", "waste", "disappointed", "awful", "useless"}

    if product_id:
        try:
            oid = ObjectId(product_id)
        except Exception:
            raise ValueError("Invalid product id")
        product = await Product.get(oid, fetch_links=True)
        if not product:
            raise ValueError("Product not found")
        reviews = product.reviews or []
    else:
        reviews = await Review.find().to_list()

    pos, neg, neu = 0, 0, 0
    for r in reviews:
        words = set(r.comment.lower().split())
        has_pos = bool(words & positive_words)
        has_neg = bool(words & negative_words)
        if has_pos and not has_neg:
            pos += 1
        elif has_neg and not has_pos:
            neg += 1
        else:
            neu += 1

    return {
        "total_reviews": len(reviews),
        "positive": pos,
        "neutral": neu,
        "negative": neg,
    }


@mcp.tool()
async def inventory_value() -> Dict[str, Any]:
    """
    Calculate total inventory value (price * stock) overall and by category.
    """
    await _ensure_db()
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


# ──────────────────────────────────────────────────────────────────────────────
# SHOPPING ASSISTANT TOOLS (AI-powered)
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def recommend_products(
    preferences: str,
    budget: Optional[float] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    AI-powered product recommendations based on user preferences.
    `preferences` is a natural language description (e.g. "looking for music gear under $300").
    """
    await _ensure_db()
    limit = _cap_limit(limit)

    # Fetch catalog snapshot for context
    products = await Product.find().to_list()
    if not products:
        return []

    catalog_text = "\n".join(
        f"- ID:{p.id} | {p.name} | {p.brand} | {p.category} | ${p.price} | stock:{p.count_in_stock} | rating:{p.rating}"
        for p in products
    )

    budget_hint = f"User budget: ${budget}" if budget else "No specific budget."

    prompt = f"""You are a shopping assistant for an e-commerce store.
Given the product catalog and user preferences, recommend up to {limit} products.
Return ONLY a JSON array of product IDs (strings), most relevant first. No explanation.

Catalog:
{catalog_text}

User preferences: {preferences}
{budget_hint}
"""

    client = _get_openai()
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    raw = resp.choices[0].message.content.strip()

    # Parse JSON array of IDs
    try:
        ids = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: extract IDs with regex
        import re
        ids = re.findall(r"[0-9a-fA-F]{24}", raw)

    # Fetch recommended products
    results = []
    for pid in ids[:limit]:
        try:
            p = await Product.get(ObjectId(pid))
            if p:
                results.append(_product_summary(p))
        except Exception:
            continue
    return results


@mcp.tool()
async def compare_products(product_ids: List[str]) -> Dict[str, Any]:
    """
    Compare multiple products side by side.
    Returns a comparison table with key attributes.
    """
    await _ensure_db()
    if len(product_ids) < 2:
        raise ValueError("Provide at least 2 product IDs to compare")
    if len(product_ids) > 5:
        product_ids = product_ids[:5]

    products = []
    for pid in product_ids:
        try:
            p = await Product.get(ObjectId(pid), fetch_links=True)
            if p:
                products.append(p)
        except Exception:
            continue

    if len(products) < 2:
        raise ValueError("Could not find enough products to compare")

    comparison = []
    for p in products:
        comparison.append(
            {
                "id": str(p.id),
                "name": p.name,
                "brand": p.brand,
                "category": p.category,
                "price": p.price,
                "rating": p.rating,
                "num_reviews": p.num_reviews,
                "count_in_stock": p.count_in_stock,
            }
        )

    # Highlight best values
    prices = [c["price"] for c in comparison]
    ratings = [c["rating"] for c in comparison]

    return {
        "products": comparison,
        "insights": {
            "lowest_price": min(prices),
            "highest_rated": max(ratings),
            "best_value_id": comparison[prices.index(min(prices))]["id"],
            "top_rated_id": comparison[ratings.index(max(ratings))]["id"],
        },
    }


@mcp.tool()
async def build_cart_suggestion(
    goal: str,
    budget: float,
) -> Dict[str, Any]:
    """
    AI builds a suggested cart that fits within a budget for a given goal.
    Returns product list and total price.
    """
    await _ensure_db()
    # Use "countInStock" - the MongoDB field name (camelCase alias)
    products = await Product.find({"countInStock": {"$gte": 1}}).to_list()
    if not products:
        return {"items": [], "total": 0, "budget": budget, "remaining": budget, "message": "No products in stock"}

    catalog_text = "\n".join(
        f"- ID:{p.id} | {p.name} | ${p.price}"
        for p in products
    )

    prompt = f"""You are a shopping assistant. The user wants: "{goal}"
Budget: ${budget}

Pick products that fit the goal and stay within budget. Maximize value.
Return ONLY a JSON array of objects: [{{"id": "...", "qty": 1}}, ...]
No explanation.

Catalog:
{catalog_text}
"""

    client = _get_openai()
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    raw = resp.choices[0].message.content.strip()

    try:
        cart_items = json.loads(raw)
    except json.JSONDecodeError:
        return {"items": [], "total": 0, "budget": budget, "remaining": budget, "message": "Could not parse AI response"}

    # Build cart with real product data
    items = []
    total = 0.0
    for item in cart_items:
        pid = item.get("id")
        qty = item.get("qty", 1)
        try:
            p = await Product.get(ObjectId(pid))
            if p and p.count_in_stock >= qty:
                item_total = p.price * qty
                if total + item_total <= budget:
                    items.append(
                        {
                            "id": str(p.id),
                            "name": p.name,
                            "price": p.price,
                            "qty": qty,
                            "subtotal": round(item_total, 2),
                        }
                    )
                    total += item_total
        except Exception:
            continue

    return {
        "items": items,
        "total": round(total, 2),
        "budget": budget,
        "remaining": round(budget - total, 2),
    }


@mcp.tool()
async def explain_product(product_id: str) -> Dict[str, Any]:
    """
    AI generates a concise, friendly summary of a product based on its details and reviews.
    """
    await _ensure_db()

    try:
        oid = ObjectId(product_id)
    except Exception:
        raise ValueError("Invalid product id")

    product = await Product.get(oid, fetch_links=True)
    if not product:
        raise ValueError("Product not found")

    reviews_text = ""
    if product.reviews:
        reviews_text = "\n".join(
            f"- {r.rating}/5: {r.comment}" for r in product.reviews[:10]
        )
    else:
        reviews_text = "No reviews yet."

    prompt = f"""Write a 2-3 sentence friendly summary for a shopper about this product.
Highlight key benefits and mention review sentiment if available.

Product: {product.name}
Brand: {product.brand}
Category: {product.category}
Price: ${product.price}
Description: {product.description}
Rating: {product.rating}/5 ({product.num_reviews} reviews)

Recent reviews:
{reviews_text}
"""

    client = _get_openai()
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    summary = resp.choices[0].message.content.strip()

    return {
        "product_id": product_id,
        "name": product.name,
        "ai_summary": summary,
    }


@mcp.tool()
async def answer_product_question(product_id: str, question: str) -> Dict[str, Any]:
    """
    AI answers a customer question about a specific product using its data and reviews.
    """
    await _ensure_db()

    try:
        oid = ObjectId(product_id)
    except Exception:
        raise ValueError("Invalid product id")

    product = await Product.get(oid, fetch_links=True)
    if not product:
        raise ValueError("Product not found")

    reviews_text = ""
    if product.reviews:
        reviews_text = "\n".join(
            f"- {r.name} ({r.rating}/5): {r.comment}" for r in product.reviews[:10]
        )

    prompt = f"""You are a helpful shopping assistant. Answer the customer's question about this product.
Use only the information provided. If you don't know, say so.

Product: {product.name}
Brand: {product.brand}
Category: {product.category}
Price: ${product.price}
In Stock: {product.count_in_stock}
Description: {product.description}
Rating: {product.rating}/5 ({product.num_reviews} reviews)

Customer reviews:
{reviews_text if reviews_text else "No reviews yet."}

Customer question: {question}
"""

    client = _get_openai()
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    answer = resp.choices[0].message.content.strip()

    return {
        "product_id": product_id,
        "question": question,
        "answer": answer,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN OPS TOOLS (with audit logging and dry-run support)
# ──────────────────────────────────────────────────────────────────────────────


async def _verify_admin(admin_email: str) -> User:
    """Verify that the given email belongs to an admin user."""
    await _ensure_db()
    user = await User.find_one(User.email == admin_email)
    if not user:
        raise ValueError(f"User not found: {admin_email}")
    if not user.is_admin:
        raise ValueError(f"User is not an admin: {admin_email}")
    return user


async def _log_audit(
    admin: Optional[User],
    action: str,
    tool_name: str,
    target_type: str,
    target_id: str,
    target_name: Optional[str] = None,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    success: bool = True,
    error_message: Optional[str] = None,
    reason: Optional[str] = None,
) -> AuditLog:
    """Create an audit log entry."""
    log = AuditLog(
        admin_id=admin.id if admin else None,
        admin_email=admin.email if admin else None,
        action=action,
        tool_name=tool_name,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        old_value=old_value,
        new_value=new_value,
        dry_run=dry_run,
        success=success,
        error_message=error_message,
        reason=reason,
    )
    await log.insert()
    return log


@mcp.tool()
async def update_stock(
    product_id: str,
    new_stock: int,
    admin_email: str,
    reason: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Update product stock level. Requires admin email for authentication.
    Use dry_run=True to preview the change without applying it.
    """
    await _ensure_db()

    # Verify admin
    try:
        admin = await _verify_admin(admin_email)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # Get product
    try:
        product = await Product.get(ObjectId(product_id))
    except Exception:
        return {"success": False, "error": "Invalid product ID"}

    if not product:
        return {"success": False, "error": "Product not found"}

    old_stock = product.count_in_stock
    old_value = {"count_in_stock": old_stock}
    new_value = {"count_in_stock": new_stock}

    if dry_run:
        # Log the dry run
        await _log_audit(
            admin=admin,
            action="update_stock",
            tool_name="update_stock",
            target_type="product",
            target_id=str(product.id),
            target_name=product.name,
            old_value=old_value,
            new_value=new_value,
            dry_run=True,
            reason=reason,
        )
        return {
            "success": True,
            "dry_run": True,
            "product_id": product_id,
            "product_name": product.name,
            "current_stock": old_stock,
            "proposed_stock": new_stock,
            "change": new_stock - old_stock,
            "message": "Dry run - no changes applied. Call with dry_run=False to apply.",
        }

    # Apply the change
    product.count_in_stock = new_stock
    await product.save()

    # Log the change
    await _log_audit(
        admin=admin,
        action="update_stock",
        tool_name="update_stock",
        target_type="product",
        target_id=str(product.id),
        target_name=product.name,
        old_value=old_value,
        new_value=new_value,
        dry_run=False,
        reason=reason,
    )

    return {
        "success": True,
        "dry_run": False,
        "product_id": product_id,
        "product_name": product.name,
        "old_stock": old_stock,
        "new_stock": new_stock,
        "change": new_stock - old_stock,
        "message": f"Stock updated from {old_stock} to {new_stock}",
    }


@mcp.tool()
async def update_product_price(
    product_id: str,
    new_price: float,
    admin_email: str,
    reason: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Update product price. Requires admin email for authentication.
    Use dry_run=True to preview the change without applying it.
    """
    await _ensure_db()

    if new_price < 0:
        return {"success": False, "error": "Price cannot be negative"}

    # Verify admin
    try:
        admin = await _verify_admin(admin_email)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # Get product
    try:
        product = await Product.get(ObjectId(product_id))
    except Exception:
        return {"success": False, "error": "Invalid product ID"}

    if not product:
        return {"success": False, "error": "Product not found"}

    old_price = product.price
    old_value = {"price": old_price}
    new_value = {"price": new_price}
    price_change_pct = ((new_price - old_price) / old_price * 100) if old_price > 0 else 0

    if dry_run:
        await _log_audit(
            admin=admin,
            action="update_price",
            tool_name="update_product_price",
            target_type="product",
            target_id=str(product.id),
            target_name=product.name,
            old_value=old_value,
            new_value=new_value,
            dry_run=True,
            reason=reason,
        )
        return {
            "success": True,
            "dry_run": True,
            "product_id": product_id,
            "product_name": product.name,
            "current_price": old_price,
            "proposed_price": new_price,
            "change_percent": round(price_change_pct, 2),
            "message": "Dry run - no changes applied. Call with dry_run=False to apply.",
        }

    # Apply the change
    product.price = new_price
    await product.save()

    await _log_audit(
        admin=admin,
        action="update_price",
        tool_name="update_product_price",
        target_type="product",
        target_id=str(product.id),
        target_name=product.name,
        old_value=old_value,
        new_value=new_value,
        dry_run=False,
        reason=reason,
    )

    return {
        "success": True,
        "dry_run": False,
        "product_id": product_id,
        "product_name": product.name,
        "old_price": old_price,
        "new_price": new_price,
        "change_percent": round(price_change_pct, 2),
        "message": f"Price updated from ${old_price} to ${new_price}",
    }


@mcp.tool()
async def flag_review(
    review_id: str,
    flag_reason: str,
    admin_email: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Flag a review for moderation (marks it for admin attention).
    Requires admin email for authentication.
    """
    await _ensure_db()

    # Verify admin
    try:
        admin = await _verify_admin(admin_email)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # Get review
    try:
        review = await Review.get(ObjectId(review_id))
    except Exception:
        return {"success": False, "error": "Invalid review ID"}

    if not review:
        return {"success": False, "error": "Review not found"}

    old_value = {"comment": review.comment, "rating": review.rating}
    new_value = {"flagged": True, "flag_reason": flag_reason}

    if dry_run:
        await _log_audit(
            admin=admin,
            action="flag_review",
            tool_name="flag_review",
            target_type="review",
            target_id=str(review.id),
            target_name=f"Review by {review.name}",
            old_value=old_value,
            new_value=new_value,
            dry_run=True,
            reason=flag_reason,
        )
        return {
            "success": True,
            "dry_run": True,
            "review_id": review_id,
            "reviewer_name": review.name,
            "rating": review.rating,
            "comment_preview": review.comment[:100] + "..." if len(review.comment) > 100 else review.comment,
            "flag_reason": flag_reason,
            "message": "Dry run - review would be flagged. Call with dry_run=False to apply.",
        }

    # Log the flag action (actual flagging would require adding a field to Review model)
    await _log_audit(
        admin=admin,
        action="flag_review",
        tool_name="flag_review",
        target_type="review",
        target_id=str(review.id),
        target_name=f"Review by {review.name}",
        old_value=old_value,
        new_value=new_value,
        dry_run=False,
        reason=flag_reason,
    )

    return {
        "success": True,
        "dry_run": False,
        "review_id": review_id,
        "reviewer_name": review.name,
        "rating": review.rating,
        "comment_preview": review.comment[:100] + "..." if len(review.comment) > 100 else review.comment,
        "flag_reason": flag_reason,
        "message": "Review flagged for moderation",
    }


@mcp.tool()
async def bulk_update_stock(
    updates: List[Dict[str, Any]],
    admin_email: str,
    reason: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Bulk update stock for multiple products.
    updates: List of {"product_id": str, "new_stock": int}
    Requires admin email for authentication.
    """
    await _ensure_db()

    # Verify admin
    try:
        admin = await _verify_admin(admin_email)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    results = []
    success_count = 0
    error_count = 0

    for update in updates[:20]:  # Limit to 20 items
        product_id = update.get("product_id")
        new_stock = update.get("new_stock")

        if not product_id or new_stock is None:
            results.append({"product_id": product_id, "success": False, "error": "Missing product_id or new_stock"})
            error_count += 1
            continue

        try:
            product = await Product.get(ObjectId(product_id))
            if not product:
                results.append({"product_id": product_id, "success": False, "error": "Product not found"})
                error_count += 1
                continue

            old_stock = product.count_in_stock

            if not dry_run:
                product.count_in_stock = new_stock
                await product.save()

            await _log_audit(
                admin=admin,
                action="bulk_update_stock",
                tool_name="bulk_update_stock",
                target_type="product",
                target_id=str(product.id),
                target_name=product.name,
                old_value={"count_in_stock": old_stock},
                new_value={"count_in_stock": new_stock},
                dry_run=dry_run,
                reason=reason,
            )

            results.append({
                "product_id": product_id,
                "product_name": product.name,
                "success": True,
                "old_stock": old_stock,
                "new_stock": new_stock,
            })
            success_count += 1

        except Exception as e:
            results.append({"product_id": product_id, "success": False, "error": str(e)})
            error_count += 1

    return {
        "success": error_count == 0,
        "dry_run": dry_run,
        "total": len(updates[:20]),
        "success_count": success_count,
        "error_count": error_count,
        "results": results,
        "message": f"{'Dry run: ' if dry_run else ''}{success_count} updated, {error_count} errors",
    }


@mcp.tool()
async def mark_order_delivered(
    order_id: str,
    admin_email: str,
    reason: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Mark an order as delivered. Requires admin email for authentication.
    """
    await _ensure_db()
    from datetime import datetime

    # Verify admin
    try:
        admin = await _verify_admin(admin_email)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # Get order
    try:
        order = await Order.get(ObjectId(order_id))
    except Exception:
        return {"success": False, "error": "Invalid order ID"}

    if not order:
        return {"success": False, "error": "Order not found"}

    if order.is_delivered:
        return {"success": False, "error": "Order is already marked as delivered"}

    if not order.is_paid:
        return {"success": False, "error": "Cannot deliver unpaid order"}

    old_value = {"is_delivered": order.is_delivered, "delivered_at": None}
    new_value = {"is_delivered": True, "delivered_at": "now"}

    if dry_run:
        await _log_audit(
            admin=admin,
            action="mark_delivered",
            tool_name="mark_order_delivered",
            target_type="order",
            target_id=str(order.id),
            old_value=old_value,
            new_value=new_value,
            dry_run=True,
            reason=reason,
        )
        return {
            "success": True,
            "dry_run": True,
            "order_id": order_id,
            "total_price": order.total_price,
            "items_count": len(order.order_items),
            "message": "Dry run - order would be marked as delivered. Call with dry_run=False to apply.",
        }

    # Apply the change
    order.is_delivered = True
    order.delivered_at = datetime.utcnow()
    await order.save()

    await _log_audit(
        admin=admin,
        action="mark_delivered",
        tool_name="mark_order_delivered",
        target_type="order",
        target_id=str(order.id),
        old_value=old_value,
        new_value={"is_delivered": True, "delivered_at": order.delivered_at.isoformat()},
        dry_run=False,
        reason=reason,
    )

    return {
        "success": True,
        "dry_run": False,
        "order_id": order_id,
        "total_price": order.total_price,
        "items_count": len(order.order_items),
        "delivered_at": order.delivered_at.isoformat(),
        "message": "Order marked as delivered",
    }


@mcp.tool()
async def get_audit_log(
    limit: int = 20,
    action_filter: Optional[str] = None,
    admin_email_filter: Optional[str] = None,
    include_dry_runs: bool = True,
) -> List[Dict[str, Any]]:
    """
    Retrieve recent audit log entries.
    Can filter by action type and admin email.
    """
    await _ensure_db()
    limit = _cap_limit(limit)

    query: Dict[str, Any] = {}
    if action_filter:
        query["action"] = action_filter
    if admin_email_filter:
        query["admin_email"] = admin_email_filter
    if not include_dry_runs:
        query["dry_run"] = False

    logs = await AuditLog.find(query).sort("-created_at").limit(limit).to_list()

    return [
        {
            "id": str(log.id),
            "admin_email": log.admin_email,
            "action": log.action,
            "tool_name": log.tool_name,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "target_name": log.target_name,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "dry_run": log.dry_run,
            "success": log.success,
            "reason": log.reason,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@mcp.tool()
async def admin_dashboard_summary(admin_email: str) -> Dict[str, Any]:
    """
    Get a quick admin dashboard summary with key metrics.
    Requires admin email for authentication.
    """
    await _ensure_db()

    # Verify admin
    try:
        admin = await _verify_admin(admin_email)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # Gather metrics
    total_products = await Product.find().count()
    total_orders = await Order.find().count()
    total_users = await User.find().count()

    # Low stock products (use "countInStock" - the MongoDB field name)
    low_stock = await Product.find({"countInStock": {"$lte": 5}}).to_list()
    low_stock_count = len(low_stock)

    # Recent orders (unpaid) - use "isPaid" MongoDB field name
    unpaid_orders = await Order.find({"isPaid": False}).count()

    # Pending deliveries (paid but not delivered)
    pending_delivery = await Order.find({"isPaid": True, "isDelivered": False}).count()

    # Revenue from paid orders
    paid_orders = await Order.find({"isPaid": True}).to_list()
    total_revenue = sum(o.total_price for o in paid_orders)

    # Recent audit actions (last 24 hours)
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_actions = await AuditLog.find({"created_at": {"$gte": yesterday}}).count()

    # Inventory value
    products = await Product.find().to_list()
    inventory_value = sum(p.price * p.count_in_stock for p in products)

    return {
        "success": True,
        "admin": admin.name,
        "metrics": {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_users": total_users,
            "low_stock_alerts": low_stock_count,
            "unpaid_orders": unpaid_orders,
            "pending_deliveries": pending_delivery,
            "total_revenue": round(total_revenue, 2),
            "inventory_value": round(inventory_value, 2),
            "recent_admin_actions_24h": recent_actions,
        },
        "low_stock_products": [
            {"id": str(p.id), "name": p.name, "stock": p.count_in_stock}
            for p in low_stock[:5]
        ],
    }


@mcp.tool()
async def list_admins() -> List[Dict[str, Any]]:
    """
    List all admin users (for reference when using admin tools).
    """
    await _ensure_db()
    # Use "isAdmin" since that's the MongoDB field name (camelCase alias)
    admins = await User.find({"isAdmin": True}).to_list()
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "email": a.email,
            "created_at": a.created_at.isoformat(),
        }
        for a in admins
    ]


if __name__ == "__main__":
    mcp.run()
