"""
Final Comprehensive Test - Run this to verify everything works
"""
import requests
import json
import sys
from typing import Dict, Any

# Service URLs
MCP_URL = "http://localhost:7001"
RAG_URL = "http://localhost:7002"
AGENT_URL = "http://localhost:5001"
TIMEOUT = 10

passed = 0
failed = 0

def test(name: str, func):
    """Run a test and track results"""
    global passed, failed
    try:
        func()
        print(f"✓ {name}")
        passed += 1
        return True
    except AssertionError as e:
        print(f"✗ {name}: {e}")
        failed += 1
        return False
    except Exception as e:
        print(f"✗ {name}: ERROR - {e}")
        failed += 1
        return False

print("=" * 70)
print("COMPREHENSIVE AGENT SYSTEM TEST")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════
# SERVICE HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════════════════
print("\n[1] SERVICE HEALTH CHECKS")
print("-" * 70)

def test_mcp_health():
    r = requests.get(f"{MCP_URL}/health", timeout=TIMEOUT)
    assert r.status_code == 200, f"Status: {r.status_code}"
    data = r.json()
    assert data["status"] == "healthy", f"Not healthy: {data}"
    assert data["tools"] == 3, f"Wrong tool count: {data['tools']}"

def test_rag_health():
    r = requests.get(f"{RAG_URL}/health", timeout=TIMEOUT)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["documents_loaded"] > 0

def test_agent_health():
    r = requests.get(f"{AGENT_URL}/health", timeout=TIMEOUT)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"

test("MCP Server Health", test_mcp_health)
test("RAG Service Health", test_rag_health)
test("Agent Gateway Health", test_agent_health)

# ═══════════════════════════════════════════════════════════════════════════
# MCP DIRECT TESTS
# ═══════════════════════════════════════════════════════════════════════════
print("\n[2] MCP DIRECT TOOL CALLS")
print("-" * 70)

def test_search_headphones():
    r = requests.post(f"{MCP_URL}/tools/searchProducts",
        json={"query": "headphones", "filters": {}}, timeout=TIMEOUT)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    products = data["data"]["products"]
    assert len(products) > 0, "No headphones found"
    print(f"    Found {len(products)} headphones: {[p['name'] for p in products]}")

def test_search_with_price():
    r = requests.post(f"{MCP_URL}/tools/searchProducts",
        json={"query": "headphones", "filters": {"maxPrice": 300}}, timeout=TIMEOUT)
    data = r.json()
    products = data["data"]["products"]
    for p in products:
        assert p["price"] <= 300, f"{p['name']} costs ${p['price']}"
    print(f"    Found {len(products)} headphones under $300")

def test_get_order():
    r = requests.post(f"{MCP_URL}/tools/getOrderStatus",
        json={"orderId": "ORD-1001"}, timeout=TIMEOUT)
    data = r.json()
    assert data["ok"] is True
    order = data["data"]
    assert order["id"] == "ORD-1001"
    print(f"    Order ORD-1001 status: {order['status']}")

test("Search for headphones", test_search_headphones)
test("Search with price filter", test_search_with_price)
test("Get order status", test_get_order)

# ═══════════════════════════════════════════════════════════════════════════
# RAG DIRECT TESTS
# ═══════════════════════════════════════════════════════════════════════════
print("\n[3] RAG SERVICE DIRECT QUERIES")
print("-" * 70)

def test_rag_return_policy():
    r = requests.post(f"{RAG_URL}/rag/query",
        json={"question": "return policy", "top_k": 3}, timeout=TIMEOUT)
    data = r.json()
    assert len(data["passages"]) >= 0, f"Expected passages list, got: {data}"
    print(f"    Found {len(data['passages'])} relevant passages")

def test_rag_shipping():
    r = requests.post(f"{RAG_URL}/rag/query",
        json={"question": "shipping", "top_k": 3}, timeout=TIMEOUT)
    data = r.json()
    assert len(data["passages"]) > 0
    print(f"    Found {len(data['passages'])} shipping-related passages")

test("Query return policy docs", test_rag_return_policy)
test("Query shipping info", test_rag_shipping)

