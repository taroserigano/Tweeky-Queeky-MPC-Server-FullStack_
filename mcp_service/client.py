"""
MCP Client Service

Connects to the local MCP server via stdio transport.
Wraps MCP tools as LangChain-compatible tools for the agent.
"""

import asyncio
import subprocess
import sys
import json
import os
from typing import Any, Dict, List, Optional, Callable
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model


# ─────────────────────────────────────────────────────────────────────────────
# MCP CLIENT SERVICE
# ─────────────────────────────────────────────────────────────────────────────

class MCPClientService:
    """
    MCP Client that connects to the MCP server and provides tool access.
    
    Usage:
        client = MCPClientService()
        await client.connect()
        result = await client.call_tool("get_product", {"product_id": "123"})
        await client.disconnect()
    """
    
    def __init__(self, server_script: str = "mcp_server/server.py"):
        self.server_script = server_script
        self._session: Optional[ClientSession] = None
        self._read = None
        self._write = None
        self._cm = None
        self._session_cm = None
        self._tools_cache: Dict[str, Any] = {}
        self._connected = False
        
    @property
    def is_connected(self) -> bool:
        return self._connected and self._session is not None
    
    async def connect(self) -> None:
        """Connect to the MCP server."""
        if self._connected:
            return
            
        # Get project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        server_path = os.path.join(project_root, self.server_script)
        
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_server.server"],
            cwd=project_root,
            env={
                **os.environ,
                "PYTHONPATH": project_root,
            }
        )
        
        # Create the stdio connection
        self._cm = stdio_client(server_params)
        self._read, self._write = await self._cm.__aenter__()
        
        # Create session
        self._session_cm = ClientSession(self._read, self._write)
        self._session = await self._session_cm.__aenter__()
        
        # Initialize
        await self._session.initialize()
        
        # Cache available tools
        await self._refresh_tools()
        
        self._connected = True
        print(f"[MCP Client] Connected to MCP server with {len(self._tools_cache)} tools")
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._connected:
            return
            
        try:
            if self._session_cm:
                await self._session_cm.__aexit__(None, None, None)
            if self._cm:
                await self._cm.__aexit__(None, None, None)
        except Exception as e:
            print(f"[MCP Client] Error during disconnect: {e}")
        finally:
            self._session = None
            self._read = None
            self._write = None
            self._cm = None
            self._session_cm = None
            self._connected = False
            print("[MCP Client] Disconnected from MCP server")
    
    async def _refresh_tools(self) -> None:
        """Refresh the tools cache from the server."""
        if not self._session:
            raise RuntimeError("Not connected to MCP server")
            
        tools_result = await self._session.list_tools()
        self._tools_cache = {
            tool.name: {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
            }
            for tool in tools_result.tools
        }
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self._tools_cache.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get info about a specific tool."""
        return self._tools_cache.get(tool_name)
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call an MCP tool by name."""
        if not self._session:
            raise RuntimeError("Not connected to MCP server")
            
        if tool_name not in self._tools_cache:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        result = await self._session.call_tool(tool_name, arguments or {})
        
        # Extract content from result
        if result.content:
            # MCP returns content as list of content items
            contents = []
            for item in result.content:
                if hasattr(item, 'text'):
                    contents.append(item.text)
                elif hasattr(item, 'data'):
                    contents.append(item.data)
            
            if len(contents) == 1:
                # Try to parse as JSON
                try:
                    return json.loads(contents[0])
                except (json.JSONDecodeError, TypeError):
                    return contents[0]
            return contents
        
        return None


# ─────────────────────────────────────────────────────────────────────────────
# LANGCHAIN TOOL WRAPPERS
# ─────────────────────────────────────────────────────────────────────────────

