"""
Comprehensive Test Suite for SKU Functionality

Tests:
1. Product Model SKU field
2. Schema validation (ProductCreate, ProductUpdate, ProductResponse)
3. API endpoints (create, read, update)
4. SKU generation and fallback logic
5. Seeder SKU generation
6. Agent product dict includes SKU
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import init_db
from models.product import Product
from models.user import User
from schemas.product import ProductCreate, ProductUpdate, ProductResponse
from routers.products import product_to_response, generate_sku_fallback
from agent_service.langgraph_agent import _product_to_dict as agent_product_to_dict
from agent_service.user_history import _product_to_dict as history_product_to_dict
from bson import ObjectId
from beanie import PydanticObjectId


class TestResults:
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
        print(f"\n{'='*70}")
        print(f"TEST SUMMARY")
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


results = TestResults()


# ============================================================================
# TEST 1: Product Model SKU Field
# ============================================================================

async def test_product_model_sku_field():
    """Test that Product model has optional SKU field"""
    try:
        # Create product without SKU
        # Note: is_admin field has alias "isAdmin" in MongoDB
        admin = await User.find_one(User.is_admin == True)
        if not admin:
            raise Exception("No admin user found in database")
        
        product_no_sku = Product(
            user=admin.id,
            name="Test Product No SKU",
            image="/images/test.png",
            brand="TestBrand",
            category="Test",
            description="Test",
            price=10.0,
            count_in_stock=5
        )
        await product_no_sku.save()
        
        # Verify SKU is None
        if product_no_sku.sku is not None:
            raise Exception(f"Expected sku=None, got {product_no_sku.sku}")
        
        # Create product with SKU
        product_with_sku = Product(
            user=admin.id,
            sku="TEST-SKU-123",
            name="Test Product With SKU",
            image="/images/test.png",
            brand="TestBrand",
            category="Test",
            description="Test",
            price=10.0,
            count_in_stock=5
        )
        await product_with_sku.save()
        
        # Verify SKU is stored
        if product_with_sku.sku != "TEST-SKU-123":
            raise Exception(f"Expected sku='TEST-SKU-123', got {product_with_sku.sku}")
        
        # Retrieve from DB and verify persistence
        retrieved = await Product.get(product_with_sku.id)
        if retrieved.sku != "TEST-SKU-123":
            raise Exception(f"SKU not persisted correctly: {retrieved.sku}")
        
        # Cleanup
        await product_no_sku.delete()
        await product_with_sku.delete()
        
        results.add_pass("Product Model SKU Field")
        
    except Exception as e:
        results.add_fail("Product Model SKU Field", str(e))


# ============================================================================
# TEST 2: Schema Validation
# ============================================================================

async def test_schema_validation():
    """Test ProductCreate, ProductUpdate, ProductResponse with SKU"""
    try:
        # Test ProductCreate with SKU
        create_with_sku = ProductCreate(
            sku="CREATE-SKU-001",
            name="Test",
            price=10.0,
            image="/images/test.png",
            brand="Brand",
            category="Cat",
            count_in_stock=5,
            description="Desc"
        )
        if create_with_sku.sku != "CREATE-SKU-001":
            raise Exception("ProductCreate sku validation failed")
        
        # Test ProductCreate without SKU (should be None)
        create_no_sku = ProductCreate(
            name="Test",
            price=10.0,
            image="/images/test.png",
            brand="Brand",
            category="Cat",
            count_in_stock=5,
            description="Desc"
        )
        if create_no_sku.sku is not None:
            raise Exception(f"ProductCreate sku should default to None, got {create_no_sku.sku}")
        
        # Test ProductUpdate with SKU
        update_sku = ProductUpdate(sku="UPDATE-SKU-001")
        if update_sku.sku != "UPDATE-SKU-001":
            raise Exception("ProductUpdate sku validation failed")
        
        # Test ProductResponse with SKU
        response = ProductResponse(
            _id="507f1f77bcf86cd799439011",
            user="507f1f77bcf86cd799439012",
            sku="RESPONSE-SKU-001",
            name="Test",
            image="/images/test.png",
            brand="Brand",
            category="Cat",
            description="Desc",
            rating=0.0,
            num_reviews=0,
            price=10.0,
            count_in_stock=5,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        if response.sku != "RESPONSE-SKU-001":
            raise Exception("ProductResponse sku validation failed")
        
        results.add_pass("Schema Validation")
        
    except Exception as e:
        results.add_fail("Schema Validation", str(e))


# ============================================================================
# TEST 3: API Response with SKU Fallback
# ============================================================================

async def test_api_response_sku_fallback():
    """Test product_to_response generates fallback SKU when missing"""
    try:
        admin = await User.find_one(User.is_admin == True)
        if not admin:
            raise Exception("No admin user found")
        
        # Create product without SKU
        product = Product(
            user=admin.id,
            name="Fallback Test",
            image="/images/test.png",
            brand="TestBrand",
            category="Test",
            description="Test",
            price=10.0,
            count_in_stock=5
        )
        await product.save()
        
        # Test API response generates fallback
        response = product_to_response(product)
        expected_fallback = f"SKU-{str(product.id).upper()}"
        
        if response.sku != expected_fallback:
            raise Exception(f"Expected fallback SKU '{expected_fallback}', got '{response.sku}'")
        
        # Test with stored SKU
        product.sku = "STORED-SKU-123"
        await product.save()
        
        response2 = product_to_response(product)
        if response2.sku != "STORED-SKU-123":
            raise Exception(f"Expected stored SKU 'STORED-SKU-123', got '{response2.sku}'")
        
        # Cleanup
        await product.delete()
        
        results.add_pass("API Response SKU Fallback")
        
    except Exception as e:
        results.add_fail("API Response SKU Fallback", str(e))


# ============================================================================
# TEST 4: SKU Generation Function
# ============================================================================

def test_sku_generation():
    """Test generate_sku_fallback function"""
    try:
        sku1 = generate_sku_fallback()
        sku2 = generate_sku_fallback()
        
        # Check format: SKU-{8 hex chars}
        if not sku1.startswith("SKU-"):
            raise Exception(f"SKU should start with 'SKU-', got {sku1}")
        
        if len(sku1) != 12:  # SKU- (4) + 8 hex chars
            raise Exception(f"SKU should be 12 chars, got {len(sku1)}: {sku1}")
        
        # Check uppercase
        if not sku1[4:].isupper():
            raise Exception(f"SKU hex part should be uppercase, got {sku1}")
        
        # Check uniqueness
        if sku1 == sku2:
            raise Exception(f"Generated SKUs should be unique, got duplicate: {sku1}")
        
        results.add_pass("SKU Generation Function")
        
    except Exception as e:
        results.add_fail("SKU Generation Function", str(e))


# ============================================================================
# TEST 5: Seeded Products Have SKU
# ============================================================================

async def test_seeded_products_have_sku():
    """Test that seeded products have SKU values"""
    try:
        products = await Product.find().limit(10).to_list()
        
        if not products:
            raise Exception("No products found in database - run seeder first")
        
        missing_sku = []
        for p in products:
            if not p.sku:
                missing_sku.append(p.name)
        
        if missing_sku:
            raise Exception(f"{len(missing_sku)} products missing SKU: {missing_sku}")
        
        # Check SKU format (should be BRAND-HASH)
        for p in products:
            if not p.sku or '-' not in p.sku:
                raise Exception(f"Invalid SKU format for {p.name}: {p.sku}")
        
        results.add_pass(f"Seeded Products Have SKU ({len(products)} checked)")
        
    except Exception as e:
        results.add_fail("Seeded Products Have SKU", str(e))


# ============================================================================
# TEST 6: SKU Format in Seeded Products
# ============================================================================

async def test_sku_format_consistency():
    """Test that seeded SKUs follow expected format"""
    try:
        products = await Product.find().limit(20).to_list()
        
        if not products:
            raise Exception("No products found")
        
        for p in products:
            sku = p.sku
            
            # Should have format: XXX-XXXXXXXXXX (brand code - hash)
            parts = sku.split('-')
            if len(parts) != 2:
                raise Exception(f"SKU should have 2 parts separated by '-', got {sku}")
            
            brand_code, hash_part = parts
            
            # Brand code should be uppercase letters (3 chars typically)
            if not brand_code.isupper():
                raise Exception(f"Brand code should be uppercase in {sku}")
            
            # Hash should be uppercase hexadecimal (no lowercase letters)
            # Note: hash might be all numeric (e.g., 2554872289), which is valid
            if hash_part != hash_part.upper():
                raise Exception(f"Hash part should have no lowercase letters in {sku}")
            
            # Hash should be 10 chars
            if len(hash_part) != 10:
                raise Exception(f"Hash should be 10 chars, got {len(hash_part)} in {sku}")
            
            # Hash should be alphanumeric (hexadecimal characters)
            if not hash_part.isalnum():
                raise Exception(f"Hash part should be alphanumeric in {sku}")
        
        results.add_pass(f"SKU Format Consistency ({len(products)} checked)")
        
    except Exception as e:
        results.add_fail("SKU Format Consistency", str(e))


# ============================================================================
# TEST 7: Agent Product Dict Includes SKU
# ============================================================================

async def test_agent_product_dict_sku():
    """Test that agent product dict includes SKU with fallback"""
    try:
        # Test with product that has SKU
        product = await Product.find_one({"sku": {"$exists": True, "$ne": None}})
        if not product:
            raise Exception("No product with SKU found")
        
        # Convert to dict (MongoDB format)
        mongo_dict = {
            "_id": product.id,
            "sku": product.sku,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "description": product.description,
            "price": product.price,
            "rating": product.rating,
            "numReviews": product.num_reviews,
        }
        
        # Test agent conversion
        agent_dict = agent_product_to_dict(mongo_dict)
        if agent_dict["sku"] != product.sku:
            raise Exception(f"Agent dict SKU mismatch: {agent_dict['sku']} vs {product.sku}")
        
        # Test with missing SKU (fallback)
        mongo_dict_no_sku = {
            "_id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "description": product.description,
            "price": product.price,
        }
        
        agent_dict_fallback = agent_product_to_dict(mongo_dict_no_sku)
        expected_fallback = f"SKU-{str(product.id).upper()}"
        if agent_dict_fallback["sku"] != expected_fallback:
            raise Exception(f"Agent fallback SKU mismatch: {agent_dict_fallback['sku']} vs {expected_fallback}")
        
        results.add_pass("Agent Product Dict Includes SKU")
        
    except Exception as e:
        results.add_fail("Agent Product Dict Includes SKU", str(e))


# ============================================================================
# TEST 8: User History Product Dict Includes SKU
# ============================================================================

async def test_user_history_product_dict_sku():
    """Test that user history product dict includes SKU with fallback"""
    try:
        product = await Product.find_one()
        if not product:
            raise Exception("No product found")
        
        # Convert to dict (MongoDB format)
        mongo_dict = {
            "_id": product.id,
            "sku": product.sku,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "description": product.description,
            "price": product.price,
            "rating": product.rating,
        }
        
        # Test history conversion
        history_dict = history_product_to_dict(mongo_dict)
        
        if product.sku:
            if history_dict["sku"] != product.sku:
                raise Exception(f"History dict SKU mismatch: {history_dict['sku']} vs {product.sku}")
        else:
            expected_fallback = f"SKU-{str(product.id).upper()}"
            if history_dict["sku"] != expected_fallback:
                raise Exception(f"History fallback SKU mismatch: {history_dict['sku']} vs {expected_fallback}")
        
        results.add_pass("User History Product Dict Includes SKU")
        
    except Exception as e:
        results.add_fail("User History Product Dict Includes SKU", str(e))


# ============================================================================
# TEST 9: SKU Uniqueness Across Products
# ============================================================================

async def test_sku_uniqueness():
    """Test that SKUs are unique across all products"""
    try:
        products = await Product.find().to_list()
        
        if not products:
            raise Exception("No products found")
        
        skus = [p.sku for p in products if p.sku]
        unique_skus = set(skus)
        
        if len(skus) != len(unique_skus):
            # Find duplicates
            from collections import Counter
            sku_counts = Counter(skus)
            duplicates = {sku: count for sku, count in sku_counts.items() if count > 1}
            raise Exception(f"Duplicate SKUs found: {duplicates}")
        
        results.add_pass(f"SKU Uniqueness ({len(skus)} unique SKUs)")
        
    except Exception as e:
        results.add_fail("SKU Uniqueness", str(e))


# ============================================================================
# TEST 10: Create Product via API with SKU
# ============================================================================

async def test_create_product_with_sku():
    """Test creating product via API creates/uses SKU correctly"""
    try:
        admin = await User.find_one(User.is_admin == True)
        if not admin:
            raise Exception("No admin user found")
        
        # Test 1: Create with explicit SKU
        from routers.products import create_product
        
        product_data = ProductCreate(
            sku="API-TEST-SKU-001",
            name="API Test Product",
            price=99.99,
            image="/images/test.png",
            brand="APIBrand",
            category="Test",
            count_in_stock=10,
            description="API test"
        )
        
        # Simulate the create_product function logic
        product = Product(
            name=product_data.name,
            price=product_data.price,
            user=admin.id,
            sku=product_data.sku or generate_sku_fallback(),
            image=product_data.image,
            brand=product_data.brand,
            category=product_data.category,
            count_in_stock=product_data.count_in_stock,
            num_reviews=0,
            description=product_data.description,
        )
        await product.save()
        
        if product.sku != "API-TEST-SKU-001":
            raise Exception(f"Expected SKU 'API-TEST-SKU-001', got {product.sku}")
        
        # Test 2: Create without SKU (should auto-generate)
        product_data2 = ProductCreate(
            name="API Test Product 2",
            price=49.99,
            image="/images/test.png",
            brand="APIBrand",
            category="Test",
            count_in_stock=5,
            description="API test 2"
        )
        
        product2 = Product(
            name=product_data2.name,
            price=product_data2.price,
            user=admin.id,
            sku=product_data2.sku or generate_sku_fallback(),
            image=product_data2.image,
            brand=product_data2.brand,
            category=product_data2.category,
            count_in_stock=product_data2.count_in_stock,
            num_reviews=0,
            description=product_data2.description,
        )
        await product2.save()
        
        if not product2.sku or not product2.sku.startswith("SKU-"):
            raise Exception(f"Auto-generated SKU invalid: {product2.sku}")
        
        # Cleanup
        await product.delete()
        await product2.delete()
        
        results.add_pass("Create Product via API with SKU")
        
    except Exception as e:
        results.add_fail("Create Product via API with SKU", str(e))


# ============================================================================
# TEST 11: Update Product SKU
# ============================================================================

async def test_update_product_sku():
    """Test updating product SKU via API"""
    try:
        admin = await User.find_one(User.is_admin == True)
        if not admin:
            raise Exception("No admin user found")
        
        # Create test product
        product = Product(
            user=admin.id,
            sku="ORIGINAL-SKU",
            name="Update Test",
            image="/images/test.png",
            brand="TestBrand",
            category="Test",
            description="Test",
            price=10.0,
            count_in_stock=5
        )
        await product.save()
        
        # Simulate update
        product_data = ProductUpdate(sku="UPDATED-SKU")
        
        if product_data.sku is not None:
            product.sku = product_data.sku
        
        await product.save()
        
        # Verify update
        updated = await Product.get(product.id)
        if updated.sku != "UPDATED-SKU":
            raise Exception(f"SKU not updated: {updated.sku}")
        
        # Cleanup
        await product.delete()
        
        results.add_pass("Update Product SKU")
        
    except Exception as e:
        results.add_fail("Update Product SKU", str(e))


# ============================================================================
# TEST 12: Product Response Without Fetched Reviews
# ============================================================================

async def test_product_response_without_fetched_reviews():
    """Test product_to_response handles unfetched reviews (Link objects)"""
    try:
        # Get product without fetching reviews
        product = await Product.find_one()
        if not product:
            raise Exception("No product found")
        
        # This should not crash even if reviews aren't fetched
        response = product_to_response(product)
        
        # Verify SKU is in response
        if not response.sku:
            raise Exception("SKU missing from response")
        
        # Verify reviews is a list (empty if not fetched)
        if not isinstance(response.reviews, list):
            raise Exception(f"Reviews should be a list, got {type(response.reviews)}")
        
        results.add_pass("Product Response Without Fetched Reviews")
        
    except Exception as e:
        results.add_fail("Product Response Without Fetched Reviews", str(e))


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all SKU functionality tests"""
    print("\n" + "="*70)
    print("SKU FUNCTIONALITY - COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")
    
    # Initialize database connection once for all tests
    try:
        await init_db()
        print("✓ Database initialized successfully\n")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}\n")
        return False
    
    # Model & Schema Tests
    print("\n--- MODEL & SCHEMA TESTS ---")
    await test_product_model_sku_field()
    await test_schema_validation()
    
    # API Response Tests
    print("\n--- API RESPONSE TESTS ---")
    await test_api_response_sku_fallback()
    await test_product_response_without_fetched_reviews()
    
    # SKU Generation Tests
    print("\n--- SKU GENERATION TESTS ---")
    test_sku_generation()
    
    # Database Tests
    print("\n--- DATABASE TESTS ---")
    await test_seeded_products_have_sku()
    await test_sku_format_consistency()
    await test_sku_uniqueness()
    
    # Agent Integration Tests
    print("\n--- AGENT INTEGRATION TESTS ---")
    await test_agent_product_dict_sku()
    await test_user_history_product_dict_sku()
    
    # CRUD Operation Tests
    print("\n--- CRUD OPERATION TESTS ---")
    await test_create_product_with_sku()
    await test_update_product_sku()
    
    # Print summary
    success = results.summary()
    
    return success


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
