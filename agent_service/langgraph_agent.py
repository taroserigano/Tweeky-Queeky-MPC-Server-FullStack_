"""
LangGraph Shopping Agent

Production-grade agentic AI using:
- LangGraph for state machine / workflow
- Tool calling with structured outputs
- Persistent memory with checkpointing
- MCP (Model Context Protocol) for simple CRUD operations
- RAG (Retrieval Augmented Generation) for semantic search
"""

from typing import Annotated, Sequence, TypedDict, Literal, Optional, Any, Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool, StructuredTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
import json
import asyncio
from bson import ObjectId

from config.settings import settings
from config.database import get_sync_db  # Use singleton connection pool


# ─────────────────────────────────────────────────────────────────────────────
# SYNC DATABASE ACCESS (Reuses connection pool)
# ─────────────────────────────────────────────────────────────────────────────

def _get_sync_db():
    """Get synchronous MongoDB connection (reuses connection pool)."""
    return get_sync_db()


def _product_to_dict(product: dict, include_reviews: bool = False) -> dict:
    """Convert MongoDB product document to clean dict.
    
    Args:
        product: Raw MongoDB product document
        include_reviews: If True, resolve review references from the reviews collection
    """
    oid = product.get("_id")
    fallback_sku = f"SKU-{str(oid).upper()}" if oid else ""
    result = {
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
        "num_reviews": product.get("numReviews", 0),
        "count_in_stock": product.get("countInStock", 0),
        "image": product.get("image", ""),
    }
    
    if include_reviews:
        result["reviews"] = _resolve_reviews(product.get("reviews", []))
    
    return result


def _resolve_reviews(review_refs: list) -> list:
    """Resolve review references (DBRefs/ObjectIds) to actual review documents."""
    if not review_refs:
        return []
    
    db = _get_sync_db()
    resolved = []
    
    for ref in review_refs:
        try:
            # Handle different reference formats
            if isinstance(ref, dict) and "$id" in ref:
                # DBRef format
                review_id = ref["$id"]
            elif isinstance(ref, ObjectId):
                review_id = ref
            elif isinstance(ref, str):
                review_id = ObjectId(ref)
            else:
                continue
            
            review_doc = db.reviews.find_one({"_id": review_id})
            if review_doc:
                resolved.append({
                    "id": str(review_doc["_id"]),
                    "name": review_doc.get("name", "Anonymous"),
                    "rating": review_doc.get("rating", 0),
                    "comment": review_doc.get("comment", ""),
                    "created_at": review_doc.get("createdAt", review_doc.get("created_at", "")),
                })
        except Exception:
            continue
    
    return resolved


# ─────────────────────────────────────────────────────────────────────────────
# STATE DEFINITION
# ─────────────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    """State for the shopping agent graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_preferences: dict
    cart: list
    session_metadata: dict


# ─────────────────────────────────────────────────────────────────────────────
# TOOL DEFINITIONS (Pure sync using PyMongo)
# ─────────────────────────────────────────────────────────────────────────────

@tool
def get_top_rated_products(limit: int = 5, min_rating: float = 4.0, category: Optional[str] = None) -> str:
    """Get the top-rated products from the entire catalog. Only use when user asks for generic 'best products' without a specific type. For type-specific queries (headphones, keyboards etc), use semantic_search instead.
    
    Args:
        limit: Number of products to return (default: 5)
        min_rating: Minimum rating threshold (default: 4.0)
        category: Optional broad category filter (e.g. 'Electronics', 'Gaming', 'Furniture')
    """
    db = _get_sync_db()
    
    query_filter = {"rating": {"$gte": min_rating}}
    if category:
        # Try exact category match first, fall back to name/description search
        query_filter["$or"] = [
            {"category": {"$regex": category, "$options": "i"}},
            {"name": {"$regex": category, "$options": "i"}},
            {"description": {"$regex": category, "$options": "i"}},
        ]
    
    # Get products sorted by rating
    products_docs = list(
        db.products.find(query_filter)
        .sort("rating", -1)
        .limit(limit)
    )
    
    if not products_docs:
        return json.dumps({"text": f"No products found matching your criteria.", "products": []})
    
    products = [_product_to_dict(p) for p in products_docs]
    
    text = f"Top {len(products)} rated products"
    return json.dumps({"text": text, "products": products})


