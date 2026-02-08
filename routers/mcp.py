"""
MCP Tools HTTP Router

Exposes safe MCP tools as HTTP endpoints for the frontend AI assistant.
Only read-only and shopping assistant tools are exposed here.
Admin tools require CLI access via the MCP server directly.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import os

from models.product import Product, Review
from models.order import Order
from config.settings import settings
from bson import ObjectId

# Optional OpenAI for AI-powered features
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    preferences: str
    budget: Optional[float] = None
    limit: int = 5


class CompareRequest(BaseModel):
    product_ids: List[str]


class CartSuggestionRequest(BaseModel):
    goal: str
    budget: float


class ProductQuestionRequest(BaseModel):
    product_id: str
    question: str


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def _get_openai():
    if not OPENAI_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenAI not available")
    api_key = settings.OPEN_AI or os.getenv("OPEN_AI")
    if not api_key:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")
    return AsyncOpenAI(api_key=api_key)


def _product_summary(product: Product) -> dict:
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


# ──────────────────────────────────────────────────────────────────────────────
# Catalog Info Endpoints (Read-only)
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/catalog/stats")
async def catalog_stats():
    """Get catalog statistics"""
    total_products = await Product.find().count()
    total_reviews = await Review.find().count()
    
    products = await Product.find().to_list()
    categories = list(set(p.category for p in products))
    category_counts = {}
    for category in categories:
        category_counts[category] = await Product.find({"category": category}).count()
    
    return {
        "total_products": total_products,
        "total_reviews": total_reviews,
        "categories": category_counts,
    }


@router.get("/catalog/categories")
async def category_price_summary():
    """Get category price summaries"""
    products = await Product.find().to_list()
    
    by_cat = {}
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


@router.get("/catalog/top-products")
async def get_top_products(limit: int = Query(5, ge=1, le=20)):
    """Get top-rated products"""
    products = await Product.find().sort("-rating").limit(limit).to_list()
    return [_product_summary(p) for p in products]


@router.get("/catalog/top-reviewed")
async def get_top_reviewed_products(limit: int = Query(3, ge=1, le=20)):
    """Get top reviewed products (by review count, then rating)"""
    products = (
        await Product.find()
        .sort("-numReviews", "-rating")
        .limit(limit)
        .to_list()
    )
    return [_product_summary(p) for p in products]


@router.get("/catalog/search")
async def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Search products by name, brand, or category"""
    import re
    escaped_query = re.escape(q)
    search = {"$regex": escaped_query, "$options": "i"}
    mongo_query = {
        "$or": [
            {"name": search},
            {"brand": search},
            {"category": search},
        ]
    }
    products = await Product.find(mongo_query).limit(limit).to_list()
    return [_product_summary(p) for p in products]


