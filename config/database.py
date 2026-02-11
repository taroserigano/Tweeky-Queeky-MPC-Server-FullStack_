from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from beanie import init_beanie
from .settings import settings
import atexit

# Global clients for proper cleanup and connection reuse
_db_client = None  # Async client (Motor)
_sync_client = None  # Sync client (PyMongo)

# Connection pool configuration
MONGO_POOL_CONFIG = {
    "maxPoolSize": 50,  # Max connections in pool (default: 100)
    "minPoolSize": 10,  # Min connections to maintain (default: 0)
    "maxIdleTimeMS": 30000,  # Close idle connections after 30s
    "waitQueueTimeoutMS": 5000,  # Max wait time for connection from pool
    "serverSelectionTimeoutMS": 5000,  # Timeout for server selection
    "connectTimeoutMS": 10000,  # Timeout for initial connection
    "socketTimeoutMS": 20000,  # Socket timeout (20 seconds)
}


async def init_db():
    """Initialize async database connection with connection pool"""
    global _db_client
    
    if _db_client is not None:
        print("[Database] Reusing existing async connection")
        return _db_client
    
    print("[Database] Creating async connection pool...")
    print(f"[Database] Pool config: maxPoolSize={MONGO_POOL_CONFIG['maxPoolSize']}, minPoolSize={MONGO_POOL_CONFIG['minPoolSize']}")
    
    _db_client = AsyncIOMotorClient(
        settings.MONGO_URI,
        **MONGO_POOL_CONFIG
    )
    
    from models.user import User
    from models.product import Product, Review
    from models.order import Order
    
    await init_beanie(
        database=_db_client.get_default_database(),
        document_models=[User, Product, Review, Order]
    )
    
    print("[Database] Async connection pool initialized")
    return _db_client


def get_sync_client():
    """Get or create singleton sync MongoDB client (for agent tools)"""
    global _sync_client
    
    if _sync_client is None:
        print("[Database] Creating sync connection pool...")
        print(f"[Database] Pool config: maxPoolSize={MONGO_POOL_CONFIG['maxPoolSize']}, minPoolSize={MONGO_POOL_CONFIG['minPoolSize']}")
        
        _sync_client = MongoClient(
            settings.MONGO_URI,
            **MONGO_POOL_CONFIG
        )
        
        # Register cleanup on program exit
        atexit.register(lambda: _sync_client.close() if _sync_client else None)
        
        print("[Database] Sync connection pool initialized")
    
    return _sync_client


def get_sync_db():
    """Get sync database instance (reuses connection pool)"""
    client = get_sync_client()
    return client.get_default_database()


async def close_db():
    """Close database connections properly"""
    global _db_client, _sync_client
    
    if _db_client is not None:
        try:
            print("[Database] Closing async connection pool...")
            _db_client.close()
            _db_client = None
        except Exception as e:
            print(f"Warning: Error closing async database: {e}")
    
    if _sync_client is not None:
        try:
            print("[Database] Closing sync connection pool...")
            _sync_client.close()
            _sync_client = None
        except Exception as e:
            print(f"Warning: Error closing sync database: {e}")


def get_pool_stats():
    """Get connection pool statistics for monitoring"""
    stats = {}
    
    if _sync_client is not None:
        try:
            # Get server info to verify connection
            server_info = _sync_client.server_info()
            stats['sync'] = {
                'connected': True,
                'pool_options': MONGO_POOL_CONFIG,
            }
        except Exception as e:
            stats['sync'] = {'connected': False, 'error': str(e)}
    else:
        stats['sync'] = {'connected': False, 'error': 'Not initialized'}
    
    if _db_client is not None:
        stats['async'] = {
            'connected': True,
            'pool_options': MONGO_POOL_CONFIG,
        }
    else:
        stats['async'] = {'connected': False, 'error': 'Not initialized'}
    
    return stats
