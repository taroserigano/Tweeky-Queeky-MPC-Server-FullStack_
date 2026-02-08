"""
Multi-Agent System for Product Recommendations and Search

Architecture:
- ProductExpertAgent: Personalized recommendations based on history, trends
- SearchAgent: Find specific products based on user requests
- AgentRouter: Routes queries to the appropriate agent(s)
"""

from typing import List, Dict, Any, Optional, Literal
from urllib.parse import urlencode, quote
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from bson import ObjectId

import httpx
import logging

logger = logging.getLogger(__name__)

from config.settings import settings
from config.database import get_sync_db  # Use singleton connection pool
from services.hybrid_search import hybrid_engine
from agent_service.user_history import (
    get_user_purchase_history,
    get_user_preferences_from_history,
    get_trending_products,
    get_similar_products_by_category,
    get_products_frequently_bought_together,
    get_best_deals,
    get_new_arrivals,
)

# ─────────────────────────────────────────────────────────────────────────────
# MCP + RAG MICROSERVICE URLs
# ─────────────────────────────────────────────────────────────────────────────

MCP_SERVER_URL = "http://localhost:7001"
RAG_SERVER_URL = "http://localhost:7002"


# ─────────────────────────────────────────────────────────────────────────────
# LLM INITIALIZATION HELPER
# ─────────────────────────────────────────────────────────────────────────────

def get_llm(temperature: float = 0.7):
    """Get the configured LLM based on settings.LLM_PROVIDER"""
    if settings.LLM_PROVIDER == "anthropic":
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            temperature=temperature,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )
    else:  # Default to OpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=temperature,
            openai_api_key=settings.OPENAI_API_KEY,
        )


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCT EXPERT AGENT - Recommendations
# ─────────────────────────────────────────────────────────────────────────────

# Note: search_products_by_keyword is added after it's defined below
PRODUCT_EXPERT_TOOLS_BASE = [
    tool(get_user_purchase_history),
    tool(get_user_preferences_from_history),
    tool(get_trending_products),
    tool(get_similar_products_by_category),
    tool(get_products_frequently_bought_together),
    tool(get_best_deals),
    tool(get_new_arrivals),
]


PRODUCT_EXPERT_PROMPT = """You are the **Product Expert Agent** - a specialist in personalized product recommendations.

⚠️ **MANDATORY FIRST STEP**: For EVERY recommendation request, you MUST call search_products_by_keyword() FIRST before considering any other tool.

Example: User says "Recommend gaming gear" → Call: search_products_by_keyword(keyword="gaming")
Example: User says "What laptops do you have" → Call: search_products_by_keyword(keyword="laptop")
Example: User says "Show me headphones" → Call: search_products_by_keyword(keyword="headphone")

**Tools (IN ORDER OF PRIORITY)**:
1. ⭐ search_products_by_keyword(keyword, category, min_price, max_price, min_rating, limit) - USE THIS FIRST ALWAYS!
2. get_user_purchase_history(user_id, limit) - Get user's past purchases
3. get_similar_products_by_category(product_id, limit) - Get similar products  
4. get_trending_products(category, limit) - ONLY if user explicitly says "trending" or "popular"
5. get_best_deals(category, limit) - ONLY if user explicitly says "deals" or "discount"
6. get_new_arrivals(category, limit) - ONLY if user explicitly says "new" or "latest"

**Response Guidelines**:
- **NEVER list product names, prices, or ratings in your text response.** Products are displayed as visual cards automatically. Write only 1-2 conversational sentences.
- Good: "Here are some great options I found for you! Let me know if you want to filter by budget."
- Bad: "1. Sony WH-1000XM5 — $349.99" ← NEVER do this.
- Bad: "Bose QuietComfort Ultra ($429.99, ⭐ 4.7/5)" ← NEVER do this.
- If search returns NO products, say "We don't currently have [category] products, but here are some alternatives:" then search for related categories
- NEVER give generic advice without first trying to search
- Be direct, confident, and helpful

Current user: {user_id} | Query type: {query_type}
"""


