"""
COMPREHENSIVE E2E TEST SUITE
Tests all critical user flows and scenarios
"""
import requests
import json
import time
from datetime import datetime
import urllib3

# Disable SSL warnings for local testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "http://localhost:5000"

class TestSession:
    """Test session with cookie handling"""
    def __init__(self):
        self.session = requests.Session()
        # Disable SSL verification for local testing
        self.session.verify = False
        self.user_info = None
        self.token = None
        
    def login(self, email, password):
        """Login and store session"""
        response = self.session.post(
            f"{BASE_URL}/api/users/auth",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            self.user_info = response.json()
            self.token = self.session.cookies.get('jwt')
            
            # Print cookie info for debugging
            print(f"ℹ️  Cookies after login: {len(self.session.cookies)} cookies")
            for cookie in self.session.cookies:
                print(f"ℹ️  Cookie: {cookie.name} = {cookie.value[:20]}...")
            
            return True
        return False
    
    def logout(self):
        """Clear session"""
        self.session.cookies.clear()
        self.user_info = None
        self.token = None


def print_test_header(test_name):
    """Print test header"""
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)


def print_success(message):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")


# ========================================================================
# TEST 1: User Authentication Tests
# ========================================================================

def test_user_registration():
    """Test user registration"""
    print_test_header("USER REGISTRATION")
    
    session = TestSession()
    timestamp = int(time.time())
    
    # Register new user
    response = session.session.post(
        f"{BASE_URL}/api/users",
        json={
            "name": f"Test User {timestamp}",
            "email": f"test{timestamp}@example.com",
            "password": "password123"
        }
    )
    
    if response.status_code == 201:
        user = response.json()
        print_success(f"User registered: {user['email']}")
        assert user['name'] == f"Test User {timestamp}"
        return True
    else:
        print_error(f"Registration failed: {response.text}")
        return False


def test_user_login():
    """Test user login"""
    print_test_header("USER LOGIN")
    
    session = TestSession()
    
    # Login with admin
    if session.login("admin@email.com", "123456"):
        print_success(f"Logged in as: {session.user_info['email']}")
        print_info(f"Is Admin: {session.user_info['isAdmin']}")
        assert session.user_info['isAdmin'] == True
        return session
    else:
        print_error("Login failed")
        return None


def test_invalid_login():
    """Test login with invalid credentials"""
    print_test_header("INVALID LOGIN")
    
    session = TestSession()
    
    response = session.session.post(
        f"{BASE_URL}/api/users/auth",
        json={"email": "wrong@email.com", "password": "wrongpass"}
    )
    
    if response.status_code == 401:
        print_success("Invalid login correctly rejected")
        return True
    else:
        print_error("Invalid login should have been rejected")
        return False


# ========================================================================
# TEST 2: Product Tests
# ========================================================================

def test_get_products(session):
    """Test getting products"""
    print_test_header("GET PRODUCTS")
    
    response = session.session.get(f"{BASE_URL}/api/products")
    
    if response.status_code == 200:
        data = response.json()
        products = data['products']
        print_success(f"Retrieved {len(products)} products")
        print_info(f"Pages: {data['pages']}, Current Page: {data['page']}")
        
        if len(products) > 0:
            product = products[0]
            print_info(f"Sample product: {product['name']} - ${product['price']}")
            return products
        return []
    else:
        print_error(f"Failed to get products: {response.text}")
        return []


def test_get_single_product(session, product_id):
    """Test getting single product"""
    print_test_header("GET SINGLE PRODUCT")
    
    response = session.session.get(f"{BASE_URL}/api/products/{product_id}")
    
    if response.status_code == 200:
        product = response.json()
        print_success(f"Retrieved product: {product['name']}")
        print_info(f"Price: ${product['price']}, Stock: {product['countInStock']}")
        return product
    else:
        print_error(f"Failed to get product: {response.text}")
        return None


def test_get_top_products(session):
    """Test getting top rated products"""
    print_test_header("GET TOP PRODUCTS")
    
    response = session.session.get(f"{BASE_URL}/api/products/top")
    
    if response.status_code == 200:
        products = response.json()
        print_success(f"Retrieved {len(products)} top products")
        return products
    else:
        print_error(f"Failed to get top products: {response.text}")
        return []


