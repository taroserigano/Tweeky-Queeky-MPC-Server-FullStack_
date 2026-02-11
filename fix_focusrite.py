"""Fix Focusrite product specifications"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config.settings import settings
from models.product import Product

async def fix_focusrite():
    """Update Focusrite product to remove 'Headphone' from specifications"""
    # Initialize database
    client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(
        database=client.get_default_database(),
        document_models=[Product]
    )
    
    # Find Focusrite product
    focusrite = await Product.find_one({"name": {"$regex": "Focusrite Scarlett", "$options": "i"}})
    
    if focusrite:
        print(f"Found: {focusrite.name}")
        print(f"Current specs: {focusrite.specifications}")
        
        # Update specifications
        if focusrite.specifications and "Headphone Outputs" in focusrite.specifications:
            focusrite.specifications["Monitor Output"] = focusrite.specifications.pop("Headphone Outputs")
            await focusrite.save()
            print(f"✓ Updated specs: {focusrite.specifications}")
            print("✓ Product updated successfully!")
        else:
            print("No update needed - 'Headphone Outputs' not found")
    else:
        print("Focusrite product not found in database")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_focusrite())
