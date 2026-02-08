"""
Agent Router - REST API endpoints for the LangGraph shopping agent

Exposes the LangGraph-based agentic AI assistant through REST endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid
import json
import asyncio
import re

from agent_service import get_shopping_agent, ShoppingAgentLangGraph


router = APIRouter(prefix="/api/agent", tags=["agent"])


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def clean_response_formatting(text: str) -> str:
    """Remove markdown bold formatting for better chat display"""
    # Remove **bold** markdown
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    return text


def strip_product_text(text: str, has_products: bool) -> str:
    """Strip text-based product listings when product cards are shown."""
    if not has_products or not text:
        return text
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        t = line.strip()
        if not t:
            continue
        if re.match(r'^\d+\.\s+', t):
            continue
        if re.match(r'^[•\-\*]\s+', t):
            continue
        if re.search(r'\$\d+(\.\d{2})?', t):
            continue
        if re.search(r'[⭐★]', t) or re.search(r'\d\.\d/5', t):
            continue
        if re.search(r'found\s+\d+\s+product', t, re.IGNORECASE):
            continue
        if re.match(r'^(my\s+)?recommendations?:', t, re.IGNORECASE):
            continue
        if re.search(r'here\s+are\s+(some|the)\s+(picks|best|top|highest|great)', t, re.IGNORECASE):
            continue
        if re.match(r'^top\s+\d+\s+rated', t, re.IGNORECASE):
            continue
        if t == '---':
            continue
        cleaned.append(line)
    result = '\n'.join(cleaned).strip()
    return result if result else "Here are the products I found for you!"


# ──────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message to the agent")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="Optional user identifier")


class ChatResponse(BaseModel):
    message: str = Field(description="Agent's response message")
    thread_id: str = Field(description="Thread ID for this conversation")
    tool_calls: List[Dict[str, Any]] = Field(description="Tools that were called")
    products: List[Dict[str, Any]] = Field(default=[], description="Structured product results")
    preferences: Dict[str, Any] = Field(description="Extracted user preferences")
    framework: str = Field(default="langgraph", description="Framework used")


class StreamChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    thread_id: Optional[str] = Field(None, description="Thread ID")


class ThreadHistoryResponse(BaseModel):
    thread_id: str
    messages: List[Dict[str, Any]]
    message_count: int


# ──────────────────────────────────────────────────────────────────────────────
# Chat Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the LangGraph shopping assistant.
    
    The agent uses a state machine architecture to:
    - Understand your request using natural language
    - Call appropriate tools (search, compare, etc.)
    - Maintain conversation state across messages
    - Extract and remember your preferences
    
    Examples:
    - "Find me a comfortable office chair under $300"
    - "Compare the Sony headphones with the Bose ones"
    - "What's a good gift for a music lover?"
    - "Build me a home office setup for $1000"
    
    Use thread_id to maintain conversation context across requests.
    """
    try:
        agent = get_shopping_agent()
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or str(uuid.uuid4())[:8]
        
        # Run the agent with timeout
        try:
            result = await asyncio.wait_for(
                agent.chat(
                    message=request.message,
                    thread_id=thread_id,
                    user_id=request.user_id,
                ),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Request timed out. The agent took too long to respond. Please try a simpler query."
            )
        
        # Clean markdown formatting for better chat display
        cleaned_message = clean_response_formatting(result["response"])
        products = result.get("products", [])
        
        # Strip text-based product listings when product cards exist
        cleaned_message = strip_product_text(cleaned_message, len(products) > 0)
        
        return ChatResponse(
            message=cleaned_message,
            thread_id=result["thread_id"],
            tool_calls=result.get("tool_calls", []),
            products=products,
            preferences=result.get("preferences", {}),
            framework="langgraph",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: StreamChatRequest):
    """
    Stream a chat response with real-time updates.
    
    Returns a Server-Sent Events stream with:
    - Tool call events as they happen
    - Token-by-token response generation
    - Final result with full context
    
    Useful for real-time UI updates.
    """
    try:
        agent = get_shopping_agent()
        thread_id = request.thread_id or str(uuid.uuid4())[:8]
        
        async def event_generator():
            async for event in agent.stream_chat(
                message=request.message,
                thread_id=thread_id,
            ):
                # Format event for SSE
                event_type = event.get("event", "unknown")
                data = json.dumps({
                    "event": event_type,
                    "data": event.get("data", {}),
                })
                yield f"data: {data}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# Thread/Session Management
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/threads/{thread_id}", response_model=ThreadHistoryResponse)
async def get_thread_history(thread_id: str):
    """
    Get conversation history for a thread.
    
    Returns all messages in the conversation including:
    - User messages
    - Agent responses
    - Tool calls and results
    """
    try:
        agent = get_shopping_agent()
        history = agent.get_conversation_history(thread_id)
        
        return ThreadHistoryResponse(
            thread_id=thread_id,
            messages=history,
            message_count=len(history),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/threads/{thread_id}")
async def clear_thread(thread_id: str):
    """
    Clear conversation history for a thread.
    
    Note: With MemorySaver, this may not fully clear history.
    For production, use PostgresSaver for full control.
    """
    try:
        agent = get_shopping_agent()
        agent.clear_conversation(thread_id)
        
        return {
            "status": "cleared",
            "thread_id": thread_id,
            "message": "Thread history cleared",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/threads/new")
async def create_new_thread():
    """
    Create a new conversation thread.
    
    Returns a new thread_id for fresh conversation.
    """
    thread_id = str(uuid.uuid4())[:8]
    
    return {
        "thread_id": thread_id,
        "message": "New thread created. Use this thread_id in your chat requests.",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Quick Action Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/quick/search")
async def quick_search(
    q: str = Query(..., min_length=1, description="Search query"),
    max_price: Optional[float] = Query(None, ge=0),
    category: Optional[str] = Query(None),
):
    """
    Quick product search without full agent conversation.
    
    Directly calls the semantic_search tool for fast results.
    """
    try:
        from agent_service.langgraph_agent import semantic_search
        
        # Tools are sync, not async - use invoke, not ainvoke
        result = semantic_search.invoke({
            "query": q,
            "max_price": max_price,
            "category": category,
            "top_k": 5,
        })
        
        return {
            "query": q,
            "results": result,
            "framework": "langgraph",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quick/recommend")
async def quick_recommend(
    limit: int = Query(default=5, ge=1, le=20),
):
    """
    Quick top product recommendations without full agent.
    
    Uses MCP tool if available, otherwise falls back to direct DB query.
    """
    try:
        # Try MCP first
        try:
            from mcp_service.client import get_mcp_client
            client = await get_mcp_client()
            if client.is_connected:
                result = await client.call_tool("get_top_products", {"limit": limit})
                return {
                    "recommendations": result,
                    "source": "mcp",
                    "framework": "langgraph",
                }
        except Exception:
            pass
        
        # Fallback to direct DB query (reuses connection pool)
        from config.database import get_sync_db
        
        db = get_sync_db()
        
        products = list(
            db.products.find()
            .sort([("rating", -1), ("numReviews", -1)])
            .limit(limit)
        )
        
        result = []
        for p in products:
            result.append({
                "id": str(p["_id"]),
                "name": p.get("name", ""),
                "brand": p.get("brand", ""),
                "price": p.get("price", 0),
                "rating": p.get("rating", 0),
            })
        
        return {
            "recommendations": result,
            "source": "native",
            "framework": "langgraph",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# Agent Info
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/info")
async def get_agent_info():
    """
    Get information about the agent's capabilities.
    
    Shows which tools are native vs MCP-powered.
    """
    agent = get_shopping_agent()
    await agent._ensure_initialized()
    
    tools_info = agent.get_tools_info()
    
    native_tools_desc = []
    from agent_service.langgraph_agent import NATIVE_TOOLS
    for tool in NATIVE_TOOLS:
        native_tools_desc.append({
            "name": tool.name,
            "description": tool.description,
            "source": "native",
        })
    
    mcp_tools_desc = []
    from agent_service.langgraph_agent import _mcp_tools
    for tool in _mcp_tools:
        mcp_tools_desc.append({
            "name": tool.name,
            "description": tool.description,
            "source": "mcp",
        })
    
    return {
        "name": "TweekySqueeky Shopping Assistant",
        "framework": "LangGraph + MCP",
        "model": "gpt-4o-mini",
        "architecture": {
            "description": "Hybrid architecture combining RAG, Agentic AI, and MCP",
            "components": [
                "RAG (Pinecone + LangChain) - Semantic product search",
                "LangGraph - Agent orchestration with memory",
                "MCP - Simple CRUD operations via Model Context Protocol",
            ],
        },
        "tools": {
            "native": native_tools_desc,
            "mcp": mcp_tools_desc,
            "total_count": tools_info["total"],
            "mcp_enabled": tools_info["mcp_enabled"],
        },
        "features": [
            "Natural language understanding",
            "Semantic product search (RAG-powered)",
            "MCP-powered product lookups",
            "Product comparison",
            "Personalized recommendations",
            "Conversation memory (LangGraph)",
            "Preference learning",
        ],
        "memory": "LangGraph MemorySaver (in-memory)",
    }


@router.get("/tools")
async def get_agent_tools():
    """
    Get detailed list of all agent tools (native + MCP).
    """
    agent = get_shopping_agent()
    await agent._ensure_initialized()
    
    return agent.get_tools_info()


@router.get("/health")
async def agent_health_check():
    """Check agent service health including MCP status."""
    try:
        agent = get_shopping_agent()
        await agent._ensure_initialized()
        
        tools_info = agent.get_tools_info()
        
        return {
            "status": "healthy",
            "framework": "langgraph",
            "agent_type": "ShoppingAgentLangGraph",
            "mcp_enabled": tools_info["mcp_enabled"],
            "tools": {
                "native": len(tools_info["native_tools"]),
                "mcp": len(tools_info["mcp_tools"]),
                "total": tools_info["total"],
            },
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/status")
async def agent_status():
    """
    Get agent status for frontend monitoring.
    Returns operational status and available capabilities.
    """
    try:
        agent = get_shopping_agent()
        await agent._ensure_initialized()
        
        tools_info = agent.get_tools_info()
        
        return {
            "status": "operational",
            "framework": "langgraph",
            "capabilities": {
                "semantic_search": True,
                "product_recommendations": True,
                "product_comparison": True,
                "cart_building": True,
                "conversation_memory": True,
            },
            "tools_count": tools_info["total"],
            "mcp_enabled": tools_info["mcp_enabled"],
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "capabilities": {},
            "tools_count": 0,
            "mcp_enabled": False,
        }
