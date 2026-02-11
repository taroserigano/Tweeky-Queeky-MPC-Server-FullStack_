# ✅ SYSTEM READY - Testing Guide

## 🏗️ What Was Built

A **3-service AI architecture** with:
- **MCP Server** (Port 7001) - Product catalog and order management tools
- **RAG Service** (Port 7002) - Document retrieval using TF-IDF  
- **Agent Gateway** (Port 5001) - Smart routing between MCP and RAG
- **React Frontend** (Port 3000) - Clean chat interface

## 🚀 Quick Start

### Option 1: Automated (Recommended)
```bash
# Run the startup script
start_services.bat
```

This will:
1. Start all 3 backend services in separate windows
2. Wait 3 seconds between each
3. Run comprehensive tests automatically

### Option 2: Manual

**Start Services:**
```bash
# Terminal 1 - MCP Server
cd services/mcp_server && python main.py

# Terminal 2 - RAG Service  
cd services/rag_service && python main.py

# Terminal 3 - Agent Gateway
cd services/agent_gateway && python main.py
```

**Run Tests:**
```bash
python test_full_system.py
```

## 🧪 Test Coverage

The test script (`test_full_system.py`) validates:

### ✅ Health Checks
- MCP Server responding on 7001
- RAG Service responding on 7002
- Agent Gateway responding on 5001

### ✅ Direct Tool Calls
- **MCP searchProducts** - "headphones" with maxPrice filter
- **RAG query** - "return policy" document retrieval

### ✅ End-to-End Agent Queries
1. **Product Search** - "Show me headphones under $300"
   - Should route to MCP
   - Extract price filter correctly
   - Return matching products

2. **Order Tracking** - "Track order ORD-1001"
   - Should route to MCP getOrderStatus
   - Return order details

3. **General Questions** - "What is your return policy?"
   - Should route to RAG service
   - Retrieve relevant documentation

### ✅ Edge Cases
- Single word: "headphones"
- No dollar sign: "laptop under 1000"
- Multi-word product: "wireless mouse"
- Natural language: "Find me a chair"

## 📊 Expected Output

```
==========================================
TESTING 3-SERVICE ARCHITECTURE
==========================================

[TEST 1] MCP Server Health Check
✓ MCP Server: {'status': 'healthy', 'service': 'mcp-tools', 'tools': 3}

[TEST 2] RAG Service Health Check
✓ RAG Service: {'status': 'healthy', 'service': 'rag', 'documents_loaded': 11}

[TEST 3] Agent Gateway Health Check
✓ Agent Gateway: {'status': 'healthy', 'service': 'agent-gateway', ...}

[TEST 4] Direct MCP Tool - Search Products
✓ Found 2 products:
  • AirPods Pro - $249.99
  • Sony WH-1000XM5 - $399.99  (excluded - over budget)

[TEST 5] Direct RAG Query
✓ Found 2 relevant passages:
  • Score: 0.85 - Our return policy allows returns within 30 days...
  
[TEST 6] Agent - Product Search Query
✓ Agent Reply:
I found 1 product matching your criteria...
  Used: MCP: searchProducts

[TEST 7] Agent - Order Tracking Query
✓ Agent Reply:
Order ORD-1001 is currently SHIPPED...
  Used: MCP: getOrderStatus

[TEST 8] Agent - General Question (RAG)
✓ Agent Reply:
Based on our documentation, our return policy...
  Used: RAG

[TEST 9] Edge Cases
✓ 'headphones' → Used: MCP: searchProducts
✓ 'laptop under 1000' → Used: MCP: searchProducts
✓ 'wireless mouse' → Used: MCP: searchProducts
✓ 'Find me a chair' → Used: MCP: searchProducts

==========================================
TESTING COMPLETE
==========================================
```

## 🔧 What Was Fixed

### Bug: Query Parsing Issue
**Problem:** Agent was including special characters (bullets, quotes) in search queries
- Input: "Show me headphones under $300"
- Parsed as: `'• " headphones $300"'` ❌
- MCP couldn't find products

**Fix:** Enhanced regex parsing in [agent_gateway/main.py](services/agent_gateway/main.py)
```python
# Strip special characters
query = re.sub(r'[•"\']', '', message)

# Better price extraction  
price_pattern = r'(?:under|less than|below)?\s*\$?(\d+)'

# Expanded product keywords
product_keywords = ["headphone", "laptop", "mouse", "chair", ...]
```

### Port Conflicts
**Problem:** Windows firewall blocking ports 7000, 8001, 8003

**Fix:** Changed agent gateway to port **5001** (commonly allowed)

## 📂 Key Files

- `services/mcp_server/main.py` - MCP tools (product search, order status)
- `services/rag_service/main.py` - Document retrieval with TF-IDF
- `services/agent_gateway/main.py` - **Intent routing logic** (just fixed)
- `test_full_system.py` - Comprehensive test suite
- `start_services.bat` - Automated startup script

## 🎯 Testing Checklist

- [ ] All 3 services start without errors
- [ ] Health checks pass for all services  
- [ ] Product search returns correct results
- [ ] Price filters work (under $300, etc.)
- [ ] Order tracking retrieves order details
- [ ] RAG answers general questions
- [ ] Intent routing works (MCP vs RAG)
- [ ] Frontend connects to agent gateway

## 🐛 Troubleshooting

**Services won't start:**
- Check if ports 7001, 7002, 5001 are free
- Make sure no other Python processes are using them
- Try running `tasklist | findstr python` to check

**Tests failing:**
- Verify all services show "Uvicorn running on..." message
- Check firewall isn't blocking localhost connections
- Try `curl http://localhost:5001/health` to test connectivity

**Agent returns wrong results:**
- Check agent gateway logs for intent detection
- Verify query is being cleaned properly (no special chars)
- Test MCP tools directly to isolate issue

## ✨ Next Steps

1. **Run the tests** using `start_services.bat`
2. **Verify all tests pass** ✅
3. **Test in browser** at http://localhost:3000/ai
4. **Try different queries** to see routing in action

---

**Status:** 🟢 All fixes implemented, ready for testing!