class ProductExpertAgent:
    """Agent specialized in product recommendations."""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.7)  # More creative for recommendations
        self.llm_with_tools = self.llm.bind_tools(PRODUCT_EXPERT_TOOLS)
        
    def recommend(self, query: str, user_id: Optional[str] = None, context: Dict[str, Any] = None) -> str:
        """Generate personalized recommendations."""
        context = context or {}
        
        # STEP 1: Always search first using keywords from the query
        search_keywords = self._extract_keywords(query)
        requested_limit = _extract_requested_limit(query)
        initial_search_result = ""
        if search_keywords:
            try:
                initial_search_result = search_products_by_keyword.invoke({"keyword": search_keywords, "limit": requested_limit})
            except Exception as e:
                initial_search_result = f"Search error: {str(e)}"

        # If no results, try fallback keywords (e.g., drop "gear", use first term)
        if initial_search_result and "No products found" in initial_search_result:
            fallback_candidates = []
            if search_keywords:
                if "gear" in search_keywords:
                    fallback_candidates.append(search_keywords.replace("gear", "").strip())
                fallback_candidates.append(search_keywords.split()[0])
            for candidate in [c for c in fallback_candidates if c]:
                try:
                    retry_result = search_products_by_keyword.invoke({"keyword": candidate})
                    if "No products found" not in retry_result:
                        initial_search_result = retry_result
                        search_keywords = candidate
                        break
                except Exception:
                    continue

        # If search returns products, respond directly with a brief conversational message.
        # Product details are shown as visual cards — no need to list them in text.
        if initial_search_result and "No products found" not in initial_search_result and "Search error" not in initial_search_result:
            return "Here are some great picks from our catalog! Let me know if you'd like me to filter by budget or brand."

        # If search fails or finds no matches, return a direct catalog-aware response.
        if "Search error" in initial_search_result or "No products found" in initial_search_result:
            return (
                f"I’m not seeing exact matches for '{search_keywords or query}' in our catalog right now. "
                "Want to try something close? You can browse: Electronics, Wearables, Furniture, Home, Personal Care. "
                "Tell me your budget or a brand you like and I’ll dig further."
            )
        
        system_prompt = PRODUCT_EXPERT_PROMPT.format(
            user_id=user_id or "None (anonymous user)",
            query_type=context.get("query_type", "general recommendation")
        )
        
        # Include search results in the initial message
        enhanced_query = query
        if initial_search_result and "No products found" not in initial_search_result:
            enhanced_query = f"""User request: {query}

I already searched our product catalog. Here are the results:
{initial_search_result}

Based on these ACTUAL products we have, provide recommendations to the user."""
        else:
            enhanced_query = f"""User request: {query}

I searched for "{search_keywords}" but found no matching products. 
Inform the user we don't have {search_keywords} products currently, and suggest they browse our available categories: Electronics, Wearables, Furniture, Home, Personal Care."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=enhanced_query),
        ]
        
        # Agentic loop - let agent use tools for additional info
        max_iterations = 5
        for i in range(max_iterations):
            response = self.llm_with_tools.invoke(messages)
            messages.append(response)
            
            # Check if agent wants to use tools
            if not response.tool_calls:
                # Agent is done, return final response
                return response.content
            
            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # Find and execute the tool
                tool_result = self._execute_tool(tool_name, tool_args)
                
                # Add tool result to messages
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                ))
        
        # Max iterations reached
        return "I've analyzed your preferences but need more information. Could you be more specific?"
    
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute a tool by name."""
        tool_map = {t.name: t for t in PRODUCT_EXPERT_TOOLS}
        
        if tool_name in tool_map:
            tool_func = tool_map[tool_name]
            try:
                return tool_func.invoke(tool_args)
            except Exception as e:
                return f"Error executing {tool_name}: {str(e)}"
        
        return f"Unknown tool: {tool_name}"
    
    def _extract_keywords(self, query: str) -> str:
        """Extract product-related keywords from query."""
        # Remove common words and keep nouns/product terms
        stop_words = {'recommend', 'show', 'find', 'get', 'me', 'i', 'want', 'need', 
                      'looking', 'for', 'some', 'a', 'an', 'the', 'best', 'good',
                      'please', 'can', 'you', 'do', 'have', 'any', 'what', 'which'}
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return ' '.join(keywords) if keywords else query


# ─────────────────────────────────────────────────────────────────────────────
# SEARCH AGENT - Find specific products
# ─────────────────────────────────────────────────────────────────────────────

def _get_sync_db():
    """Get synchronous MongoDB connection (reuses connection pool)."""
    return get_sync_db()


# Shared mutable list — the router endpoint reads this after each agent call
_pending_product_cards: List[Dict[str, Any]] = []


def _extract_requested_limit(query: str) -> int:
    """Extract the number of products the user asked for from the query.
    Returns the number if found, otherwise 5 (default).
    E.g. 'find me 2 headphones' → 2, 'top 3 laptops' → 3
    """
    import re
    q = query.lower()
    # "find me 2", "show 3", "get me 2", "give me 5"
    m = re.search(r'(?:find|show|get|list|give|display|recommend)(?:\s+\w+){0,3}\s+(\d{1,2})\b', q)
    if m:
        return max(int(m.group(1)), 1)
    # "2 headphones", "3 products", "2 best headphones"
    m2 = re.search(r'\b(\d{1,2})\s+(?:product|item|result|thing|headphone|laptop|phone|keyboard|mouse|speaker|earphone|earbud|monitor|chair|watch|camera|tv|tablet)', q)
    if m2:
        return max(int(m2.group(1)), 1)
    # "top 3", "best 5"
    m3 = re.search(r'(?:top|best)\s+(\d{1,2})\b', q)
    if m3:
        return max(int(m3.group(1)), 1)
    return 5  # default


def _strip_product_listing(text: str) -> str:
    """Remove text-based product listings from response when product cards are shown."""
    if not text:
        return text
    import re as _re
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            continue
        # Skip numbered lists: "1. Product Name ..."
        if _re.match(r'^\d+\.\s+', trimmed):
            continue
        # Skip bullet lists: "• Product", "- **Product", "* Product"
        if _re.match(r'^[•\-\*]\s+', trimmed):
            continue
        # Skip lines with price patterns: "$99.99", "— $"
        if _re.search(r'\$\d+(\.\d{2})?', trimmed):
            continue
        # Skip lines with star/rating patterns
        if _re.search(r'[⭐★]', trimmed) or _re.search(r'\d\.\d/5', trimmed):
            continue
        # Skip "Found X products" lines
        if _re.search(r'found\s+\d+\s+product', trimmed, _re.IGNORECASE):
            continue
        # Skip recommendation headers
        if _re.search(r'^(my\s+)?recommendations?:', trimmed, _re.IGNORECASE):
            continue
        if _re.search(r'here\s+are\s+(some|the)\s+(picks|best|top|highest|great)', trimmed, _re.IGNORECASE):
            continue
        # Skip "Top N rated products" lines
        if _re.search(r'^top\s+\d+\s+rated', trimmed, _re.IGNORECASE):
            continue
        # Skip markdown separator lines
        if trimmed == '---':
            continue
        # Skip "Tip:" lines
        if _re.match(r'^💡\s*Tip:', trimmed):
            continue
        cleaned.append(line)
    result = '\n'.join(cleaned).strip()
    return result if result else "Here are the products I found for you!"


