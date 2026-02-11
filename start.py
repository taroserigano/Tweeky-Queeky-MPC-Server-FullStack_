"""
Simple startup script for TweekySqueeky E-Commerce App
Starts both backend and frontend servers with proper process management
"""
import subprocess
import sys
import time
import webbrowser
import os
import signal
import atexit
from pathlib import Path

# Track child processes for cleanup
_child_processes = []

def cleanup_on_exit():
    """Cleanup function called on script exit"""
    print("\n\n[Cleanup] Stopping child processes...")
    for proc in _child_processes:
        try:
            if proc.poll() is None:  # Still running
                proc.terminate()
                proc.wait(timeout=5)
        except Exception:
            pass

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\n[Signal] Received shutdown signal")
    cleanup_on_exit()
    sys.exit(0)

# Register cleanup handlers
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)

def save_pid(name, pid):
    """Save process PID to file for tracking"""
    pid_dir = Path(__file__).parent / ".pids"
    pid_dir.mkdir(exist_ok=True)
    (pid_dir / f"{name}.pid").write_text(str(pid))

def kill_port(port):
    """Kill any process using the specified port"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                pids = set()
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5 and parts[-1].isdigit():
                        pids.add(parts[-1])
                
                for pid in pids:
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                    print(f"  Killed process {pid} on port {port}")
        else:
            subprocess.run(f'lsof -ti:{port} | xargs kill -9 2>/dev/null || true', shell=True)
            print(f"  Cleaned port {port}")
    except Exception as e:
        print(f"  Warning: Could not clean port {port}: {e}")

def main():
    print("=" * 50)
    print("Starting TweekySqueeky E-Commerce App")
    print("=" * 50)
    print()
    
    # Get project root directory
    project_root = Path(__file__).parent
    frontend_dir = project_root / "frontend"
    
    # Clean up ports
    print("Cleaning up ports...")
    kill_port(5003)
    kill_port(3000)
    time.sleep(2)
    print()
    
    # Start Backend (without creating detached window)
    print("[1/2] Starting Backend API on port 5003...")
    if sys.platform == "win32":
        # Use CREATE_NEW_PROCESS_GROUP instead of starting new window
        backend_process = subprocess.Popen(
            ['python', '-m', 'uvicorn', 'main:app', '--reload', '--port', '5003',
             '--host', '127.0.0.1'],
            cwd=project_root,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        backend_process = subprocess.Popen(
            ['python', '-m', 'uvicorn', 'main:app', '--reload', '--port', '5003'],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    _child_processes.append(backend_process)
    save_pid('backend', backend_process.pid)
    print(f"  Backend starting... (PID: {backend_process.pid})")
    time.sleep(5)
    
    # Start Frontend (without creating detached window)
    print("[2/2] Starting Frontend on port 3000...")
    # Prevent React from auto-opening a browser (we open it ourselves later)
    frontend_env = os.environ.copy()
    frontend_env["BROWSER"] = "none"
    if sys.platform == "win32":
        frontend_process = subprocess.Popen(
            ['npm.cmd', 'start'],  # Use npm.cmd instead of npm
            cwd=frontend_dir,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=frontend_env
        )
    else:
        frontend_process = subprocess.Popen(
            ['npm', 'start'],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=frontend_env
        )
    
    _child_processes.append(frontend_process)
    save_pid('frontend', frontend_process.pid)
    print(f"  Frontend starting... (PID: {frontend_process.pid})")
    time.sleep(6)
    
    print()
    print("=" * 50)
    print("Services Started!")
    print("=" * 50)
    print("Backend API:  http://localhost:5003")
    print("API Docs:     http://localhost:5003/docs")
    print("Frontend:     http://localhost:3000")
    print("=" * 50)
    print()
    print("Wait 10-15 seconds for services to fully start...")
    print()
    print("✓ Services are running!")
    print("  Press Ctrl+C to stop all services")
    print("  Or run 'python stop.py' from another terminal")
    print()
    
    try:
        # Keep script running and monitor child processes
        while True:
            time.sleep(2)
            # Check if any process died unexpectedly
            for proc in _child_processes:
                if proc.poll() is not None:
                    print(f"\n⚠ Warning: A child process exited (PID: {proc.pid})")
    except KeyboardInterrupt:
        print("\n\n[Shutdown] Stopping all services gracefully...")
        cleanup_on_exit()
        print("✓ All services stopped!")

if __name__ == "__main__":
    main()
