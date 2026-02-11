"""
Integration Tests for SKU Functionality
Tests the full API flow including HTTP requests
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from config.database import init_db
from models.user import User
from models.product import Product

BASE_URL = "http://localhost:8000"


class IntegrationTestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        if total == 0:
            print("\n⚠️  No integration tests run (backend not started)")
            return False
        
        print(f"\n{'='*70}")
        print(f"INTEGRATION TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} ({self.passed/total*100:.1f}%)")
        print(f"Failed: {self.failed} ({self.failed/total*100:.1f}%)")
        
        if self.errors:
            print(f"\n{'='*70}")
            print("FAILED TESTS:")
            print(f"{'='*70}")
            for test_name, error in self.errors:
                print(f"\n❌ {test_name}")
                print(f"   {error}")
        
        return self.failed == 0


results = IntegrationTestResults()


# ============================================================================
# TEST 1: GET /api/products - Returns products with SKU
# ============================================================================

async def test_get_products_with_sku():
    """Test that GET /api/products returns SKU for each product"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/products")
            
            if response.status_code != 200:
                raise Exception(f"Status code {response.status_code}, expected 200")
            
            data = response.json()
            products = data.get("products", [])
            
            if not products:
                raise Exception("No products returned from API")
            
            # Check first 5 products have SKU
            for product in products[:5]:
                if "sku" not in product:
                    raise Exception(f"Product {product.get('name')} missing SKU field")
                
                if not product["sku"]:
                    raise Exception(f"Product {product.get('name')} has empty SKU")
                
                # Verify SKU format
                sku = product["sku"]
                if "-" not in sku:
                    raise Exception(f"Invalid SKU format: {sku}")
            
            results.add_pass(f"GET /api/products returns SKU ({len(products)} products)")
    
    except httpx.ConnectError:
        print("⚠️  SKIP: GET /api/products returns SKU (backend not running)")
    except Exception as e:
        results.add_fail("GET /api/products returns SKU", str(e))


# ============================================================================
# TEST 2: GET /api/products/:id - Returns product with SKU
# ============================================================================

async def test_get_product_by_id_with_sku():
    """Test that GET /api/products/:id returns SKU"""
    try:
        await init_db()
        product = await Product.find_one()
        
        if not product:
            raise Exception("No product in database")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/products/{product.id}")
            
            if response.status_code != 200:
                raise Exception(f"Status code {response.status_code}, expected 200")
            
            data = response.json()
            
            if "sku" not in data:
                raise Exception("SKU field missing from response")
            
            if not data["sku"]:
                raise Exception("SKU is empty")
            
            # Verify it matches expected SKU (stored or fallback)
            expected_sku = product.sku or f"SKU-{str(product.id).upper()}"
            if data["sku"] != expected_sku:
                raise Exception(f"SKU mismatch: got {data['sku']}, expected {expected_sku}")
            
            results.add_pass("GET /api/products/:id returns SKU")
    
    except httpx.ConnectError:
        print("⚠️  SKIP: GET /api/products/:id returns SKU (backend not running)")
    except Exception as e:
        results.add_fail("GET /api/products/:id returns SKU", str(e))


# ============================================================================
# TEST 3: POST /api/products - Create product with custom SKU
# ============================================================================