def _collect_product_card(product: dict) -> None:
    """Collect structured product data for frontend card rendering."""
    pid = str(product.get('_id', ''))
    # Deduplicate — skip if this product was already collected
    if any(c['_id'] == pid for c in _pending_product_cards):
        return
    _pending_product_cards.append({
        "_id": pid,
        "name": product.get('name', 'N/A'),
        "brand": product.get('brand', 'N/A'),
        "price": product.get('price', 0),
        "rating": product.get('rating', 0),
        "numReviews": product.get('numReviews', 0),
        "countInStock": product.get('countInStock', 0),
        "image": product.get('image', '/images/sample.jpg'),
        "description": (product.get('description', '') or '')[:120],
    })


def drain_product_cards(limit: int = None, keyword: str = None) -> List[Dict[str, Any]]:
    """Pop all pending product cards (called by the router endpoint).
    
    Args:
        limit: Max number of cards to return (user-requested quantity).
        keyword: If provided, boost relevance by sorting matched products first
                 and filtering out clearly unrelated items.
    """
    cards = list(_pending_product_cards)
    _pending_product_cards.clear()

    # Relevance boost — sort cards so keyword-matching ones come first
    if keyword:
        import re
        # Extract core product-type words from the keyword
        stop = {'find', 'me', 'show', 'get', 'best', 'top', 'highest', 'lowest',
                'rated', 'reviews', 'review', 'rating', 'with', 'the', 'and',
                'most', 'popular', 'cheap', 'expensive', 'good', 'great', 'a',
                'an', 'for', 'my', 'some', 'any', 'recommend', 'i', 'want',
                'need', 'looking', 'like', 'budget', 'affordable', 'premium'}
        kw_words = [w for w in re.split(r'\s+', keyword.lower()) if w not in stop and len(w) > 1]
        
        # Expand common synonyms so "headphones" also matches "earbuds", "earphones", "airpods"
        synonym_groups = [
            {'headphone', 'headphones', 'earphone', 'earphones', 'earbud', 'earbuds', 'airpod', 'airpods', 'headset'},
            {'keyboard', 'keyboards'},
            {'mouse', 'mice'},
            {'laptop', 'laptops', 'notebook', 'notebooks'},
            {'phone', 'phones', 'smartphone', 'smartphones'},
            {'speaker', 'speakers'},
            {'monitor', 'monitors', 'display', 'displays'},
            {'watch', 'watches', 'smartwatch'},
            {'camera', 'cameras'},
            {'tv', 'television', 'televisions'},
            {'tablet', 'tablets', 'ipad'},
            {'chair', 'chairs'},
        ]
        expanded_kw = set(kw_words)
        for group in synonym_groups:
            if expanded_kw & group:
                expanded_kw |= group
        
        if expanded_kw:
            def relevance_score(card):
                haystack = f"{card.get('name', '')} {card.get('description', '')} {card.get('brand', '')}".lower()
                return sum(1 for w in expanded_kw if w in haystack)
            
            # Separate into relevant and non-relevant
            scored = [(relevance_score(c), c) for c in cards]
            relevant = [c for score, c in scored if score > 0]
            non_relevant = [c for score, c in scored if score == 0]
            
            # Use relevant cards first; only add non-relevant if we need more
            if relevant:
                cards = relevant + non_relevant

    if limit and limit < len(cards):
        cards = cards[:limit]

    return cards


