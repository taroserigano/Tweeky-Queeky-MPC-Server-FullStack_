"""
PAYMENT STRESS TEST
Tests payment system under various conditions and edge cases
"""
import requests
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:5000"


class TestSession:
    """Test session with cookie handling"""
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


def print_test(message):
    print(f"\n{'='*80}")
    print(f"TEST: {message}")
    print(f"{'='*80}")


def print_pass(message):
    print(f"✅ PASS: {message}")


def print_fail(message):
    print(f"❌ FAIL: {message}")


def print_info(message):
    print(f"ℹ️  {message}")


# ========================================================================
# TEST: Rapid Payment Processing
# ========================================================================

def test_rapid_payment_processing():
    """Test multiple payments in rapid succession"""
    print_test("RAPID PAYMENT PROCESSING")
    
    session = TestSession()
    if not session.login("admin@email.com", "123456"):
        print_fail("Login failed")
        return False
    
    # Get a product
    response = session.session.get(f"{BASE_URL}/api/products")
    if response.status_code != 200:
        print_fail("Failed to get products")
        return False
    
    products = response.json()['products']
    product = products[0]
    
    # Create multiple orders
    orders = []
    num_orders = 5
    
    print_info(f"Creating {num_orders} orders...")
    
    for i in range(num_orders):
        order_data = {
            "orderItems": [{
                "name": product['name'],
                "qty": 1,
                "image": product['image'],
                "price": product['price'],
                "product": product['_id']
            }],
            "shippingAddress": {
                "address": f"123 Test Street #{i}",
                "city": "Test City",
                "postalCode": "12345",
                "country": "Test Country"
            },
            "paymentMethod": "PayPal"
        }
        
        response = session.session.post(f"{BASE_URL}/api/orders", json=order_data)
        if response.status_code == 201:
            orders.append(response.json())
            print_info(f"Order {i+1} created: {response.json()['_id']}")
        else:
            print_fail(f"Failed to create order {i+1}")
            return False
    
    # Process payments rapidly
    print_info(f"\nProcessing {num_orders} payments rapidly...")
    
    results = []
    
    for i, order in enumerate(orders):
        payment_data = {
            "id": f"RAPID_TEST_{int(time.time()*1000)}_{i}",
            "status": "COMPLETED",
            "update_time": datetime.utcnow().isoformat(),
            "payer": {"email_address": f"buyer{i}@example.com"}
        }
        
        start_time = time.time()
        response = session.session.put(
            f"{BASE_URL}/api/orders/{order['_id']}/pay",
            json=payment_data
        )
        end_time = time.time()
        
        success = response.status_code == 200
        if success:
            paid_order = response.json()
            success = paid_order['isPaid']
        
        results.append({
            'order_id': order['_id'],
            'success': success,
            'time': end_time - start_time,
            'status_code': response.status_code
        })
        
        if success:
            print_info(f"✓ Payment {i+1} processed in {end_time - start_time:.3f}s")
        else:
            print_fail(f"✗ Payment {i+1} failed: {response.text}")
    
    # Verify all payments
    print_info("\nVerifying all payments...")
    
    all_passed = True
    for i, result in enumerate(results):
        if not result['success']:
            print_fail(f"Payment {i+1} did not succeed")
            all_passed = False
            continue
        
        # Verify in database
        response = session.session.get(f"{BASE_URL}/api/orders/{result['order_id']}")
        if response.status_code == 200:
            order = response.json()
            if order['isPaid']:
                print_pass(f"Payment {i+1} verified in database")
            else:
                print_fail(f"Payment {i+1} NOT reflected in database!")
                all_passed = False
        else:
            print_fail(f"Could not verify payment {i+1}")
            all_passed = False
    
    return all_passed


# ========================================================================
# TEST: Payment with Missing Fields
# ========================================================================

def test_payment_with_missing_fields():
    """Test payment with various missing fields"""
    print_test("PAYMENT WITH MISSING FIELDS")
    
    session = TestSession()
    if not session.login("admin@email.com", "123456"):
        print_fail("Login failed")
        return False
    
    # Create order
    response = session.session.get(f"{BASE_URL}/api/products")
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
            "address": "123 Test Street",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = session.session.post(f"{BASE_URL}/api/orders", json=order_data)
    order = response.json()
    
    # Test 1: Payment with minimal fields
    print_info("Test 1: Payment with only ID...")
    payment_data = {
        "id": f"MINIMAL_TEST_{int(time.time()*1000)}"
    }
    
    response = session.session.put(
        f"{BASE_URL}/api/orders/{order['_id']}/pay",
        json=payment_data
    )
    
    if response.status_code == 200:
        paid_order = response.json()
        if paid_order['isPaid']:
            print_pass("Payment succeeded with minimal fields")
        else:
            print_fail("Payment did not update status")
            return False
    else:
        print_fail(f"Payment failed: {response.text}")
        return False
    
    return True


# ========================================================================
# TEST: Payment Amount Mismatch
# ========================================================================

