"""
Comprehensive test to verify review append functionality
Tests that new reviews are ADDED, not OVERWRITING existing reviews
"""
import asyncio
import httpx
from bson import ObjectId

BASE_URL = "http://127.0.0.1:5000"

# User credentials
ADMIN_EMAIL = "admin@email.com"
ADMIN_PASSWORD = "123456"

USER1_EMAIL = "john@email.com"
USER1_PASSWORD = "123456"

USER2_EMAIL = "jane@email.com"
USER2_PASSWORD = "123456"


async def login(email: str, password: str):
    """Login and get JWT token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/users/login",
            json={"email": email, "password": password},
            timeout=10.0
        )
        if response.status_code == 200:
            return response.json().get("token")
        return None


async def get_products():
    """Get all products"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/products", timeout=10.0)
        if response.status_code == 200:
            return response.json()["products"]
        return []


async def get_product_detail(product_id: str):
    """Get single product with reviews"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/products/{product_id}", timeout=10.0)
        if response.status_code == 200:
            return response.json()
        return None


async def add_review(product_id: str, token: str, rating: int, comment: str):
    """Add a review to a product"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/products/{product_id}/reviews",
            json={"rating": rating, "comment": comment},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        return response.status_code, response.json() if response.status_code != 500 else response.text


async def run_thorough_test():
    print("=" * 80)
    print("COMPREHENSIVE REVIEW APPEND TEST")
    print("=" * 80)
    print()
    
    # Step 1: Get test product
    print("Step 1: Getting test product...")
    products = await get_products()
    
    if not products:
        print("❌ FAIL: No products found!")
        return False
    
    # Use first product
    test_product = products[0]
    product_id = test_product["_id"]
    product_name = test_product["name"]
    
    print(f"✅ Using product: {product_name}")
    print(f"   ID: {product_id}")
    print()
    
    # Step 2: Check INITIAL state
    print("Step 2: Checking INITIAL state...")
    initial_product = await get_product_detail(product_id)
    initial_reviews = initial_product.get("reviews", [])
    initial_count = len(initial_reviews)
    
    print(f"   Reviews count: {initial_count}")
    print(f"   Rating: {initial_product.get('rating')}")
    print(f"   Num reviews: {initial_product.get('numReviews')}")
    
    if initial_reviews:
        print(f"   Existing reviews:")
        for i, rev in enumerate(initial_reviews, 1):
            print(f"     {i}. {rev.get('name')}: {rev.get('rating')}⭐ - {rev.get('comment')[:30]}...")
    print()
    
    # Step 3: Login users
    print("Step 3: Logging in test users...")
    admin_token = await login(ADMIN_EMAIL, ADMIN_PASSWORD)
    user1_token = await login(USER1_EMAIL, USER1_PASSWORD)
    user2_token = await login(USER2_EMAIL, USER2_PASSWORD)
    
    if not admin_token:
        print("❌ FAIL: Could not login admin")
        return False
    
    print(f"✅ Admin logged in")
    if user1_token:
        print(f"✅ User1 logged in")
    if user2_token:
        print(f"✅ User2 logged in")
    print()
    
    # Step 4: Add FIRST review
    print("Step 4: Adding FIRST test review...")
    status1, response1 = await add_review(
        product_id,
        admin_token,
        5,
        "TEST REVIEW 1 - This should be ADDED to existing reviews!"
    )
    print(f"   Status: {status1}")
    print(f"   Response: {response1}")
    
    if status1 == 400 and "already reviewed" in str(response1):
        print("   ⚠️  Admin already reviewed, trying user1...")
        if user1_token:
            status1, response1 = await add_review(
                product_id,
                user1_token,
                5,
                "TEST REVIEW 1 - This should be ADDED to existing reviews!"
            )
            print(f"   Status: {status1}")
            print(f"   Response: {response1}")
    print()
    
    # Step 5: Check state AFTER first review
    print("Step 5: Verifying state AFTER first review...")
    await asyncio.sleep(1)  # Give DB time to update
    
    after_first = await get_product_detail(product_id)
    reviews_after_first = after_first.get("reviews", [])
    count_after_first = len(reviews_after_first)
    
    expected_count_1 = initial_count + 1
    
    print(f"   Reviews count: {count_after_first} (expected: {expected_count_1})")
    print(f"   Rating: {after_first.get('rating')}")
    print(f"   Num reviews: {after_first.get('numReviews')}")
    
    print(f"   All reviews after first:")
    for i, rev in enumerate(reviews_after_first, 1):
        print(f"     {i}. {rev.get('name')}: {rev.get('rating')}⭐ - {rev.get('comment')[:40]}...")
    print()
    
    if count_after_first != expected_count_1:
        print(f"❌ CRITICAL FAILURE!")
        print(f"   Expected {expected_count_1} reviews, but got {count_after_first}")
        print(f"   This means reviews were OVERWRITTEN, not APPENDED!")
        print()
        print("   Initial reviews:")
        for i, rev in enumerate(initial_reviews, 1):
            print(f"     {i}. {rev.get('name')}")
        print()
        print("   Current reviews:")
        for i, rev in enumerate(reviews_after_first, 1):
            print(f"     {i}. {rev.get('name')}")
        return False
    
    print(f"✅ PASS: First review was APPENDED correctly")
    print()
    
    # Step 6: Add SECOND review
    if user2_token:
        print("Step 6: Adding SECOND test review...")
        status2, response2 = await add_review(
            product_id,
            user2_token,
            4,
            "TEST REVIEW 2 - This should also be ADDED, not replace!"
        )
        print(f"   Status: {status2}")
        print(f"   Response: {response2}")
        print()
        
        # Step 7: Check state AFTER second review
        print("Step 7: Verifying state AFTER second review...")
        await asyncio.sleep(1)  # Give DB time to update
        
        after_second = await get_product_detail(product_id)
        reviews_after_second = after_second.get("reviews", [])
        count_after_second = len(reviews_after_second)
        
        expected_count_2 = initial_count + 2
        
        print(f"   Reviews count: {count_after_second} (expected: {expected_count_2})")
        print(f"   Rating: {after_second.get('rating')}")
        print(f"   Num reviews: {after_second.get('numReviews')}")
        
        print(f"   All reviews after second:")
        for i, rev in enumerate(reviews_after_second, 1):
            print(f"     {i}. {rev.get('name')}: {rev.get('rating')}⭐ - {rev.get('comment')[:40]}...")
        print()
        
        if count_after_second != expected_count_2:
            print(f"❌ CRITICAL FAILURE!")
            print(f"   Expected {expected_count_2} reviews, but got {count_after_second}")
            print(f"   Second review OVERWROTE previous reviews!")
            return False
        
        print(f"✅ PASS: Second review was also APPENDED correctly")
    
    print()
    print("=" * 80)
    print("🎉 ALL TESTS PASSED!")
    print("   Reviews are being APPENDED correctly, not overwritten!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(run_thorough_test())
        if not success:
            print("\n💥 TEST SUITE FAILED")
            exit(1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