@router.get("/catalog/sentiment")
async def reviews_sentiment(product_id: Optional[str] = None):
    """Get sentiment summary of reviews"""
    positive_words = {"great", "love", "excellent", "amazing", "good", "best", "perfect", "awesome", "fantastic", "happy"}
    negative_words = {"bad", "poor", "terrible", "worst", "hate", "broken", "waste", "disappointed", "awful", "useless"}
    
    if product_id:
        try:
            oid = ObjectId(product_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid product ID")
        product = await Product.get(oid, fetch_links=True)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
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


# ──────────────────────────────────────────────────────────────────────────────
# AI Shopping Assistant Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/ai/recommend")
async def recommend_products(request: RecommendRequest):
    """AI-powered product recommendations"""
    import json
    
    client = _get_openai()
    products = await Product.find().to_list()
    
    if not products:
        return []
    
    catalog_text = "\n".join(
        f"- ID:{p.id} | {p.name} | {p.brand} | {p.category} | ${p.price} | rating:{p.rating}"
        for p in products[:100]  # Limit for context
    )
    
    budget_hint = f"User budget: ${request.budget}" if request.budget else "No specific budget."
    
    prompt = f"""You are a shopping assistant for Tweeky Queeky e-commerce store.
Given the product catalog and user preferences, recommend up to {request.limit} products.
Return ONLY a JSON array of product IDs (strings), most relevant first. No explanation.

Catalog:
{catalog_text}

User preferences: {request.preferences}
{budget_hint}
"""
    
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    raw = resp.choices[0].message.content.strip()
    
    try:
        ids = json.loads(raw)
    except json.JSONDecodeError:
        import re
        ids = re.findall(r"[0-9a-fA-F]{24}", raw)
    
    results = []
    for pid in ids[:request.limit]:
        try:
            p = await Product.get(ObjectId(pid))
            if p:
                results.append(_product_summary(p))
        except Exception:
            continue
    
    return results


@router.post("/ai/compare")
async def compare_products(request: CompareRequest):
    """Compare multiple products side by side"""
    if len(request.product_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 product IDs")
    
    product_ids = request.product_ids[:5]  # Max 5
    products = []
    
    for pid in product_ids:
        try:
            p = await Product.get(ObjectId(pid))
            if p:
                products.append(p)
        except Exception:
            continue
    
    if len(products) < 2:
        raise HTTPException(status_code=404, detail="Could not find enough products")
    
    comparison = []
    for p in products:
        comparison.append({
            "id": str(p.id),
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "price": p.price,
            "rating": p.rating,
            "num_reviews": p.num_reviews,
            "count_in_stock": p.count_in_stock,
            "image": p.image,
        })
    
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


@router.post("/ai/cart-suggestion")
async def build_cart_suggestion(request: CartSuggestionRequest):
    """AI builds a suggested cart within budget"""
    import json
    
    client = _get_openai()
    products = await Product.find({"countInStock": {"$gte": 1}}).to_list()
    
    if not products:
        return {"items": [], "total": 0, "budget": request.budget, "remaining": request.budget}
    
    catalog_text = "\n".join(
        f"- ID:{p.id} | {p.name} | ${p.price}"
        for p in products[:100]
    )
    
    prompt = f"""You are a shopping assistant. The user wants: "{request.goal}"
Budget: ${request.budget}

Pick products that fit the goal and stay within budget. Maximize value.
Return ONLY a JSON array of objects: [{{"id": "...", "qty": 1}}, ...]
No explanation.

Catalog:
{catalog_text}
"""
    
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    raw = resp.choices[0].message.content.strip()
    
    try:
        cart_items = json.loads(raw)
    except json.JSONDecodeError:
        return {"items": [], "total": 0, "budget": request.budget, "remaining": request.budget}
    
    items = []
    total = 0.0
    for item in cart_items:
        pid = item.get("id")
        qty = item.get("qty", 1)
        try:
            p = await Product.get(ObjectId(pid))
            if p and p.count_in_stock >= qty:
                item_total = p.price * qty
                if total + item_total <= request.budget:
                    items.append({
                        "id": str(p.id),
                        "name": p.name,
                        "price": p.price,
                        "qty": qty,
                        "subtotal": round(item_total, 2),
                        "image": p.image,
                    })
                    total += item_total
        except Exception:
            continue
    
    return {
        "items": items,
        "total": round(total, 2),
        "budget": request.budget,
        "remaining": round(request.budget - total, 2),
    }


@router.post("/ai/explain")
async def explain_product(product_id: str):
    """AI generates a product summary"""
    client = _get_openai()
    
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = await Product.get(oid, fetch_links=True)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
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


@router.post("/ai/ask")
async def answer_product_question(request: ProductQuestionRequest):
    """AI answers a question about a product"""
    client = _get_openai()
    
    try:
        oid = ObjectId(request.product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = await Product.get(oid, fetch_links=True)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reviews_text = ""
    if product.reviews:
        reviews_text = "\n".join(
            f"- {r.rating}/5: {r.comment}" for r in product.reviews[:10]
        )
    
    prompt = f"""You are a helpful shopping assistant. Answer the customer's question about this product.
Be concise and helpful. If the answer isn't in the data, say so politely.

Product: {product.name}
Brand: {product.brand}
Category: {product.category}
Price: ${product.price}
Description: {product.description}
Rating: {product.rating}/5 ({product.num_reviews} reviews)
Stock: {product.count_in_stock} units

Reviews:
{reviews_text}

Customer question: {request.question}
"""
    
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    answer = resp.choices[0].message.content.strip()
    
    return {
        "product_id": request.product_id,
        "question": request.question,
        "answer": answer,
    }


@router.post("/ai/chat")
async def shopping_chat(request: ChatRequest):
    """General shopping assistant chat"""
    client = _get_openai()
    
    # Get catalog context
    products = await Product.find().limit(50).to_list()
    catalog_context = "\n".join(
        f"- {p.name} ({p.brand}) - ${p.price} - {p.category}"
        for p in products
    )
    
    stats = await Product.find().count()
    reviews_count = await Review.find().count()
    
    system_prompt = f"""You are a friendly shopping assistant for Tweeky Queeky, an e-commerce store.
You help customers find products, answer questions, and provide recommendations.
Be helpful, concise, and friendly.

Store stats: {stats} products, {reviews_count} reviews

Sample products in catalog:
{catalog_context}

Guidelines:
- Help users find what they're looking for
- Suggest alternatives if requested item isn't available
- Be honest about limitations
- Keep responses concise (2-3 sentences usually)
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message}
    ]
    
    if request.context:
        messages.insert(1, {"role": "assistant", "content": f"Previous context: {request.context}"})
    
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
    )
    
    return {
        "message": request.message,
        "response": resp.choices[0].message.content.strip(),
    }


@router.get("/tools")
async def list_available_tools():
    """List all available MCP tools for the UI"""
    return {
        "catalog_tools": [
            {"name": "catalog_stats", "description": "Get catalog statistics", "endpoint": "/api/mcp/catalog/stats"},
            {"name": "category_summary", "description": "Get category price summaries", "endpoint": "/api/mcp/catalog/categories"},
            {"name": "top_products", "description": "Get top-rated products", "endpoint": "/api/mcp/catalog/top-products"},
            {"name": "top_reviewed", "description": "Get top reviewed products", "endpoint": "/api/mcp/catalog/top-reviewed"},
            {"name": "search", "description": "Search products", "endpoint": "/api/mcp/catalog/search"},
            {"name": "sentiment", "description": "Review sentiment analysis", "endpoint": "/api/mcp/catalog/sentiment"},
        ],
        "ai_tools": [
            {"name": "recommend", "description": "AI product recommendations", "endpoint": "/api/mcp/ai/recommend"},
            {"name": "compare", "description": "Compare products", "endpoint": "/api/mcp/ai/compare"},
            {"name": "cart_suggestion", "description": "AI cart builder", "endpoint": "/api/mcp/ai/cart-suggestion"},
            {"name": "explain", "description": "AI product summary", "endpoint": "/api/mcp/ai/explain"},
            {"name": "ask", "description": "Ask about a product", "endpoint": "/api/mcp/ai/ask"},
            {"name": "chat", "description": "Shopping assistant chat", "endpoint": "/api/mcp/ai/chat"},
        ],
    }
