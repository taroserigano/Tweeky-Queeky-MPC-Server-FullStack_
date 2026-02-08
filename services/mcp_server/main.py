"""
MCP Server - Tool Provider (Port 7001)
Exposes product and order tools as simple HTTP endpoints
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Tools Server", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────────────────────────────────────
# MOCK DATA (In-Memory)
# ────────────────────────────────────────────────────────────────────────────

PRODUCTS = [
    {"id": "P001", "name": "AirPods Pro", "description": "Noise-cancelling wireless earbuds", "price": 249.99, "category": "Audio"},
    {"id": "P002", "name": "Sony WH-1000XM5", "description": "Premium noise-cancelling headphones", "price": 399.99, "category": "Audio"},
    {"id": "P003", "name": "iPad Air", "description": "Lightweight powerful tablet", "price": 599.99, "category": "Tablets"},
    {"id": "P004", "name": "MacBook Air M2", "description": "Thin and light laptop", "price": 1199.99, "category": "Laptops"},
    {"id": "P005", "name": "Samsung Galaxy S24", "description": "Flagship Android smartphone", "price": 899.99, "category": "Phones"},
    {"id": "P006", "name": "Magic Mouse", "description": "Wireless rechargeable mouse", "price": 79.99, "category": "Accessories"},
    {"id": "P007", "name": "Herman Miller Aeron", "description": "Ergonomic office chair", "price": 1495.00, "category": "Furniture"},
    {"id": "P008", "name": "LG UltraFine 5K", "description": "27-inch 5K display", "price": 1299.99, "category": "Monitors"},
]

ORDERS = [
    {"orderId": "ORD-1001", "status": "shipped", "etaDate": (datetime.now() + timedelta(days=2)).isoformat(), "items": ["P001", "P006"]},
    {"orderId": "ORD-1002", "status": "processing", "etaDate": (datetime.now() + timedelta(days=5)).isoformat(), "items": ["P004"]},
    {"orderId": "ORD-1003", "status": "delivered", "etaDate": datetime.now().isoformat(), "items": ["P002"]},
]

# ────────────────────────────────────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ────────────────────────────────────────────────────────────────────────────

class SearchProductsRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class GetProductRequest(BaseModel):
    id: str

class GetOrderStatusRequest(BaseModel):
    orderId: str

class SuccessResponse(BaseModel):
    ok: bool = True
    data: Any

class ErrorResponse(BaseModel):
    ok: bool = False
    error: Dict[str, str]

# ────────────────────────────────────────────────────────────────────────────
# MIDDLEWARE
# ────────────────────────────────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"← {request.method} {request.url.path} - {response.status_code}")
    return response

# ────────────────────────────────────────────────────────────────────────────
# TOOL ENDPOINTS
# ────────────────────────────────────────────────────────────────────────────

# Synonyms for better matching
SYNONYMS = {
    "headphones": ["headphone", "earbuds", "earphone", "airpods", "audio", "wh-"],
    "laptop": ["macbook", "notebook", "computer"],
    "phone": ["smartphone", "iphone", "galaxy", "mobile"],
    "tablet": ["ipad"],
    "mouse": ["mice", "magic mouse"],
    "chair": ["aeron", "office chair", "ergonomic"],
    "monitor": ["display", "screen", "5k", "4k"],
}

def matches_query(product: dict, query: str) -> bool:
    """Check if product matches query with synonyms"""
    query_lower = query.lower().strip()
    if not query_lower:
        return True  # Empty query matches all
    
    # Check each word in query
    query_words = query_lower.split()
    searchable = (product["name"] + " " + product["description"] + " " + product["category"]).lower()
    
    for word in query_words:
        # Direct match
        if word in searchable:
            return True
        # Check synonyms
        for key, synonyms in SYNONYMS.items():
            if word == key or word in synonyms:
                for syn in synonyms + [key]:
                    if syn in searchable:
                        return True
    return False


@app.post("/tools/searchProducts", response_model=SuccessResponse)
async def search_products(req: SearchProductsRequest):
    """Search products by query with optional filters"""
    try:
        results = []
        
        for product in PRODUCTS:
            # Use improved matching
            if matches_query(product, req.query):
                # Apply filters
                if req.filters:
                    if "maxPrice" in req.filters and product["price"] > req.filters["maxPrice"]:
                        continue
                    if "category" in req.filters and product["category"].lower() != req.filters["category"].lower():
                        continue
                
                results.append(product)
        
        logger.info(f"Found {len(results)} products for query: {req.query}")
        return {"ok": True, "data": {"products": results, "count": len(results)}}
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail={"ok": False, "error": {"code": "SEARCH_ERROR", "message": str(e)}})


@app.post("/tools/getProduct", response_model=SuccessResponse)
async def get_product(req: GetProductRequest):
    """Get product details by ID"""
    try:
        product = next((p for p in PRODUCTS if p["id"] == req.id), None)
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail={"ok": False, "error": {"code": "NOT_FOUND", "message": f"Product {req.id} not found"}}
            )
        
        logger.info(f"Retrieved product: {product['name']}")
        return {"ok": True, "data": product}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product error: {e}")
        raise HTTPException(status_code=500, detail={"ok": False, "error": {"code": "GET_ERROR", "message": str(e)}})


@app.post("/tools/getOrderStatus", response_model=SuccessResponse)
async def get_order_status(req: GetOrderStatusRequest):
    """Get order status and ETA"""
    try:
        order = next((o for o in ORDERS if o["orderId"] == req.orderId), None)
        
        if not order:
            raise HTTPException(
                status_code=404,
                detail={"ok": False, "error": {"code": "NOT_FOUND", "message": f"Order {req.orderId} not found"}}
            )
        
        # Add 'id' field for consistency
        order_data = {**order, "id": order["orderId"]}
        logger.info(f"Retrieved order: {order['orderId']} - {order['status']}")
        return {"ok": True, "data": order_data}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get order error: {e}")
        raise HTTPException(status_code=500, detail={"ok": False, "error": {"code": "ORDER_ERROR", "message": str(e)}})


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "mcp-tools", "tools": 3}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7001)
