import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import bcrypt

from models.user import User
from models.product import Product, Review
from models.order import Order
from config.settings import settings


# Hash passwords using bcrypt directly
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Sample users
USERS = [
    {
        "name": "Admin User",
        "email": "admin@email.com",
        "password": hash_password("123456"),
        "is_admin": True
    },
    {
        "name": "John Doe",
        "email": "john@email.com",
        "password": hash_password("123456"),
        "is_admin": False
    },
    {
        "name": "Jane Doe",
        "email": "jane@email.com",
        "password": hash_password("123456"),
        "is_admin": False
    }
]

# Sample products (simplified - add more as needed)
PRODUCTS = [
    {
        "name": "Apple AirPods 4",
        "image": "/images/Apple-AirPods-4_970671e7-764d-4536-9f51-666941f35ad3.012d4c1b577966703dc4b6947a77677b.avif",
        "brand": "Apple",
        "category": "Electronics",
        "description": "Premium wireless earbuds with spatial audio",
        "price": 179.99,
        "count_in_stock": 10,
        "rating": 4.5,
        "num_reviews": 12
    },
    {
        "name": "BOSSIN Home Office Chair",
        "image": "/images/BOSSIN-Home-Office-Chair-Adult-Leather-High-Back-Adjustable-with-Arms-and-Lumbar-Support-Pink_c2ae285f-055d-4b7d-b5c1-3a5cd089c0ff.db5e5b58f7627bfdd0e560d711f1282e.avif",
        "brand": "BOSSIN",
        "category": "Furniture",
        "description": "Ergonomic office chair with lumbar support",
        "price": 249.99,
        "count_in_stock": 7,
        "rating": 4.0,
        "num_reviews": 8
    },
    {
        "name": "DYU 14 Folding Electric Bike",
        "image": "/images/DYU-14-Folding-Electric-Bike-for-Adults-Teens-350W-36V-7-5AH-Pedal-Assist-Commuter-Cruiser-City-E-Bike_bcd35cdc-65ff-486b-abd1-908daaac7871.085ea88ceec9fe2467d1776a8.avif",
        "brand": "DYU",
        "category": "Sports",
        "description": "Folding electric bike for adults",
        "price": 599.99,
        "count_in_stock": 5,
        "rating": 5.0,
        "num_reviews": 3
    },
    {
        "name": "Focusrite Scarlett 2i2 4th Gen",
        "image": "/images/Focusrite-Scarlett-2i2-4th-Gen-USB-Audio-Interface-with-Hi-Z-Instrument_93631c3b-e9b8-45d7-9f2d-219a79591be3.968b73e11420b91fae88e621862d6004.avif",
        "brand": "Focusrite",
        "category": "Electronics",
        "description": "USB Audio Interface for recording",
        "price": 189.99,
        "count_in_stock": 11,
        "rating": 4.8,
        "num_reviews": 15
    },
    {
        "name": "Ibanez Gio GRX70QA Electric Guitar",
        "image": "/images/Ibanez-Gio-GRX70QA-Electric-Guitar-Trans-Violet-Sunburst-853_6bc3c252-632f-4f5e-af9a-bb38e238c3fe.37fa073e3e42738a9019d7f4c2f5f2af.avif",
        "brand": "Ibanez",
        "category": "Music",
        "description": "Electric guitar with quilted maple art grain top",
        "price": 299.99,
        "count_in_stock": 6,
        "rating": 4.5,
        "num_reviews": 10
    },
    {
        "name": "Owala FreeSip Water Bottle 24oz",
        "image": "/images/Owala-FreeSip-Stainless-Steel-Water-Bottle-24oz-White_69369768-4981-497b-8eba-c02663e7c575.7acc737755cc5a214a1a0e7ca6d7ac0a.avif",
        "brand": "Owala",
        "category": "Home",
        "description": "Insulated stainless steel water bottle",
        "price": 32.99,
        "count_in_stock": 20,
        "rating": 4.9,
        "num_reviews": 25
    }
]


async def init_db_connection():
    """Initialize database connection"""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(
        database=client.get_default_database(),
        document_models=[User, Product, Review, Order]
    )


async def import_data():
    """Import sample data"""
    try:
        # Delete existing data
        await Order.delete_all()
        await Product.delete_all()
        await User.delete_all()
        
        print("Deleted existing data")
        
        # Insert users
        created_users = []
        for user_data in USERS:
            user = User(**user_data)
            # Password is already hashed, mark it as such
            user.password = user_data["password"]
            await user.insert()
            created_users.append(user)
        
        admin_user = created_users[0]
        print(f"Created {len(created_users)} users")
        
        # Insert products
        for product_data in PRODUCTS:
            product = Product(
                **product_data,
                user=admin_user.id
            )
            await product.insert()
        
        print(f"Created {len(PRODUCTS)} products")
        print("✅ Data Imported Successfully!")
        
    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


async def destroy_data():
    """Destroy all data"""
    try:
        await Order.delete_all()
        await Product.delete_all()
        await User.delete_all()
        
        print("✅ Data Destroyed Successfully!")
        
    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


async def main():
    """Main function"""
    await init_db_connection()
    
    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        await destroy_data()
    else:
        await import_data()


if __name__ == "__main__":
    asyncio.run(main())
