# 🚀 Quick Start Guide - All Features

## New Features Implemented

### ✅ 1. Product Sorting
Products can now be sorted by:
- **Price: Low to High** - Find budget options
- **Price: High to Low** - Browse premium items
- **Rating: Highest First** - Top-rated products
- **Newest First** - Latest additions
- **Oldest First** - Classic products

**How to use:** Select from the dropdown on the home page

### ✅ 2. Search Autocomplete
Real-time search suggestions as you type!
- Suggests product names
- Suggests brands
- Suggests categories
- Click any suggestion to navigate directly
- Use arrow keys to navigate suggestions
- Press Enter to select

**How to use:** Start typing in the search box - suggestions appear automatically

### ✅ 3. Enhanced Loading Skeletons
Beautiful loading states for better UX:
- Product grid skeletons
- Product detail skeletons
- Table skeletons for admin pages
- Smooth animations

### ✅ 4. Dark Mode
Toggle between light and dark themes!
- Auto-detects system preference on first load
- Remembers your choice in localStorage
- Smooth transitions between themes
- Click moon/sun icon in header to toggle

**How to use:** Click the theme toggle button (🌙/☀️) in the header

### ✅ 5. Breadcrumbs Navigation
Easy navigation trail showing your location:
- Home > Category > Product
- Click any breadcrumb to navigate back
- Automatically generated from URL
- Shows on product detail pages

### ✅ 6. MCP + RAG 3-Service Architecture
Advanced AI capabilities with clean separation:
- **Main Backend** (5000) - FastAPI with LangGraph agent
- **Agent Gateway** (7000) - Routes queries to MCP or RAG
- **MCP Server** (7001) - Product/order tools
- **RAG Service** (7002) - Document retrieval with TF-IDF

## 🏃 How to Run Everything

### Option 1: All-in-One Script (Recommended)
```bash
python start_all_services.py
```
This starts ALL services:
- Main backend (port 5000)
- Agent Gateway (port 7000)
- MCP Server (port 7001)
- RAG Service (port 7002)
- Frontend (port 3000)

### Option 2: Individual Services
```bash
# Terminal 1 - Main Backend
python -m uvicorn main:app --port 5000 --reload

# Terminal 2 - Agent Gateway
python -m uvicorn services.agent_gateway.main:app --port 7000

# Terminal 3 - MCP Server
python -m uvicorn services.mcp_server.main:app --port 7001

# Terminal 4 - RAG Service
python -m uvicorn services.rag_service.main:app --port 7002

# Terminal 5 - Frontend
cd frontend && npm start
```

### Option 3: Legacy (Main + Frontend Only)
```bash
# Terminal 1
python -m uvicorn main:app --port 5000 --reload

# Terminal 2
cd frontend && npm start
```

## 🧪 Testing

### Test MCP + RAG Services
```bash
python test_mcp_rag.py
```

This will test:
- MCP Server product search
- RAG Service document retrieval
- Agent Gateway routing logic

### Manual Testing
1. **Product Sorting**
   - Go to http://localhost:3000
   - Select different sort options from dropdown
   - Verify products reorder correctly

2. **Search Autocomplete**
   - Click search box
   - Type "air" or "sony"
   - See suggestions appear
   - Click a suggestion

3. **Dark Mode**
   - Click moon icon in header
   - Page should switch to dark theme
   - Refresh page - theme persists

4. **Breadcrumbs**
   - Click any product
   - See breadcrumb trail at top
   - Click breadcrumb to navigate back

5. **AI Chat (MCP + RAG)**
   - Go to http://localhost:3000/ai
   - Try: "show me headphones under $300"
   - Try: "track order ORD-1001"
   - Try: "what's your return policy?"
   - Chat should route to appropriate service

## 📍 Service URLs

| Service | URL | API Docs |
|---------|-----|----------|
| Main Backend | http://localhost:5000 | http://localhost:5000/docs |
| Agent Gateway | http://localhost:7000 | http://localhost:7000/docs |
| MCP Server | http://localhost:7001 | http://localhost:7001/docs |
| RAG Service | http://localhost:7002 | http://localhost:7002/docs |
| Frontend | http://localhost:3000 | N/A |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Frontend (React)                  │
│              Port 3000                      │
└─────────────────┬───────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
    ▼                           ▼
┌───────────────┐      ┌────────────────────┐
│ Main Backend  │      │  Agent Gateway     │
│  (Port 5000)  │      │   (Port 7000)      │
│  - REST API   │      │  - Routes queries  │
│  - Auth       │      └─────────┬──────────┘
│  - Orders     │                │
│  - Products   │      ┌─────────┴──────────┐
└───────────────┘      │                    │
                       ▼                    ▼
              ┌─────────────┐    ┌──────────────┐
              │ MCP Server  │    │ RAG Service  │
              │ (Port 7001) │    │ (Port 7002)  │
              │ - Products  │    │ - Documents  │
              │ - Orders    │    │ - TF-IDF     │
              └─────────────┘    └──────────────┘
```

## 🎯 Feature Highlights

1. **Smart Routing**: Agent Gateway intelligently routes queries
   - Product searches → MCP Server
   - Order tracking → MCP Server
   - Policy questions → RAG Service

2. **Real-time Search**: Autocomplete with keyboard navigation

3. **Persistent Theme**: Dark mode preference saved locally

4. **Better UX**: Loading skeletons prevent layout shifts

5. **Easy Navigation**: Breadcrumbs show where you are

## 🐛 Troubleshooting

**Port already in use?**
```bash
# Windows
netstat -ano | findstr ":5000"
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:5000 | xargs kill -9
```

**Services not connecting?**
- Check all services are running with `netstat -an | findstr "5000 7000 7001 7002 3000"`
- Check firewall settings
- Try restarting services

**Frontend not loading?**
- Run `npm install` in frontend directory
- Clear browser cache
- Check console for errors

## 📝 Notes

- MCP + RAG services are independent and can run separately
- Main backend works fine without MCP/RAG services
- Frontend automatically detects which services are available
- Dark mode uses CSS variables for instant theme switching
- All new features are production-ready

## 🎉 Success Criteria

You know everything is working when:
- ✅ You can sort products by price/rating
- ✅ Search shows suggestions as you type
- ✅ Dark mode toggle works and persists
- ✅ Breadcrumbs show on product pages
- ✅ Chat agent responds to queries
- ✅ All 5 services are running without errors

Enjoy your enhanced e-commerce platform! 🚀
