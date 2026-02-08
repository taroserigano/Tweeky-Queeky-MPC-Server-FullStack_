"""
Agent Gateway - Orchestrates MCP Tools and RAG (Port 7000)
Simple routing logic - no LLM needed yet
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import httpx
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Gateway", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
MCP_SERVER = "http://localhost:7001"
RAG_SERVER = "http://localhost:7002"

# ────────────────────────────────────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    sessionId: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    used: Dict[str, Any]
    debug: Optional[Dict[str, Any]] = None

# ────────────────────────────────────────────────────────────────────────────
# ROUTING LOGIC
# ────────────────────────────────────────────────────────────────────────────

async def handle_order_query(message: str) -> ChatResponse:
    """Handle order-related queries"""
    # Try to extract order ID from message
    order_match = re.search(r'ORD-\d+', message, re.IGNORECASE)
    order_id = order_match.group(0).upper() if order_match else "ORD-1001"
    
    logger.info(f"Handling order query for: {order_id}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{MCP_SERVER}/tools/getOrderStatus",
                json={"orderId": order_id},
                timeout=5.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("ok"):
                order = result["data"]
                reply = f"Order {order['orderId']} status: {order['status'].upper()}. "
                if order['status'] == 'shipped':
                    reply += f"Estimated delivery: {order['etaDate']}"
                elif order['status'] == 'delivered':
                    reply += "Your order has been delivered!"
                else:
                    reply += f"Expected delivery: {order['etaDate']}"
                
                return ChatResponse(
                    reply=reply,
                    used={"mcpTools": ["getOrderStatus"], "rag": False},
                    debug={"toolResponses": result}
                )
            else:
                return ChatResponse(
                    reply=f"Sorry, couldn't find order {order_id}.",
                    used={"mcpTools": ["getOrderStatus"], "rag": False},
                    debug={"toolResponses": result}
                )
        except Exception as e:
            logger.error(f"MCP call failed: {e}")
            return ChatResponse(
                reply=f"Sorry, I couldn't retrieve order information right now.",
                used={"mcpTools": ["getOrderStatus"], "rag": False},
                debug={"error": str(e)}
            )


async def handle_product_search(message: str) -> ChatResponse:
    """Handle product search/recommendation queries"""
    logger.info("Handling product search")
    
    # Extract price limit if mentioned (look for $XXX or "under XXX")
    price_match = re.search(r'(?:under|less than|below)?\s*\$?(\d+)', message, re.IGNORECASE)
    max_price = float(price_match.group(1)) if price_match else None
    
    # Extract search keywords - be less aggressive with cleaning
    # Remove special characters but preserve word boundaries
    cleaned = re.sub(r'[•"\']', '', message)  # Remove bullets and quotes
    # Remove filler words but use word boundaries to preserve actual product terms
    query = re.sub(r'\b(under|for|recommend|find|show|me|a|the|price|less|than|below)\b\s*', '', cleaned, flags=re.IGNORECASE)
    query = re.sub(r'\$?\d+', '', query)  # Remove all numbers (prices)
    query = re.sub(r'\s+', ' ', query).strip()  # Normalize whitespace
    
    logger.info(f"Cleaned query: '{query}', max_price: {max_price}")
    
    async with httpx.AsyncClient() as client:
        try:
            filters = {}
            if max_price:
                filters["maxPrice"] = max_price
            
            response = await client.post(
                f"{MCP_SERVER}/tools/searchProducts",
                json={"query": query, "filters": filters},
                timeout=5.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("ok"):
                products = result["data"]["products"]
                
                if not products:
                    reply = f"Sorry, I couldn't find any products matching '{query}'"
                    if max_price:
                        reply += f" under ${max_price}"
                else:
                    reply = f"Found {len(products)} product(s):\n\n"
                    for p in products[:5]:  # Show max 5
                        reply += f"• {p['name']} - ${p['price']:.2f}\n  {p['description']}\n\n"
                
                return ChatResponse(
                    reply=reply.strip(),
                    used={"mcpTools": ["searchProducts"], "rag": False},
                    debug={"toolResponses": result, "filters": filters}
                )
            else:
                return ChatResponse(
                    reply="Sorry, product search failed.",
                    used={"mcpTools": ["searchProducts"], "rag": False},
                    debug={"toolResponses": result}
                )
        except Exception as e:
            logger.error(f"MCP call failed: {e}")
            return ChatResponse(
                reply="Sorry, I couldn't search products right now.",
                used={"mcpTools": ["searchProducts"], "rag": False},
                debug={"error": str(e)}
            )


async def handle_rag_query(message: str) -> ChatResponse:
    """Handle general questions using RAG"""
    logger.info("Handling RAG query")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{RAG_SERVER}/rag/query",
                json={"question": message, "top_k": 3},
                timeout=5.0
            )
            response.raise_for_status()
            result = response.json()
            
            passages = result.get("passages", [])
            
            if not passages:
                reply = "I don't have specific information about that. Try asking about products, orders, or shipping."
            else:
                # Build reply from top passages
                reply = "Based on our documentation:\n\n"
                for i, passage in enumerate(passages[:2], 1):
                    reply += f"{passage['text']}\n\n"
                
                reply += f"\n(Source: {', '.join(set(p['sourceFile'] for p in passages))})"
            
            return ChatResponse(
                reply=reply.strip(),
                used={"rag": True, "mcpTools": []},
                debug={"ragPassages": passages}
            )
        except Exception as e:
            logger.error(f"RAG call failed: {e}")
            return ChatResponse(
                reply="Sorry, I couldn't retrieve information right now.",
                used={"rag": True, "mcpTools": []},
                debug={"error": str(e)}
            )


# ────────────────────────────────────────────────────────────────────────────
# MAIN ROUTING
# ────────────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Main chat endpoint - routes to appropriate handler"""
    message_lower = req.message.lower()
    
    logger.info(f"Chat message: {req.message}")
    
    # Route based on intent detection
    if any(word in message_lower for word in ["order", "tracking", "delivery", "ord-", "track my"]):
        return await handle_order_query(req.message)
    
    elif any(word in message_lower for word in ["price", "recommend", "under", "find", "show", "search", "product", "headphone", "laptop", "mouse", "chair", "monitor", "phone", "tablet", "$"]):
        return await handle_product_search(req.message)
    
    else:
        return await handle_rag_query(req.message)


@app.get("/health")
async def health():
    """Health check"""
    # Check if backend services are available
    services_status = {}
    
    async with httpx.AsyncClient() as client:
        try:
            mcp_response = await client.get(f"{MCP_SERVER}/health", timeout=2.0)
            services_status["mcp"] = "healthy" if mcp_response.status_code == 200 else "unhealthy"
        except:
            services_status["mcp"] = "unreachable"
        
        try:
            rag_response = await client.get(f"{RAG_SERVER}/health", timeout=2.0)
            services_status["rag"] = "healthy" if rag_response.status_code == 200 else "unhealthy"
        except:
            services_status["rag"] = "unreachable"
    
    return {
        "status": "healthy",
        "service": "agent-gateway",
        "backends": services_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
