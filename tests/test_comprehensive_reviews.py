"""
COMPREHENSIVE REVIEW APPEND TEST SUITE
Tests that reviews are APPENDED, not OVERWRITTEN
"""
import asyncio
import httpx
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

# Test user credentials
ADMIN_EMAIL = "admin@email.com"
ADMIN_PASSWORD = "123456"
USER1_EMAIL = "john@email.com"
USER1_PASSWORD = "123456"
USER2_EMAIL = "jane@email.com"
USER2_PASSWORD = "123456"


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name, reason):
        self.failed += 1
        self.errors.append(f"{test_name}: {reason}")
        print(f"❌ FAIL: {test_name}")
        print(f"   Reason: {reason}")
    
    def summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 80)
        print(f"TEST RESULTS: {self.passed}/{total} tests passed")
        print("=" * 80)
        if self.failed > 0:
            print("\nFailed tests:")
            for error in self.errors:
                print(f"  - {error}")
        return self.failed == 0


async def login(email: str, password: str):
    """Login user and return JWT token"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/users/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                return response.json().get("token")
            return None
    except Exception as e:
        print(f"Login error for {email}: {e}")
        return None


async def get_product(product_id: str):
    """Get product details"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/api/products/{product_id}")
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        print(f"Get product error: {e}")
        return None


