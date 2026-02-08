"""
Services Layer - Shared Business Logic

This module provides a clean separation between API/MCP interfaces and database operations.
All business logic lives here and is consumed by both REST endpoints and MCP tools.
"""

from services.product_service import ProductService
from services.catalog_service import CatalogService
from services.analytics_service import AnalyticsService

__all__ = [
    "ProductService",
    "CatalogService", 
    "AnalyticsService",
]
