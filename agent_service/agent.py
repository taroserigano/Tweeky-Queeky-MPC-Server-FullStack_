"""
Shopping Agent - ReAct-based autonomous agent

Implements the ReAct (Reasoning + Acting) pattern:
1. Observe: Receive user input and context
2. Think: Reason about what to do
3. Act: Execute tools
4. Observe: See tool results
5. Repeat until task complete

Features:
- Multi-step reasoning
- Tool selection and execution
- Error recovery
- Conversation context awareness
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from openai import AsyncOpenAI

from config.settings import settings
from agent_service.memory import ConversationMemory, SessionMemory
from agent_service.tools import ToolRegistry, tool_registry as default_tool_registry, ToolCategory


class AgentState(str, Enum):
    """Agent execution states"""
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    RESPONDING = "responding"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class AgentStep:
    """A single step in agent execution"""
    state: AgentState
    thought: Optional[str] = None
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AgentResponse:
    """Final response from agent"""
    message: str
    steps: List[AgentStep]
    products_mentioned: List[str]  # Product IDs
    session_id: str
    success: bool


class ShoppingAgent:
    """
    ReAct Shopping Assistant Agent.
    
    Handles complex shopping queries through multi-step reasoning:
    - "Find me a comfortable office chair under $300 with good reviews"
    - "Compare the top 3 wireless headphones"
    - "Build a home office setup for $1000"
    
    Usage:
        agent = ShoppingAgent()
        response = await agent.run("Find me a gift for a tech lover under $100")
    """
    
    SYSTEM_PROMPT = """You are a helpful shopping assistant for TweekyQueeky Shop, an e-commerce store.

Your job is to help customers find products, compare options, and make informed purchasing decisions.

You have access to tools that let you:
- Search for products semantically (understanding intent, not just keywords)
- Get product details and reviews
- Compare products side by side
- Find similar products
- Build suggested carts within a budget
- Answer questions about specific products

IMPORTANT GUIDELINES:
1. ALWAYS use tools to get real product data - NEVER make up products, prices, or give generic recommendations
2. When users ask vague questions, use semantic_search to find relevant products
3. For comparisons, always fetch actual product data first
4. Be concise but helpful - provide key info (price, rating, stock)
5. If a product is out of stock, mention it and suggest alternatives
6. When recommending, explain WHY a product fits the user's needs
7. If no products are found, simply state that and ask if they'd like to search for something else
8. Keep responses focused on actual products from the database - no generic lists or advice
9. Do NOT mention sales, deals, promotions, or trending items UNLESS the user specifically asks for them

RESPONSE FORMAT:
- Start with a direct answer to the user's question
- Include specific product recommendations with prices
- Mention ratings and reviews when relevant
- Offer to help with follow-up questions

