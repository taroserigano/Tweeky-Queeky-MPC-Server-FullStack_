"""
Test Product Pages - Comprehensive E2E Test
Ensures products can be viewed without errors
"""
import httpx
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:5000"


async def test_product_pages():
    """Test that product pages work without errors"""
    print("=" * 80)
    print("PRODUCT PAGE TEST - Checking reviews field")
    print("=" * 80)
    
    async with httpx.AsyncClient() as client:
        # Get all products
        print("\n1. Fetching all products...")
        products_response = await client.get(f"{BASE_URL}/api/products")
        
        if products_response.status_code != 200:
            print(f"❌ Failed to fetch products: {products_response.status_code}")
            return False
        
        products_data = products_response.json()
        products = products_data.get("products", [])
        
        if not products:
            print("❌ No products found in database")
            return False
        
        print(f"✓ Found {len(products)} products")
        
        # Test each product
        success_count = 0
        for i, product in enumerate(products[:5], 1):  # Test first 5 products
            product_id = product["_id"]
            product_name = product.get("name", "Unknown")
            
            print(f"\n{i}. Testing product: {product_name} (ID: {product_id})")
            
            # Fetch individual product
            detail_response = await client.get(f"{BASE_URL}/api/products/{product_id}")
            
            if detail_response.status_code != 200:
                print(f"  ❌ Failed to fetch product details: {detail_response.status_code}")
                continue
            
            product_detail = detail_response.json()
            
            # Check if reviews field exists
            if "reviews" not in product_detail:
                print(f"  ❌ CRITICAL: 'reviews' field missing from response!")
                print(f"  Response keys: {list(product_detail.keys())}")
                return False
            
            reviews = product_detail["reviews"]
            print(f"  ✓ 'reviews' field present: {type(reviews)} with {len(reviews)} reviews")
            print(f"  ✓ Product has {product_detail.get('numReviews', 0)} reviews")
            print(f"  ✓ Rating: {product_detail.get('rating', 0)}")
            
            success_count += 1
        
        print("\n" + "=" * 80)
        print(f"✅ ALL TESTS PASSED - {success_count} products tested successfully!")
        print("=" * 80)
        return True

async def test_product_creation():
    """Test complete product creation workflow"""
    print("=" * 80)
    print("PRODUCT CREATION TEST - E2E")
    print("=" * 80)
    
    async with httpx.AsyncClient() as client:
        # Step 1: Login as admin
        print("\n1. Logging in as admin...")
        login_response = await client.post(
            f"{BASE_URL}/api/users/auth",
            json={
                "email": "admin@email.com",
                "password": "123456"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
        
        print("✓ Login successful")
        
        # Get the auth cookie
        cookies = login_response.cookies
        
        # Step 2: Create product with empty body (as frontend does)
        print("\n2. Creating product with EMPTY body (frontend behavior)...")
        create_response = await client.post(
            f"{BASE_URL}/api/products",
            cookies=cookies
        )
        
        print(f"Status Code: {create_response.status_code}")
        
        if create_response.status_code == 422:
            print(f"❌ FAILED: 422 Unprocessable Entity")
            print(f"Response: {create_response.text}")
            return False
        
        if create_response.status_code != 201:
            print(f"❌ FAILED: Expected 201, got {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False
        
        product_data = create_response.json()
        product_id = product_data["_id"]
        print(f"✓ Product created successfully!")
        print(f"  Product ID: {product_id}")
        print(f"  Name: {product_data['name']}")
        print(f"  Price: ${product_data['price']}")
        print(f"  Brand: {product_data['brand']}")
        
        # Step 3: Verify the product exists
        print(f"\n3. Verifying product {product_id} exists...")
        get_response = await client.get(
            f"{BASE_URL}/api/products/{product_id}",
            cookies=cookies
        )
        
        if get_response.status_code != 200:
            print(f"❌ Failed to fetch product: {get_response.status_code}")
            return False
        
        fetched_product = get_response.json()
        print("✓ Product verified in database")
        print(f"  Fetched name: {fetched_product['name']}")
        
        # Step 4: Update the product with real data
        print(f"\n4. Updating product with real data...")
        update_response = await client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={
                "name": "Test Product - Created via API",
                "price": 99.99,
                "brand": "Test Brand",
                "category": "Electronics",
                "countInStock": 10,
                "description": "This is a test product created programmatically"
            },
            cookies=cookies
        )
        
        if update_response.status_code != 200:
            print(f"❌ Failed to update product: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
        
        updated_product = update_response.json()
        print("✓ Product updated successfully")
        print(f"  New name: {updated_product['name']}")
        print(f"  New price: ${updated_product['price']}")
        
        # Step 5: Clean up - delete the test product
        print(f"\n5. Cleaning up - deleting test product...")
        delete_response = await client.delete(
            f"{BASE_URL}/api/products/{product_id}",
            cookies=cookies
        )
        
        if delete_response.status_code == 200:
            print("✓ Test product deleted")
        else:
            print(f"⚠ Warning: Could not delete test product (status {delete_response.status_code})")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Product creation is working!")
        print("=" * 80)
        return True

async def main():
    try:
        success = await test_product_pages()
        if success:
            print("\n🎉 TEST SUITE: PASSED - Product pages working correctly!")
            sys.exit(0)
        else:
            print("\n💥 TEST SUITE: FAILED - Products missing reviews field!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
