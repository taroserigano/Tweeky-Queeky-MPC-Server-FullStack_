#!/usr/bin/env python3
"""
Complete system cleanup and restart
"""
import subprocess
import time
import os
import shutil

def cleanup_pycache():
    """Remove all __pycache__ directories"""
    print("Cleaning __pycache__ directories...")
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_path)
                print(f"✓ Removed {cache_path}")
            except Exception as e:
                print(f"✗ Could not remove {cache_path}: {e}")

def kill_all_python():
    """Kill all Python processes"""
    print("\nKilling all Python processes...")
    try:
        # Windows command to kill Python processes
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                      capture_output=True)
        subprocess.run(['taskkill', '/F', '/IM', 'python3.exe'], 
                      capture_output=True)
        subprocess.run(['taskkill', '/F', '/IM', 'python3.12.exe'], 
                      capture_output=True)
        time.sleep(2)
        print("✓ All Python processes killed")
    except Exception as e:
        print(f"⚠ Error killing processes: {e}")

def start_server():
    """Start the server"""
    print("\nStarting backend server...")
    process = subprocess.Popen(
        ['python', 'run_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(5)
    print("✓ Server started (PID: {})".format(process.pid))
    return process

if __name__ == "__main__":
    print("="*60)
    print("COMPLETE SYSTEM CLEANUP AND RESTART")
    print("="*60 + "\n")
    
    cleanup_pycache()
    kill_all_python()
    server_process = start_server()
    
    print("\n" + "="*60)
    print("SYSTEM RESTARTED")
    print("="*60)
    print("Backend: http://localhost:5000")
    print("\nWaiting for server to be ready...")
    time.sleep(3)
    
    # Test endpoint
    try:
        import requests
        response = requests.get("http://localhost:5000/api/products/top")
        if response.status_code == 200:
            print("✓ Server is responding!")
        else:
            print(f"⚠ Server returned status {response.status_code}")
    except Exception as e:
        print(f"✗ Server not responding: {e}")
