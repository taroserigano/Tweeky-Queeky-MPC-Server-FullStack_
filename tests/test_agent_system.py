"""
Comprehensive test suite for the 3-service agent architecture
Tests MCP, RAG, and Agent Gateway end-to-end
"""
import pytest
import requests
import time
from typing import Dict, Any

# Service URLs
MCP_URL = "http://localhost:7001"
RAG_URL = "http://localhost:7002"
AGENT_URL = "http://localhost:5001"

# Timeout for all requests
TIMEOUT = 10


class TestServiceHealth:
    """Test that all services are running and healthy"""
    
    def test_mcp_server_health(self):
        """MCP Server should respond with health status"""
        response = requests.get(f"{MCP_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "mcp-tools"
        assert data["tools"] == 3
    
    def test_rag_service_health(self):
        """RAG Service should respond with health status"""
        response = requests.get(f"{RAG_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "rag"
        assert data["documents_loaded"] > 0
    
    def test_agent_gateway_health(self):
        """Agent Gateway should respond with health status"""
        response = requests.get(f"{AGENT_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "agent-gateway"


class TestMCPToolsDirect:
    """Test MCP tools directly without going through agent"""
    
    def test_search_products_no_filters(self):
        """Search products without any filters"""
        response = requests.post(
            f"{MCP_URL}/tools/searchProducts",
            json={"query": "headphones", "filters": {}},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "products" in data["data"]
        products = data["data"]["products"]
        assert len(products) > 0
        # Should find at least AirPods Pro and Sony headphones
        assert any("headphone" in p["name"].lower() or "airpods" in p["name"].lower() for p in products)
    
    def test_search_products_with_price_filter(self):
        """Search products with price filter"""
        response = requests.post(
            f"{MCP_URL}/tools/searchProducts",
            json={"query": "headphones", "filters": {"maxPrice": 300}},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        products = data["data"]["products"]
        # All returned products should be under $300
        for product in products:
            assert product["price"] <= 300
    
    def test_search_products_case_insensitive(self):
        """Search should be case insensitive"""
        response = requests.post(
            f"{MCP_URL}/tools/searchProducts",
            json={"query": "LAPTOP", "filters": {}},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["data"]["products"]) > 0
    
    def test_get_product_by_id(self):
        """Get specific product by ID"""
        response = requests.post(
            f"{MCP_URL}/tools/getProduct",
            json={"productId": "PROD-001"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        product = data["data"]["product"]
        assert product["id"] == "PROD-001"
        assert "name" in product
        assert "price" in product
    
    def test_get_product_invalid_id(self):
        """Should handle invalid product ID gracefully"""
        response = requests.post(
            f"{MCP_URL}/tools/getProduct",
            json={"productId": "INVALID-999"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        # Should either return ok=False or empty product
        assert data["ok"] is False or data["data"]["product"] is None
    
    def test_get_order_status(self):
        """Get order status by ID"""
        response = requests.post(
            f"{MCP_URL}/tools/getOrderStatus",
            json={"orderId": "ORD-1001"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        order = data["data"]["order"]
        assert order["id"] == "ORD-1001"
        assert "status" in order
        assert "items" in order


class TestRAGServiceDirect:
    """Test RAG service directly without going through agent"""
    
    def test_rag_query_return_policy(self):
        """Query about return policy should find relevant docs"""
        response = requests.post(
            f"{RAG_URL}/rag/query",
            json={"question": "return policy", "top_k": 3},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "passages" in data
        assert len(data["passages"]) > 0
        # Check that passages have required fields
        for passage in data["passages"]:
            assert "text" in passage
            assert "score" in passage
            assert passage["score"] > 0
    
    def test_rag_query_shipping(self):
        """Query about shipping should find relevant docs"""
        response = requests.post(
            f"{RAG_URL}/rag/query",
            json={"question": "shipping", "top_k": 3},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["passages"]) > 0
    
    def test_rag_query_empty(self):
        """Empty query should handle gracefully"""
        response = requests.post(
            f"{RAG_URL}/rag/query",
            json={"question": "", "top_k": 3},
            timeout=TIMEOUT
        )
        assert response.status_code == 200


class TestAgentRouting:
    """Test that agent correctly routes queries to MCP or RAG"""
    
    def test_product_search_routes_to_mcp(self):
        """Product search should route to MCP"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "Show me headphones"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "used" in data
        # Should use MCP tools
        assert "mcpTools" in data["used"]
        assert "searchProducts" in data["used"]["mcpTools"]
    
    def test_product_search_with_price_routes_to_mcp(self):
        """Product search with price should route to MCP with filter"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "Show me headphones under $300"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "mcpTools" in data["used"]
        assert "searchProducts" in data["used"]["mcpTools"]
        # Should mention products in reply
        assert len(data["reply"]) > 0
    
    def test_order_tracking_routes_to_mcp(self):
        """Order tracking should route to MCP"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "Track order ORD-1001"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "mcpTools" in data["used"]
        assert "getOrderStatus" in data["used"]["mcpTools"]
        # Should mention order status
        assert "ORD-1001" in data["reply"]
    
    def test_general_question_routes_to_rag(self):
        """General questions should route to RAG"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "What is your return policy?"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "used" in data
        # Should use RAG, not MCP
        assert data["used"].get("rag") is True or "rag" in str(data["used"]).lower()
    
    def test_support_question_routes_to_rag(self):
        """Support questions should route to RAG"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "How do I contact customer support?"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        # Should use RAG
        assert data["used"].get("rag") is True or "rag" in str(data["used"]).lower()


class TestAgentQueryParsing:
    """Test that agent correctly parses different query formats"""
    
    def test_single_word_product(self):
        """Single word product query"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "headphones"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "mcpTools" in data["used"]
    
    def test_price_without_dollar_sign(self):
        """Price without $ sign should still work"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "laptop under 1000"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "mcpTools" in data["used"]
    
    def test_multi_word_product(self):
        """Multi-word product name"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "wireless mouse"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "mcpTools" in data["used"]
    
    def test_natural_language_request(self):
        """Natural language product request"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "Find me a chair"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "mcpTools" in data["used"]
    
    def test_price_variations(self):
        """Different ways to express price limits"""
        test_cases = [
            "headphones under $300",
            "headphones less than $300",
            "headphones below $300",
            "headphones under 300",
        ]
        for query in test_cases:
            response = requests.post(
                f"{AGENT_URL}/chat",
                json={"message": query},
                timeout=TIMEOUT
            )
            assert response.status_code == 200
            data = response.json()
            assert "mcpTools" in data["used"], f"Failed for query: {query}"


class TestAgentEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_message(self):
        """Empty message should handle gracefully"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": ""},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
    
    def test_very_long_message(self):
        """Very long message should handle gracefully"""
        long_message = "headphones " * 100
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": long_message},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
    
    def test_special_characters_in_query(self):
        """Special characters should be handled"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": '• "Show me headphones under $300"'},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        # Should still route to MCP and work
        assert "mcpTools" in data["used"]
    
    def test_invalid_order_id(self):
        """Invalid order ID should handle gracefully"""
        response = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "Track order INVALID-999"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        # Should attempt MCP call
        assert "mcpTools" in data["used"]


class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_complete_shopping_flow(self):
        """Simulate a complete shopping conversation"""
        # 1. Search for products
        response1 = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "Show me laptops under $1500"},
            timeout=TIMEOUT
        )
        assert response1.status_code == 200
        
        # 2. Ask about shipping
        response2 = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "What are the shipping options?"},
            timeout=TIMEOUT
        )
        assert response2.status_code == 200
        
        # 3. Track an order
        response3 = requests.post(
            f"{AGENT_URL}/chat",
            json={"message": "Track order ORD-1001"},
            timeout=TIMEOUT
        )
        assert response3.status_code == 200
    
    def test_mixed_queries_in_sequence(self):
        """Test different query types in sequence"""
        queries = [
            ("headphones", "mcpTools"),
            ("What's the return policy?", "rag"),
            ("Track order ORD-1002", "mcpTools"),
            ("wireless keyboard", "mcpTools"),
        ]
        
        for query, expected_service in queries:
            response = requests.post(
                f"{AGENT_URL}/chat",
                json={"message": query},
                timeout=TIMEOUT
            )
            assert response.status_code == 200
            data = response.json()
            if expected_service == "rag":
                assert data["used"].get("rag") is True or "rag" in str(data["used"]).lower()
            else:
                assert "mcpTools" in data["used"]


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
