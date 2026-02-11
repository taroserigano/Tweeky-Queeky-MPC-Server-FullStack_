# MCP Server Integration Plan

**Portfolio Project: RAG + Agentic AI + MCP Showcase**

## 🎯 Goal

Integrate the MCP server into the portfolio to demonstrate:

- **RAG**: Vector search with Pinecone + LangChain
- **Agentic AI**: LangGraph multi-agent system with memory
- **MCP**: Model Context Protocol for AI-powered shopping assistant tools

## 📋 Current State

### What Exists ✅

- MCP server with 20+ tools in `mcp_server/server.py`
- LangGraph agent with 8 native tools in `agent_service/langgraph_agent.py`
- RAG service with Pinecone vector search
- HTTP endpoints exposing MCP-like features in `routers/mcp.py`
- Comprehensive test suite (116 tests passing)

### What's Missing ❌

- MCP server not running with the main app
- LangGraph agent doesn't use MCP tools
- No MCP client integration
- MCP capabilities not showcased in frontend
- No documentation highlighting MCP integration

## 🏗️ Architecture Design

### Clear Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                    ┌──────────────┐     │
│  │  RAG Service │                    │ MCP Server   │     │
│  │  (Pinecone)  │                    │ (FastMCP)    │     │
│  │              │                    │              │     │
│  │ • Search     │                    │ • Get info   │     │
│  │ • Recommend  │                    │ • List items │     │
│  │ • Compare    │                    │ • Stats      │     │
│  │ • Q&A        │                    │ • Basic CRUD │     │
│  └──────────────┘                    └──────────────┘     │
│         │                                    │              │
│         └──────────┬─────────────────────────┘              │
│                    │                                        │
│           ┌────────▼────────┐                               │
│           │ LangGraph Agent │                               │
│           │                 │                               │
│           │  Routing Logic: │                               │
│           │  - Complex query? → RAG                         │
│           │  - Simple fetch? → MCP                          │
│           │                 │                               │
│           └─────────────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Division of Responsibilities:**

**RAG (Complex, Knowledge-Based):**

- Semantic product search
- AI recommendations
- Product comparisons
- Product Q&A
- "Find products similar to..."

**MCP (Simple, Direct Operations):**

- Get product by ID
- List products (basic pagination)
- Catalog statistics
- Category listings
- Simple info retrieval

## 📝 Implementation Steps

### Phase 1: MCP Client Service (Day 1)

**File:** `mcp_service/client.py`

Create an MCP client that:

- Connects to the MCP server (stdio transport)
- Provides async methods to call MCP tools
- Handles connection lifecycle
- Caches tool schemas

**Tasks:**

- [ ] Create `mcp_service/` directory
- [ ] Implement `MCPClient` class
- [ ] Add connection management (startup/shutdown)
- [ ] Add tool discovery and calling methods
- [ ] Create helper to convert MCP tools to LangChain tools

### Phase 2: LangGraph Agent Integration (Day 1-2)

**File:** `agent_service/langgraph_agent.py`

Enhance the agent to:

- Load MCP tools on startup
- Add MCP tools to the agent's tool list
- Use tool calling to decide between native/MCP tools
- Track which tools are from MCP (for analytics)

**Tasks:**

- [ ] Initialize MCP client in agent service
- [ ] Wrap MCP tools as LangChain tools
- [ ] Add MCP tools to agent state
- [ ] Update system prompt to mention MCP capabilities
- [ ] Add MCP tool usage tracking

### Phase 3: FastAPI Lifecycle Integration (Day 2)

**File:** `main.py`

Start MCP server with the app:

- [ ] Add MCP server startup in lifespan hook
- [ ] Run MCP server in background thread/process
- [ ] Graceful shutdown on app close
- [ ] Health check for MCP server
- [ ] Environment variable for MCP server path

### Phase 4: API Endpoints (Day 2)

**New File:** `routers/mcp_showcase.py`

Create demo endpoints:

- [ ] `GET /api/mcp/status` - MCP server health
- [ ] `GET /api/mcp/tools` - List available MCP tools
- [ ] `POST /api/mcp/call` - Direct MCP tool execution (demo)
- [ ] `GET /api/agent/tools` - Show agent's native + MCP tools
- [ ] `POST /api/agent/chat-with-mcp` - Chat highlighting MCP usage

### Phase 5: Testing (Day 3)

**File:** `tests/mcp/test_mcp_integration.py`

Test the integration:

- [ ] Test MCP client connection
- [ ] Test MCP tool discovery
- [ ] Test agent using MCP tools
- [ ] Test native vs MCP tool selection
- [ ] Test MCP server lifecycle with FastAPI
- [ ] Test error handling (MCP server down)

### Phase 6: Documentation (Day 3)

**Files:** `README.md`, `docs/MCP_SHOWCASE.md`