def create_langchain_tool_from_mcp(
    mcp_client: MCPClientService,
    tool_name: str,
    description_override: str = None,
) -> StructuredTool:
    """
    Create a LangChain StructuredTool from an MCP tool.
    
    This allows the LangGraph agent to use MCP tools seamlessly.
    """
    tool_info = mcp_client.get_tool_info(tool_name)
    if not tool_info:
        raise ValueError(f"Tool {tool_name} not found in MCP server")
    
    description = description_override or tool_info.get("description", f"MCP tool: {tool_name}")
    input_schema = tool_info.get("input_schema", {})
    
    # Build Pydantic model from JSON schema
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])
    
    # Create field definitions for Pydantic model
    field_definitions = {}
    for prop_name, prop_schema in properties.items():
        prop_type = prop_schema.get("type", "string")
        prop_desc = prop_schema.get("description", "")
        default = ... if prop_name in required else None
        
        # Map JSON schema types to Python types
        type_map = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        python_type = type_map.get(prop_type, str)
        
        if prop_name not in required:
            python_type = Optional[python_type]
        
        field_definitions[prop_name] = (python_type, Field(default=default, description=prop_desc))
    
    # Create the args schema dynamically
    if field_definitions:
        ArgsSchema = create_model(f"{tool_name}Args", **field_definitions)
    else:
        ArgsSchema = create_model(f"{tool_name}Args")
    
    # Create sync wrapper that runs async call using nest_asyncio for nested loops
    def sync_tool_func(**kwargs) -> str:
        """Synchronous wrapper for MCP tool call."""
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass  # Will try without it
            
        try:
            # Use asyncio.run with nest_asyncio to handle nested event loops
            async def _call():
                return await mcp_client.call_tool(tool_name, kwargs)
            
            # Try to get existing loop
            try:
                loop = asyncio.get_running_loop()
                # Create a new task in the existing loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(lambda: asyncio.run(_call())).result(timeout=30)
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                result = asyncio.run(_call())
            
            # Format result as string for the agent
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2, default=str)
            return str(result)
            
        except Exception as e:
            import traceback
            return f"Error calling MCP tool {tool_name}: {str(e)}\n{traceback.format_exc()}"
    
    # Create async wrapper
    async def async_tool_func(**kwargs) -> str:
        """Async wrapper for MCP tool call."""
        try:
            result = await mcp_client.call_tool(tool_name, kwargs)
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2, default=str)
            return str(result)
        except Exception as e:
            return f"Error calling MCP tool {tool_name}: {str(e)}"
    
    return StructuredTool(
        name=f"mcp_{tool_name}",
        description=description,
        func=sync_tool_func,
        coroutine=async_tool_func,
        args_schema=ArgsSchema,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CLIENT INSTANCE
# ─────────────────────────────────────────────────────────────────────────────

_mcp_client: Optional[MCPClientService] = None


async def get_mcp_client() -> MCPClientService:
    """Get the global MCP client instance, connecting if needed."""
    global _mcp_client
    
    if _mcp_client is None:
        _mcp_client = MCPClientService()
    
    if not _mcp_client.is_connected:
        await _mcp_client.connect()
    
    return _mcp_client


async def close_mcp_client() -> None:
    """Close the global MCP client."""
    global _mcp_client
    
    if _mcp_client and _mcp_client.is_connected:
        await _mcp_client.disconnect()
    
    _mcp_client = None


def get_mcp_tools_for_agent(mcp_client: MCPClientService) -> List[StructuredTool]:
    """
    Get the MCP tools that should be used by the agent.
    
    These are simple CRUD operations - complex queries use RAG instead.
    """
    # Tools we want to expose to the agent (simple CRUD only)
    mcp_tools_config = [
        {
            "name": "get_product",
            "description": "Get detailed information about a specific product by ID. Use when user asks for details about a known product."
        },
        {
            "name": "get_top_products", 
            "description": "Get the top-rated products. Use when user asks for best or highest rated products."
        },
        {
            "name": "get_product_reviews",
            "description": "Get reviews for a specific product. Use when user wants to see what others say about a product."
        },
        {
            "name": "catalog_stats",
            "description": "Get catalog statistics including total products, categories, and counts. Use for general store info."
        },
        {
            "name": "list_products",
            "description": "List products with optional filters (category, price range). Use for browsing by category or price."
        },
    ]
    
    tools = []
    for tool_config in mcp_tools_config:
        try:
            tool = create_langchain_tool_from_mcp(
                mcp_client,
                tool_config["name"],
                tool_config["description"]
            )
            tools.append(tool)
        except Exception as e:
            print(f"[MCP Client] Warning: Could not create tool {tool_config['name']}: {e}")
    
    return tools