# ========================================================================
# TEST 3: Order Creation Tests
# ========================================================================

def test_create_order(session, product):
    """Test creating an order"""
    print_test_header("CREATE ORDER")
    
    order_data = {
        "orderItems": [{
            "name": product['name'],
            "qty": 2,
            "image": product['image'],
            "price": product['price'],
            "product": product['_id']
        }],
        "shippingAddress": {
            "address": "123 Test Street",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    print_info(f"Creating order for: {product['name']} x 2")
    
    response = session.session.post(
        f"{BASE_URL}/api/orders",
        json=order_data
    )
    
    if response.status_code == 201:
        order = response.json()
        print_success(f"Order created: {order['_id']}")
        print_info(f"Total: ${order['totalPrice']}")
        print_info(f"Items Price: ${order['itemsPrice']}")
        print_info(f"Tax: ${order['taxPrice']}")
        print_info(f"Shipping: ${order['shippingPrice']}")
        print_info(f"Payment Status: {'PAID' if order['isPaid'] else 'NOT PAID'}")
        
        assert order['isPaid'] == False, "New order should not be paid"
        return order
    else:
        print_error(f"Failed to create order: {response.text}")
        return None


def test_create_order_without_items(session):
    """Test creating order without items (should fail)"""
    print_test_header("CREATE ORDER WITHOUT ITEMS (NEGATIVE TEST)")
    
    order_data = {
        "orderItems": [],
        "shippingAddress": {
            "address": "123 Test Street",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = session.session.post(
        f"{BASE_URL}/api/orders",
        json=order_data
    )
    
    if response.status_code == 400:
        print_success("Empty order correctly rejected")
        return True
    else:
        print_error("Empty order should have been rejected")
        return False


# ========================================================================
# TEST 4: Payment Tests (CRITICAL)
# ========================================================================

def test_payment_flow(session, order):
    """Test complete payment flow"""
    print_test_header("PAYMENT FLOW (CRITICAL TEST)")
    
    order_id = order['_id']
    total_price = order['totalPrice']
    
    # Step 1: Verify order is NOT paid
    print_info("Step 1: Verifying order is NOT paid before payment...")
    response = session.session.get(f"{BASE_URL}/api/orders/{order_id}")
    
    if response.status_code != 200:
        print_error(f"Failed to get order: {response.text}")
        return False
    
    order_before = response.json()
    if order_before['isPaid']:
        print_error("Order should NOT be paid before payment")
        return False
    
    print_success("Order is NOT paid (correct)")
    
    # Step 2: Process payment
    print_info("Step 2: Processing payment...")
    
    payment_data = {
        "id": f"TEST_PAYMENT_{int(time.time() * 1000)}",
        "status": "COMPLETED",
        "update_time": datetime.utcnow().isoformat(),
        "payer": {
            "email_address": "buyer@example.com",
            "payer_id": "TEST_BUYER_123",
            "name": {
                "given_name": "Test",
                "surname": "Buyer"
            }
        },
        "purchase_units": [{
            "amount": {
                "value": str(total_price),
                "currency_code": "USD"
            }
        }]
    }
    
    print_info(f"Payment ID: {payment_data['id']}")
    print_info(f"Amount: ${total_price}")
    
    response = session.session.put(
        f"{BASE_URL}/api/orders/{order_id}/pay",
        json=payment_data
    )
    
    print_info(f"Payment response status: {response.status_code}")
    
    if response.status_code != 200:
        print_error(f"Payment failed: {response.text}")
        return False
    
    order_after_payment = response.json()
    
    # Step 3: CRITICAL - Verify payment status in response
    print_info("Step 3: Verifying payment status in response...")
    
    if not order_after_payment['isPaid']:
        print_error("CRITICAL: Payment status NOT updated in response!")
        return False
    
    print_success("Payment status updated in response ✓")
    
    if not order_after_payment.get('paidAt'):
        print_error("CRITICAL: paidAt timestamp missing!")
        return False
    
    print_success(f"paidAt timestamp set: {order_after_payment['paidAt']}")
    
    if not order_after_payment.get('paymentResult'):
        print_error("CRITICAL: paymentResult missing!")
        return False
    
    print_success(f"paymentResult stored: {order_after_payment['paymentResult']['id']}")
    
    # Step 4: Verify by fetching order again
    print_info("Step 4: Fetching order from database to verify...")
    
    time.sleep(0.5)  # Small delay to ensure DB write completed
    
    response = session.session.get(f"{BASE_URL}/api/orders/{order_id}")
    
    if response.status_code != 200:
        print_error(f"Failed to get order: {response.text}")
        return False
    
    order_final = response.json()
    
    if not order_final['isPaid']:
        print_error("CRITICAL: Payment status NOT persisted in database!")
        return False
    
    print_success("Payment status persisted in database ✓")
    
    print_success("✓✓✓ PAYMENT FLOW COMPLETED SUCCESSFULLY ✓✓✓")
    return True


def test_duplicate_payment(session, order, payment_id):
    """Test duplicate payment (should fail)"""
    print_test_header("DUPLICATE PAYMENT (NEGATIVE TEST)")
    
    order_id = order['_id']
    total_price = order['totalPrice']
    
    # Try to pay again with same transaction ID
    payment_data = {
        "id": payment_id,  # Reuse same payment ID
        "status": "COMPLETED",
        "update_time": datetime.utcnow().isoformat(),
        "payer": {
            "email_address": "buyer@example.com"
        }
    }
    
    response = session.session.put(
        f"{BASE_URL}/api/orders/{order_id}/pay",
        json=payment_data
    )
    
    if response.status_code == 400:
        print_success("Duplicate payment correctly rejected")
        return True
    else:
        print_error("Duplicate payment should have been rejected")
        return False


# ========================================================================
# TEST 5: Order Retrieval Tests
# ========================================================================

def test_get_my_orders(session):
    """Test getting user's orders"""
    print_test_header("GET MY ORDERS")
    
    response = session.session.get(f"{BASE_URL}/api/orders/mine")
    
    if response.status_code == 200:
        orders = response.json()
        print_success(f"Retrieved {len(orders)} orders")
        
        if len(orders) > 0:
            paid_orders = [o for o in orders if o['isPaid']]
            unpaid_orders = [o for o in orders if not o['isPaid']]
            print_info(f"Paid orders: {len(paid_orders)}")
            print_info(f"Unpaid orders: {len(unpaid_orders)}")
        
        return orders
    else:
        print_error(f"Failed to get orders: {response.text}")
        return []


def test_get_order_details(session, order_id):
    """Test getting order details"""
    print_test_header("GET ORDER DETAILS")
    
    response = session.session.get(f"{BASE_URL}/api/orders/{order_id}")
    
    if response.status_code == 200:
        order = response.json()
        print_success(f"Retrieved order: {order['_id']}")
        print_info(f"Payment Status: {'PAID' if order['isPaid'] else 'NOT PAID'}")
        print_info(f"Delivery Status: {'DELIVERED' if order['isDelivered'] else 'NOT DELIVERED'}")
        return order
    else:
        print_error(f"Failed to get order: {response.text}")
        return None


# ========================================================================
# TEST 6: Admin Tests
# ========================================================================

def test_get_all_orders_as_admin(session):
    """Test getting all orders (admin only)"""
    print_test_header("GET ALL ORDERS (ADMIN)")
    
    response = session.session.get(f"{BASE_URL}/api/orders")
    
    if response.status_code == 200:
        orders = response.json()
        print_success(f"Retrieved {len(orders)} orders")
        return orders
    else:
        print_error(f"Failed to get all orders: {response.text}")
        return []


def test_mark_order_delivered(session, order_id):
    """Test marking order as delivered (admin only)"""
    print_test_header("MARK ORDER AS DELIVERED (ADMIN)")
    
    response = session.session.put(f"{BASE_URL}/api/orders/{order_id}/deliver")
    
    if response.status_code == 200:
        order = response.json()
        print_success("Order marked as delivered")
        print_info(f"Delivered at: {order.get('deliveredAt', 'N/A')}")
        
        assert order['isDelivered'] == True
        assert order.get('deliveredAt') is not None
        
        return True
    else:
        print_error(f"Failed to mark as delivered: {response.text}")
        return False


# ========================================================================
# RUN ALL TESTS
# ========================================================================

def run_all_tests():
    """Run complete test suite"""
    
    print("\n" + "🔥"*40)
    print("    COMPREHENSIVE E2E TEST SUITE")
    print("🔥"*40)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    results = []
    
    # Test 1: User Registration
    total_tests += 1
    if test_user_registration():
        passed_tests += 1
        results.append(("User Registration", True))
    else:
        failed_tests += 1
        results.append(("User Registration", False))
    
    # Test 2: Invalid Login
    total_tests += 1
    if test_invalid_login():
        passed_tests += 1
        results.append(("Invalid Login", True))
    else:
        failed_tests += 1
        results.append(("Invalid Login", False))
    
    # Test 3: Valid Login
    total_tests += 1
    session = test_user_login()
    if session:
        passed_tests += 1
        results.append(("User Login", True))
    else:
        failed_tests += 1
        results.append(("User Login", False))
        print_error("Cannot continue without valid session")
        return
    
    # Test 4: Get Products
    total_tests += 1
    products = test_get_products(session)
    if products:
        passed_tests += 1
        results.append(("Get Products", True))
    else:
        failed_tests += 1
        results.append(("Get Products", False))
        return
    
    # Test 5: Get Single Product
    total_tests += 1
    product = test_get_single_product(session, products[0]['_id'])
    if product:
        passed_tests += 1
        results.append(("Get Single Product", True))
    else:
        failed_tests += 1
        results.append(("Get Single Product", False))
    
    # Test 6: Get Top Products
    total_tests += 1
    if test_get_top_products(session):
        passed_tests += 1
        results.append(("Get Top Products", True))
    else:
        failed_tests += 1
        results.append(("Get Top Products", False))
    
    # Test 7: Create Order Without Items (Negative)
    total_tests += 1
    if test_create_order_without_items(session):
        passed_tests += 1
        results.append(("Create Order Without Items (Negative)", True))
    else:
        failed_tests += 1
        results.append(("Create Order Without Items (Negative)", False))
    
    # Test 8: Create Order
    total_tests += 1
    order = test_create_order(session, products[0])
    if order:
        passed_tests += 1
        results.append(("Create Order", True))
    else:
        failed_tests += 1
        results.append(("Create Order", False))
        return
    
    # Test 9: CRITICAL - Payment Flow
    total_tests += 1
    payment_id = f"TEST_PAYMENT_{int(time.time() * 1000)}"
    if test_payment_flow(session, order):
        passed_tests += 1
        results.append(("Payment Flow (CRITICAL)", True))
    else:
        failed_tests += 1
        results.append(("Payment Flow (CRITICAL)", False))
    
    # Test 10: Get My Orders
    total_tests += 1
    my_orders = test_get_my_orders(session)
    if my_orders:
        passed_tests += 1
        results.append(("Get My Orders", True))
    else:
        failed_tests += 1
        results.append(("Get My Orders", False))
    
    # Test 11: Get Order Details
    total_tests += 1
    if test_get_order_details(session, order['_id']):
        passed_tests += 1
        results.append(("Get Order Details", True))
    else:
        failed_tests += 1
        results.append(("Get Order Details", False))
    
    # Test 12: Get All Orders (Admin)
    total_tests += 1
    if test_get_all_orders_as_admin(session):
        passed_tests += 1
        results.append(("Get All Orders (Admin)", True))
    else:
        failed_tests += 1
        results.append(("Get All Orders (Admin)", False))
    
    # Test 13: Mark Order Delivered (Admin)
    total_tests += 1
    if test_mark_order_delivered(session, order['_id']):
        passed_tests += 1
        results.append(("Mark Order Delivered (Admin)", True))
    else:
        failed_tests += 1
        results.append(("Mark Order Delivered (Admin)", False))
    
    # Print Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    print("="*80 + "\n")
    
    if failed_tests == 0:
        print("🎉🎉🎉 ALL TESTS PASSED! 🎉🎉🎉\n")
        return True
    else:
        print(f"❌ {failed_tests} TEST(S) FAILED ❌\n")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
