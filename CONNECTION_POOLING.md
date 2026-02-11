# Database Connection Pooling

## Overview

The application now uses **optimized connection pooling** for MongoDB to improve performance and prevent connection leaks.

## Architecture

### Before (Inefficient)

```python
# ❌ PROBLEM: New client created on every function call
def search_products():
    client = MongoClient(settings.MONGO_URI)  # New connection!
    db = client.get_default_database()
    return db.products.find(...)
```

**Issues:**

- 20+ files creating new `MongoClient` instances
- No connection reuse
- Default pool of 100 connections per client (wasteful)
- Connection overhead on every request
- Potential connection leaks

### After (Optimized)

```python
# ✅ SOLUTION: Singleton connection pool
from config.database import get_sync_db

def search_products():
    db = get_sync_db()  # Reuses existing pool!
    return db.products.find(...)
```

## Configuration

### Connection Pool Settings

Located in: [`config/database.py`](config/database.py)

```python
MONGO_POOL_CONFIG = {
    "maxPoolSize": 50,           # Max connections (was: 100 default)
    "minPoolSize": 10,           # Min connections to maintain (was: 0)
    "maxIdleTimeMS": 30000,      # Close idle connections after 30s
    "waitQueueTimeoutMS": 5000,  # Max wait for connection from pool
    "serverSelectionTimeoutMS": 5000,
    "connectTimeoutMS": 10000,
    "socketTimeoutMS": 45000,
}
```

### Why 50 connections?

- **Single MongoDB instance**: Localhost dev server
- **Light concurrent load**: Usually <10 active requests
- **50 connections** = comfortable headroom without waste
- **For production**: Tune based on load (start at 20-50, monitor)

### Two Connection Pools

1. **Async Pool** (Motor): Used by FastAPI endpoints via Beanie ODM
2. **Sync Pool** (PyMongo): Used by LangGraph agent tools

Both share the same configuration and are cleaned up on shutdown.

## Monitoring

### Health Check Endpoint

```bash
curl http://localhost:5000/api/health
```

Response includes connection pool stats:

```json
{
  "status": "healthy",
  "connection_pools": {
    "async": {
      "connected": true,
      "pool_options": {
        "maxPoolSize": 50,
        "minPoolSize": 10
      }
    },
    "sync": {
      "connected": true,
      "pool_options": {
        "maxPoolSize": 50,
        "minPoolSize": 10
      }
    }
  }
}
```

### Connection Reuse

All agent tools now import from `config.database`:

```python
from config.database import get_sync_db  # Singleton pool

def _get_sync_db():
    return get_sync_db()  # Reuses connections
```

## Updated Files

### Core Database

- [`config/database.py`](config/database.py) - Added `get_sync_client()`, `get_sync_db()`, pool config

### Agent Services (Now use singleton pool)

- [`agent_service/langgraph_agent.py`](agent_service/langgraph_agent.py)
- [`agent_service/multi_agents.py`](agent_service/multi_agents.py)
- [`agent_service/user_history.py`](agent_service/user_history.py)

### API Routers (Now use singleton pool)

- [`routers/agent.py`](routers/agent.py)
- [`routers/rag.py`](routers/rag.py)

### Application

- [`main.py`](main.py) - Health endpoint now shows pool stats

## Benefits

✅ **Reduced connection overhead** - Reuse existing connections
✅ **Faster response times** - No connection handshake per request
✅ **Lower memory usage** - 50 max connections vs 100+ per client
✅ **Better resource management** - Idle connections auto-close after 30s
✅ **Graceful shutdown** - All connections properly closed via `atexit`
✅ **Production-ready** - Explicit timeouts and queue limits

## Production Tuning

### When to adjust pool size:

#### Increase `maxPoolSize` if:

- Seeing "waiting for connection" errors
- High concurrent traffic (e.g., >50 requests/sec)
- Connection wait times >100ms

#### Decrease `maxPoolSize` if:

- Low traffic (<10 requests/sec)
- Limited server resources
- MongoDB connection limits reached

### Recommended settings by load:

| Load Level            | Concurrent Requests | maxPoolSize | minPoolSize |
| --------------------- | ------------------- | ----------- | ----------- |
| **Development**       | 1-5                 | 10-20       | 5           |
| **Light Production**  | 5-20                | 20-50       | 10          |
| **Medium Production** | 20-100              | 50-100      | 20          |
| **Heavy Production**  | 100+                | 100-200     | 50          |

## Testing Connection Pool

1. **Start the server:**

   ```bash
   python start.py
   ```

2. **Check health endpoint:**

   ```bash
   curl http://localhost:5000/api/health | python -m json.tool
   ```

3. **Load test** (optional):

   ```bash
   # Install Apache Bench
   # Windows: choco install apache-httpd
   # Mac: brew install httpd

   # Test with 100 requests, 10 concurrent
   ab -n 100 -c 10 http://localhost:5000/api/health
   ```

4. **Monitor MongoDB connections:**
   ```javascript
   // In MongoDB shell
   db.serverStatus().connections;
   // Shows: current, available, totalCreated
   ```

## Common Issues

### ⚠️ "Too many connections"

**Cause:** `maxPoolSize` too high for your MongoDB server
**Fix:** Lower `maxPoolSize` in `config/database.py`

### ⚠️ "Connection timeout"

**Cause:** All connections busy, queue timeout reached
**Fix:** Increase `maxPoolSize` or optimize slow queries

### ⚠️ "Connection closed"

**Cause:** Connection idle > `maxIdleTimeMS`
**Fix:** Normal behavior, pool will create new connection

## References

- [Motor Connection Pooling](https://motor.readthedocs.io/en/stable/tutorial-asyncio.html#connection-pooling)
- [PyMongo Connection Pooling](https://pymongo.readthedocs.io/en/stable/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient)
- [MongoDB Connection Pool Options](https://www.mongodb.com/docs/manual/reference/connection-string/#connection-pool-options)
