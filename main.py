from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from pathlib import Path
import os
import signal
import sys
import logging

logger = logging.getLogger(__name__)

from config.database import init_db, close_db
from config.settings import settings
from services.hybrid_search import hybrid_engine
from routers import users_router, products_router, orders_router, upload_router, rag_router, agent_router
from routers.multi_agent import router as multi_agent_router
from routers.gateway import router as gateway_router


# MCP Client for cleanup
_mcp_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle handler for startup and shutdown"""
    global _mcp_client
    
    # Startup
    print("[Startup] Initializing database...")
    await init_db()
    
    # Initialize hybrid search engine (BM25 + semantic embeddings)
    print("[Startup] Building hybrid search index (BM25 + OpenAI embeddings)...")
    try:
        hs_status = await hybrid_engine.initialize()
        print(f"[Startup] Hybrid search ready: {hs_status}")
    except Exception as e:
        print(f"[Startup] Hybrid search init failed (will fallback to regex): {e}")
    
    # MCP/RAG/Gateway microservices run on separate ports (7000-7002)
    print("[Startup] Gateway proxy registered (-> Agent Gateway :7000 -> MCP :7001 / RAG :7002)")
    print("[Startup] Server ready!")
    
    yield
    
    # Shutdown - cleanup all resources
    print("\n[Shutdown] Closing database connections...")
    await close_db()
    print("[Shutdown] Cleanup complete!")


app = FastAPI(
    title="Tweeky Queeky Shop API",
    description="Modern ecommerce platform API built with FastAPI",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://18.118.137.212",  # Frontend ECS Fargate public IP
        "*"  # Allow all origins in production (or specify your domain)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors with request body for debugging"""
    try:
        body_str = exc.body if exc.body else "<no body>"
    except Exception:
        body_str = "<could not read body>"
    
    logger.error(f"[VALIDATION ERROR] {request.method} {request.url}")
    logger.error(f"[VALIDATION ERROR] Body: {body_str}")
    logger.error(f"[VALIDATION ERROR] Errors: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


# Mount static files for uploads
upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(users_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(upload_router)
# MCP is internal - used only by agent, not exposed via HTTP
app.include_router(rag_router)
app.include_router(agent_router)
app.include_router(multi_agent_router)  # AI multi-agent recommendation system
app.include_router(gateway_router)  # MCP + RAG gateway proxy (7000/7001/7002)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "API is running..."}


@app.get("/api/health")
async def health_check():
    """Health check endpoint with connection pool stats"""
    from config.database import get_pool_stats
    
    mcp_status = "unknown"
    mcp_tools = []
    
    try:
        from mcp_service.client import get_mcp_client
        client = await get_mcp_client()
        if client.is_connected:
            mcp_status = "connected"
            mcp_tools = client.get_available_tools()
        else:
            mcp_status = "disconnected"
    except Exception as e:
        mcp_status = f"error: {str(e)[:50]}"
    
    pool_stats = get_pool_stats()
    
    return {
        "status": "healthy",
        "message": "API is running",
        "services": {
            "database": "connected",
            "mcp_server": mcp_status,
            "mcp_tools_count": len(mcp_tools),
            "hybrid_search": hybrid_engine.health(),
        },
        "connection_pools": pool_stats
    }


@app.get("/api/mcp/status")
async def mcp_status():
    """Get MCP server status and available tools"""
    try:
        from mcp_service.client import get_mcp_client
        client = await get_mcp_client()
        
        return {
            "status": "connected" if client.is_connected else "disconnected",
            "tools": client.get_available_tools(),
            "tools_count": len(client.get_available_tools()),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "tools": [],
            "tools_count": 0,
        }


@app.get("/api/config/paypal")
async def get_paypal_config():
    """Get PayPal client ID"""
    client_id = settings.PAYPAL_CLIENT_ID or ""
    print(f"[CONFIG] PayPal Client ID: {client_id[:20] if client_id else 'NOT SET'}...")
    return {"clientId": client_id}


@app.get("/api/config/stripe")
async def get_stripe_config():
    """Get Stripe publishable key"""
    key = settings.STRIPE_PUBLISHABLE_KEY or ""
    print(f"[CONFIG] Stripe Publishable Key: {key[:20] if key else 'NOT SET'}...")
    return {"publishableKey": key}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": str(exc) if settings.NODE_ENV == "development" else "Internal server error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.NODE_ENV == "development"
    )
