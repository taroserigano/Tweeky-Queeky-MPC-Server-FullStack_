"""
Multi-Agent Router API

Exposes the multi-agent recommendation and search system via REST endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from agent_service.multi_agents import get_multi_agent_router, drain_product_cards
import re as _re


def _strip_product_text(text: str) -> str:
    """Strip text-based product listings — products are shown as cards."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        t = line.strip()
        if not t:
            continue
        if _re.match(r'^\d+\.\s+', t):
            continue
        if _re.match(r'^[•\-\*]\s+', t):
            continue
        if _re.search(r'\$\d+(\.\d{2})?', t):
            continue
        if _re.search(r'[⭐★]', t) or _re.search(r'\d\.\d/5', t):
            continue
        if _re.search(r'found\s+\d+\s+product', t, _re.IGNORECASE):
            continue
        if _re.match(r'^(my\s+)?recommendations?:', t, _re.IGNORECASE):
            continue
        if _re.search(r'here\s+are\s+(some|the)\s+(picks|best|top|highest|great)', t, _re.IGNORECASE):
            continue
        if _re.match(r'^top\s+\d+\s+rated', t, _re.IGNORECASE):
            continue
        if t == '---':
            continue
        if _re.match(r'^💡\s*Tip:', t):
            continue
        cleaned.append(line)
    result = '\n'.join(cleaned).strip()
    return result if result else "Here are the products I found for you!"


router = APIRouter(prefix="/api/agent/v2", tags=["multi-agent"])


# ──────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────────────────────

class MultiAgentRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User's natural language query")
    user_id: Optional[str] = Field(None, description="User ID for personalization")


class MultiAgentResponse(BaseModel):
    query: str = Field(description="Original query")
    intent: str = Field(description="Detected intent: 'recommendation', 'search', 'cart', or 'both'")
    confidence: float = Field(description="Confidence in intent classification (0-1)")
    reasoning: str = Field(description="Why this intent was chosen")
    response: str = Field(description="Primary response to user")
    agent_used: str = Field(description="Which agent(s) were used")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    cart_actions: List[Dict[str, Any]] = Field(default_factory=list, description="Products to add to cart")
    product_cards: List[Dict[str, Any]] = Field(default_factory=list, description="Product cards for rich display")


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=MultiAgentResponse)
async def multi_agent_chat(request: MultiAgentRequest):
    """
    **Multi-Agent Product Recommendation & Search System**
    
    This endpoint uses specialized AI agents:
    
    **ProductExpertAgent** - For recommendations:
    - "What's good for a music lover?"
    - "Recommend me gaming gear"
    - "Best products for home office"
    - Analyzes your purchase history for personalization
    
    **SearchAgent** - For finding specific items:
    - "Find me Sony headphones"
    - "Show me phones under $500"
    - "Do you have gaming keyboards?"
    
    The system automatically routes your query to the right agent(s) based on intent.
    
    Examples:
    ```
    "Recommend me a good laptop for programming"  → ProductExpertAgent
    "Find Apple products"                          → SearchAgent
    "Show me your best headphones"                 → Both agents
    ```
    """
    try:
        router = get_multi_agent_router()
        
        result = router.route_and_execute(
            query=request.query,
            user_id=request.user_id
        )
        
        # Determine which agent was used
        agent_used = []
        if "product_expert" in result.get("responses", {}):
            agent_used.append("ProductExpertAgent")
        if "search" in result.get("responses", {}):
            agent_used.append("SearchAgent")
        
        product_cards = result.get("product_cards", [])
        response_text = result["primary_response"]
        
        # Strip text-based product listings when we have product cards
        if product_cards:
            response_text = _strip_product_text(response_text)
        
        return MultiAgentResponse(
            query=result["query"],
            intent=result["intent"],
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            response=response_text,
            agent_used=" + ".join(agent_used) if agent_used else "Router",
            details=result.get("responses", {}),
            cart_actions=result.get("cart_actions", []),
            product_cards=product_cards,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/recommend")
async def get_recommendations(request: MultiAgentRequest):
    """
    **Direct access to ProductExpertAgent**
    
    Get personalized product recommendations based on:
    - User's purchase history (if user_id provided)
    - Trending products
    - Best deals and new arrivals
    - Products frequently bought together
    
    Examples:
    - "What should I buy for my home office?"
    - "Recommend gaming accessories"
    - "Best gifts for $100"
    """
    try:
        from agent_service.multi_agents import ProductExpertAgent
        
        agent = ProductExpertAgent()
        response = agent.recommend(
            query=request.query,
            user_id=request.user_id,
            context={"query_type": "recommendation"}
        )
        
        return {
            "query": request.query,
            "response": response,
            "agent": "ProductExpertAgent"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")


@router.post("/search")
async def search_products(request: MultiAgentRequest):
    """
    **Direct access to SearchAgent**
    
    Find specific products using natural language:
    - Search by keyword, brand, category
    - Filter by price range
    - Filter by rating
    
    Examples:
    - "Find Sony headphones"
    - "Show me phones under $500"
    - "Search for gaming keyboards"
    """
    try:
        from agent_service.multi_agents import SearchAgent
        
        agent = SearchAgent()
        response = agent.search(
            query=request.query,
            context={}
        )
        
        return {
            "query": request.query,
            "response": response,
            "agent": "SearchAgent"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/health")
async def health_check():
    """Check if multi-agent system is operational."""
    try:
        router = get_multi_agent_router()
        return {
            "status": "healthy",
            "agents": ["ProductExpertAgent", "SearchAgent", "AgentRouter"],
            "version": "2.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
