import asyncio
import httpx
from bson import ObjectId

BASE_URL = "http://127.0.0.1:5000"

# Test credentials (you may need to adjust these)
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
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        else:
            print(f"❌ Login failed for {email}: {response.status_code}")
            print(response.text)
            return None


async def get_product(product_id: str):
    """Get product details"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/products/{product_id}")
        if response.status_code == 200:
            return response.json()
        return None


async def add_review(product_id: str, token: str, rating: int, comment: str):
    """Add a review to a product"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/products/{product_id}/reviews",
            json={"rating": rating, "comment": comment},
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code, response.json()


async def test_review_persistence():
    print("🧪 TESTING REVIEW PERSISTENCE\n")
    print("=" * 60)
    
    # Step 1: Get product to test
    products_response = await httpx.AsyncClient().get(f"{BASE_URL}/api/products")
    products = products_response.json()["products"]
    
    if not products:
        print("❌ No products found!")
        return False
    
    test_product_id = products[0]["_id"]
    product_name = products[0]["name"]
    
    print(f"📦 Testing with product: {product_name}")
    print(f"   ID: {test_product_id}\n")
    
    # Step 2: Check initial review count
    product = await get_product(test_product_id)
    initial_reviews = product.get("reviews", [])
    initial_count = len(initial_reviews)
    
    print(f"📊 Initial state:")
    print(f"   Reviews count: {initial_count}")
    print(f"   Rating: {product.get('rating')}")
    print(f"   Num reviews: {product.get('numReviews')}\n")
    
    if initial_reviews:
        print(f"   Existing reviews:")
        for i, rev in enumerate(initial_reviews, 1):
            print(f"   {i}. {rev.get('name')}: {rev.get('rating')}⭐ - {rev.get('comment')[:50]}...")
        print()
    
    # Step 3: Login users
    print("🔐 Logging in users...")
    user1_token = await login(USER1_EMAIL, USER1_PASSWORD)
    user2_token = await login(USER2_EMAIL, USER2_PASSWORD)
    
    if not user1_token:
        print("❌ Could not login user1")
        return False
    
    print("✅ Users logged in\n")
    
    # Step 4: Add first review
    print("📝 Adding review 1...")
    status1, response1 = await add_review(
        test_product_id, 
        user1_token, 
        5, 
        "First test review - this is amazing!"
    )
    print(f"   Status: {status1}")
    print(f"   Response: {response1}\n")
    
    # Check after first review
    product_after_1 = await get_product(test_product_id)
    reviews_after_1 = product_after_1.get("reviews", [])
    count_after_1 = len(reviews_after_1)
    
    print(f"📊 After review 1:")
    print(f"   Reviews count: {count_after_1} (expected: {initial_count + 1})")
    print(f"   Rating: {product_after_1.get('rating')}")
    print(f"   Num reviews: {product_after_1.get('numReviews')}\n")
    
    if count_after_1 != initial_count + 1:
        print(f"❌ FAIL: Expected {initial_count + 1} reviews, got {count_after_1}")
        print(f"   Reviews list: {reviews_after_1}")
        return False
    
    print("✅ First review added successfully\n")
    
    # Step 5: Add second review (if user2 token available)
    if user2_token:
        print("📝 Adding review 2...")
        status2, response2 = await add_review(
            test_product_id,
            user2_token,
            4,
            "Second test review - pretty good!"
        )
        print(f"   Status: {status2}")
        print(f"   Response: {response2}\n")
        
        # Check after second review
        product_after_2 = await get_product(test_product_id)
        reviews_after_2 = product_after_2.get("reviews", [])
        count_after_2 = len(reviews_after_2)
        
        print(f"📊 After review 2:")
        print(f"   Reviews count: {count_after_2} (expected: {initial_count + 2})")
        print(f"   Rating: {product_after_2.get('rating')}")
        print(f"   Num reviews: {product_after_2.get('numReviews')}\n")
        
        if count_after_2 != initial_count + 2:
            print(f"❌ FAIL: Expected {initial_count + 2} reviews, got {count_after_2}")
            print(f"   ALL REVIEWS WERE OVERWRITTEN!")
            print(f"   Reviews list:")
            for i, rev in enumerate(reviews_after_2, 1):
                print(f"   {i}. {rev.get('name')}: {rev.get('rating')}⭐")
            return False
        
        print("✅ Second review added successfully\n")
    
    # Final verification
    print("=" * 60)
    print("🎉 FINAL VERIFICATION:")
    final_product = await get_product(test_product_id)
    final_reviews = final_product.get("reviews", [])
    
    print(f"   Total reviews: {len(final_reviews)}")
    print(f"   All reviews:")
    for i, rev in enumerate(final_reviews, 1):
        print(f"   {i}. {rev.get('name')}: {rev.get('rating')}⭐ - {rev.get('comment')[:50]}...")
    
    print("\n✅ TEST PASSED: Reviews are being appended correctly!")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_review_persistence())
        if not success:
            print("\n💥 TEST FAILED")
            exit(1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
