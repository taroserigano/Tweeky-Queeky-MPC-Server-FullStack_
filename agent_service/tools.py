"""
Tool Registry - Available tools for the agent

Defines all tools the agent can use, with:
- Clear descriptions for the LLM
- Input/output schemas
- Execution handlers
"""

from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class ToolCategory(str, Enum):
    """Categories of tools"""
    SEARCH = "search"
    PRODUCT = "product"
    CART = "cart"
    ORDER = "order"
    ANALYTICS = "analytics"
    UTILITY = "utility"


@dataclass
class ToolParameter:
    """Definition of a tool parameter"""
    name: str
    type: str  # 'string', 'number', 'boolean', 'array', 'object'
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


@dataclass 
class Tool:
    """Definition of an agent tool"""
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter] = field(default_factory=list)
    handler: Optional[Callable] = None
    requires_confirmation: bool = False  # For destructive actions
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop: Dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            
            # Handle array types - OpenAI requires 'items' for arrays
            if param.type == "array":
                prop["items"] = {"type": "string"}
            
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
    
    def to_prompt_description(self) -> str:
        """Get description for including in prompts"""
        params_str = ", ".join(
            f"{p.name}: {p.type}" + ("?" if not p.required else "")
            for p in self.parameters
        )
        return f"- {self.name}({params_str}): {self.description}"