@tool
def search_products_by_keyword(
    keyword: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    limit: int = 5,
) -> str:
    """Search for products by keyword with optional filters.
    Uses hybrid search (BM25 keyword matching + semantic embedding similarity).
    
    Args:
        keyword: Search term (product name, brand, description, or natural language query)
        category: Filter by category
        min_price: Minimum price
        max_price: Maximum price
        min_rating: Minimum rating (0-5)
        limit: Max number of results
    """
    # Use hybrid engine if ready, otherwise fall back to MongoDB regex
    # Auto-detect price limits embedded in keyword text
    import re as _re
    _under = _re.search(r'(?:under|below|less than|up to|cheaper than|within|max)\s*\$?(\d+(?:\.\d+)?)', keyword, _re.IGNORECASE)
    _over = _re.search(r'(?:over|above|more than|at least|min|starting)\s*\$?(\d+(?:\.\d+)?)', keyword, _re.IGNORECASE)
    _between = _re.search(r'\$?(\d+(?:\.\d+)?)\s*(?:to|-)\s*\$?(\d+(?:\.\d+)?)', keyword, _re.IGNORECASE)
    if _under and max_price is None:
        max_price = float(_under.group(1))
    if _over and min_price is None:
        min_price = float(_over.group(1))
    if _between and min_price is None and max_price is None:
        min_price = float(_between.group(1))
        max_price = float(_between.group(2))
    # Clean price text from keyword for search
    _clean_kw = _re.sub(
        r'(?:under|below|less than|up to|cheaper than|over|above|more than|at least|starting|within)\s*\$?\d+(?:\.\d+)?',
        '', keyword, flags=_re.IGNORECASE
    ).strip()
    _clean_kw = _re.sub(r'\$\d+(?:\.\d+)?', '', _clean_kw).strip()
    # If keyword was ONLY a price reference, use a broad search
    if not _clean_kw or _clean_kw.lower() in ('find', 'show', 'any', 'products', 'items', 'me', 'any products', 'some', 'get'):
        # Redirect to price-range search which uses MongoDB directly
        if min_price is not None or max_price is not None:
            return search_by_price_range.invoke({
                "min_price": min_price or 0,
                "max_price": max_price or 99999,
                "category": category,
                "limit": limit,
            })

    if hybrid_engine.ready:
        results = hybrid_engine.search(
            keyword,
            limit=limit,
            category=category,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
        )

        # Supplement with MongoDB if hybrid returned fewer than requested
        if len(results) < limit:
            existing_ids = {str(r.get('_id', '')) for r in results}
            db = _get_sync_db()
            # Use structured filters to fill remaining slots — keep keyword requirement
            fallback_q: Dict[str, Any] = {}
            conditions = []
            if category:
                conditions.append({"category": {"$regex": category, "$options": "i"}})
            if min_price is not None or max_price is not None:
                pq: Dict[str, Any] = {}
                if min_price is not None:
                    pq["$gte"] = min_price
                if max_price is not None:
                    pq["$lte"] = max_price
                conditions.append({"price": pq})
            if min_rating is not None:
                conditions.append({"rating": {"$gte": min_rating}})
            # Add keyword regex as one condition — always require keyword match
            conditions.append({"$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"brand": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}},
            ]})
            fallback_q = {"$and": conditions} if len(conditions) > 1 else conditions[0]
            for p in db.products.find(fallback_q).sort("rating", -1).limit(limit * 2):
                pid = str(p.get('_id', ''))
                if pid not in existing_ids:
                    results.append(p)
                    existing_ids.add(pid)
                    if len(results) >= limit:
                        break

        if not results:
            return f"No products found matching '{keyword}'"

        # Collect product cards for visual display
        for p in results:
            _collect_product_card(p)

        return f"Found {len(results)} matching products. They are displayed as product cards."

    # Fallback: MongoDB regex search
    db = _get_sync_db()
    
    # Build query
    query: Dict[str, Any] = {
        "$or": [
            {"name": {"$regex": keyword, "$options": "i"}},
            {"brand": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}},
        ]
    }
    
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    
    if min_price is not None or max_price is not None:
        price_query: Dict[str, Any] = {}
        if min_price is not None:
            price_query["$gte"] = min_price
        if max_price is not None:
            price_query["$lte"] = max_price
        query["price"] = price_query
    
    if min_rating is not None:
        query["rating"] = {"$gte": min_rating}
    
    # Execute search
    products = list(
        db.products.find(query)
        .sort("rating", -1)
        .limit(limit)
    )
    
    if not products:
        return f"No products found matching '{keyword}'"
    
    # Collect product cards for visual display
    for p in products:
        _collect_product_card(p)
    
    return f"Found {len(products)} matching products. They are displayed as product cards."


@tool
def search_by_category(category: str, limit: int = 5) -> str:
    """Get all products in a specific category.
    Uses hybrid search to rank results by relevance within the category.
    
    Args:
        category: Category name (e.g., "Electronics", "Headphones")
        limit: Max results
    """
    if hybrid_engine.ready:
        results = hybrid_engine.search(category, limit=limit, category=category)

        # Supplement with MongoDB if hybrid returned fewer than requested
        if len(results) < limit:
            existing_ids = {str(r.get('_id', '')) for r in results}
            db = _get_sync_db()
            for p in db.products.find({"category": {"$regex": category, "$options": "i"}}).sort("rating", -1).limit(limit * 2):
                pid = str(p.get('_id', ''))
                if pid not in existing_ids:
                    results.append(p)
                    existing_ids.add(pid)
                    if len(results) >= limit:
                        break

        if not results:
            return f"No products found in category '{category}'"

        for p in results:
            _collect_product_card(p)
        return f"Found {len(results)} products in {category}. They are displayed as product cards."

    # Fallback: MongoDB regex
    db = _get_sync_db()
    
    products = list(
        db.products.find({"category": {"$regex": category, "$options": "i"}})
        .sort("rating", -1)
        .limit(limit)
    )
    
    if not products:
        return f"No products found in category '{category}'"
    
    for p in products:
        _collect_product_card(p)
    
    return f"Found {len(products)} products in {category}. They are displayed as product cards."


@tool
def search_by_brand(brand: str, limit: int = 5) -> str:
    """Get all products from a specific brand.
    Uses hybrid search to rank results by relevance within the brand.
    
    Args:
        brand: Brand name (e.g., "Sony", "Apple")
        limit: Max results
    """
    if hybrid_engine.ready:
        results = hybrid_engine.search(brand, limit=limit, brand=brand)

        # Supplement with MongoDB if hybrid returned fewer than requested
        if len(results) < limit:
            existing_ids = {str(r.get('_id', '')) for r in results}
            db = _get_sync_db()
            for p in db.products.find({"brand": {"$regex": brand, "$options": "i"}}).sort("rating", -1).limit(limit * 2):
                pid = str(p.get('_id', ''))
                if pid not in existing_ids:
                    results.append(p)
                    existing_ids.add(pid)
                    if len(results) >= limit:
                        break

        if not results:
            return f"No products found from brand '{brand}'"

        for p in results:
            _collect_product_card(p)
        return f"Found {len(results)} products from {brand}. They are displayed as product cards."

    # Fallback: MongoDB regex
    db = _get_sync_db()
    
    products = list(
        db.products.find({"brand": {"$regex": brand, "$options": "i"}})
        .sort("rating", -1)
        .limit(limit)
    )
    
    if not products:
        return f"No products found from brand '{brand}'"
    
    for p in products:
        _collect_product_card(p)
    
    return f"Found {len(products)} products from {brand}. They are displayed as product cards."