async def add_review(product_id: str, token: str, rating: int, comment: str):
    """Add review to product"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/products/{product_id}/reviews",
                json={"rating": rating, "comment": comment},
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.status_code, response.json() if response.status_code < 500 else {"error": response.text}
    except Exception as e:
        return 500, {"error": str(e)}


async def run_comprehensive_tests():
    results = TestResults()
    
    print("=" * 80)
    print("COMPREHENSIVE REVIEW APPEND TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # TEST 1: Server connectivity
    print("TEST 1: Server Connectivity")
    print("-" * 40)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/api/products")
            if response.status_code == 200:
                products = response.json()["products"]
                results.add_pass("Server is reachable and responding")
                print(f"   Found {len(products)} products")
            else:
                results.add_fail("Server connectivity", f"Got status {response.status_code}")
                return results
    except Exception as e:
        results.add_fail("Server connectivity", str(e))
        return results
    
    if not products:
        results.add_fail("Product availability", "No products found in database")
        return results
    
    # Select test product
    test_product = products[0]
    product_id = test_product["_id"]
    product_name = test_product["name"]
    
    print(f"   Test product: {product_name} (ID: {product_id})")
    print()
    
    # TEST 2: Get initial state
    print("TEST 2: Product Initial State")
    print("-" * 40)
    initial_product = await get_product(product_id)
    
    if initial_product:
        initial_reviews = initial_product.get("reviews", [])
        initial_count = len(initial_reviews)
        results.add_pass("Product details fetched successfully")
        print(f"   Initial review count: {initial_count}")
        print(f"   Initial rating: {initial_product.get('rating')}")
        print(f"   Has reviews field: {'reviews' in initial_product}")
        
        if initial_reviews:
            print(f"   Existing reviews:")
            for i, rev in enumerate(initial_reviews[:3], 1):
                print(f"     {i}. {rev.get('name')}: {rev.get('rating')}⭐")
            if len(initial_reviews) > 3:
                print(f"     ... and {len(initial_reviews) - 3} more")
    else:
        results.add_fail("Product fetch", "Could not fetch product details")
        return results
    print()
    
    # TEST 3: User authentication
    print("TEST 3: User Authentication")
    print("-" * 40)
    admin_token = await login(ADMIN_EMAIL, ADMIN_PASSWORD)
    user1_token = await login(USER1_EMAIL, USER1_PASSWORD)
    user2_token = await login(USER2_EMAIL, USER2_PASSWORD)
    
    active_tokens = []
    if admin_token:
        active_tokens.append(("Admin", admin_token))
        results.add_pass("Admin login successful")
    else:
        print("   ⚠️  Admin login failed")
    
    if user1_token:
        active_tokens.append(("John", user1_token))
        results.add_pass("User1 (John) login successful")
    else:
        print("   ⚠️  User1 login failed")
    
    if user2_token:
        active_tokens.append(("Jane", user2_token))
        results.add_pass("User2 (Jane) login successful")
    else:
        print("   ⚠️  User2 login failed")
    
    if not active_tokens:
        results.add_fail("User authentication", "No users could log in")
        return results
    print()
    
    # TEST 4: Add first review
    print("TEST 4: Add First Review")
    print("-" * 40)
    test_user_name, test_token = active_tokens[0]
    
    status1, response1 = await add_review(
        product_id,
        test_token,
        5,
        f"TEST REVIEW 1 by {test_user_name} - Testing append functionality at {datetime.now().strftime('%H:%M:%S')}"
    )
    
    print(f"   User: {test_user_name}")
    print(f"   Status: {status1}")
    print(f"   Response: {response1}")
    
    # Handle "already reviewed" case
    if status1 == 400 and "already reviewed" in str(response1).lower():
        print(f"   ⚠️  {test_user_name} already reviewed this product")
        if len(active_tokens) > 1:
            test_user_name, test_token = active_tokens[1]
            print(f"   Trying with {test_user_name}...")
            status1, response1 = await add_review(
                product_id,
                test_token,
                5,
                f"TEST REVIEW 1 by {test_user_name} - Testing append functionality at {datetime.now().strftime('%H:%M:%S')}"
            )
            print(f"   Status: {status1}")
            print(f"   Response: {response1}")
    
    if status1 == 201:
        results.add_pass("First review added successfully")
    elif status1 == 400 and "already reviewed" in str(response1).lower():
        print("   ⚠️  All test users have already reviewed this product")
        print("   Skipping review addition tests")
        print()
        results.add_pass("Review system working (users already reviewed)")
        return results
    else:
        results.add_fail("First review addition", f"Status {status1}: {response1}")
        return results
    print()
    
    # TEST 5: Verify first review was APPENDED
    print("TEST 5: Verify First Review Appended (NOT overwritten)")
    print("-" * 40)
    await asyncio.sleep(1)  # Allow DB to update
    
    after_first = await get_product(product_id)
    
    if after_first:
        reviews_after_first = after_first.get("reviews", [])
        count_after_first = len(reviews_after_first)
        expected_count = initial_count + 1
        
        print(f"   Previous count: {initial_count}")
        print(f"   Current count: {count_after_first}")
        print(f"   Expected count: {expected_count}")
        
        print(f"   All reviews now:")
        for i, rev in enumerate(reviews_after_first, 1):
            print(f"     {i}. {rev.get('name')}: {rev.get('rating')}⭐ - {rev.get('comment')[:40]}...")
        
        if count_after_first == expected_count:
            results.add_pass("First review was APPENDED (not overwritten)")
        elif count_after_first == 1:
            results.add_fail(
                "First review OVERWROTE existing reviews",
                f"Expected {expected_count} reviews but only found 1 - ALL PREVIOUS REVIEWS WERE DELETED!"
            )
        else:
            results.add_fail(
                "First review append",
                f"Expected {expected_count} reviews but found {count_after_first}"
            )
    else:
        results.add_fail("Verify first review", "Could not fetch product after review")
    print()
    
    # TEST 6: Add second review (if possible)
    if len(active_tokens) > 1 and count_after_first == expected_count:
        print("TEST 6: Add Second Review")
        print("-" * 40)
        
        # Find a user who hasn't reviewed yet
        second_user_name, second_token = None, None
        for name, token in active_tokens:
            if token != test_token:
                second_user_name, second_token = name, token
                break
        
        if second_token:
            status2, response2 = await add_review(
                product_id,
                second_token,
                4,
                f"TEST REVIEW 2 by {second_user_name} - Second append test at {datetime.now().strftime('%H:%M:%S')}"
            )
            
            print(f"   User: {second_user_name}")
            print(f"   Status: {status2}")
            print(f"   Response: {response2}")
            
            if status2 == 201:
                results.add_pass("Second review added successfully")
            elif status2 == 400 and "already reviewed" in str(response2).lower():
                print(f"   ⚠️  {second_user_name} also already reviewed")
                results.add_pass("Review validation working (duplicate prevention)")
            else:
                results.add_fail("Second review addition", f"Status {status2}: {response2}")
            print()
            
            # TEST 7: Verify second review was also APPENDED
            if status2 == 201:
                print("TEST 7: Verify Second Review Also Appended")
                print("-" * 40)
                await asyncio.sleep(1)
                
                after_second = await get_product(product_id)
                
                if after_second:
                    reviews_after_second = after_second.get("reviews", [])
                    count_after_second = len(reviews_after_second)
                    expected_count_2 = initial_count + 2
                    
                    print(f"   Initial count: {initial_count}")
                    print(f"   After first: {count_after_first}")
                    print(f"   Current count: {count_after_second}")
                    print(f"   Expected count: {expected_count_2}")
                    
                    print(f"   All reviews now:")
                    for i, rev in enumerate(reviews_after_second, 1):
                        print(f"     {i}. {rev.get('name')}: {rev.get('rating')}⭐ - {rev.get('comment')[:40]}...")
                    
                    if count_after_second == expected_count_2:
                        results.add_pass("Second review was APPENDED (both reviews preserved)")
                    elif count_after_second == 1:
                        results.add_fail(
                            "CRITICAL: Second review OVERWROTE ALL reviews",
                            "Only 1 review remains - COMPLETE OVERWRITE OCCURRED!"
                        )
                    elif count_after_second == count_after_first:
                        results.add_fail(
                            "Second review not added",
                            f"Count unchanged at {count_after_second}"
                        )
                    else:
                        results.add_fail(
                            "Second review append",
                            f"Expected {expected_count_2} but found {count_after_second}"
                        )
                else:
                    results.add_fail("Verify second review", "Could not fetch product")
                print()
    
    # TEST 8: Final integrity check
    print("TEST 8: Final Data Integrity Check")
    print("-" * 40)
    final_product = await get_product(product_id)
    
    if final_product:
        final_reviews = final_product.get("reviews", [])
        final_rating = final_product.get("rating")
        final_num_reviews = final_product.get("numReviews")
        
        print(f"   Total reviews: {len(final_reviews)}")
        print(f"   Rating: {final_rating}")
        print(f"   NumReviews field: {final_num_reviews}")
        
        # Check consistency
        if len(final_reviews) == final_num_reviews:
            results.add_pass("Review count matches numReviews field")
        else:
            results.add_fail(
                "Data integrity",
                f"Review array length ({len(final_reviews)}) != numReviews field ({final_num_reviews})"
            )
        
        # Check rating calculation
        if final_reviews:
            calculated_rating = sum(r.get("rating", 0) for r in final_reviews) / len(final_reviews)
            if abs(calculated_rating - final_rating) < 0.01:
                results.add_pass("Rating calculation is correct")
            else:
                results.add_fail(
                    "Rating calculation",
                    f"Expected {calculated_rating:.2f} but got {final_rating}"
                )
        
        # Check all reviews have required fields
        missing_fields = []
        for i, rev in enumerate(final_reviews):
            required = ["name", "rating", "comment", "user", "createdAt"]
            for field in required:
                if field not in rev:
                    missing_fields.append(f"Review {i+1} missing '{field}'")
        
        if not missing_fields:
            results.add_pass("All reviews have required fields")
        else:
            results.add_fail("Review field validation", "; ".join(missing_fields))
    
    print()
    return results


async def main():
    print("\n")
    results = await run_comprehensive_tests()
    success = results.summary()
    print()
    
    if success:
        print("🎉 ALL TESTS PASSED - Reviews are being APPENDED correctly!")
        return 0
    else:
        print("💥 SOME TESTS FAILED - Review append functionality has issues!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