@tool
def semantic_search(
    query: str,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    category: Optional[str] = None,
    top_k: int = 5,
) -> str:
    """Search for products using natural language. Understands intent and context.
    Use for queries like 'comfortable chair for work' or 'gift for music lover'."""
    
    from services.hybrid_search import hybrid_engine
    
    # Use hybrid search (BM25 + semantic + RRF) for better relevance
    results = hybrid_engine.search(
        query=query,
        limit=top_k,
        category=category,
        max_price=max_price,
        min_price=None,
        min_rating=min_rating,
    )
    
    if not results:
        # Fallback to direct DB search using PyMongo
        db = _get_sync_db()
        filter_query = {}
        if category:
            filter_query["category"] = {"$regex": category, "$options": "i"}
        
        products = list(db.products.find(filter_query).limit(top_k))
        if not products:
            return json.dumps({"text": "No products found matching your criteria.", "products": []})
        
        product_list = [_product_to_dict(p) for p in products]
        text = f"Found {len(product_list)} products"
        return json.dumps({"text": text, "products": product_list})
    
    # Convert hybrid search results to product dicts for structured response
    product_list = []
    for p in results:
        product_list.append({
            "id": p.get("_id", ""),
            "name": p.get("name", ""),
            "brand": p.get("brand", ""),
            "category": p.get("category", ""),
            "description": p.get("description", ""),
            "detailed_description": p.get("detailed_description", p.get("detailedDescription", "")),
            "specifications": p.get("specifications", {}),
            "price": p.get("price", 0),
            "rating": p.get("rating", 0),
            "numReviews": p.get("numReviews", 0),
            "countInStock": p.get("countInStock", 0),
            "image": p.get("image", ""),
        })
    
    text = f"Found {len(product_list)} products"
    return json.dumps({"text": text, "products": product_list})


@tool
def get_product_details(product_id: str) -> str:
    """Get full details about a specific product including description, specifications, stock, rating, and customer reviews.
    Use when user asks about a specific product's reviews, ratings, details, specs, weight, or any attribute.
    ALWAYS use this tool when user asks about reviews or ratings of a specific product.
    
    Args:
        product_id: The MongoDB ObjectId of the product
    """
    db = _get_sync_db()
    
    try:
        oid = ObjectId(product_id)
    except Exception:
        return json.dumps({"error": f"Invalid product ID: {product_id}"})
    
    product_doc = db.products.find_one({"_id": oid})
    if not product_doc:
        return json.dumps({"error": f"Product {product_id} not found."})
    
    product = _product_to_dict(product_doc, include_reviews=True)
    
    # Build a comprehensive text summary for the LLM
    text_parts = [
        f"Product: {product['name']}",
        f"Brand: {product['brand']}",
        f"Category: {product['category']}",
        f"Price: ${product['price']:.2f}",
        f"Rating: {product['rating']}/5 ({product['num_reviews']} reviews)",
        f"In Stock: {product['count_in_stock']} units",
        f"Description: {product['description']}",
    ]
    
    if product.get('detailed_description'):
        text_parts.append(f"Detailed Description: {product['detailed_description']}")
    
    if product.get('specifications'):
        specs_str = ", ".join(f"{k}: {v}" for k, v in product['specifications'].items())
        text_parts.append(f"Specifications: {specs_str}")
    
    reviews = product.get('reviews', [])
    if reviews:
        text_parts.append(f"\nCustomer Reviews ({len(reviews)}):")
        for r in reviews[:15]:
            text_parts.append(f"  - {r.get('name', 'Anonymous')} ({r.get('rating', 0)}/5): {r.get('comment', '')}")
    else:
        text_parts.append("\nNo customer reviews yet.")
    
    return json.dumps({"text": "\n".join(text_parts), "product": product})


