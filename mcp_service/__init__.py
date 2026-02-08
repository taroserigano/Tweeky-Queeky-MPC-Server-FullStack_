"""
MCP Client Service

Provides a client to connect to the MCP server and call tools.
Used by the LangGraph agent for simple CRUD operations.
"""

from mcp_service.client import MCPClientService, get_mcp_client

__all__ = ["MCPClientService", "get_mcp_client"]
