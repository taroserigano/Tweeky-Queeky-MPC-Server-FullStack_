"""
COMPLETE WORKFLOW TESTS
Simulates real user journeys through the application
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"


class UserSession:
    """Simulates a user browser session"""
    def __init__(self):
        self.session = requests.Session()
        self.user_info = None
        
    def register(self, name, email, password):
        response = self.session.post(
            f"{BASE_URL}/api/users",
            json={"name": name, "email": email, "password": password}
        )
        if response.status_code == 201:
            self.user_info = response.json()
            return True
        return False
    
    def login(self, email, password):
        response = self.session.post(
            f"{BASE_URL}/api/users/auth",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            self.user_info = response.json()
            return True
        return False
    
    def logout(self):
        response = self.session.post(f"{BASE_URL}/api/users/logout")
        self.user_info = None
        return response.status_code == 200


def test_header(name):
    print(f"\n{'='*80}")
    print(f"WORKFLOW: {name}")
    print(f"{'='*80}")


def test_pass(msg):
    print(f"✅ {msg}")


def test_fail(msg):
    print(f"❌ {msg}")


def test_info(msg):
    print(f"ℹ️  {msg}")


# ========================================================================
# WORKFLOW 1: Complete Shopping Journey (Guest → Customer → Buyer)
# ========================================================================

def test_complete_shopping_journey():
    """Simulate a complete shopping journey from browsing to purchase"""
    test_header("COMPLETE SHOPPING JOURNEY")
    
    timestamp = int(time.time())
    user = UserSession()
    
    # Step 1: Browse products as guest
    test_info("Step 1: Browsing products as guest...")
    response = user.session.get(f"{BASE_URL}/api/products")
    if response.status_code != 200:
        test_fail("Failed to browse products")
        return False
    
    products = response.json()['products']
    test_pass(f"Browsed {len(products)} products")
    
    # Step 2: View product details
    test_info("Step 2: Viewing product details...")
    product = products[0]
    response = user.session.get(f"{BASE_URL}/api/products/{product['_id']}")
    if response.status_code != 200:
        test_fail("Failed to get product details")
        return False
    
    product_details = response.json()
    test_pass(f"Viewed: {product_details['name']} - ${product_details['price']}")
    
    # Step 3: Try to create order without login (should fail)
    test_info("Step 3: Attempting to order without login...")
    order_data = {
        "orderItems": [{
            "name": product['name'],
            "qty": 1,
            "image": product['image'],
            "price": product['price'],
            "product": product['_id']
        }],
        "shippingAddress": {
            "address": "123 Test St",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = user.session.post(f"{BASE_URL}/api/orders", json=order_data)
    if response.status_code == 401:
        test_pass("Correctly rejected - login required")
    else:
        test_fail("Should have been rejected without login")
        return False
    
    # Step 4: Register new account
    test_info("Step 4: Registering new account...")
    if not user.register(
        f"Shopper {timestamp}",
        f"shopper{timestamp}@test.com",
        "password123"
    ):
        test_fail("Registration failed")
        return False
    
    test_pass(f"Registered as: {user.user_info['email']}")
    
    # Step 5: Create order after login
    test_info("Step 5: Creating order after login...")
    response = user.session.post(f"{BASE_URL}/api/orders", json=order_data)
    if response.status_code != 201:
        test_fail(f"Order creation failed: {response.text}")
        return False
    
    order = response.json()
    test_pass(f"Order created: {order['_id']} - ${order['totalPrice']}")
    
    # Step 6: View my orders
    test_info("Step 6: Viewing my orders...")
    response = user.session.get(f"{BASE_URL}/api/orders/mine")
    if response.status_code != 200:
        test_fail("Failed to get orders")
        return False
    
    my_orders = response.json()
    test_pass(f"Found {len(my_orders)} order(s)")
    
    # Step 7: Process payment
    test_info("Step 7: Processing payment...")
    payment_data = {
        "id": f"WORKFLOW_TEST_{timestamp}",
        "status": "COMPLETED",
        "update_time": datetime.utcnow().isoformat(),
        "payer": {"email_address": user.user_info['email']}
    }
    
    response = user.session.put(
        f"{BASE_URL}/api/orders/{order['_id']}/pay",
        json=payment_data
    )
    
    if response.status_code != 200:
        test_fail(f"Payment failed: {response.text}")
        return False
    
    paid_order = response.json()
    if not paid_order['isPaid']:
        test_fail("Order not marked as paid!")
        return False
    
    test_pass(f"Payment successful! Paid at: {paid_order['paidAt']}")
    
    # Step 8: Verify order status changed
    test_info("Step 8: Verifying order status...")
    response = user.session.get(f"{BASE_URL}/api/orders/{order['_id']}")
    final_order = response.json()
    
    if not final_order['isPaid']:
        test_fail("Order status not updated!")
        return False
    
    test_pass("Order status verified - PAID")
    
    # Step 9: Logout
    test_info("Step 9: Logging out...")
    if user.logout():
        test_pass("Logged out successfully")
    
    return True


# ========================================================================
# WORKFLOW 2: Multi-Item Cart Purchase
# ========================================================================

def test_multi_item_cart():
    """Test ordering multiple items at once"""
    test_header("MULTI-ITEM CART PURCHASE")
    
    user = UserSession()
    if not user.login("admin@email.com", "123456"):
        test_fail("Login failed")
        return False
    
    # Get multiple products
    response = user.session.get(f"{BASE_URL}/api/products")
    products = response.json()['products']
    
    if len(products) < 3:
        test_fail("Not enough products for multi-item test")
        return False
    
    # Create order with multiple items
    test_info(f"Creating order with {min(3, len(products))} items...")
    
    order_items = []
    for i, product in enumerate(products[:3]):
        order_items.append({
            "name": product['name'],
            "qty": i + 1,  # Different quantities
            "image": product['image'],
            "price": product['price'],
            "product": product['_id']
        })
    
    order_data = {
        "orderItems": order_items,
        "shippingAddress": {
            "address": "456 Multi St",
            "city": "Cart City",
            "postalCode": "54321",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = user.session.post(f"{BASE_URL}/api/orders", json=order_data)
    if response.status_code != 201:
        test_fail(f"Order creation failed: {response.text}")
        return False
    
    order = response.json()
    test_pass(f"Multi-item order created: ${order['totalPrice']}")
    test_info(f"  Items: {len(order['orderItems'])} products")
    test_info(f"  Subtotal: ${order['itemsPrice']}")
    test_info(f"  Tax: ${order['taxPrice']}")
    test_info(f"  Total: ${order['totalPrice']}")
    
    return True


# ========================================================================
# WORKFLOW 3: Admin Order Management
# ========================================================================

def test_admin_order_management():
    """Test complete admin workflow for managing orders"""
    test_header("ADMIN ORDER MANAGEMENT")
    
    admin = UserSession()
    if not admin.login("admin@email.com", "123456"):
        test_fail("Admin login failed")
        return False
    
    test_pass("Logged in as admin")
    
    # Step 1: View all orders
    test_info("Step 1: Viewing all orders...")
    response = admin.session.get(f"{BASE_URL}/api/orders")
    if response.status_code != 200:
        test_fail("Failed to get all orders")
        return False
    
    all_orders = response.json()
    test_pass(f"Retrieved {len(all_orders)} total orders")
    
    # Step 2: Find a paid order
    paid_orders = [o for o in all_orders if o['isPaid'] and not o['isDelivered']]
    
    if not paid_orders:
        test_info("No paid undelivered orders, creating one...")
        
        # Create and pay an order
        response = admin.session.get(f"{BASE_URL}/api/products")
        product = response.json()['products'][0]
        
        order_data = {
            "orderItems": [{
                "name": product['name'],
                "qty": 1,
                "image": product['image'],
                "price": product['price'],
                "product": product['_id']
            }],
            "shippingAddress": {
                "address": "789 Admin St",
                "city": "Admin City",
                "postalCode": "99999",
                "country": "Test Country"
            },
            "paymentMethod": "PayPal"
        }
        
        response = admin.session.post(f"{BASE_URL}/api/orders", json=order_data)
        order = response.json()
        
        # Pay the order
        payment_data = {
            "id": f"ADMIN_TEST_{int(time.time())}",
            "status": "COMPLETED",
            "payer": {"email_address": "admin@email.com"}
        }
        
        response = admin.session.put(
            f"{BASE_URL}/api/orders/{order['_id']}/pay",
            json=payment_data
        )
        
        order = response.json()
        test_info(f"Created and paid order: {order['_id']}")
    else:
        order = paid_orders[0]
        test_info(f"Using existing order: {order['_id']}")
    
    # Step 3: Mark as delivered
    test_info("Step 2: Marking order as delivered...")
    response = admin.session.put(f"{BASE_URL}/api/orders/{order['_id']}/deliver")
    
    if response.status_code != 200:
        test_fail(f"Failed to mark as delivered: {response.text}")
        return False
    
    delivered_order = response.json()
    test_pass(f"Order marked as delivered at: {delivered_order['deliveredAt']}")
    
    # Step 4: Verify the change
    response = admin.session.get(f"{BASE_URL}/api/orders/{order['_id']}")
    verified_order = response.json()
    
    if not verified_order['isDelivered']:
        test_fail("Delivery status not persisted!")
        return False
    
    test_pass("Delivery status verified in database")
    
    return True


# ========================================================================
# WORKFLOW 4: User Profile Management
# ========================================================================

def test_user_profile_management():
    """Test user profile operations"""
    test_header("USER PROFILE MANAGEMENT")
    
    timestamp = int(time.time())
    user = UserSession()
    
    # Register
    test_info("Step 1: Registering new user...")
    if not user.register(
        f"Profile Test {timestamp}",
        f"profile{timestamp}@test.com",
        "testpass123"
    ):
        test_fail("Registration failed")
        return False
    
    test_pass(f"Registered: {user.user_info['email']}")
    
    # View profile
    test_info("Step 2: Viewing profile...")
    response = user.session.get(f"{BASE_URL}/api/users/profile")
    if response.status_code != 200:
        test_fail("Failed to get profile")
        return False
    
    profile = response.json()
    test_pass(f"Profile: {profile['name']} - {profile['email']}")
    
    # Update profile
    test_info("Step 3: Updating profile...")
    new_name = f"Updated Profile {timestamp}"
    response = user.session.put(
        f"{BASE_URL}/api/users/profile",
        json={
            "name": new_name,
            "email": user.user_info['email']
        }
    )
    
    if response.status_code != 200:
        test_fail("Profile update failed")
        return False
    
    updated_profile = response.json()
    if updated_profile['name'] != new_name:
        test_fail("Profile name not updated")
        return False
    
    test_pass(f"Profile updated: {updated_profile['name']}")
    
    # Verify by fetching again
    response = user.session.get(f"{BASE_URL}/api/users/profile")
    verified_profile = response.json()
    
    if verified_profile['name'] != new_name:
        test_fail("Profile update not persisted")
        return False
    
    test_pass("Profile update verified")
    
    return True


# ========================================================================
# WORKFLOW 5: Product Search and Discovery
# ========================================================================

def test_product_discovery():
    """Test product browsing, search, and filtering"""
    test_header("PRODUCT SEARCH AND DISCOVERY")
    
    user = UserSession()
    
    # Browse all products
    test_info("Step 1: Browsing all products...")
    response = user.session.get(f"{BASE_URL}/api/products")
    if response.status_code != 200:
        test_fail("Failed to get products")
        return False
    
    data = response.json()
    test_pass(f"Found {len(data['products'])} products (Page {data['page']} of {data['pages']})")
    
    # Search products
    test_info("Step 2: Searching for 'chair'...")
    response = user.session.get(f"{BASE_URL}/api/products?keyword=chair")
    if response.status_code != 200:
        test_fail("Search failed")
        return False
    
    search_results = response.json()
    test_pass(f"Found {len(search_results['products'])} matching products")
    
    # Get top products
    test_info("Step 3: Getting top rated products...")
    response = user.session.get(f"{BASE_URL}/api/products/top")
    if response.status_code != 200:
        test_fail("Failed to get top products")
        return False
    
    top_products = response.json()
    test_pass(f"Retrieved {len(top_products)} top products")
    for p in top_products:
        test_info(f"  {p['name']} - Rating: {p.get('rating', 0)}")
    
    return True


# ========================================================================
# RUN ALL WORKFLOWS
# ========================================================================

def run_all_workflows():
    print("\n" + "🔥"*40)
    print("    COMPLETE WORKFLOW TEST SUITE")
    print("🔥"*40)
    
    workflows = [
        ("Complete Shopping Journey", test_complete_shopping_journey),
        ("Multi-Item Cart Purchase", test_multi_item_cart),
        ("Admin Order Management", test_admin_order_management),
        ("User Profile Management", test_user_profile_management),
        ("Product Search and Discovery", test_product_discovery),
    ]
    
    results = []
    for name, test_func in workflows:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            test_fail(f"Workflow crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("WORKFLOW TEST SUMMARY")
    print("="*80)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    print("\n" + "="*80)
    print(f"Total: {total} | Passed: {passed} | Failed: {total - passed}")
    print("="*80 + "\n")
    
    if passed == total:
        print("🎉 ALL WORKFLOW TESTS PASSED! 🎉\n")
        return True
    else:
        print(f"❌ {total - passed} WORKFLOW TEST(S) FAILED ❌\n")
        return False


if __name__ == "__main__":
    try:
        success = run_all_workflows()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