@tool
def get_product_reviews(product_id: str) -> str:
    """Get all customer reviews for a specific product. Returns review text, ratings, and reviewer names.
    Use when user asks about what customers think, review sentiment, or product feedback.
    
    Args:
        product_id: The MongoDB ObjectId of the product
    """
    db = _get_sync_db()
    
    try:
        oid = ObjectId(product_id)
    except Exception:
        return json.dumps({"error": f"Invalid product ID: {product_id}"})
    
    product_doc = db.products.find_one({"_id": oid})
    if not product_doc:
        return json.dumps({"error": f"Product {product_id} not found."})
    
    product_name = product_doc.get("name", "Unknown")
    product_rating = product_doc.get("rating", 0)
    num_reviews = product_doc.get("numReviews", 0)
    
    # Resolve review references
    reviews = _resolve_reviews(product_doc.get("reviews", []))
    
    if not reviews:
        return json.dumps({
            "text": f"{product_name} has a rating of {product_rating}/5 with {num_reviews} reviews, but no detailed review text is available.",
            "product_name": product_name,
            "rating": product_rating,
            "num_reviews": num_reviews,
            "reviews": []
        })
    
    # Build review summary
    avg_review_rating = sum(r.get('rating', 0) for r in reviews) / len(reviews) if reviews else 0
    rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        rating_val = r.get('rating', 0)
        if rating_val in rating_dist:
            rating_dist[rating_val] += 1
    
    text_parts = [
        f"Reviews for {product_name}:",
        f"Overall Rating: {product_rating}/5 ({num_reviews} reviews)",
        f"Average Review Rating: {avg_review_rating:.1f}/5",
        f"Rating Distribution: 5★={rating_dist[5]}, 4★={rating_dist[4]}, 3★={rating_dist[3]}, 2★={rating_dist[2]}, 1★={rating_dist[1]}",
        "",
    ]
    
    for r in reviews:
        text_parts.append(f"- {r.get('name', 'Anonymous')} ({r.get('rating', 0)}/5): {r.get('comment', '')}")
    
    return json.dumps({
        "text": "\n".join(text_parts),
        "product_name": product_name,
        "rating": product_rating,
        "num_reviews": num_reviews,
        "avg_review_rating": round(avg_review_rating, 1),
        "rating_distribution": rating_dist,
        "reviews": reviews
    })


@tool
def search_products_by_price(
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    category: Optional[str] = None,
    sort_by: str = "price",
    limit: int = 5,
) -> str:
    """Search products filtered by price range. ALWAYS use this tool when the user mentions a specific dollar amount, budget, price limit, or price range.
    Examples: 'under $100', 'between $50 and $200', 'less than $300', 'cheapest', 'budget-friendly'.
    
    Args:
        max_price: Maximum price filter (e.g. 100.0 for 'under $100')
        min_price: Minimum price filter (e.g. 50.0 for 'above $50')
        min_rating: Minimum star rating filter (e.g. 4.0 for '4+ stars')
        category: Optional category to filter (e.g. 'Electronics', 'headphones')
        sort_by: Sort order - 'price' (low to high), '-price' (high to low), 'rating' (by rating desc)
        limit: Max number of products to return (default 5)
    """
    db = _get_sync_db()
    
    query_filter: dict = {}
    
    # Price filters
    if max_price is not None or min_price is not None:
        price_filter: dict = {}
        if max_price is not None:
            price_filter["$lte"] = max_price
        if min_price is not None:
            price_filter["$gte"] = min_price
        query_filter["price"] = price_filter
    
    # Rating filter
    if min_rating is not None:
        query_filter["rating"] = {"$gte": min_rating}
    
    # Category filter (regex, case insensitive)
    if category:
        query_filter["$or"] = [
            {"category": {"$regex": category, "$options": "i"}},
            {"name": {"$regex": category, "$options": "i"}},
            {"description": {"$regex": category, "$options": "i"}},
        ]
    
    # Determine sort
    if sort_by == "price":
        sort_spec = [("price", 1)]  # ascending
    elif sort_by == "-price":
        sort_spec = [("price", -1)]  # descending
    elif sort_by == "rating":
        sort_spec = [("rating", -1)]
    else:
        sort_spec = [("price", 1)]
    
    products_docs = list(
        db.products.find(query_filter)
        .sort(sort_spec)
        .limit(limit)
    )
    
    if not products_docs:
        price_desc = ""
        if max_price:
            price_desc += f" under ${max_price:.0f}"
        if min_price:
            price_desc += f" above ${min_price:.0f}"
        return json.dumps({"text": f"No products found{price_desc}.", "products": []})
    
    products = [_product_to_dict(p) for p in products_docs]
    
    price_desc = ""
    if max_price:
        price_desc += f" under ${max_price:.0f}"
    if min_price:
        price_desc += f" above ${min_price:.0f}"
    if min_rating:
        price_desc += f" rated {min_rating}+ stars"
    
    text = f"Found {len(products)} products{price_desc}"
    return json.dumps({"text": text, "products": products})


