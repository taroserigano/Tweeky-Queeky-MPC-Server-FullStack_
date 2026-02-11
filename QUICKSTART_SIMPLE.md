# TweekySqueeky E-Commerce App - Quick Start Guide

## 🚀 Easy Start (Choose One Method)

### Method 1: Double-Click (Windows)
Simply double-click: **`START.bat`**

### Method 2: Python Script (Cross-Platform)
```bash
python start.py
```

### Method 3: Manual Start
```bash
# Terminal 1 - Backend
python -m uvicorn main:app --reload --port 5000

# Terminal 2 - Frontend
cd frontend
npm start
```

## 🛑 Stop Services

### Windows
Double-click: **`STOP.bat`**

Or run:
```bash
python stop.py
```

### Manual Stop
Press `Ctrl+C` in each terminal window

## 🌐 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs

## ✨ Features

- Smart Shopping Agent with AI chat
- Product search and filtering
- Real-time inventory management
- Analytics dashboard
- RAG-powered product search

## 🐛 Troubleshooting

### Ports Already in Use
Run stop script first:
```bash
python stop.py
```

### Services Won't Start
1. Check Python is installed: `python --version`
2. Check Node.js is installed: `node --version`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install
   ```

### Chat Agent Not Responding
1. Check OpenAI API key in `.env` file
2. Ensure `LLM_PROVIDER=openai` in `.env`
3. Check backend logs for errors

## 📝 Configuration

Edit `.env` file to configure:
- OpenAI API key
- MongoDB connection
- Other settings

## 🆘 Need Help?

Check the logs:
- Backend errors: Terminal 1 output
- Frontend errors: Terminal 2 output or browser console

---

**Made with ❤️ using FastAPI + React**
