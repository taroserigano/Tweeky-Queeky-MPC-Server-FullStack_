"""
INTEGRATION TEST SUITE
Tests all API endpoints and integrations
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"


class APIClient:
    """API client for testing"""
    
    def __init__(self):
        self.session = requests.Session()
        self.user_info = None
    
    def login(self, email, password):
        """Login and store session"""
        response = self.session.post(
            f"{BASE_URL}/api/users/auth",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            self.user_info = response.json()
            return True
        return False
    
    def logout(self):
        """Logout and clear session"""
        response = self.session.post(f"{BASE_URL}/api/users/logout")
        self.session.cookies.clear()
        self.user_info = None
        return response.status_code == 200


def test(name):
    """Decorator for tests"""
    def decorator(func):
        func.test_name = name
        return func
    return decorator


def run_test(func):
    """Run a single test"""
    print(f"\n{'='*80}")
    print(f"TEST: {func.test_name}")
    print(f"{'='*80}")
    
    try:
        result = func()
        if result:
            print(f"✅ PASS: {func.test_name}")
            return True
        else:
            print(f"❌ FAIL: {func.test_name}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {func.test_name} - {e}")
        import traceback
        traceback.print_exc()
        return False


# ========================================================================
# USER ENDPOINTS
# ========================================================================

@test("POST /api/users - Register User")
def test_register_user():
    client = APIClient()
    timestamp = int(time.time())
    
    response = client.session.post(
        f"{BASE_URL}/api/users",
        json={
            "name": f"Integration Test User {timestamp}",
            "email": f"integration{timestamp}@test.com",
            "password": "testpass123"
        }
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        user = response.json()
        print(f"User ID: {user['_id']}")
        print(f"Email: {user['email']}")
        assert user['email'] == f"integration{timestamp}@test.com"
        return True
    
    print(f"Error: {response.text}")
    return False


@test("POST /api/users/auth - Login User")
def test_login_user():
    client = APIClient()
    
    if client.login("admin@email.com", "123456"):
        print(f"User: {client.user_info['email']}")
        print(f"Admin: {client.user_info['isAdmin']}")
        return True
    
    return False


@test("POST /api/users/logout - Logout User")
def test_logout_user():
    client = APIClient()
    
    if not client.login("admin@email.com", "123456"):
        return False
    
    if client.logout():
        print("Logged out successfully")
        return True
    
    return False


@test("GET /api/users/profile - Get User Profile")
def test_get_profile():
    client = APIClient()
    
    if not client.login("admin@email.com", "123456"):
        return False
    
    response = client.session.get(f"{BASE_URL}/api/users/profile")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        profile = response.json()
        print(f"Email: {profile['email']}")
        return True
    
    print(f"Error: {response.text}")
    return False


@test("PUT /api/users/profile - Update User Profile")
def test_update_profile():
    client = APIClient()
    
    if not client.login("admin@email.com", "123456"):
        return False
    
    response = client.session.put(
        f"{BASE_URL}/api/users/profile",
        json={
            "name": "Admin User Updated",
            "email": "admin@email.com"
        }
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        profile = response.json()
        print(f"Updated name: {profile['name']}")
        return True
    
    print(f"Error: {response.text}")
    return False


@test("GET /api/users - Get All Users (Admin)")
def test_get_all_users():
    client = APIClient()
    
    if not client.login("admin@email.com", "123456"):
        return False
    
    response = client.session.get(f"{BASE_URL}/api/users")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        users = response.json()
        print(f"Total users: {len(users)}")
        return True
    
    print(f"Error: {response.text}")
    return False


# ========================================================================
# PRODUCT ENDPOINTS
# ========================================================================

@test("GET /api/products - Get All Products")
def test_get_products():
    client = APIClient()
    
    response = client.session.get(f"{BASE_URL}/api/products")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        products = data['products']
        print(f"Products: {len(products)}")
        print(f"Pages: {data['pages']}")
        print(f"Current page: {data['page']}")
        return len(products) > 0
    
    print(f"Error: {response.text}")
    return False


@test("GET /api/products/:id - Get Single Product")
def test_get_single_product():
    client = APIClient()
    
    # Get first product ID
    response = client.session.get(f"{BASE_URL}/api/products")
    if response.status_code != 200:
        return False
    
    products = response.json()['products']
    if not products:
        return False
    
    product_id = products[0]['_id']
    
    response = client.session.get(f"{BASE_URL}/api/products/{product_id}")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        product = response.json()
        print(f"Product: {product['name']}")
        print(f"Price: ${product['price']}")
        return True
    
    print(f"Error: {response.text}")
    return False


@test("GET /api/products/top - Get Top Products")
def test_get_top_products():
    client = APIClient()
    
    response = client.session.get(f"{BASE_URL}/api/products/top")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        products = response.json()
        print(f"Top products: {len(products)}")
        return True
    
    print(f"Error: {response.text}")
    return False


@test("GET /api/products?keyword=... - Search Products")
def test_search_products():
    client = APIClient()
    
    response = client.session.get(f"{BASE_URL}/api/products?keyword=chair")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        products = data['products']
        print(f"Search results: {len(products)}")
        if products:
            print(f"First result: {products[0]['name']}")
        return True
    
    print(f"Error: {response.text}")
    return False


@test("GET /api/products?pageNumber=2 - Pagination")
def test_product_pagination():
    client = APIClient()
    
    response = client.session.get(f"{BASE_URL}/api/products?pageNumber=1")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Page {data['page']} of {data['pages']}")
        print(f"Products on page: {len(data['products'])}")
        return True
    
    print(f"Error: {response.text}")
    return False


# ========================================================================
# ORDER ENDPOINTS
# ========================================================================

@test("POST /api/orders - Create Order")
def test_create_order():
    client = APIClient()
    
    if not client.login("admin@email.com", "123456"):
        return False
    
    # Get a product
    response = client.session.get(f"{BASE_URL}/api/products")
    if response.status_code != 200:
        return False
    
    product = response.json()['products'][0]
    
    order_data = {
        "orderItems": [{
            "name": product['name'],
            "qty": 2,
            "image": product['image'],
            "price": product['price'],
            "product": product['_id']
        }],
        "shippingAddress": {
            "address": "123 Integration Test St",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = client.session.post(
        f"{BASE_URL}/api/orders",
        json=order_data
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        order = response.json()
        print(f"Order ID: {order['_id']}")
        print(f"Total: ${order['totalPrice']}")
        print(f"Items: ${order['itemsPrice']}")
        print(f"Tax: ${order['taxPrice']}")
        print(f"Shipping: ${order['shippingPrice']}")
        return True
    
    print(f"Error: {response.text}")
    return False


@test("GET /api/orders/:id - Get Order Details")
def test_get_order_details():
    client = APIClient()
    
    if not client.login("admin@email.com", "123456"):
        return False
    
    # Create an order first
    response = client.session.get(f"{BASE_URL}/api/products")
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
            "address": "123 Test St",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = client.session.post(f"{BASE_URL}/api/orders", json=order_data)
    order_id = response.json()['_id']
    
    # Get order details
    response = client.session.get(f"{BASE_URL}/api/orders/{order_id}")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        order = response.json()
        print(f"Order ID: {order['_id']}")
        print(f"Status: {'Paid' if order['isPaid'] else 'Not Paid'}")
        return True
    
    print(f"Error: {response.text}")
    return False


@test("PUT /api/orders/:id/pay - Pay Order")
def test_pay_order():
    client = APIClient()
    
    if not client.login("admin@email.com", "123456"):
        return False
    
    # Create an order
    response = client.session.get(f"{BASE_URL}/api/products")
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
            "address": "123 Test St",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = client.session.post(f"{BASE_URL}/api/orders", json=order_data)
    order = response.json()
    order_id = order['_id']
    
    print(f"Order created: {order_id}")
    
    # Pay order
    payment_data = {
        "id": f"INTEGRATION_TEST_{int(time.time()*1000)}",
        "status": "COMPLETED",
        "update_time": datetime.utcnow().isoformat(),
        "payer": {"email_address": "integration@test.com"}
    }
    
    response = client.session.put(
        f"{BASE_URL}/api/orders/{order_id}/pay",
        json=payment_data
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        paid_order = response.json()
        print(f"Payment status: {'PAID' if paid_order['isPaid'] else 'NOT PAID'}")
        print(f"Paid at: {paid_order.get('paidAt', 'N/A')}")
        
        if not paid_order['isPaid']:
            print("❌ CRITICAL: Order not marked as paid!")
            return False
        
        return True
    
    print(f"Error: {response.text}")
    return False


@test("GET /api/orders/mine - Get My Orders")
def test_get_my_orders():
    client = APIClient()
    
    if not client.login("admin@email.com", "123456"):
        return False
    
    response = client.session.get(f"{BASE_URL}/api/orders/mine")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        orders = response.json()
        print(f"My orders: {len(orders)}")
        return True
    
    print(f"Error: {response.text}")
    return False


@test("GET /api/orders - Get All Orders (Admin)")
def test_get_all_orders():
    client = APIClient()
    
    if not client.login("admin@email.com", "123456"):
        return False
    
    response = client.session.get(f"{BASE_URL}/api/orders")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        orders = response.json()
        print(f"Total orders: {len(orders)}")
        return True
    
    print(f"Error: {response.text}")
    return False


@test("PUT /api/orders/:id/deliver - Mark Order Delivered (Admin)")
def test_mark_delivered():
    client = APIClient()
    
    if not client.login("admin@email.com", "123456"):
        return False
    
    # Create and pay an order
    response = client.session.get(f"{BASE_URL}/api/products")
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
            "address": "123 Test St",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = client.session.post(f"{BASE_URL}/api/orders", json=order_data)
    order_id = response.json()['_id']
    
    # Pay order
    payment_data = {
        "id": f"DELIVER_TEST_{int(time.time()*1000)}",
        "status": "COMPLETED",
        "payer": {"email_address": "test@test.com"}
    }
    
    client.session.put(f"{BASE_URL}/api/orders/{order_id}/pay", json=payment_data)
    
    # Mark as delivered
    response = client.session.put(f"{BASE_URL}/api/orders/{order_id}/deliver")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        order = response.json()
        print(f"Delivery status: {'DELIVERED' if order['isDelivered'] else 'NOT DELIVERED'}")
        print(f"Delivered at: {order.get('deliveredAt', 'N/A')}")
        return order['isDelivered']
    
    print(f"Error: {response.text}")
    return False


# ========================================================================
# RUN ALL INTEGRATION TESTS
# ========================================================================

def run_all_integration_tests():
    """Run all integration tests"""
    
    print("\n" + "🔥"*40)
    print("    INTEGRATION TEST SUITE")
    print("🔥"*40)
    
    all_tests = [
        # User endpoints
        test_register_user,
        test_login_user,
        test_logout_user,
        test_get_profile,
        test_update_profile,
        test_get_all_users,
        
        # Product endpoints
        test_get_products,
        test_get_single_product,
        test_get_top_products,
        test_search_products,
        test_product_pagination,
        
        # Order endpoints
        test_create_order,
        test_get_order_details,
        test_pay_order,
        test_get_my_orders,
        test_get_all_orders,
        test_mark_delivered,
    ]
    
    results = []
    for test_func in all_tests:
        result = run_test(test_func)
        results.append((test_func.test_name, result))
    
    # Summary
    print("\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    print("\n" + "="*80)
    print(f"Total: {total} | Passed: {passed} | Failed: {total - passed}")
    print("="*80 + "\n")
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED! 🎉\n")
        return True
    else:
        print(f"❌ {total - passed} INTEGRATION TEST(S) FAILED ❌\n")
        return False


if __name__ == "__main__":
    try:
        success = run_all_integration_tests()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