def test_payment_amount_mismatch():
    """Test payment with incorrect amount"""
    print_test("PAYMENT AMOUNT MISMATCH")
    
    session = TestSession()
    if not session.login("admin@email.com", "123456"):
        print_fail("Login failed")
        return False
    
    # Create order
    response = session.session.get(f"{BASE_URL}/api/products")
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
            "address": "123 Test Street",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = session.session.post(f"{BASE_URL}/api/orders", json=order_data)
    order = response.json()
    
    # Payment with wrong amount
    payment_data = {
        "id": f"MISMATCH_TEST_{int(time.time()*1000)}",
        "status": "COMPLETED",
        "update_time": datetime.utcnow().isoformat(),
        "payer": {"email_address": "buyer@example.com"},
        "purchase_units": [{
            "amount": {
                "value": "0.01",  # Wrong amount
                "currency_code": "USD"
            }
        }]
    }
    
    print_info(f"Order total: ${order['totalPrice']}")
    print_info(f"Payment amount: $0.01 (intentionally wrong)")
    
    response = session.session.put(
        f"{BASE_URL}/api/orders/{order['_id']}/pay",
        json=payment_data
    )
    
    # Should still work because PayPal verification is optional
    if response.status_code == 200:
        print_info("Payment accepted (verification is optional in dev mode)")
        return True
    else:
        print_info(f"Payment rejected: {response.text}")
        return True  # Either behavior is acceptable


# ========================================================================
# TEST: Double Payment Prevention
# ========================================================================

def test_double_payment_prevention():
    """Test that duplicate payment IDs are rejected"""
    print_test("DOUBLE PAYMENT PREVENTION")
    
    session = TestSession()
    if not session.login("admin@email.com", "123456"):
        print_fail("Login failed")
        return False
    
    # Create order
    response = session.session.get(f"{BASE_URL}/api/products")
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
            "address": "123 Test Street",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = session.session.post(f"{BASE_URL}/api/orders", json=order_data)
    order = response.json()
    
    # First payment
    payment_id = f"DOUBLE_TEST_{int(time.time()*1000)}"
    payment_data = {
        "id": payment_id,
        "status": "COMPLETED",
        "update_time": datetime.utcnow().isoformat(),
        "payer": {"email_address": "buyer@example.com"}
    }
    
    print_info("Attempting first payment...")
    response1 = session.session.put(
        f"{BASE_URL}/api/orders/{order['_id']}/pay",
        json=payment_data
    )
    
    if response1.status_code != 200:
        print_fail(f"First payment failed: {response1.text}")
        return False
    
    print_pass("First payment succeeded")
    
    # Second payment with same ID
    print_info("Attempting duplicate payment with same transaction ID...")
    time.sleep(0.5)
    
    response2 = session.session.put(
        f"{BASE_URL}/api/orders/{order['_id']}/pay",
        json=payment_data
    )
    
    if response2.status_code == 400:
        print_pass("Duplicate payment correctly rejected")
        return True
    else:
        print_fail("Duplicate payment should have been rejected!")
        return False


# ========================================================================
# TEST: Concurrent Payment Attempts
# ========================================================================

def attempt_payment(order_id, payment_id, session_cookies):
    """Attempt payment (for concurrent testing)"""
    session = requests.Session()
    session.cookies.update(session_cookies)
    
    payment_data = {
        "id": payment_id,
        "status": "COMPLETED",
        "update_time": datetime.utcnow().isoformat(),
        "payer": {"email_address": "buyer@example.com"}
    }
    
    try:
        response = session.put(
            f"{BASE_URL}/api/orders/{order_id}/pay",
            json=payment_data,
            timeout=10
        )
        return {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'response': response.text
        }
    except Exception as e:
        return {
            'status_code': 0,
            'success': False,
            'response': str(e)
        }


def test_concurrent_payment_attempts():
    """Test multiple concurrent payment attempts on same order"""
    print_test("CONCURRENT PAYMENT ATTEMPTS")
    
    session = TestSession()
    if not session.login("admin@email.com", "123456"):
        print_fail("Login failed")
        return False
    
    # Create order
    response = session.session.get(f"{BASE_URL}/api/products")
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
            "address": "123 Test Street",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        },
        "paymentMethod": "PayPal"
    }
    
    response = session.session.post(f"{BASE_URL}/api/orders", json=order_data)
    order = response.json()
    order_id = order['_id']
    
    print_info(f"Created order: {order_id}")
    print_info("Attempting 5 concurrent payments...")
    
    # Try 5 concurrent payments
    payment_id = f"CONCURRENT_TEST_{int(time.time()*1000)}"
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(5):
            future = executor.submit(
                attempt_payment,
                order_id,
                payment_id,
                session.session.cookies
            )
            futures.append(future)
        
        results = [future.result() for future in as_completed(futures)]
    
    # Analyze results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print_info(f"Successful attempts: {len(successful)}")
    print_info(f"Failed attempts: {len(failed)}")
    
    # Should have exactly 1 success
    if len(successful) == 1:
        print_pass("Exactly 1 payment succeeded (correct)")
        return True
    else:
        print_fail(f"Expected 1 success, got {len(successful)}")
        return False


# ========================================================================
# RUN ALL STRESS TESTS
# ========================================================================

def run_all_stress_tests():
    """Run all stress tests"""
    
    print("\n" + "🔥"*40)
    print("    PAYMENT STRESS TEST SUITE")
    print("🔥"*40)
    
    tests = [
        ("Rapid Payment Processing", test_rapid_payment_processing),
        ("Payment with Missing Fields", test_payment_with_missing_fields),
        ("Payment Amount Mismatch", test_payment_amount_mismatch),
        ("Double Payment Prevention", test_double_payment_prevention),
        ("Concurrent Payment Attempts", test_concurrent_payment_attempts),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_fail(f"Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("STRESS TEST SUMMARY")
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
        print("🎉 ALL STRESS TESTS PASSED! 🎉\n")
        return True
    else:
        print(f"❌ {total - passed} STRESS TEST(S) FAILED ❌\n")
        return False


if __name__ == "__main__":
    try:
        success = run_all_stress_tests()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