@tool
def search_by_price_range(
    min_price: float,
    max_price: float,
    category: Optional[str] = None,
    limit: int = 5,
) -> str:
    """Find products within a price range.
    Uses MongoDB price filtering — best for numeric range lookups.
    
    Args:
        min_price: Minimum price
        max_price: Maximum price
        category: Optional category filter
        limit: Max results
    """
    # Price range is a structured filter — use MongoDB directly (not hybrid search)
    db = _get_sync_db()
    
    query: Dict[str, Any] = {
        "price": {"$gte": min_price, "$lte": max_price}
    }
    
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    
    products = list(
        db.products.find(query)
        .sort("rating", -1)
        .limit(limit)
    )
    
    if not products:
        return f"No products found between ${min_price} and ${max_price}"
    
    for p in products:
        _collect_product_card(p)
    
    return f"Found {len(products)} products in ${min_price:.0f}-${max_price:.0f} range. They are displayed as product cards."


# ─────────────────────────────────────────────────────────────────────────────
# MCP SERVER TOOLS - Order tracking & quick product lookup (port 7001)
# ─────────────────────────────────────────────────────────────────────────────

@tool
def mcp_track_order(order_id: str) -> str:
    """Track an order by order ID.
    Use this when the user asks about order status, delivery, or tracking.
    Accepts either a MongoDB ObjectId or a short order reference.

    Args:
        order_id: Order ID (MongoDB ObjectId string)
    """
    try:
        from bson import ObjectId
        db = _get_sync_db()

        # Try to find the order by ObjectId
        order = None
        if len(order_id) == 24:
            try:
                order = db.orders.find_one({"_id": ObjectId(order_id)})
            except Exception:
                pass

        # Fallback: search by the last few chars of the ID
        if not order:
            orders = list(db.orders.find().sort("createdAt", -1).limit(50))
            for o in orders:
                if str(o["_id"]).endswith(order_id.lower().replace("ord-", "").replace("ord", "")):
                    order = o
                    break

        # Final fallback: get most recent order
        if not order and order_id.lower() in ["latest", "recent", "last", "my order", "my latest order"]:
            order = db.orders.find_one(sort=[("createdAt", -1)])

        if not order:
            total = db.orders.count_documents({})
            if total == 0:
                return "No orders found in the system yet. Place an order first!"
            return f"Order '{order_id}' not found. Please check the order ID."

        oid = str(order["_id"])
        items = order.get("orderItems", [])
        item_names = [item.get("name", "Unknown") for item in items]
        total = order.get("totalPrice", 0)
        is_paid = order.get("isPaid", False)
        is_delivered = order.get("isDelivered", False)
        created = order.get("createdAt", "")

        if is_delivered:
            status = "DELIVERED ✅"
        elif is_paid:
            status = "PAID — Awaiting Shipment 📦"
        else:
            status = "PENDING PAYMENT ⏳"

        output = f"**Order #{oid[-6:].upper()}**\n\n"
        output += f"- **Status**: {status}\n"
        output += f"- **Total**: ${total:.2f}\n"
        output += f"- **Items**: {', '.join(item_names)}\n"
        if created:
            output += f"- **Placed**: {str(created)[:10]}\n"
        output += f"\n[View full order details](/order/{oid})"
        return output

    except Exception as e:
        return f"Error tracking order: {str(e)}"


@tool
def mcp_quick_product_search(query: str, max_price: Optional[float] = None) -> str:
    """Quick product search using the MCP Server's built-in catalog.
    Use this for fast lookups when users ask about common products like headphones, laptops, phones.

    Args:
        query: Search term
        max_price: Optional maximum price filter
    """
    try:
        filters = {}
        if max_price is not None:
            filters["maxPrice"] = max_price
        with httpx.Client(timeout=5.0) as client:
            r = client.post(f"{MCP_SERVER_URL}/tools/searchProducts",
                           json={"query": query, "filters": filters})
            r.raise_for_status()
            data = r.json()
            if data.get("ok"):
                products = data["data"]["products"]
                if not products:
                    return f"No MCP catalog products found for '{query}'."
                output = f"MCP Catalog — {len(products)} result(s):\n\n"
                for p in products:
                    output += f"• {p['name']} — ${p['price']:.2f}\n  {p['description']}\n\n"
                return output.strip()
            return "MCP search returned no results."
    except httpx.ConnectError:
        return "MCP Server is not available."
    except Exception as e:
        return f"MCP search error: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────────
# RAG SERVICE TOOL - Document retrieval (port 7002)
# ─────────────────────────────────────────────────────────────────────────────