Document for portfolio:

- [ ] Update main README with MCP section
- [ ] Create dedicated MCP showcase doc
- [ ] Add architecture diagrams
- [ ] Document MCP tools vs native tools
- [ ] Add "Try It" examples
- [ ] Create Postman/curl examples

### Phase 7: Frontend Demo (Day 4 - Optional)

**Files:** `frontend/src/screens/MCPDemoScreen.jsx`

Create UI to showcase:

- [ ] MCP server status indicator
- [ ] Available MCP tools list
- [ ] Live chat showing which tools are used
- [ ] Side-by-side comparison: Native vs MCP tools
- [ ] Visual tool execution flow

## 🔧 Technical Details

### MCP Tools to Integrate (Priority)

**Simple CRUD Operations (MCP Handles):**

- ✅ `list_products` - Basic product listing with filters
- ✅ `get_product` - Get product by ID
- ✅ `get_product_reviews` - Get reviews for a product
- ✅ `catalog_stats` - Simple catalog statistics
- ✅ `get_top_products` - Top rated products (simple sort)
- ✅ `category_price_summary` - Category price stats

**Keep as Native/RAG (Complex Operations):**

- ❌ `recommend_products` - Keep in RAG (AI-powered)
- ❌ `compare_products` - Keep in RAG (complex analysis)
- ❌ `build_cart_suggestion` - Keep in RAG (AI reasoning)
- ❌ `explain_product` - Keep in RAG (LLM generation)
- ❌ `answer_product_question` - Keep in RAG (semantic Q&A)
- ❌ `semantic_search` - Keep in RAG (vector search)

### LangChain Tool Wrapper

```python
from langchain.tools import Tool
from mcp_service.client import MCPClient

def wrap_mcp_tool(mcp_client: MCPClient, tool_name: str) -> Tool:
    """Convert MCP tool to LangChain tool"""
    tool_info = await mcp_client.get_tool_info(tool_name)

    return Tool(
        name=f"mcp_{tool_name}",  # Prefix to distinguish
        description=tool_info.description,
        func=lambda **kwargs: mcp_client.call_tool(tool_name, kwargs),
        coroutine=mcp_client.call_tool_async,
    )
```

### Agent System Prompt Update

```
You are a shopping assistant with access to:

NATIVE TOOLS (Direct Database):
- get_product_details: Fast product lookup
- semantic_search: Vector search via Pinecone
- ...

MCP TOOLS (AI-Powered):
- mcp_recommend_products: AI-powered recommendations
- mcp_compare_products: Detailed comparison
- mcp_explain_product: Natural language summaries
- ...

Choose the appropriate tool based on the task.
```

## 📊 Success Metrics

### For Portfolio/Resume

- [ ] Architecture diagram in README
- [ ] "Powered by MCP" badge
- [ ] Live demo showing MCP in action
- [ ] Performance comparison (native vs MCP)
- [ ] Documentation of design decisions

### Technical

- [ ] All existing tests still pass (116 tests)
- [ ] New MCP integration tests pass (target: 20+)
- [ ] No performance regression
- [ ] MCP server starts/stops cleanly
- [ ] Error handling for MCP failures

## 🎓 Portfolio Highlights

This project demonstrates:

1. **RAG Implementation**: Production-ready Pinecone + LangChain
2. **Agentic AI**: LangGraph with memory and tool orchestration
3. **MCP Integration**: Model Context Protocol for extensible AI tools
4. **System Design**: Hybrid architecture combining multiple AI paradigms
5. **Testing**: Comprehensive test coverage (100+ tests)

## 📅 Timeline

**Day 1 (4-6 hours):**

- Phase 1: MCP Client Service ✓
- Phase 2: LangGraph Integration (partial) ✓

**Day 2 (4-6 hours):**

- Phase 2: Complete LangGraph Integration ✓
- Phase 3: FastAPI Lifecycle ✓
- Phase 4: API Endpoints ✓

**Day 3 (3-4 hours):**

- Phase 5: Testing ✓
- Phase 6: Documentation ✓

**Day 4 (Optional, 4-6 hours):**

- Phase 7: Frontend Demo ✓

**Total Estimated Time:** 12-20 hours

## 🚀 Quick Start Commands

After implementation:

```bash
# Start the app (MCP server starts automatically)
python main.py

# Test MCP integration
python scripts/test_mcp_integration.py

# Run all tests including MCP
python scripts/run_langchain_tests.py

# Check MCP server status
curl http://localhost:8000/api/mcp/status

# Try agent with MCP tools
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Recommend me a laptop under $1000"}'
```

## 📚 Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [LangChain MCP Integration](https://python.langchain.com/docs/integrations/tools/mcp)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

---

**Next Steps:** Review this plan and confirm to proceed with implementation!
