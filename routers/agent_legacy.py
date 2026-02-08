"""
Agent Router - REST API endpoints for the shopping agent

Exposes the agentic AI assistant through REST endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid

from agent_service.agent import ShoppingAgent
from agent_service.memory import ConversationMemory, SessionMemory


router = APIRouter(prefix="/api/agent", tags=["agent"])


# ──────────────────────────────────────────────────────────────────────────────
# In-memory session storage (use Redis in production)
# ──────────────────────────────────────────────────────────────────────────────

_sessions: Dict[str, SessionMemory] = {}
_conversations: Dict[str, ConversationMemory] = {}


def _get_or_create_session(session_id: Optional[str]) -> tuple[str, SessionMemory, ConversationMemory]:
    """Get existing session or create new one"""
    if session_id and session_id in _sessions:
        return session_id, _sessions[session_id], _conversations[session_id]
    
    # Create new session
    new_id = str(uuid.uuid4())[:8]
    _sessions[new_id] = SessionMemory(session_id=new_id)
    _conversations[new_id] = ConversationMemory(
        system_prompt=ShoppingAgent.SYSTEM_PROMPT,
        max_messages=30,
    )
    
    return new_id, _sessions[new_id], _conversations[new_id]


# ──────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message to the agent")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    message: str
    session_id: str
    products_mentioned: List[str]
    steps_taken: int
    success: bool


class DetailedChatResponse(BaseModel):
    message: str
    session_id: str
    products_mentioned: List[str]
    steps: List[Dict[str, Any]]
    success: bool
    session_context: Dict[str, Any]


class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    preferences: Dict[str, Any]
    recently_viewed: List[str]
    message_count: int


class SetPreferenceRequest(BaseModel):
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_categories: Optional[List[str]] = None
    preferred_brands: Optional[List[str]] = None


# ──────────────────────────────────────────────────────────────────────────────
# Chat Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the shopping assistant agent.
    
    The agent will:
    - Understand your request using natural language
    - Search for relevant products
    - Compare options
    - Provide personalized recommendations
    
    Examples:
    - "Find me a comfortable office chair under $300"
    - "Compare the Sony headphones with the Bose ones"
    - "What's a good gift for a music lover?"
    - "Build me a home office setup for $1000"
    
    Use session_id to maintain conversation context across requests.
    """
    try:
        # Get or create session
        session_id, session, conversation = _get_or_create_session(request.session_id)
        
        # Create agent and run
        agent = ShoppingAgent()
        response = await agent.run(
            user_message=request.message,
            conversation=conversation,
            session=session,
        )
        
        # Track viewed products in session
        for product_id in response.products_mentioned:
            session.add_viewed_product(product_id)
        
        return ChatResponse(
            message=response.message,
            session_id=session_id,
            products_mentioned=response.products_mentioned,
            steps_taken=len(response.steps),
            success=response.success,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/detailed", response_model=DetailedChatResponse)
async def chat_detailed(request: ChatRequest):
    """
    Send a message to the agent with detailed response including reasoning steps.
    
    Same as /chat but includes:
    - All reasoning steps the agent took
    - Tool calls and their results
    - Session context information
    
    Useful for debugging and understanding agent behavior.
    """
    try:
        session_id, session, conversation = _get_or_create_session(request.session_id)
        
        agent = ShoppingAgent()
        response = await agent.run(
            user_message=request.message,
            conversation=conversation,
            session=session,
        )
        
        for product_id in response.products_mentioned:
            session.add_viewed_product(product_id)
        
        # Format steps for response
        steps = []
        for step in response.steps:
            steps.append({
                "state": step.state.value,
                "thought": step.thought,
                "action": step.action,
                "action_input": step.action_input,
                "observation": step.observation[:500] if step.observation else None,
                "error": step.error,
            })
        
        return DetailedChatResponse(
            message=response.message,
            session_id=session_id,
            products_mentioned=response.products_mentioned,
            steps=steps,
            success=response.success,
            session_context=session.to_dict(),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# Session Management
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """
    Get session information including preferences and history.
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = _sessions[session_id]
    conversation = _conversations.get(session_id)
    
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at.isoformat(),
        preferences=session.preferences,
        recently_viewed=list(session.recently_viewed),
        message_count=len(conversation.messages) if conversation else 0,
    )


@router.post("/session/{session_id}/preferences")
async def set_preferences(session_id: str, request: SetPreferenceRequest):
    """
    Set user preferences for a session.
    
    Preferences help the agent make better recommendations:
    - budget_min/max: Price range
    - preferred_categories: Categories of interest
    - preferred_brands: Favorite brands
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = _sessions[session_id]
    
    if request.budget_min is not None:
        session.set_preference("budget_min", request.budget_min)
    if request.budget_max is not None:
        session.set_preference("budget_max", request.budget_max)
    if request.preferred_categories is not None:
        session.set_preference("preferred_categories", request.preferred_categories)
    if request.preferred_brands is not None:
        session.set_preference("preferred_brands", request.preferred_brands)
    
    return {"status": "updated", "preferences": session.preferences}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its conversation history.
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del _sessions[session_id]
    if session_id in _conversations:
        del _conversations[session_id]
    
    return {"status": "deleted", "session_id": session_id}


@router.post("/session/new")
async def create_session():
    """
    Create a new session explicitly.
    
    Returns a session_id to use in subsequent chat requests.
    """
    session_id, session, _ = _get_or_create_session(None)
    
    return {
        "session_id": session_id,
        "created_at": session.created_at.isoformat(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Quick Actions (Direct tool access without full agent loop)
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/quick/search")
async def quick_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(5, ge=1, le=20),
    max_price: Optional[float] = Query(None),
):
    """
    Quick semantic search without full agent conversation.
    
    For simple searches where you don't need the agent's reasoning.
    """
    from rag_service.retriever import RAGRetriever
    
    retriever = RAGRetriever()
    results = await retriever.search_with_filters(
        query=q,
        max_price=max_price,
        top_k=limit,
    )
    
    return {
        "query": q,
        "results": [
            {
                "id": r.product_id,
                "score": round(r.score, 3),
                **r.product,
            }
            for r in results
        ],
    }


@router.get("/quick/recommend")
async def quick_recommend(
    preferences: str = Query(..., description="What you're looking for"),
    budget: Optional[float] = Query(None),
    limit: int = Query(5, ge=1, le=10),
):
    """
    Quick product recommendations without full agent conversation.
    """
    from rag_service.retriever import RAGRetriever
    
    retriever = RAGRetriever()
    results = await retriever.search_with_filters(
        query=preferences,
        max_price=budget,
        top_k=limit,
    )
    
    return {
        "preferences": preferences,
        "budget": budget,
        "recommendations": [
            {
                "id": r.product_id,
                "match_score": round(r.score, 3),
                "name": r.product.get("name"),
                "price": r.product.get("price"),
                "rating": r.product.get("rating"),
                "why": f"Matches '{preferences}' with {round(r.score * 100)}% relevance",
            }
            for r in results
        ],
    }