@tool
def rag_query_documents(question: str) -> str:
    """Query the RAG knowledge base for shipping info, return policies, support contacts, or product guides.
    Use this when users ask general questions about the store, policies, or support — NOT for product search.

    Args:
        question: The user's question about store policies, shipping, returns, support, etc.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.post(f"{RAG_SERVER_URL}/rag/query",
                           json={"question": question, "top_k": 3})
            r.raise_for_status()
            data = r.json()
            passages = data.get("passages", [])
            if not passages:
                return "No relevant documentation found."
            output = "From our knowledge base:\n\n"
            for p in passages:
                if p.get("score", 0) > 0:
                    output += f"{p['text']}\n(Source: {p['sourceFile']})\n\n"
            return output.strip() if output.strip() != "From our knowledge base:" else "No relevant documentation found."
    except httpx.ConnectError:
        return "RAG Service is not available. Knowledge base is temporarily offline."
    except Exception as e:
        return f"RAG query error: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────────
# CART TOOL - Add products to cart from chat
# ─────────────────────────────────────────────────────────────────────────────

# Shared mutable list that the router endpoint can read after each agent call
_pending_cart_actions: List[Dict[str, Any]] = []

@tool
def chat_add_to_cart(product_name: str, qty: int = 1) -> str:
    """Add a product to the user's shopping cart.
    Use this when the user explicitly asks to add a product to their cart,
    e.g. "add the Ibanez guitar to my cart" or "I want to buy the Sony headphones".

    Args:
        product_name: Name (or partial name) of the product to add
        qty: Quantity to add (default 1)
    """
    try:
        db = _get_sync_db()
        import re
        pattern = re.compile(re.escape(product_name), re.IGNORECASE)
        product = db.products.find_one({"name": {"$regex": pattern}})

        if not product:
            # Try broader search
            words = product_name.split()
            for word in words:
                if len(word) > 3:
                    product = db.products.find_one(
                        {"name": {"$regex": re.compile(re.escape(word), re.IGNORECASE)}}
                    )
                    if product:
                        break

        if not product:
            return f"Could not find a product matching '{product_name}'. Please search for it first."

        if product.get("countInStock", 0) < qty:
            return f"Sorry, **{product['name']}** is out of stock."

        pid = str(product["_id"])
        cart_item = {
            "_id": pid,
            "name": product["name"],
            "image": product.get("image", "/images/sample.jpg"),
            "price": product["price"],
            "countInStock": product.get("countInStock", 0),
            "qty": qty,
        }
        _pending_cart_actions.append(cart_item)

        return (
            f"✅ Added **{product['name']}** (×{qty}) to your cart — ${product['price'] * qty:.2f}\n\n"
            f"[View your cart](/cart)"
        )
    except Exception as e:
        return f"Error adding to cart: {str(e)}"


def drain_cart_actions() -> List[Dict[str, Any]]:
    """Pop all pending cart actions (called by the router endpoint)."""
    actions = list(_pending_cart_actions)
    _pending_cart_actions.clear()
    return actions


# ─────────────────────────────────────────────────────────────────────────────
# TOOL LISTS
# ─────────────────────────────────────────────────────────────────────────────

SEARCH_AGENT_TOOLS = [
    search_products_by_keyword,
    search_by_category,
    search_by_brand,
    search_by_price_range,
    mcp_quick_product_search,  # MCP fallback
    mcp_track_order,           # Order tracking via MCP
    rag_query_documents,       # Knowledge base via RAG
    chat_add_to_cart,          # Add to cart from chat
]

# PRODUCT_EXPERT_TOOLS - search_products_by_keyword FIRST for priority
PRODUCT_EXPERT_TOOLS = [search_products_by_keyword] + PRODUCT_EXPERT_TOOLS_BASE + [
    mcp_track_order,
    rag_query_documents,
    chat_add_to_cart,
]


SEARCH_AGENT_PROMPT = """You are the **Search Agent** - a specialist in finding products and answering questions.

Your expertise:
- Finding products via **hybrid search** (BM25 keyword matching + semantic embedding similarity)
- Order tracking directly from the database
- Answering store policy questions via RAG knowledge base
- Filtering by category, brand, price, rating

Available Tools:
**Product Search (Hybrid BM25 + Semantic)**:
- search_products_by_keyword(keyword, category, min_price, max_price, min_rating, limit) — Primary search: uses BM25 + semantic vector ranking
- search_by_category(category, limit) — Search within a category
- search_by_brand(brand, limit) — Search by brand
- search_by_price_range(min_price, max_price, category, limit) — Filter by price range

**MCP Server Tools**:
- mcp_quick_product_search(query, max_price) — Quick product lookup

**Order Tracking (Real DB)**:
- mcp_track_order(order_id) — Track orders from the database.
  Accepts: a 24-char MongoDB ObjectId, a partial ID suffix, OR the keywords "latest", "recent", "last", "my order", "my latest order".
  If the user says "track my order" or "my latest order" without providing an ID, call mcp_track_order("latest").

**RAG Knowledge Base**:
- rag_query_documents(question) — Shipping info, return policies, support contacts

**Shopping Cart**:
- chat_add_to_cart(product_name, qty) — Adds a product to the user's cart.
  Use when the user says "add X to cart", "buy X", "I want the X", etc.

Routing Rules:
1. **Order tracking**: If user mentions order/tracking/delivery → use mcp_track_order. If no specific ID given, pass "latest" as order_id.
2. **Store policies**: If user asks about shipping, returns, support, hours → use rag_query_documents
3. **Product search**: For keyword-based queries ("headphones", "Sony laptop") → use search_products_by_keyword
4. **Price filter**: If user specifies a budget or price range (e.g. "under $300", "$50-$200", "cheap") → use search_by_price_range with min_price=0 (or stated min) and max_price. This is the BEST tool for price filtering.
5. **Category/brand browsing**: Use search_by_category or search_by_brand for specific category/brand lookups
6. **Add to cart**: If user explicitly asks to add, buy, purchase, or get a product → use chat_add_to_cart with the product name
7. **Handle 'not found'** gracefully with suggestions

