"""
Stop all TweekySqueeky services with AGGRESSIVE cleanup
"""
import subprocess
import sys
import time
from pathlib import Path

def kill_port_aggressive(port, retries=3):
    """Aggressively kill any process using the specified port with retries"""
    killed_any = False
    
    for attempt in range(retries):
        try:
            if sys.platform == "win32":
                # Windows - get ALL connections on this port (LISTENING, TIME_WAIT, ESTABLISHED)
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
                        # Force kill without confirmation
                        kill_result = subprocess.run(
                            f'taskkill /F /PID {pid}',
                            shell=True,
                            capture_output=True,
                            text=True
                        )
                        if kill_result.returncode == 0:
                            print(f"  ✓ Killed process {pid} on port {port}")
                            killed_any = True
                        
                    if pids:
                        time.sleep(1)  # Wait for processes to die
                        
            else:
                # Unix/Linux/Mac
                result = subprocess.run(
                    f'lsof -ti:{port}',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if result.stdout.strip():
                    subprocess.run(f'lsof -ti:{port} | xargs kill -9', shell=True)
                    print(f"  ✓ Killed processes on port {port}")
                    killed_any = True
                    time.sleep(1)
                    
        except Exception as e:
            print(f"  ⚠ Warning on attempt {attempt + 1}: {e}")
    
    # Final verification
    if sys.platform == "win32":
        result = subprocess.run(
            f'netstat -ano | findstr :{port} | findstr LISTENING',
            shell=True,
            capture_output=True,
            text=True
        )
        if not result.stdout:
            if not killed_any:
                print(f"  ✓ No process on port {port}")
            return True
        else:
            print(f"  ⚠ Warning: Port {port} still has active connections")
            return False
    
    return killed_any

def kill_process_tree(pid):
    """Kill a process and all its children"""
    try:
        if sys.platform == "win32":
            subprocess.run(f'taskkill /F /T /PID {pid}', shell=True, capture_output=True)
        else:
            subprocess.run(f'pkill -TERM -P {pid}', shell=True)
            subprocess.run(f'kill -9 {pid}', shell=True)
    except Exception:
        pass

def cleanup_pid_files():
    """Remove PID tracking files"""
    pid_dir = Path(__file__).parent / ".pids"
    if pid_dir.exists():
        for pid_file in pid_dir.glob("*.pid"):
            try:
                pid_file.unlink()
            except Exception:
                pass
        try:
            pid_dir.rmdir()
        except Exception:
            pass

def main():
    print("=" * 50)
    print("Stopping TweekySqueeky Services (AGGRESSIVE)")
    print("=" * 50)
    print()
    
    # Kill by PID files first
    pid_dir = Path(__file__).parent / ".pids"
    if pid_dir.exists():
        print("Stopping tracked processes...")
        for pid_file in pid_dir.glob("*.pid"):
            try:
                pid = int(pid_file.read_text().strip())
                print(f"  Killing {pid_file.stem} (PID: {pid})...")
                kill_process_tree(pid)
            except Exception:
                pass
    
    print("\nStopping Backend (port 5000)...")
    kill_port_aggressive(5000)
    
    print("\nStopping Frontend (port 3000)...")
    kill_port_aggressive(3000)
    
    print("\nCleaning up PID files...")
    cleanup_pid_files()
    
    print()
    print("=" * 50)
    print("✓ All services stopped!")
    print("=" * 50)

if __name__ == "__main__":
    main()