@tool
def compare_products_by_type(type_a: str, type_b: str, limit_each: int = 3) -> str:
    """Compare two types/categories of products side by side.
    ALWAYS use this tool when the user asks to compare different product types or categories.
    Examples: 'compare headphones and keyboards', 'headphones vs speakers', 'which is better, a mouse or a keyboard?'
    
    Args:
        type_a: First product type/category to search (e.g. 'headphones')
        type_b: Second product type/category to search (e.g. 'keyboards')
        limit_each: How many of each type to return (default 3)
    """
    from services.hybrid_search import hybrid_engine
    
    results_a = hybrid_engine.search(query=type_a, limit=limit_each)
    results_b = hybrid_engine.search(query=type_b, limit=limit_each)
    
    def _to_product(p: dict) -> dict:
        return {
            "id": p.get("_id", ""),
            "name": p.get("name", ""),
            "brand": p.get("brand", ""),
            "category": p.get("category", ""),
            "description": p.get("description", ""),
            "price": p.get("price", 0),
            "rating": p.get("rating", 0),
            "numReviews": p.get("numReviews", 0),
            "countInStock": p.get("countInStock", 0),
            "image": p.get("image", ""),
        }
    
    products_a = [_to_product(p) for p in results_a]
    products_b = [_to_product(p) for p in results_b]
    all_products = products_a + products_b
    
    # Build comparison text
    text_parts = [f"Comparing {type_a} vs {type_b}:"]
    
    if products_a:
        avg_price_a = sum(p["price"] for p in products_a) / len(products_a)
        avg_rating_a = sum(p["rating"] for p in products_a) / len(products_a)
        text_parts.append(f"\n{type_a.title()} ({len(products_a)} found): Avg price ${avg_price_a:.2f}, Avg rating {avg_rating_a:.1f}/5")
    else:
        text_parts.append(f"\nNo {type_a} found.")
    
    if products_b:
        avg_price_b = sum(p["price"] for p in products_b) / len(products_b)
        avg_rating_b = sum(p["rating"] for p in products_b) / len(products_b)
        text_parts.append(f"{type_b.title()} ({len(products_b)} found): Avg price ${avg_price_b:.2f}, Avg rating {avg_rating_b:.1f}/5")
    else:
        text_parts.append(f"No {type_b} found.")
    
    return json.dumps({"text": "\n".join(text_parts), "products": all_products})


@tool
def add_to_cart(product_id: str, quantity: int = 1) -> str:
    """Add a product to the shopping cart.
    Use when user wants to buy or add something to cart."""
    
    db = _get_sync_db()
    
    try:
        oid = ObjectId(product_id)
    except:
        return f"Invalid product ID: {product_id}"
    
    product_doc = db.products.find_one({"_id": oid})
    if not product_doc:
        return f"Product {product_id} not found."
    
    product = _product_to_dict(product_doc)
    
    if product.get('count_in_stock', 0) < quantity:
        return f"Sorry, only {product.get('count_in_stock', 0)} units available in stock."
    
    return f"Added {quantity}x **{product['name']}** (${product['price']:.2f} each) to cart."


@tool
def compare_products(product_ids: List[str]) -> str:
    """Compare multiple products side by side.
    Use when user wants to compare different products."""
    
    db = _get_sync_db()
    
    # Convert to ObjectIds
    oids = []
    for pid in product_ids:
        try:
            oids.append(ObjectId(pid))
        except:
            pass
    
    if not oids:
        return "No valid product IDs provided."
    
    products_docs = list(db.products.find({"_id": {"$in": oids}}))
    if not products_docs:
        return "Could not find the products to compare."
    
    products = [_product_to_dict(p) for p in products_docs]
    output = "⚖️ Product Comparison:\n\n"
    
    for p in products:
        output += f"• {p['name']}\n"
        output += f"  💰 ${p['price']:.2f}\n"
        output += f"  ⭐ {p.get('rating', 0)}/5\n"
        output += f"  🏷️ {p.get('brand', 'N/A')}\n"
        output += f"  📦 {p.get('count_in_stock', 0)} in stock\n"
        output += f"\n"
    
    # Add summary
    if len(products) > 1:
        prices = [p['price'] for p in products]
        ratings = [p.get('rating', 0) for p in products]
        
        output += f"📊 Summary:\n"
        output += f"  💵 Price Range: ${min(prices):.2f} - ${max(prices):.2f}\n"
        
        best_rated = max(products, key=lambda x: x.get('rating', 0))
        output += f"  🏆 Highest Rated: {best_rated['name']}\n"
        
        best_value = min(products, key=lambda x: x['price'] / max(x.get('rating', 1), 0.1))
        output += f"- Best Value: {best_value['name']}\n"
    
    return output