You think step by step before acting. For each step:
1. THINK about what information you need
2. ACT by calling a tool
3. OBSERVE the results
4. Either continue with more actions or provide final response
"""

    def __init__(
        self,
        tools: Optional[ToolRegistry] = None,
        max_steps: int = 10,
        model: str = None,
    ):
        self._tools = tools or default_tool_registry
        self._max_steps = max_steps
        self._model = model or settings.OPENAI_MODEL
        self._client: Optional[AsyncOpenAI] = None
    
    def _get_client(self) -> AsyncOpenAI:
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            api_key = settings.openai_key
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            self._client = AsyncOpenAI(api_key=api_key)
        return self._client
    
    async def run(
        self,
        user_message: str,
        conversation: Optional[ConversationMemory] = None,
        session: Optional[SessionMemory] = None,
    ) -> AgentResponse:
        """
        Run the agent on a user message.
        
        Args:
            user_message: The user's request
            conversation: Optional conversation history
            session: Optional session context
            
        Returns:
            AgentResponse with message, steps, and metadata
        """
        # Initialize memory if not provided
        conversation = conversation or ConversationMemory(system_prompt=self.SYSTEM_PROMPT)
        session = session or SessionMemory()
        
        # Add user message to conversation
        conversation.add_user_message(user_message)
        
        steps: List[AgentStep] = []
        products_mentioned: List[str] = []
        
        try:
            # Run ReAct loop
            final_response = await self._react_loop(
                user_message=user_message,
                conversation=conversation,
                session=session,
                steps=steps,
                products_mentioned=products_mentioned,
            )
            
            # Add assistant response to conversation
            conversation.add_assistant_message(final_response)
            
            return AgentResponse(
                message=final_response,
                steps=steps,
                products_mentioned=products_mentioned,
                session_id=session.session_id,
                success=True,
            )
            
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try again."
            steps.append(AgentStep(state=AgentState.ERROR, error=str(e)))
            
            return AgentResponse(
                message=error_msg,
                steps=steps,
                products_mentioned=products_mentioned,
                session_id=session.session_id,
                success=False,
            )
    
    async def _react_loop(
        self,
        user_message: str,
        conversation: ConversationMemory,
        session: SessionMemory,
        steps: List[AgentStep],
        products_mentioned: List[str],
    ) -> str:
        """
        Execute the ReAct loop.
        
        Returns:
            Final response message
        """
        client = self._get_client()
        
        # Build initial prompt with context
        context_summary = session.get_context_summary()
        
        messages = conversation.get_messages_for_llm()
        
        # Add context if available
        if context_summary and context_summary != "New session":
            messages.insert(1, {
                "role": "system",
                "content": f"Session context: {context_summary}"
            })
        
        # Get available tools
        tools = self._tools.get_openai_tools()
        
        for step_num in range(self._max_steps):
            # Call LLM with tools
            response = await client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000,
            )
            
            assistant_message = response.choices[0].message
            
            # Check if we have tool calls
            if assistant_message.tool_calls:
                # Process each tool call
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    # Record the action step
                    step = AgentStep(
                        state=AgentState.ACTING,
                        action=tool_name,
                        action_input=tool_args,
                    )
                    
                    # Execute the tool
                    try:
                        result = await self._execute_tool(tool_name, tool_args)
                        step.observation = json.dumps(result, default=str)[:2000]
                        step.state = AgentState.OBSERVING
                        
                        # Track mentioned products
                        self._extract_product_ids(result, products_mentioned)
                        
                    except Exception as e:
                        step.observation = f"Error: {str(e)}"
                        step.error = str(e)
                    
                    steps.append(step)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call],
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": step.observation,
                    })
            
            else:
                # No tool calls - this is the final response
                final_response = assistant_message.content or "I'm not sure how to help with that."
                
                steps.append(AgentStep(
                    state=AgentState.RESPONDING,
                    thought=final_response[:200],
                ))
                
                return final_response
        
        # Max steps reached
        return "I've done extensive research but need more specific information to help you better. Could you clarify what you're looking for?"
    
    async def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool and return results"""
        
        # Import services here to avoid circular imports
        from services.product_service import product_service
        from services.catalog_service import catalog_service
        from services.analytics_service import analytics_service
        from rag_service.retriever import RAGRetriever
        
        retriever = RAGRetriever()
        
        # Route to appropriate handler
        if tool_name == "semantic_search":
            results = await retriever.search_with_filters(
                query=params.get("query", ""),
                category=params.get("category"),
                max_price=params.get("max_price"),
                min_rating=params.get("min_rating"),
                top_k=params.get("top_k", 5),
            )
            return [{"id": r.product_id, "score": r.score, **r.product} for r in results]
        
        elif tool_name == "keyword_search":
            return await product_service.search_products(
                query=params.get("query", ""),
                limit=params.get("limit", 10),
            )
        
        elif tool_name == "find_similar":
            results = await retriever.find_similar_products(
                product_id=params.get("product_id"),
                top_k=params.get("limit", 5),
            )
            return [{"id": r.product_id, "score": r.score, **r.product} for r in results]
        
        elif tool_name == "get_product_details":
            return await product_service.get_product(
                product_id=params.get("product_id"),
                include_reviews=params.get("include_reviews", True),
            )
        
        elif tool_name == "compare_products":
            return await product_service.compare_products(
                product_ids=params.get("product_ids", []),
            )
        
        elif tool_name == "get_product_reviews":
            reviews = await product_service.get_product_reviews(params.get("product_id"))
            sentiment = await analytics_service.get_reviews_sentiment(params.get("product_id"))
            return {"reviews": reviews[:10], "sentiment": sentiment}
        
        elif tool_name == "ask_about_product":
            return await retriever.answer_product_question(
                product_id=params.get("product_id"),
                question=params.get("question"),
            )
        
        elif tool_name == "get_categories":
            return await catalog_service.get_categories()
        
        elif tool_name == "get_top_products":
            return await product_service.get_top_products(
                limit=params.get("limit", 5),
                sort_by=params.get("sort_by", "rating"),
            )
        
        elif tool_name == "get_deals":
            # Get top rated products within price range
            products = await product_service.list_products(
                limit=params.get("limit", 5) * 3,
                category=params.get("category"),
                max_price=params.get("max_price"),
                sort_by="-rating",
            )
            # Filter to high-rated products
            deals = [p for p in products if p.get("rating", 0) >= 4.0]
            return deals[:params.get("limit", 5)]
        
        elif tool_name == "build_cart":
            # Use RAG to find products for the goal
            results = await retriever.search(
                query=params.get("goal", ""),
                top_k=20,
            )
            
            budget = params.get("budget", 1000)
            cart = []
            total = 0
            
            for r in results:
                price = r.product.get("price", 0)
                if total + price <= budget and r.product.get("count_in_stock", 0) > 0:
                    cart.append({
                        "id": r.product_id,
                        "name": r.product.get("name"),
                        "price": price,
                        "relevance_score": r.score,
                    })
                    total += price
            
            return {
                "goal": params.get("goal"),
                "budget": budget,
                "items": cart[:10],
                "total": round(total, 2),
                "remaining": round(budget - total, 2),
            }
        
        elif tool_name == "recommend_products":
            results = await retriever.search(
                query=params.get("preferences", ""),
                top_k=params.get("limit", 5),
            )
            
            recommendations = []
            budget = params.get("budget")
            
            for r in results:
                if budget is None or r.product.get("price", 0) <= budget:
                    recommendations.append({
                        "id": r.product_id,
                        "match_score": r.score,
                        **r.product,
                    })
            
            return recommendations
        
        elif tool_name == "check_stock":
            product = await product_service.get_product(params.get("product_id"))
            if product:
                return {
                    "product_id": params.get("product_id"),
                    "name": product.get("name"),
                    "in_stock": product.get("count_in_stock", 0) > 0,
                    "quantity_available": product.get("count_in_stock", 0),
                }
            return {"error": "Product not found"}
        
        elif tool_name == "calculate_total":
            items = params.get("items", [])
            total = 0
            details = []
            
            for item in items:
                product = await product_service.get_product(item.get("product_id"))
                if product:
                    qty = item.get("quantity", 1)
                    subtotal = product.get("price", 0) * qty
                    total += subtotal
                    details.append({
                        "product_id": item.get("product_id"),
                        "name": product.get("name"),
                        "price": product.get("price"),
                        "quantity": qty,
                        "subtotal": subtotal,
                    })
            
            return {"items": details, "total": round(total, 2)}
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def _extract_product_ids(self, result: Any, products: List[str]) -> None:
        """Extract product IDs from tool results"""
        if isinstance(result, dict):
            if "id" in result and isinstance(result["id"], str):
                if result["id"] not in products:
                    products.append(result["id"])
            if "product_id" in result:
                if result["product_id"] not in products:
                    products.append(result["product_id"])
            for value in result.values():
                self._extract_product_ids(value, products)
        elif isinstance(result, list):
            for item in result:
                self._extract_product_ids(item, products)


# Singleton instance
agent = ShoppingAgent()
