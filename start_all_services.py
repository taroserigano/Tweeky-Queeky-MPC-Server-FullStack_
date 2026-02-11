#!/usr/bin/env python3
"""
Start all services for MCP + RAG architecture
- Main backend (port 5000)
- Agent Gateway (port 7000)
- MCP Server (port 7001)
- RAG Service (port 7002)
- Frontend (port 3000)
"""
import subprocess
import sys
import time
import platform
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent

def start_service(name, command, cwd=None, shell=False):
    """Start a service in the background"""
    print(f"🚀 Starting {name}...")
    
    if platform.system() == "Windows":
        # Windows: use CREATE_NEW_CONSOLE flag
        process = subprocess.Popen(
            command,
            cwd=cwd or PROJECT_ROOT,
            shell=shell,
            creationflags=subprocess.CREATE_NEW_CONSOLE if not shell else 0
        )
    else:
        # Unix: use subprocess normally
        process = subprocess.Popen(
            command,
            cwd=cwd or PROJECT_ROOT,
            shell=shell,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    time.sleep(1)
    return process

def main():
    print("=" * 60)
    print("🎯 Starting MCP + RAG + Agent Architecture")
    print("=" * 60)
    
    processes = []
    
    try:
        # 1. Main Backend (FastAPI with LangGraph agent)
        processes.append(start_service(
            "Main Backend",
            [sys.executable, "-m", "uvicorn", "main:app", "--port", "5000", "--reload"],
            cwd=PROJECT_ROOT
        ))
        time.sleep(3)
        
        # 2. Agent Gateway (Routes to MCP + RAG)
        processes.append(start_service(
            "Agent Gateway",
            [sys.executable, "-m", "uvicorn", "services.agent_gateway.main:app", "--port", "7000", "--reload"],
            cwd=PROJECT_ROOT
        ))
        time.sleep(2)
        
        # 3. MCP Server (Product/Order tools)
        processes.append(start_service(
            "MCP Server",
            [sys.executable, "-m", "uvicorn", "services.mcp_server.main:app", "--port", "7001", "--reload"],
            cwd=PROJECT_ROOT
        ))
        time.sleep(2)
        
        # 4. RAG Service (Document retrieval)
        processes.append(start_service(
            "RAG Service",
            [sys.executable, "-m", "uvicorn", "services.rag_service.main:app", "--port", "7002", "--reload"],
            cwd=PROJECT_ROOT
        ))
        time.sleep(2)
        
        # 5. Frontend
        frontend_dir = PROJECT_ROOT / "frontend"
        if frontend_dir.exists():
            print("🚀 Starting Frontend...")
            if platform.system() == "Windows":
                subprocess.Popen(
                    "npm start",
                    cwd=frontend_dir,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen(
                    ["npm", "start"],
                    cwd=frontend_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        
        print("\n" + "=" * 60)
        print("✅ All services started!")
        print("=" * 60)
        print("\n📍 Service URLs:")
        print("   Main Backend:   http://localhost:5000")
        print("   Agent Gateway:  http://localhost:7000")
        print("   MCP Server:     http://localhost:7001")
        print("   RAG Service:    http://localhost:7002")
        print("   Frontend:       http://localhost:3000")
        print("\n📖 API Docs:")
        print("   Main:    http://localhost:5000/docs")
        print("   Gateway: http://localhost:7000/docs")
        print("   MCP:     http://localhost:7001/docs")
        print("   RAG:     http://localhost:7002/docs")
        print("\n⚠️  Press Ctrl+C to stop all services\n")
        
        # Keep script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all services...")
        for process in processes:
            try:
                process.terminate()
            except:
                pass
        print("✅ All services stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
