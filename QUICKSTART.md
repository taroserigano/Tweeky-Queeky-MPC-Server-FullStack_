# 🚀 Quick Start Guide

## ✅ What You Just Built

A **clean 3-service FastAPI architecture** where:
- **MCP Server** (7001) provides tools (hidden from frontend)
- **RAG Service** (7002) retrieves documents (hidden from frontend)
- **Agent Gateway** (7000) orchestrates both (only endpoint frontend calls)

## 🏃 Running the Application

### Step 1: Start Backend Services

Open 3 separate terminals:

**Terminal 1 - MCP Server:**
```bash
cd services/mcp_server
python main.py
# Running on http://localhost:7001
```

**Terminal 2 - RAG Service:**
```bash
cd services/rag_service
python main.py
# Running on http://localhost:7002
```

**Terminal 3 - Agent Gateway:**
```bash
cd services/agent_gateway
python main.py
# Running on http://localhost:7000
```

### Step 2: Start Frontend

```bash
cd frontend
npm install  # if first time
npm start
```

Visit: **http://localhost:3000/ai**

## 🧪 Testing the Services

### Test Agent (Main Interface)

```python
import requests

# Product search
response = requests.post("http://localhost:7000/chat", json={
    "message": "Show me headphones under $300"
})
print(response.json())

# Order tracking
response = requests.post("http://localhost:7000/chat", json={
    "message": "Track order ORD-1001"
})
print(response.json())

# General question (uses RAG)
response = requests.post("http://localhost:7000/chat", json={
    "message": "What is your return policy?"
})
print(response.json())
```

### Health Checks

```bash
# Check all services
curl http://localhost:7000/health
curl http://localhost:7001/health
curl http://localhost:7002/health
```

## 💡 Example Queries to Try

In the frontend chat:

1. **Product Search** (uses MCP):
   - "Show me headphones under $300"
   - "Find laptops"
   - "Recommend a wireless mouse"

2. **Order Tracking** (uses MCP):
   - "Track order ORD-1001"
   - "Where is my order ORD-1002?"
   - "Check delivery status"

3. **General Info** (uses RAG):
   - "What's your return policy?"
   - "How long does shipping take?"
   - "How do I contact support?"

## 🎯 What Makes This Clean

✅ **Frontend only calls `/chat`** - doesn't know about MCP or RAG  
✅ **Agent decides** which backend to use  
✅ **MCP is hidden** - just a tool provider  
✅ **No external deps** - runs locally, no API keys needed  
✅ **Simple & clear** - easy to understand and extend  

## 📂 Project Structure

```
services/
├── mcp_server/          # Port 7001
│   ├── main.py         # 3 tools (search/get/order)
│   └── requirements.txt
├── rag_service/         # Port 7002
│   ├── main.py         # TF-IDF retrieval
│   ├── docs/           # Auto-generated docs
│   └── requirements.txt
└── agent_gateway/       # Port 7000
    ├── main.py         # Routes to MCP/RAG
    └── requirements.txt

frontend/
└── src/
    ├── hooks/
    │   └── useAgent.js      # Simple API hook
    ├── components/
    │   └── SimpleAgentChat.jsx  # Chat UI
    └── screens/
        └── SimpleAIHub.jsx  # Main page
```

## 🔧 Troubleshooting

**Services won't start?**
- Make sure ports 7000, 7001, 7002 aren't in use
- Install requirements: `pip install -r requirements.txt` in each service folder

**Frontend can't connect?**
- Make sure Agent Gateway is running on port 7000
- Check browser console for CORS errors

**No documents in RAG?**
- Documents auto-generate on first run in `services/rag_service/docs/`
- Check the startup logs for "Loaded X document chunks"

## 🚀 Next Steps

1. ✅ You have a working 3-service architecture
2. Add real LLM to agent (OpenAI API)
3. Add more MCP tools (reviews, recommendations)
4. Enhance RAG with embeddings (optional)
5. Deploy with Docker

**See ARCHITECTURE.md for detailed documentation.**
