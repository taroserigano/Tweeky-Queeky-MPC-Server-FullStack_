from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from .settings import settings


async def init_db():
    """Initialize database connection"""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    
    # Import models here to avoid circular imports
    from models.user import User
    from models.product import Product, Review
    from models.order import Order
    
    await init_beanie(
        database=client.get_default_database(),
        document_models=[User, Product, Review, Order]
    )


async def close_db():
    """Close database connection"""
    pass  # Beanie handles this automatically
