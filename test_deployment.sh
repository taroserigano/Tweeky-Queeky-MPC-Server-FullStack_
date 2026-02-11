#!/bin/bash

# Comprehensive API Testing Script for TweekySqueeky E-commerce App
# Tests all major features and reports status

BACKEND_URL="http://52.14.207.180:5000"
FRONTEND_URL="http://3.23.130.136"

echo "==================================="
echo "TweekySqueeky API Test Suite"
echo "==================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
   local expected_code="$3"
    
    echo -n "Testing $name... "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$HTTP_CODE" == "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $HTTP_CODE)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_code, got $HTTP_CODE)"
        ((FAILED++))
    fi
}

# Helper function to test POST endpoint
test_post_endpoint() {
    local name="$1"
    local url="$2"
    local data="$3"
    local expected_code="$4"
    
    echo -n "Testing $name... "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$url")
    
    if [ "$HTTP_CODE" == "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $HTTP_CODE)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_code, got $HTTP_CODE)"
        ((FAILED++))
    fi
}

echo "==================================="
echo "1. CORE API ENDPOINTS"
echo "==================================="
test_endpoint "Root API" "$BACKEND_URL/" "200"
test_endpoint "Health Check" "$BACKEND_URL/api/health" "200"
echo ""

echo "==================================="
echo "2. PRODUCT ENDPOINTS"
echo "==================================="
test_endpoint "List Products" "$BACKEND_URL/api/products" "200"
test_endpoint "Search Products" "$BACKEND_URL/api/products?keyword=apple" "200"
test_endpoint "Get Single Product" "$BACKEND_URL/api/products/69274df94bad953f769f2068" "200"
test_endpoint "Get Top Products" "$BACKEND_URL/api/products/top" "200"
echo ""

echo "==================================="
echo "3. PAYMENT CONFIG ENDPOINTS"
echo "==================================="
echo -n "Testing PayPal Config... "
PAYPAL_RESPONSE=$(curl -s "$BACKEND_URL/api/config/paypal")
if echo "$PAYPAL_RESPONSE" | grep -q "clientId"; then
    CLIENT_ID=$(echo "$PAYPAL_RESPONSE" | grep -o '"clientId":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$CLIENT_ID" ] && [ "$CLIENT_ID" != "null" ]; then
        echo -e "${GREEN}✓ PASS${NC} (ClientID present)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (ClientID empty)"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗ FAIL${NC} (Invalid response)"
    ((FAILED++))
fi

echo -n "Testing Stripe Config... "
STRIPE_RESPONSE=$(curl -s "$BACKEND_URL/api/config/stripe")
if echo "$STRIPE_RESPONSE" | grep -q "publishableKey"; then
    PUB_KEY=$(echo "$STRIPE_RESPONSE" | grep -o '"publishableKey":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$PUB_KEY" ] && [ "$PUB_KEY" != "" ]; then
        echo -e "${GREEN}✓ PASS${NC} (PublishableKey present: ${PUB_KEY:0:20}...)"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠ WARN${NC} (PublishableKey empty - Stripe payment won't work)"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗ FAIL${NC} (Invalid response)"
    ((FAILED++))
fi
echo ""

echo "==================================="
echo "4. AI AGENT ENDPOINTS"
echo "==================================="
test_post_endpoint "Agent Chat v2" "$BACKEND_URL/api/agent/v2/chat" '{"query":"test"}' "200"
test_post_endpoint "Agent Search Products" "$BACKEND_URL/api/agent/v2/chat" '{"query":"show me headphones"}' "200"
test_post_endpoint "Multi-Agent System" "$BACKEND_URL/api/multi-agent/chat" '{"query":"recommend products"}' "200"
echo ""

echo "==================================="
echo "5. FRONTEND ACCESSIBILITY"
echo "==================================="
test_endpoint "Frontend Homepage" "$FRONTEND_URL" "200"
echo ""

echo "==================================="
echo "6. ADVANCED FEATURES"
echo "==================================="
echo -n "Testing Product Search with Filters... "
SEARCH_RESPONSE=$(curl -s "$BACKEND_URL/api/products?keyword=apple&minPrice=50&maxPrice=200")
if echo "$SEARCH_RESPONSE" | grep -q "products"; then
    PRODUCT_COUNT=$(echo "$SEARCH_RESPONSE" | grep -o '"_id"' | wc -l)
    echo -e "${GREEN}✓ PASS${NC} (Found $PRODUCT_COUNT products)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

echo -n "Testing Agent Product Recommendations... "
AGENT_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d '{"query":"I need good quality headphones under $300"}' "$BACKEND_URL/api/agent/v2/chat")
if echo "$AGENT_RESPONSE" | grep -q "response"; then
    echo -e "${GREEN}✓ PASS${NC} (Agent responded)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi
echo ""

echo "==================================="
echo "TEST SUMMARY"
echo "==================================="
TOTAL=$((PASSED + FAILED))
PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED/$TOTAL)*100}")

echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total: $TOTAL"
echo "Pass Rate: $PASS_RATE%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Please review.${NC}"
    exit 1
fi
