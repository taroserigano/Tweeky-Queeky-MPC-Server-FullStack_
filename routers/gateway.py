"""
Gateway Proxy Router

Forwards requests from the main backend to the Agent Gateway (port 7000),
which orchestrates MCP Server (7001) and RAG Service (7002).

Architecture:
  Frontend (3000) → Main Backend (5000) → Agent Gateway (7000) → MCP (7001) / RAG (7002)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gateway", tags=["gateway"])

GATEWAY_URL = "http://localhost:7000"
MCP_URL = "http://localhost:7001"
RAG_URL = "http://localhost:7002"


# ──────────────────────────────────────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────────────────────────────────────

class GatewayChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's message")
    sessionId: Optional[str] = None


class GatewayChatResponse(BaseModel):
    reply: str
    used: Dict[str, Any]
    debug: Optional[Dict[str, Any]] = None


class ServiceHealth(BaseModel):
    service: str
    status: str
    details: Optional[Dict[str, Any]] = None


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=GatewayChatResponse)
async def gateway_chat(request: GatewayChatRequest):
    """
    **MCP + RAG Gateway Chat**

    Routes your message through the 3-service architecture:
    - **MCP Server** (7001): Product search, order tracking
    - **RAG Service** (7002): Document retrieval (shipping, support, product guides)
    - **Agent Gateway** (7000): Intent detection & routing

    Examples:
    - "Show me headphones under $300" → MCP product search
    - "What's your return policy?" → RAG document retrieval
    - "Track order ORD-1001" → MCP order status
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{GATEWAY_URL}/chat",
                json={"message": request.message, "sessionId": request.sessionId},
            )
            response.raise_for_status()
            data = response.json()
            return GatewayChatResponse(**data)
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Agent Gateway (port 7000) is not reachable. Start it with: python start_all_services.py",
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"Gateway proxy error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def gateway_health():
    """Health check for all 3 microservices"""
    services = {}

    async with httpx.AsyncClient(timeout=3.0) as client:
        # Agent Gateway
        try:
            r = await client.get(f"{GATEWAY_URL}/health")
            services["agent_gateway"] = {"status": "healthy", "port": 7000, **r.json()}
        except Exception:
            services["agent_gateway"] = {"status": "unreachable", "port": 7000}

        # MCP Server
        try:
            r = await client.get(f"{MCP_URL}/health")
            services["mcp_server"] = {"status": "healthy", "port": 7001, **r.json()}
        except Exception:
            services["mcp_server"] = {"status": "unreachable", "port": 7001}

        # RAG Service
        try:
            r = await client.get(f"{RAG_URL}/health")
            services["rag_service"] = {"status": "healthy", "port": 7002, **r.json()}
        except Exception:
            services["rag_service"] = {"status": "unreachable", "port": 7002}

    all_healthy = all(s["status"] == "healthy" for s in services.values())

    return {
        "architecture": "MCP + RAG + Agent Gateway",
        "all_healthy": all_healthy,
        "services": services,
    }