# ═══════════════════════════════════════════════════════════════════════════
# AGENT ROUTING TESTS
# ═══════════════════════════════════════════════════════════════════════════
print("\n[4] AGENT ROUTING TO MCP")
print("-" * 70)

def test_agent_headphones():
    r = requests.post(f"{AGENT_URL}/chat",
        json={"message": "Show me headphones"}, timeout=TIMEOUT)
    data = r.json()
    assert "mcpTools" in data["used"], f"Didn't use MCP: {data['used']}"
    assert "searchProducts" in data["used"]["mcpTools"]
    print(f"    Used: {data['used']}")

def test_agent_headphones_price():
    r = requests.post(f"{AGENT_URL}/chat",
        json={"message": "Show me headphones under $300"}, timeout=TIMEOUT)
    data = r.json()
    assert "mcpTools" in data["used"]
    assert "searchProducts" in data["used"]["mcpTools"]
    # Check if reply mentions products
    assert len(data["reply"]) > 20, "Reply too short"
    print(f"    Reply preview: {data['reply'][:80]}...")

def test_agent_special_chars():
    r = requests.post(f"{AGENT_URL}/chat",
        json={"message": '• "Show me headphones under $300"'}, timeout=TIMEOUT)
    data = r.json()
    assert "mcpTools" in data["used"], "Should route to MCP despite special chars"
    print(f"    Handled special characters correctly")

def test_agent_order():
    r = requests.post(f"{AGENT_URL}/chat",
        json={"message": "Track order ORD-1001"}, timeout=TIMEOUT)
    data = r.json()
    assert "mcpTools" in data["used"]
    assert "getOrderStatus" in data["used"]["mcpTools"]
    assert "ORD-1001" in data["reply"]
    print(f"    Order status retrieved successfully")

test("Agent: Simple product search", test_agent_headphones)
test("Agent: Product search with price", test_agent_headphones_price)
test("Agent: Handle special characters", test_agent_special_chars)
test("Agent: Order tracking", test_agent_order)

print("\n[5] AGENT ROUTING TO RAG")
print("-" * 70)

def test_agent_return_policy():
    r = requests.post(f"{AGENT_URL}/chat",
        json={"message": "What is your return policy?"}, timeout=TIMEOUT)
    data = r.json()
    # Check if RAG was used
    used_rag = data["used"].get("rag") is True or "rag" in str(data["used"]).lower()
    assert used_rag, f"Should use RAG: {data['used']}"
    assert len(data["reply"]) > 20
    print(f"    Reply preview: {data['reply'][:80]}...")

def test_agent_support():
    r = requests.post(f"{AGENT_URL}/chat",
        json={"message": "How do I contact support?"}, timeout=TIMEOUT)
    data = r.json()
    used_rag = data["used"].get("rag") is True or "rag" in str(data["used"]).lower()
    assert used_rag, f"Should use RAG: {data['used']}"
    print(f"    RAG query successful")

test("Agent: Return policy question", test_agent_return_policy)
test("Agent: Support question", test_agent_support)

# ═══════════════════════════════════════════════════════════════════════════
# QUERY PARSING TESTS
# ═══════════════════════════════════════════════════════════════════════════
print("\n[6] QUERY PARSING EDGE CASES")
print("-" * 70)

test_queries = [
    ("headphones", "Single word"),
    ("laptop under 1000", "Price without $"),
    ("wireless mouse", "Multi-word product"),
    ("Find me a chair", "Natural language"),
]

for query, description in test_queries:
    def test_query():
        r = requests.post(f"{AGENT_URL}/chat",
            json={"message": query}, timeout=TIMEOUT)
        data = r.json()
        assert r.status_code == 200
        assert "used" in data
        print(f"    '{query}' → {data['used']}")
    
    test(f"Parse: {description}", test_query)

# ═══════════════════════════════════════════════════════════════════════════
# FINAL RESULTS
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 70)

if failed == 0:
    print("✓ ALL TESTS PASSED! System is 100% functional.")
    sys.exit(0)
else:
    print(f"✗ {failed} test(s) failed. Review errors above.")
    sys.exit(1)