CRITICAL RESPONSE RULES:
- **NEVER list product names, prices, or ratings in your text response.** Products are displayed as visual cards automatically. Write only 1-2 conversational sentences.
- Good: "Here are the best headphones I found for you! Let me know if you'd like to filter by price."
- Bad: "1. Sony WH-1000XM5 — $349.99 (⭐ 4.6/5)" ← NEVER do this.
- Bad: "Bose QuietComfort Ultra ($429.99, ⭐ 4.7/5)" ← NEVER do this.
- When tool results say "Found N products", just write a brief friendly sentence. Do NOT repeat product details.
- For order tracking and policy questions, include the full details in your text response (those are not shown as cards).
- When tool results contain markdown links for orders like [text](/order/xxx) or [text](/cart), preserve them EXACTLY.

Current query: {query}
"""


class SearchAgent:
    """Agent specialized in finding specific products."""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.2)  # More precise for search
        self.llm_with_tools = self.llm.bind_tools(SEARCH_AGENT_TOOLS)

    # ── deterministic pre-routing ─────────────────────────────────────────
    @staticmethod
    def _detect_price_and_limit(query: str):
        """Extract price range + requested limit from the raw user query.
        Returns (min_price, max_price, limit) or (None, None, None) if no
        price pattern is found.
        """
        import re
        q = query.lower()

        min_p = max_p = None
        # "under / below / less than / up to $300"
        m = re.search(r'(?:under|below|less than|up to|cheaper than|within|max)\s*\$?(\d+(?:\.\d+)?)', q)
        if m:
            max_p = float(m.group(1))
            min_p = 0.0
        # "over / above / more than $100"
        m2 = re.search(r'(?:over|above|more than|at least|min|starting)\s*\$?(\d+(?:\.\d+)?)', q)
        if m2:
            min_p = float(m2.group(1))
            if max_p is None:
                max_p = 99999.0  # no cap
        # "$100 to $300" or "100-300" or "between 50 and 200"
        m3 = re.search(r'\$?(\d+(?:\.\d+)?)\s*(?:to|-|and)\s*\$?(\d+(?:\.\d+)?)', q)
        if m3:
            min_p = float(m3.group(1))
            max_p = float(m3.group(2))
        # "cheap" / "budget" / "affordable" → under $150
        if min_p is None and max_p is None:
            if re.search(r'\b(cheap|budget|affordable|inexpensive)\b', q):
                min_p, max_p = 0.0, 150.0

        # Extract requested limit: "find 3", "find me 3", "show me 5", "top 10"
        lim = 5  # sensible default
        # verb + optional filler words + number: "find me 3", "show 5", "get me like 3"
        lm = re.search(r'(?:find|show|get|list|give|top|display)(?:\s+\w+){0,3}\s+(\d{1,2})\b', q)
        if lm:
            lim = max(int(lm.group(1)), 1)
        else:
            # "3 products", "3 items", "3 some stuff", "3 things"
            lm2 = re.search(r'\b(\d{1,2})\s+(?:product|item|result|thing|some|any|cheap|good|best)', q)
            if lm2:
                lim = max(int(lm2.group(1)), 1)

        if min_p is not None and max_p is not None:
            return min_p, max_p, lim
        return None, None, None

    def search(self, query: str, context: Dict[str, Any] = None) -> str:
        """Execute search based on user query."""
        context = context or {}

        # ── STEP 1: deterministic pre-routing for price queries ──────────
        min_p, max_p, lim = self._detect_price_and_limit(query)
        if min_p is not None and max_p is not None:
            logger.info(f"[SearchAgent] Pre-routing price query: ${min_p}-${max_p}, limit={lim}")
            print(f"[SearchAgent] Pre-routing price query: ${min_p}-${max_p}, limit={lim}", flush=True)
            # Call the tool directly — no LLM needed for tool selection
            tool_result = search_by_price_range.invoke({
                "min_price": min_p,
                "max_price": max_p,
                "limit": lim,
            })
            # Let the LLM format a nice response around the pre-fetched results
            return self._format_prefetched(query, tool_result)

        # ── STEP 2: standard LLM-driven tool selection ───────────────────
        requested_limit = _extract_requested_limit(query)
        system_prompt = SEARCH_AGENT_PROMPT.format(query=query)
        # Tell the LLM the exact limit the user wants
        if requested_limit != 5:
            system_prompt += f"\n\n**IMPORTANT: The user asked for exactly {requested_limit} product(s). You MUST pass limit={requested_limit} to search tools.**"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query),
        ]
        
        # Agentic loop
        max_iterations = 5
        for i in range(max_iterations):
            response = self.llm_with_tools.invoke(messages)
            messages.append(response)
            
            if not response.tool_calls:
                return response.content
            
            # Execute tools
            for tool_call in response.tool_calls:
                tool_result = self._execute_tool(tool_call["name"], tool_call["args"])
                
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                ))
        
        return "I couldn't find what you're looking for. Could you provide more details?"

    def _format_prefetched(self, query: str, tool_result: str) -> str:
        """Let the LLM compose a friendly response from pre-fetched tool data."""
        messages = [
            SystemMessage(content=(
                "You are a helpful e-commerce assistant. The user asked a question "
                "and product search results have ALREADY been fetched. "
                "Products are displayed as visual cards with images and add-to-cart buttons automatically. "
                "Write only 1-2 friendly conversational sentences. "
                "Do NOT list product names, prices, or ratings in your response — the cards handle that."
            )),
            HumanMessage(content=f"User query: {query}\n\nSearch results:\n{tool_result}"),
        ]
        # No tools bound — just format the response
        response = self.llm.invoke(messages)
        return response.content

    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute a tool by name."""
        print(f"[SearchAgent] Tool call: {tool_name}({tool_args})", flush=True)
        tool_map = {t.name: t for t in SEARCH_AGENT_TOOLS}
        
        if tool_name in tool_map:
            tool_func = tool_map[tool_name]
            try:
                return tool_func.invoke(tool_args)
            except Exception as e:
                return f"Error: {str(e)}"
        
        return f"Unknown tool: {tool_name}"


