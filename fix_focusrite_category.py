"""Fix Focusrite product to prevent it appearing in headphone searches"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config.settings import settings
from models.product import Product

async def fix_focusrite_category():
    """Update Focusrite product category and description"""
    
    # Initialize database
    client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(
        database=client.get_default_database(),
        document_models=[Product]
    )
    
    # Find Focusrite product
    focusrite = await Product.find_one({"name": {"$regex": "Focusrite Scarlett", "$options": "i"}})
    
    if not focusrite:
        print("ERROR: Focusrite product not found in database")
        client.close()
        return
    
    print(f"Found: {focusrite.name}")
    print(f"Current category: {focusrite.category}")
    print(f"Current description: {focusrite.description}")
    
    # Update category to be more specific
    focusrite.category = "Recording Equipment"
    
    # Update description to be more specific (avoid "audio" alone)
    focusrite.description = "Professional USB recording interface with 2 inputs and 2 outputs. Features high-performance preamps, Air mode, and easy-to-use design perfect for recording vocals and instruments in home studios"
    
    # Add detailed description from seeder
    focusrite.detailed_description = "The Focusrite Scarlett 2i2 4th Generation is the world's best-selling USB audio interface, now even better. Featuring high-performance 4th generation preamps with the best-performing mic preamp the Scarlett range has ever seen. Air mode gives your recordings a brighter, more open sound. Two balanced line outputs connect to studio monitors. Auto Gain and Clip Safe features intelligently set your levels. USB-C connectivity provides bus power - no external power supply needed. Direct monitoring with no latency. Works with all major DAWs including Pro Tools, Ableton, Logic Pro, and more. Two combination inputs accept XLR, 1/4\" TRS, and Hi-Z instrument cables. Perfect for singer-songwriters, podcasters, and home studio producers."
    
    # Ensure specifications don't have "Headphone" references
    if focusrite.specifications:
        if "Headphone Outputs" in focusrite.specifications:
            focusrite.specifications["Monitor Output"] = focusrite.specifications.pop("Headphone Outputs")
            print("OK: Removed 'Headphone Outputs' from specifications")
    else:
        # Add specifications from seeder
        focusrite.specifications = {
            "Inputs": "2x Combination XLR-1/4\" TRS",
            "Outputs": "2x 1/4\" TRS balanced line outputs",
            "Monitor Output": "1x 1/4\" TRS stereo output",
            "Preamps": "High-performance 4th gen Scarlett preamps",
            "Sample Rate": "Up to 192kHz/24-bit",
            "Dynamic Range": "120dB (A-D, D-A)",
            "Connectivity": "USB-C",
            "Power": "Bus-powered via USB",
            "Dimensions": "7.3 x 3.7 x 1.9 inches",
            "Weight": "1.3 lbs",
            "Phantom Power": "+48V switchable",
            "Air Mode": "Yes",
            "Direct Monitor": "Yes",
            "Software Included": "Pro Tools Artist, Ableton Live Lite, Plugin Collective"
        }
    
    # Save changes
    await focusrite.save()
    
    print("\n[SUCCESS] Updated Focusrite product:")
    print(f"   Category: {focusrite.category}")
    print(f"   Description: {focusrite.description[:80]}...")
    print(f"   Detailed Description: {focusrite.detailed_description[:80]}...")
    print(f"   Specifications: {len(focusrite.specifications)} items")
    
    client.close()
    print("\n[SUCCESS] Database updated!")
    print("\n[IMPORTANT] Restart the backend server to rebuild the search index!")

if __name__ == "__main__":
    asyncio.run(fix_focusrite_category())
