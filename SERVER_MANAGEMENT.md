# Server Management Guide

## Fixed Issues ✅

### 1. **Port Not Released After Shutdown**

**Problem:** Ports 5000 and 3000 remained occupied even after stopping services, causing "Address already in use" errors.

**Root Causes:**

- `start.py` used `start cmd /k` which created detached Windows processes
- No proper process termination handlers
- Database connections weren't properly closed
- No PID tracking

**Solutions Implemented:**

- ✅ Rewrote `start.py` to use `subprocess.Popen` with proper process group management
- ✅ Added PID file tracking in `.pids/` directory
- ✅ Implemented `atexit` and signal handlers for graceful cleanup
- ✅ Fixed database connection cleanup in `config/database.py`
- ✅ Made `stop.py` aggressive with retry logic

### 2. **Multiple Backend Servers Running**

**Problem:** Multiple uvicorn instances running simultaneously on port 5000.

**Root Causes:**

- `start.py` created orphan processes that weren't tracked
- `stop.py` only killed LISTENING state, not all connections
- No parent-child process relationship

**Solutions Implemented:**

- ✅ Track all child processes in `_child_processes` list
- ✅ Kill entire process tree with `/T` flag on Windows
- ✅ Added `CREATE_NEW_PROCESS_GROUP` flag for proper management
- ✅ Monitor child processes and report unexpected deaths

### 3. **No Hard Close Mechanism**

**Problem:** No way to force-kill stuck processes.

**Solutions Implemented:**

- ✅ Created `hard_shutdown.py` - nuclear option script
- ✅ Kills processes by port (ALL states, not just LISTENING)
- ✅ Kills by process name (node, python, uvicorn)
- ✅ 3-second countdown with cancel option

### 4. **No Graceful Shutdown**

**Problem:** Server didn't cleanup resources on shutdown.

**Solutions Implemented:**

- ✅ Added proper lifespan handlers in `main.py`
- ✅ Database client properly closed in `close_db()`
- ✅ Signal handlers for SIGINT and SIGTERM
- ✅ Cleanup function registered with `atexit`

---

## How to Use

### Normal Start

```bash
python start.py
```

- Creates PID files in `.pids/`
- Tracks child processes
- Opens browser automatically
- Press Ctrl+C to stop all services gracefully

### Normal Stop

```bash
python stop.py
```

- Kills tracked processes from PID files first
- Aggressively cleans ports (all connection states)
- Retries 3 times
- Removes PID files

### Nuclear Option (When Normal Stop Fails)

```bash
python hard_shutdown.py
```

**⚠️ WARNING:** This kills ALL Python and Node processes!

- Finds and kills EVERYTHING on ports 5000 and 3000
- Kills by process name (node, python, uvicorn)
- 3-second countdown to cancel
- Use only when processes are truly stuck

---

## Technical Details

### Process Management Architecture

**start.py:**

- Uses `subprocess.Popen` instead of `start cmd /k`
- Sets `creationflags=CREATE_NEW_PROCESS_GROUP` on Windows
- Registers cleanup with `atexit` and signal handlers
- Tracks PIDs in `.pids/backend.pid` and `.pids/frontend.pid`
- Monitors child processes for unexpected deaths
- Graceful shutdown on Ctrl+C

**stop.py:**

- Reads PID files and kills process trees first
- Falls back to port-based killing
- Checks ALL connection states (not just LISTENING)
- Retries up to 3 times
- Cleans up PID files
- Uses `taskkill /F /T` for process tree termination

**main.py:**

- Proper lifespan context manager
- Database client stored globally for cleanup
- Prints startup/shutdown messages
- Handles exceptions in close_db()

**database.py:**

- Global `_db_client` variable for tracking
- Properly closes MongoDB client
- Error handling in cleanup

### PID File System

```
.pids/
├── backend.pid    # Contains backend process PID
└── frontend.pid   # Contains frontend process PID
```

### Signal Handling

- `SIGINT` (Ctrl+C): Graceful shutdown
- `SIGTERM`: Graceful shutdown (Unix)
- `atexit`: Cleanup on normal exit

### Port Cleanup Strategy

1. Kill by PID file (fastest, most accurate)
2. Find all PIDs on port (netstat on Windows, lsof on Unix)
3. Kill all found PIDs with force flag
4. Wait 1 second
5. Retry if still occupied (up to 3 times)
6. Report final status

---

## Troubleshooting

### "Port already in use" Error

```bash
# Option 1: Normal stop
python stop.py

# Option 2: If that fails, use nuclear option
python hard_shutdown.py

# Option 3: Manual check
netstat -ano | findstr :5000
# Then kill manually: taskkill /F /PID <PID>
```

### Zombie Processes

Some PIDs may show in `netstat` but not exist in `wmic process`. These are TCP stack artifacts and will clear within 60 seconds. They don't block new connections on the same port.

### Services Don't Stop

```bash
# Use the nuclear option
python hard_shutdown.py

# Or kill specific PID
taskkill /F /T /PID <PID>
```

### Multiple Backends Running

```bash
# Check how many are running
netstat -ano | findstr :5000 | findstr LISTENING

# Stop all
python hard_shutdown.py

# Start fresh
python start.py
```

---

## Best Practices

1. **Always use `python start.py`** - Don't use `uvicorn` directly
2. **Use `python stop.py`** - Don't manually kill processes
3. **Check `.pids/` directory** - Useful for tracking
4. **Wait 2-3 seconds** between stop and start
5. **Use `hard_shutdown.py`** sparingly - it's aggressive
6. **Monitor terminal output** - Shows process deaths
7. **Don't close terminal** - Use Ctrl+C instead

---

## Files Modified

1. `start.py` - Complete rewrite with process management
2. `stop.py` - Aggressive cleanup with PID tracking
3. `main.py` - Added signal handlers and proper lifespan
4. `config/database.py` - Proper client cleanup
5. `hard_shutdown.py` - NEW: Nuclear option script
6. `.pids/` - NEW: Directory for PID tracking (gitignored)

---

## What's NOT Fixed

- **TCP TIME_WAIT states**: Normal TCP behavior, clears in ~60s
- **System-reserved ports**: Can't force-kill system processes
- **Antivirus interference**: May block aggressive kills

---

## Summary

All major issues are now **FIXED**:

- ✅ Ports properly released
- ✅ No multiple instances
- ✅ Hard shutdown available
- ✅ Graceful shutdown works
- ✅ Database properly closed
- ✅ Process tracking implemented
- ✅ No orphan processes

**The server management is now production-grade!** 🎉