# ─────────────────────────────────────────────────────────────────────────────
# NATIVE TOOLS (Keep locally - need state or complex logic)
# These tools stay in the agent, not moved to MCP
# ─────────────────────────────────────────────────────────────────────────────

NATIVE_TOOLS = [
    get_top_rated_products,       # Get best products by rating
    semantic_search,              # Uses RAG/Pinecone - complex semantic understanding
    search_products_by_price,     # Filter by exact price range / budget
    get_product_details,          # Full product info with reviews & specs
    get_product_reviews,          # Customer reviews & rating analysis
    add_to_cart,                  # Needs session state management
    compare_products,             # Compare products by ID
    compare_products_by_type,     # Compare product categories (headphones vs keyboards)
]


# ─────────────────────────────────────────────────────────────────────────────
# MCP TOOLS INTEGRATION
# Simple CRUD operations delegated to MCP server
# ─────────────────────────────────────────────────────────────────────────────

_mcp_tools: List[StructuredTool] = []
_mcp_initialized = False


async def initialize_mcp_tools() -> List[StructuredTool]:
    """Initialize MCP tools for the agent."""
    import os
    global _mcp_tools, _mcp_initialized
    
    # Check if MCP should be disabled
    if os.environ.get("SKIP_MCP", "false").lower() == "true":
        print("[Agent] MCP disabled via SKIP_MCP environment variable")
        _mcp_initialized = True
        return []
    
    if _mcp_initialized:
        return _mcp_tools
    
    try:
        from mcp_service.client import get_mcp_client, get_mcp_tools_for_agent
        
        mcp_client = await get_mcp_client()
        _mcp_tools = get_mcp_tools_for_agent(mcp_client)
        _mcp_initialized = True
        
        print(f"[Agent] Initialized {len(_mcp_tools)} MCP tools: {[t.name for t in _mcp_tools]}")
        return _mcp_tools
    except Exception as e:
        print(f"[Agent] Warning: Could not initialize MCP tools: {e}")
        print("[Agent] Falling back to native tools only")
        _mcp_initialized = True  # Don't retry on every call
        return []


def get_all_tools() -> List:
    """Get all available tools (native + MCP)."""
    return NATIVE_TOOLS + _mcp_tools


# For backwards compatibility - will be updated with MCP tools after init
SHOPPING_TOOLS = NATIVE_TOOLS.copy()


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH NODES
# ─────────────────────────────────────────────────────────────────────────────

def get_llm():
    """Get the LLM instance"""
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.1,
        openai_api_key=settings.OPENAI_API_KEY,
    )


SYSTEM_PROMPT = """You are a helpful shopping assistant for TweekySqueeky Shop.

**MANDATORY: You MUST call a tool before responding to ANY product-related question. NEVER answer about products from memory.**

Tools:
- semantic_search: Use for natural-language product discovery (e.g. "comfortable chair", "gift for music lover"). Do NOT use for price-specific queries.
- search_products_by_price: Use WHENEVER the user mentions a specific dollar amount, budget, or price limit (e.g. "under $100", "between $50-$200", "less than $300", "cheapest"). This guarantees exact price filtering.
- get_top_rated_products: Only for generic "show me best products" when NO specific type or price is mentioned.
- get_product_details: Get FULL details about a specific product.
- get_product_reviews: Get customer reviews and rating analysis for a specific product.
- compare_products_by_type: Use when user wants to compare different product categories (e.g. "compare headphones and keyboards", "headphones vs speakers").
- compare_products: Compare specific products by ID.
- add_to_cart: Add a product to the cart.

**CRITICAL TOOL SELECTION RULES:**

1. **PRICE QUERIES → search_products_by_price:** If the user mentions ANY dollar amount or budget ("under $100", "$50-$200", "cheapest", "budget"), you MUST use search_products_by_price with the appropriate max_price/min_price. NEVER use semantic_search or get_top_rated_products for price-filtered queries.
   Examples:
   - "products under $100" → search_products_by_price(max_price=100)
   - "rated 4+ stars under $200" → search_products_by_price(max_price=200, min_rating=4.0)
   - "electronics under $150" → search_products_by_price(max_price=150, category="electronics")

2. **REVIEW/SENTIMENT QUERIES → semantic_search + get_product_reviews:** When the user asks about customer satisfaction, review sentiment, what people think, or best reviews, ALWAYS call semantic_search first to find products, then call get_product_reviews on the results. NEVER use only get_top_rated_products for review sentiment questions.
   Examples:
   - "Are customers happy?" → semantic_search(query="popular well-reviewed products") then get_product_reviews for each
   - "Which have the best reviews?" → semantic_search(query="best reviewed products") then get_product_reviews

3. **COMPARISON QUERIES → compare_products_by_type:** When the user asks to compare different types/categories, use compare_products_by_type.
   Examples:
   - "Compare headphones and keyboards" → compare_products_by_type(type_a="headphones", type_b="keyboards")
   - "headphones vs speakers" → compare_products_by_type(type_a="headphones", type_b="speakers")

4. **GENERAL SEARCH → semantic_search:** For natural language queries without price constraints.

5. **NEVER list product names, prices, or ratings in your text.** Products are displayed as visual cards. Write only 1-2 conversational sentences.
6. Be confident and concise. No apologies.

Current user preferences: {preferences}
"""


