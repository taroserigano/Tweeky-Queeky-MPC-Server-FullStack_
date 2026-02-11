#!/usr/bin/env python3
"""
Kill all processes on port 5000 and restart the server
"""
import subprocess
import time
import sys

def kill_port_5000():
    """Kill all processes using port 5000"""
    try:
        # Get PIDs using port 5000
        result = subprocess.run(
            ['netstat', '-ano'], 
            capture_output=True, 
            text=True
        )
        
        pids = set()
        for line in result.stdout.split('\n'):
            if ':5000' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    pids.add(pid)
        
        # Kill each PID
        for pid in pids:
            print(f"Killing PID {pid}...")
            subprocess.run(['taskkill', '/F', '/PID', pid], 
                         capture_output=True)
        
        if pids:
            print(f"✓ Killed {len(pids)} processes")
            time.sleep(2)
        else:
            print("No processes found on port 5000")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("Starting server...")
    subprocess.Popen(
        ['python', 'run_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)
    print("✓ Server started")

if __name__ == "__main__":
    print("="*60)
    print("RESTARTING BACKEND SERVER")
    print("="*60)
    
    if kill_port_5000():
        start_server()
        print("\n✓ Backend server restarted successfully!")
        print("Testing at: http://localhost:5000")
    else:
        print("\n✗ Failed to restart server")
        sys.exit(1)