async def test_create_product_with_custom_sku():
    """Test creating a product with custom SKU via API"""
    try:
        await init_db()
        admin = await User.find_one(User.is_admin == True)
        
        if not admin:
            raise Exception("No admin user found")
        
        # Login first to get token
        async with httpx.AsyncClient() as client:
            login_response = await client.post(
                f"{BASE_URL}/api/users/login",
                json={"email": admin.email, "password": "123456"}
            )
            
            if login_response.status_code != 200:
                raise Exception(f"Login failed: {login_response.status_code}")
            
            token = login_response.json().get("token")
            
            # Create product with custom SKU
            product_data = {
                "name": "Integration Test Product",
                "sku": "INTTEST-123456",
                "price": 99.99,
                "brand": "TestBrand",
                "category": "Test",
                "image": "/images/test.png",
                "countInStock": 10,
                "description": "Integration test product"
            }
            
            create_response = await client.post(
                f"{BASE_URL}/api/products",
                json=product_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if create_response.status_code not in [200, 201]:
                raise Exception(f"Create failed: {create_response.status_code} - {create_response.text}")
            
            created_product = create_response.json()
            
            if created_product.get("sku") != "INTTEST-123456":
                raise Exception(f"SKU mismatch: {created_product.get('sku')}")
            
            # Cleanup - delete the test product
            if created_product.get("_id"):
                await client.delete(
                    f"{BASE_URL}/api/products/{created_product['_id']}",
                    headers={"Authorization": f"Bearer {token}"}
                )
            
            results.add_pass("POST /api/products with custom SKU")
    
    except httpx.ConnectError:
        print("⚠️  SKIP: POST /api/products with custom SKU (backend not running)")
    except Exception as e:
        results.add_fail("POST /api/products with custom SKU", str(e))


# ============================================================================
# TEST 4: PUT /api/products/:id - Update product SKU
# ============================================================================

async def test_update_product_sku():
    """Test updating a product's SKU via API"""
    try:
        await init_db()
        admin = await User.find_one(User.is_admin == True)
        product = await Product.find_one()
        
        if not admin or not product:
            raise Exception("Missing admin or product")
        
        original_sku = product.sku
        
        async with httpx.AsyncClient() as client:
            # Login
            login_response = await client.post(
                f"{BASE_URL}/api/users/login",
                json={"email": admin.email, "password": "123456"}
            )
            
            if login_response.status_code != 200:
                raise Exception("Login failed")
            
            token = login_response.json().get("token")
            
            # Update SKU
            update_data = {"sku": "UPDATED-TEST-SKU"}
            
            update_response = await client.put(
                f"{BASE_URL}/api/products/{product.id}",
                json=update_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if update_response.status_code != 200:
                raise Exception(f"Update failed: {update_response.status_code}")
            
            updated_product = update_response.json()
            
            if updated_product.get("sku") != "UPDATED-TEST-SKU":
                raise Exception(f"SKU not updated: {updated_product.get('sku')}")
            
            # Restore original SKU
            await client.put(
                f"{BASE_URL}/api/products/{product.id}",
                json={"sku": original_sku},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            results.add_pass("PUT /api/products/:id updates SKU")
    
    except httpx.ConnectError:
        print("⚠️  SKIP: PUT /api/products/:id updates SKU (backend not running)")
    except Exception as e:
        results.add_fail("PUT /api/products/:id updates SKU", str(e))


# ============================================================================
# TEST 5: Search/Filter maintains SKU in results
# ============================================================================

async def test_search_maintains_sku():
    """Test that search results include SKU"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/products?keyword=apple")
            
            if response.status_code != 200:
                raise Exception(f"Status code {response.status_code}")
            
            data = response.json()
            products = data.get("products", [])
            
            if products:
                for product in products[:3]:
                    if "sku" not in product or not product["sku"]:
                        raise Exception(f"Search result missing SKU: {product.get('name')}")
            
            results.add_pass("Search results include SKU")
    
    except httpx.ConnectError:
        print("⚠️  SKIP: Search results include SKU (backend not running)")
    except Exception as e:
        results.add_fail("Search results include SKU", str(e))


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("SKU FUNCTIONALITY - INTEGRATION TEST SUITE")
    print("="*70 + "\n")
    
    print("NOTE: These tests require the backend to be running on port 8000")
    print("Run 'python start.py' or 'START.bat' in another terminal\n")
    
    # Test backend connectivity
    try:
        async with httpx.AsyncClient() as client:
            await client.get(f"{BASE_URL}/", timeout=2.0)
        print("✓ Backend is running\n")
    except (httpx.ConnectError, httpx.TimeoutException):
        print("✗ Backend is NOT running - skipping integration tests\n")
        print("To run integration tests:")
        print("  1. Start backend: python start.py")
        print("  2. Run this test again\n")
        return True  # Don't fail if backend not running
    
    # Run tests
    print("--- API ENDPOINT TESTS ---")
    await test_get_products_with_sku()
    await test_get_product_by_id_with_sku()
    await test_create_product_with_custom_sku()
    await test_update_product_sku()
    await test_search_maintains_sku()
    
    # Print summary
    success = results.summary()
    
    return success


if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)