def create_agent_node(tools: list):
    """Create the agent reasoning node"""
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)
    
    def agent(state: AgentState) -> AgentState:
        """The agent reasoning step"""
        preferences = state.get("user_preferences", {})
        pref_str = json.dumps(preferences) if preferences else "None yet"
        
        # Build messages with system prompt
        system_msg = SystemMessage(content=SYSTEM_PROMPT.format(preferences=pref_str))
        messages = [system_msg] + list(state["messages"])
        
        # Get LLM response
        response = llm_with_tools.invoke(messages)
        
        return {"messages": [response]}
    
    return agent


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Determine if we should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def extract_preferences(state: AgentState) -> AgentState:
    """Extract user preferences from the conversation."""
    preferences = state.get("user_preferences", {})
    
    for msg in state["messages"][-3:]:
        if isinstance(msg, HumanMessage):
            content = msg.content.lower()
            
            # Budget extraction
            if "budget" in content or "$" in content:
                import re
                prices = re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', content)
                if prices:
                    preferences["max_budget"] = float(prices[-1].replace(",", ""))
            
            # Category preferences
            categories = ["electronics", "headphones", "chairs", "keyboard", "monitor", "camera"]
            for cat in categories:
                if cat in content:
                    if "interested_categories" not in preferences:
                        preferences["interested_categories"] = []
                    if cat not in preferences["interested_categories"]:
                        preferences["interested_categories"].append(cat)
    
    return {"user_preferences": preferences}


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH CONSTRUCTION
# ─────────────────────────────────────────────────────────────────────────────

def create_shopping_agent(tools: List = None):
    """Create the LangGraph shopping agent with the given tools."""
    if tools is None:
        tools = get_all_tools()
    
    workflow = StateGraph(AgentState)
    
    agent_node = create_agent_node(tools)
    tool_node = ToolNode(tools)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("extract_preferences", extract_preferences)
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": "extract_preferences",
        },
    )
    workflow.add_edge("tools", "agent")
    workflow.add_edge("extract_preferences", END)
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

