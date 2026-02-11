"""
NUCLEAR OPTION: Hard shutdown of all services
Use this when stop.py fails or processes are stuck
"""
import subprocess
import sys
import time
from pathlib import Path


def nuclear_kill_port(port):
    """Kill EVERYTHING on a port - no mercy"""
    print(f"\n NUCLEAR CLEANUP on port {port}")
    print("=" * 50)
    
    if sys.platform == "win32":
        # Get ALL connections (not just LISTENING)
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            pids = set()
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 5 and parts[-1].isdigit():
                    pids.add(parts[-1])
            
            print(f"Found {len(pids)} processes to kill")
            
            for pid in pids:
                # Kill with extreme prejudice
                subprocess.run(f'taskkill /F /T /PID {pid}', shell=True, capture_output=True)
                print(f"  ☠ KILLED PID {pid}")
            
            time.sleep(2)
            
            # Verify
            verify = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            
            if not verify.stdout:
                print(f"  ✓ Port {port} is NOW CLEAN")
            else:
                print(f"  ⚠ Port {port} still has connections (may be system reserved)")
        else:
            print(f"  ✓ Port {port} is clean")
    else:
        # Unix - kill with -9
        subprocess.run(f'lsof -ti:{port} | xargs kill -9 2>/dev/null || true', shell=True)
        print(f"  ✓ Killed all processes on port {port}")


def kill_by_name(name):
    """Kill all processes by name"""
    if sys.platform == "win32":
        subprocess.run(f'taskkill /F /IM {name}.exe /T', shell=True, capture_output=True)
        print(f"  Killed all {name} processes")
    else:
        subprocess.run(f'pkill -9 {name}', shell=True)


def main():
    print("=" * 50)
    print("🔥 HARD SHUTDOWN - NUCLEAR OPTION 🔥")
    print("=" * 50)
    print("\nThis will FORCE KILL all related processes")
    print("Use only when normal stop.py fails!\n")
    
    # Give user a chance to cancel
    print("Starting in 3 seconds... (Ctrl+C to cancel)")
    try:
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        return
    
    print("\n🔥 INITIATING HARD SHUTDOWN...")
    
    # 1. Kill by ports
    nuclear_kill_port(5000)
    nuclear_kill_port(3000)
    
    # 2. Kill by process names
    print("\n💀 Killing processes by name...")
    kill_by_name("node")
    kill_by_name("python")
    kill_by_name("uvicorn")
    
    # 3. Clean up PID files
    print("\n🧹 Cleaning up PID files...")
    pid_dir = Path(__file__).parent / ".pids"
    if pid_dir.exists():
        for pid_file in pid_dir.glob("*.pid"):
            try:
                pid_file.unlink()
                print(f"  Removed {pid_file.name}")
            except Exception:
                pass
        try:
            pid_dir.rmdir()
        except Exception:
            pass
    
    print("\n" + "=" * 50)
    print("✓ HARD SHUTDOWN COMPLETE!")
    print("=" * 50)
    print("\nAll processes should now be terminated.")
    print("You can now run 'python start.py' to restart cleanly.")
    

if __name__ == "__main__":
    main()