# ─────────────────────────────────────────────────────────────────────────────
# AGENT ROUTER - Routes queries to appropriate agent
# ─────────────────────────────────────────────────────────────────────────────

class QueryIntent(BaseModel):
    """Classification of user query intent."""
    intent: Literal["recommendation", "search", "order_tracking", "knowledge", "cart", "both"] = Field(
        description="Type of query: 'recommendation' for suggestions, 'search' for finding items, 'order_tracking' for order status, 'knowledge' for store policies/shipping/support, 'cart' for adding products to cart/buying, 'both' for combination"
    )
    confidence: float = Field(description="Confidence score 0-1")
    reasoning: str = Field(description="Why this intent was chosen")


ROUTER_PROMPT = """Analyze the user's query and determine their intent:

**RECOMMENDATION intent** - User wants suggestions, advice, or personalized recommendations:
- "What should I get for..."
- "Recommend me..."
- "What's good for..."
- "Best products for..."

**SEARCH intent** - User wants to find specific products:
- "Find me..."
- "Show me..."
- "Do you have..."
- Mentions specific brands, models, or product names

**ORDER_TRACKING intent** - User asks about order status, delivery, or tracking:
- "Where is my order..."
- "Track my order"
- "Track my latest order"
- "When will my order arrive"
- "Delivery status"

**KNOWLEDGE intent** - User asks about store policies, shipping, returns, or support:
- "What's your return policy?"
- "How long does shipping take?"
- "How do I contact support?"
- "What are your business hours?"

**CART intent** - User wants to add a product to their shopping cart or buy something:
- "Add the Ibanez guitar to my cart"
- "I want to buy the Sony headphones"
- "Put 2 of the office chair in my cart"
- "Buy the electric bike"

**BOTH** - Query needs multiple intents:
- "Find and recommend..."
- "Show me your best..."

Analyze this query and determine the intent:
"{query}"
"""


class AgentRouter:
    """Routes queries to the appropriate agent(s)."""
    
    def __init__(self):
        self.llm = get_llm(temperature=0)
        self.product_expert = ProductExpertAgent()
        self.search_agent = SearchAgent()
    
    def route_and_execute(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Route query to appropriate agent(s) and execute."""
        
        # Clear any stale product cards from previous requests
        _pending_product_cards.clear()
        _pending_cart_actions.clear()
        
        # Classify intent
        intent = self._classify_intent(query)
        
        result = {
            "query": query,
            "intent": intent.intent,
            "confidence": intent.confidence,
            "reasoning": intent.reasoning,
            "responses": {},
        }
        
        # Execute based on intent
        if intent.intent == "recommendation":
            result["responses"]["product_expert"] = self.product_expert.recommend(
                query, user_id=user_id, context={"query_type": "recommendation"}
            )
            result["primary_response"] = result["responses"]["product_expert"]
            
        elif intent.intent == "search":
            result["responses"]["search"] = self.search_agent.search(query)
            result["primary_response"] = result["responses"]["search"]

        elif intent.intent == "order_tracking":
            # Route to SearchAgent which has mcp_track_order tool
            result["responses"]["search"] = self.search_agent.search(query)
            result["primary_response"] = result["responses"]["search"]

        elif intent.intent == "knowledge":
            # Route to SearchAgent which has rag_query_documents tool
            result["responses"]["search"] = self.search_agent.search(query)
            result["primary_response"] = result["responses"]["search"]

        elif intent.intent == "cart":
            # Route to SearchAgent which has chat_add_to_cart tool
            result["responses"]["search"] = self.search_agent.search(query)
            result["primary_response"] = result["responses"]["search"]
            
        elif intent.intent == "both":
            # Use only ONE agent to avoid duplicate product cards.
            # ProductExpert already searches, so prefer it for "both" intent.
            result["responses"]["product_expert"] = self.product_expert.recommend(
                query, user_id=user_id, context={"query_type": "hybrid"}
            )
            result["primary_response"] = result["responses"]["product_expert"]
        
        # Attach any cart actions the tools produced during this run
        result["cart_actions"] = drain_cart_actions()
        
        # Extract the requested limit and keyword for filtering
        requested_limit = _extract_requested_limit(query)
        # Extract core keyword for relevance filtering
        import re as _route_re
        _kw_for_filter = _route_re.sub(
            r'\b(find|show|get|me|with|the|best|top|highest|lowest|rated|reviews?|ratings?|most|popular|recommend|\d+)\b',
            '', query.lower()
        ).strip() or None
        result["product_cards"] = drain_product_cards(limit=requested_limit, keyword=_kw_for_filter)

        # Strip any text-based product listings from the response
        # since products are shown as visual cards
        if result["product_cards"]:
            result["primary_response"] = _strip_product_listing(result["primary_response"])

        return result
    
    def _classify_intent(self, query: str) -> QueryIntent:
        """Classify the user's query intent."""
        structured_llm = self.llm.with_structured_output(QueryIntent)
        
        prompt = ROUTER_PROMPT.format(query=query)
        
        try:
            intent = structured_llm.invoke(prompt)
            return intent
        except Exception as e:
            # Fallback to search if classification fails
            return QueryIntent(
                intent="search",
                confidence=0.5,
                reasoning=f"Fallback due to error: {str(e)}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def get_multi_agent_router() -> AgentRouter:
    """Get the multi-agent router singleton."""
    return AgentRouter()