class ShoppingAgentLangGraph:
    """High-level interface for the LangGraph shopping agent."""
    
    def __init__(self, use_mcp: bool = True):
        self._use_mcp = use_mcp
        self._mcp_initialized = False
        self.graph = None
        self._tools = []
    
    async def _ensure_initialized(self):
        """Ensure the agent is initialized with MCP tools if enabled."""
        if self.graph is not None:
            return
        
        self._tools = NATIVE_TOOLS.copy()
        
        if self._use_mcp and not self._mcp_initialized:
            try:
                mcp_tools = await initialize_mcp_tools()
                self._tools.extend(mcp_tools)
                self._mcp_initialized = True
                print(f"[Agent] Total tools available: {len(self._tools)}")
            except Exception as e:
                print(f"[Agent] MCP init failed, using native tools only: {e}")
        
        self.graph = create_shopping_agent(self._tools)
    
    async def chat(
        self,
        message: str,
        thread_id: str = "default",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message and get a response."""
        await self._ensure_initialized()
        
        config = {"configurable": {"thread_id": thread_id}}
        
        input_state = {
            "messages": [HumanMessage(content=message)],
            "user_preferences": {},
            "cart": [],
            "session_metadata": {"user_id": user_id},
        }
        
        # Run the graph
        result = await asyncio.to_thread(
            self.graph.invoke,
            input_state,
            config,
        )
        
        # Extract response
        messages = result.get("messages", [])
        last_ai_message = None
        tool_calls_made = []
        products_found = []
        seen_product_ids = set()
        
        # Find the last HumanMessage index to only collect products from the current turn
        last_human_idx = 0
        for i, msg in enumerate(messages):
            if isinstance(msg, HumanMessage):
                last_human_idx = i
        
        # Only scan messages after the last HumanMessage (current turn)
        for msg in reversed(messages[last_human_idx:]):
            if isinstance(msg, AIMessage) and last_ai_message is None:
                last_ai_message = msg
            elif isinstance(msg, ToolMessage):
                # Determine tool source (MCP vs Native)
                tool_source = "mcp" if msg.name.startswith("mcp_") else "native"
                tool_calls_made.append({
                    "tool": msg.name,
                    "source": tool_source,
                    "result_preview": msg.content[:200] if msg.content else "",
                })
                # Extract structured products from tool results (deduplicated)
                if msg.content:
                    try:
                        parsed = json.loads(msg.content)
                        if isinstance(parsed, dict) and "products" in parsed:
                            for prod in parsed["products"]:
                                pid = prod.get("id") or prod.get("_id") or prod.get("name")
                                if pid and pid not in seen_product_ids:
                                    seen_product_ids.add(pid)
                                    products_found.append(prod)
                    except (json.JSONDecodeError, TypeError):
                        pass
        
        response_text = last_ai_message.content if last_ai_message else ""
        
        # Strip text-based product listings when we have structured product data
        if products_found and response_text:
            response_text = self._strip_product_listing(response_text)
        
        return {
            "response": response_text,
            "tool_calls": list(reversed(tool_calls_made)),
            "products": products_found,
            "preferences": result.get("user_preferences", {}),
            "thread_id": thread_id,
            "mcp_enabled": self._mcp_initialized and len(_mcp_tools) > 0,
        }
    
    def get_tools_info(self) -> Dict[str, Any]:
        """Get information about available tools."""
        native = [t.name for t in NATIVE_TOOLS]
        mcp = [t.name for t in _mcp_tools]
        return {
            "native_tools": native,
            "mcp_tools": mcp,
            "total": len(native) + len(mcp),
            "mcp_enabled": self._mcp_initialized,
        }
    
    @staticmethod
    def _strip_product_listing(text: str) -> str:
        """Remove text-based product listings when product cards are shown."""
        import re as _re
        lines = text.split('\n')
        cleaned = []
        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue
            # Skip numbered lists
            if _re.match(r'^\d+\.\s+', trimmed):
                continue
            # Skip bullet lists
            if _re.match(r'^[•\-\*]\s+', trimmed):
                continue
            # Skip lines with price patterns
            if _re.search(r'\$\d+(\.\d{2})?', trimmed):
                continue
            # Skip lines with star/rating patterns
            if _re.search(r'[⭐★]', trimmed) or _re.search(r'\d\.\d/5', trimmed):
                continue
            # Skip "Found X products" or "Top N" lines
            if _re.search(r'found\s+\d+\s+product', trimmed, _re.IGNORECASE):
                continue
            if _re.search(r'^top\s+\d+\s+rated', trimmed, _re.IGNORECASE):
                continue
            cleaned.append(line)
        result = '\n'.join(cleaned).strip()
        return result if result else "Here are the products I found for you!"
    
    def get_conversation_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a thread"""
        if not self.graph:
            return []
            
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            state = self.graph.get_state(config)
            messages = state.values.get("messages", [])
            
            history = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    history.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    history.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, ToolMessage):
                    history.append({"role": "tool", "name": msg.name, "content": msg.content[:200]})
            
            return history
        except Exception:
            return []
    
    def clear_conversation(self, thread_id: str) -> bool:
        """Clear conversation history for a thread"""
        return True


# Singleton instance
_agent_instance: Optional[ShoppingAgentLangGraph] = None


def get_shopping_agent() -> ShoppingAgentLangGraph:
    """Get the singleton agent instance"""
    import os
    global _agent_instance
    if _agent_instance is None:
        # Check if MCP should be disabled
        skip_mcp = os.environ.get("SKIP_MCP", "false").lower() == "true"
        _agent_instance = ShoppingAgentLangGraph(use_mcp=not skip_mcp)
    return _agent_instance
