# Clean 3-Service Architecture: MCP + RAG + Agent

A **simplified FastAPI implementation** demonstrating proper separation of concerns with MCP, RAG, and an orchestrating Agent.

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ (React - Port 3000)
└──────┬──────┘
       │ Only talks to Agent Gateway
       ▼
┌─────────────────┐
│ Agent Gateway   │ (FastAPI - Port 7000)
│ - Routes queries│
│ - Orchestrates  │
└────┬──────┬─────┘
     │      │
     ▼      ▼
┌──────┐  ┌──────┐
│ MCP  │  │ RAG  │
│ Tools│  │ TF-  │
│ :7001│  │ IDF  │
│      │  │ :7002│
└──────┘  └──────┘
```

### Services

1. **MCP Server** (Port 7001) - Tool Provider
   - `POST /tools/searchProducts` - Search with filters
   - `POST /tools/getProduct` - Get product by ID
   - `POST /tools/getOrderStatus` - Track orders
   - Uses in-memory mock data (no database)

2. **RAG Service** (Port 7002) - Document Retrieval
   - `POST /rag/query` - Semantic search in docs
   - Simple TF-IDF scoring (no vector DB)
   - Loads markdown files on startup

3. **Agent Gateway** (Port 7000) - Orchestrator
   - `POST /chat` - Main endpoint for frontend
   - Routes to MCP or RAG based on intent:
     - "order" → calls MCP getOrderStatus
     - "price"/"recommend" → calls MCP searchProducts
     - Otherwise → calls RAG query

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# MCP Server
cd services/mcp_server
pip install -r requirements.txt

# RAG Service
cd ../rag_service
pip install -r requirements.txt

# Agent Gateway
cd ../agent_gateway
pip install -r requirements.txt
```

### 2. Start All Services

**Windows:**
```cmd
run_all.bat
```

**Linux/Mac:**
```bash
chmod +x run_all.sh
./run_all.sh
```

**Or start individually:**
```bash
# Terminal 1 - MCP Server
cd services/mcp_server
python main.py

# Terminal 2 - RAG Service
cd services/rag_service
python main.py

# Terminal 3 - Agent Gateway
cd services/agent_gateway
python main.py
```

### 3. Test with curl

```bash
# Health checks
curl http://localhost:7000/health
curl http://localhost:7001/health
curl http://localhost:7002/health

# Chat with agent (order query - uses MCP)
curl -X POST http://localhost:7000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Track order ORD-1001"}'

# Chat with agent (product search - uses MCP)
curl -X POST http://localhost:7000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me headphones under $300"}'

# Chat with agent (general question - uses RAG)
curl -X POST http://localhost:7000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your return policy?"}'

# Direct MCP tool call (if needed for testing)
curl -X POST http://localhost:7001/tools/searchProducts \
  -H "Content-Type: application/json" \
  -d '{"query": "headphones", "filters": {"maxPrice": 300}}'

# Direct RAG query (if needed for testing)
curl -X POST http://localhost:7002/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "shipping times", "top_k": 3}'
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm start
```

Visit http://localhost:3000/ai

## 📦 What's Included

### Mock Data (MCP Server)
- 8 products (headphones, laptops, tablets, accessories)
- 3 sample orders with tracking info

### Documents (RAG Service)
Auto-generated in `services/rag_service/docs/`:
- `products.md` - Product catalog info
- `shipping.md` - Delivery and returns
- `support.md` - Contact and support

### Agent Routing Logic
- **Order queries** → MCP `getOrderStatus`
- **Product queries** → MCP `searchProducts`
- **General questions** → RAG document retrieval

## 🎯 Key Features

✅ **No external dependencies** - No MongoDB, no Pinecone, no OpenAI  
✅ **Simple & clear** - Easy to understand architecture  
✅ **MCP hidden from frontend** - Proper separation of concerns  
✅ **Fully local** - Runs without API keys  
✅ **Request logging** - See what's happening  
✅ **Type-safe** - Pydantic models for validation  

## 🔍 Response Format

Agent responses include:
- `reply` - User-facing message
- `used` - Which tools were called (MCP/RAG)
- `debug` - Tool responses for inspection

Example:
```json
{
  "reply": "Order ORD-1001 status: SHIPPED. Estimated delivery: 2026-01-28",
  "used": {
    "mcpTools": ["getOrderStatus"],
    "rag": false
  },
  "debug": {
    "toolResponses": { ... }
  }
}
```

## 🎨 Frontend Integration

The frontend (`SimpleAIHub.jsx`) shows:
- Clean chat interface
- Tool badges showing what was used
- Architecture diagram
- Only calls `/chat` endpoint

**No MCP-specific code in frontend** - it's hidden behind the agent!

## 📚 Next Steps

1. Add real LLM (OpenAI) to agent for smarter routing
2. Add more MCP tools (reviews, recommendations)
3. Enhance RAG with better chunking strategies
4. Add conversation memory to agent
5. Deploy services in containers

## 🤝 Architecture Benefits

1. **Modularity** - Each service is independent
2. **Testability** - Easy to test each service separately
3. **Scalability** - Services can scale independently
4. **Clarity** - Clear responsibilities for each component
5. **Portfolio-ready** - Demonstrates modern AI patterns

---

**This is the clean, minimal version.** MCP is just a tool provider, RAG is just a document retriever, and the Agent orchestrates both.