class ToolRegistry:
    """
    Registry of all available tools for the agent.
    
    Tools are organized by category and can be:
    - Listed for LLM prompts
    - Converted to OpenAI function format
    - Executed with validation
    """
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def register(self, tool: Tool) -> None:
        """Register a tool"""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[Tool]:
        """List all tools, optionally filtered by category"""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    def get_openai_tools(self, categories: Optional[List[ToolCategory]] = None) -> List[Dict]:
        """Get tools in OpenAI function calling format"""
        tools = self.list_tools()
        if categories:
            tools = [t for t in tools if t.category in categories]
        return [t.to_openai_function() for t in tools]
    
    def get_tools_prompt(self, categories: Optional[List[ToolCategory]] = None) -> str:
        """Get tools description for prompts"""
        tools = self.list_tools()
        if categories:
            tools = [t for t in tools if t.category in categories]
        
        lines = ["Available tools:"]
        for tool in tools:
            lines.append(tool.to_prompt_description())
        return "\n".join(lines)
    
    async def execute(self, name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool by name"""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        
        if not tool.handler:
            raise ValueError(f"Tool {name} has no handler")
        
        # Validate required parameters
        for param in tool.parameters:
            if param.required and param.name not in params:
                raise ValueError(f"Missing required parameter: {param.name}")
        
        # Execute handler
        result = await tool.handler(**params)
        return result
    
    def _register_default_tools(self) -> None:
        """Register all default shopping assistant tools"""
        
        # ─────────────────────────────────────────────────────────────
        # SEARCH TOOLS
        # ─────────────────────────────────────────────────────────────
        
        self.register(Tool(
            name="semantic_search",
            description="Search for products using natural language. Understands intent, not just keywords. Use for queries like 'comfortable chair for long work sessions' or 'gift for music lover'.",
            category=ToolCategory.SEARCH,
            parameters=[
                ToolParameter("query", "string", "Natural language search query"),
                ToolParameter("top_k", "number", "Number of results (1-20)", required=False, default=5),
                ToolParameter("category", "string", "Filter by category", required=False),
                ToolParameter("max_price", "number", "Maximum price filter", required=False),
                ToolParameter("min_rating", "number", "Minimum rating (0-5)", required=False),
            ],
        ))
        
        self.register(Tool(
            name="keyword_search",
            description="Search products by exact keyword matching in name, brand, or category. Use when user mentions specific product names or brands.",
            category=ToolCategory.SEARCH,
            parameters=[
                ToolParameter("query", "string", "Search keywords"),
                ToolParameter("limit", "number", "Number of results", required=False, default=10),
            ],
        ))
        
        self.register(Tool(
            name="find_similar",
            description="Find products similar to a given product. Great for 'show me more like this' requests.",
            category=ToolCategory.SEARCH,
            parameters=[
                ToolParameter("product_id", "string", "ID of the source product"),
                ToolParameter("limit", "number", "Number of similar products", required=False, default=5),
            ],
        ))
        
        # ─────────────────────────────────────────────────────────────
        # PRODUCT TOOLS
        # ─────────────────────────────────────────────────────────────
        
        self.register(Tool(
            name="get_product_details",
            description="Get detailed information about a specific product including description, specs, and reviews.",
            category=ToolCategory.PRODUCT,
            parameters=[
                ToolParameter("product_id", "string", "The product ID"),
                ToolParameter("include_reviews", "boolean", "Include customer reviews", required=False, default=True),
            ],
        ))
        
        self.register(Tool(
            name="compare_products",
            description="Compare 2-5 products side by side. Shows price, rating, features comparison.",
            category=ToolCategory.PRODUCT,
            parameters=[
                ToolParameter("product_ids", "array", "List of product IDs to compare (2-5)"),
            ],
        ))
        
        self.register(Tool(
            name="get_product_reviews",
            description="Get customer reviews for a product with sentiment analysis.",
            category=ToolCategory.PRODUCT,
            parameters=[
                ToolParameter("product_id", "string", "The product ID"),
            ],
        ))
        
        self.register(Tool(
            name="ask_about_product",
            description="Answer a specific question about a product using its details and reviews.",
            category=ToolCategory.PRODUCT,
            parameters=[
                ToolParameter("product_id", "string", "The product ID"),
                ToolParameter("question", "string", "Question about the product"),
            ],
        ))
        
        # ─────────────────────────────────────────────────────────────
        # CATALOG TOOLS
        # ─────────────────────────────────────────────────────────────
        
        self.register(Tool(
            name="get_categories",
            description="Get list of all product categories available in the store.",
            category=ToolCategory.UTILITY,
            parameters=[],
        ))
        
        self.register(Tool(
            name="get_top_products",
            description="Get top-rated or most popular products, optionally in a category.",
            category=ToolCategory.PRODUCT,
            parameters=[
                ToolParameter("limit", "number", "Number of products", required=False, default=5),
                ToolParameter("category", "string", "Filter by category", required=False),
                ToolParameter("sort_by", "string", "Sort by 'rating' or 'reviews'", required=False, default="rating"),
            ],
        ))
        
        self.register(Tool(
            name="get_deals",
            description="Find products with good value (high rating, reasonable price).",
            category=ToolCategory.PRODUCT,
            parameters=[
                ToolParameter("max_price", "number", "Maximum price", required=False),
                ToolParameter("category", "string", "Filter by category", required=False),
                ToolParameter("limit", "number", "Number of deals", required=False, default=5),
            ],
        ))
        
        # ─────────────────────────────────────────────────────────────
        # CART/RECOMMENDATION TOOLS  
        # ─────────────────────────────────────────────────────────────
        
        self.register(Tool(
            name="build_cart",
            description="AI builds a suggested cart/bundle for a goal within a budget. E.g., 'home office setup for $500'.",
            category=ToolCategory.CART,
            parameters=[
                ToolParameter("goal", "string", "What the user wants to achieve"),
                ToolParameter("budget", "number", "Maximum total budget"),
            ],
        ))
        
        self.register(Tool(
            name="recommend_products",
            description="Get personalized product recommendations based on preferences.",
            category=ToolCategory.CART,
            parameters=[
                ToolParameter("preferences", "string", "User preferences in natural language"),
                ToolParameter("budget", "number", "Budget limit", required=False),
                ToolParameter("limit", "number", "Number of recommendations", required=False, default=5),
            ],
        ))
        
        # ─────────────────────────────────────────────────────────────
        # ORDER TOOLS
        # ─────────────────────────────────────────────────────────────
        
        self.register(Tool(
            name="check_stock",
            description="Check if a product is in stock and how many are available.",
            category=ToolCategory.ORDER,
            parameters=[
                ToolParameter("product_id", "string", "The product ID"),
            ],
        ))
        
        # ─────────────────────────────────────────────────────────────
        # UTILITY TOOLS
        # ─────────────────────────────────────────────────────────────
        
        self.register(Tool(
            name="calculate_total",
            description="Calculate total price for a list of products with quantities.",
            category=ToolCategory.UTILITY,
            parameters=[
                ToolParameter("items", "array", "List of {product_id, quantity} objects"),
            ],
        ))


# Singleton instance
tool_registry = ToolRegistry()
