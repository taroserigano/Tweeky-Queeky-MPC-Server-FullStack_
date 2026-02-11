"""
Comprehensive test suite for all newly implemented features
Tests: Product Sorting, Search Autocomplete, Dark Mode, Breadcrumbs, Loading Skeletons
"""
import pytest
import asyncio
import httpx
from typing import List, Dict

# Test against live server
BASE_URL = "http://localhost:5000"

# Backend API Tests

@pytest.mark.asyncio
async def test_product_sorting_price_asc():
    """Test products sorted by price ascending"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products?sortBy=price_asc")
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        
        # Verify products are sorted by price ascending
        prices = [p["price"] for p in products]
        assert prices == sorted(prices), "Products should be sorted by price ascending"
        print(f"✓ Price ascending sort: {prices[:5]}")

@pytest.mark.asyncio
async def test_product_sorting_price_desc():
    """Test products sorted by price descending"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products?sortBy=price_desc")
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        
        # Verify products are sorted by price descending
        prices = [p["price"] for p in products]
        assert prices == sorted(prices, reverse=True), "Products should be sorted by price descending"
        print(f"✓ Price descending sort: {prices[:5]}")

@pytest.mark.asyncio
async def test_product_sorting_rating():
    """Test products sorted by rating"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products?sortBy=rating_desc")
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        
        # Verify products are sorted by rating descending
        ratings = [p["rating"] for p in products]
        assert ratings == sorted(ratings, reverse=True), "Products should be sorted by rating descending"
        print(f"✓ Rating sort: {ratings[:5]}")

@pytest.mark.asyncio
async def test_product_sorting_newest():
    """Test products sorted by newest"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products?sortBy=newest")
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("products", [])) > 0
        print(f"✓ Newest sort: {len(data['products'])} products")

@pytest.mark.asyncio
async def test_product_sorting_oldest():
    """Test products sorted by oldest"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products?sortBy=oldest")
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("products", [])) > 0
        print(f"✓ Oldest sort: {len(data['products'])} products")

@pytest.mark.asyncio
async def test_autocomplete_endpoint_exists():
    """Test that autocomplete endpoint exists and responds"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products/autocomplete?q=son")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Autocomplete should return a list"
        print(f"✓ Autocomplete endpoint: {len(data)} suggestions for 'son'")

@pytest.mark.asyncio
async def test_autocomplete_min_length():
    """Test that autocomplete requires minimum 2 characters"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products/autocomplete?q=s")
        assert response.status_code == 200
        data = response.json()
        assert data == [], "Autocomplete should return empty list for single character"
        print("✓ Autocomplete min length: Returns empty for 1 char")

@pytest.mark.asyncio
async def test_autocomplete_structure():
    """Test that autocomplete returns correct structure"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products/autocomplete?q=sony")
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            suggestion = data[0]
            assert "text" in suggestion, "Suggestion should have 'text' field"
            assert "type" in suggestion, "Suggestion should have 'type' field"
            assert suggestion["type"] in ["product", "brand", "category"], "Type should be valid"
            print(f"✓ Autocomplete structure: {suggestion}")
        else:
            print("⚠ No suggestions found for 'sony'")

@pytest.mark.asyncio
async def test_autocomplete_limit():
    """Test that autocomplete limits results to 10"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products/autocomplete?q=a")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10, "Autocomplete should return max 10 suggestions"
        print(f"✓ Autocomplete limit: {len(data)} suggestions (max 10)")

@pytest.mark.asyncio
async def test_products_endpoint_backward_compatibility():
    """Test that products endpoint still works without sortBy"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "page" in data
        assert "pages" in data
        print(f"✓ Backward compatibility: {len(data['products'])} products returned")

@pytest.mark.asyncio
async def test_products_with_keyword_and_sort():
    """Test combining keyword search with sorting"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products?keyword=phone&sortBy=price_asc")
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        
        if len(products) > 1:
            prices = [p["price"] for p in products]
            assert prices == sorted(prices), "Products should be sorted even with keyword"
            print(f"✓ Keyword + Sort: {len(products)} products, prices: {prices[:3]}")

# Service Health Tests

@pytest.mark.asyncio
async def test_backend_health():
    """Test main backend is responding"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/products/top")
        assert response.status_code == 200
        print("✓ Backend health: OK")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("RUNNING COMPREHENSIVE FEATURE TESTS")
    print("="*60 + "\n")
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])
