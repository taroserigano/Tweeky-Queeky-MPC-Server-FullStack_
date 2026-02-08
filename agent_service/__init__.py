"""
Agent Service - Agentic AI for autonomous task execution

This module provides intelligent agents that can:
- Plan multi-step tasks
- Use tools (via MCP or direct calls)
- Maintain conversation memory
- Reason through complex requests

Architecture:
- LangGraph Agent: Production-grade state machine (recommended)
- Legacy Agent: Custom ReAct implementation (reference)
- Memory: LangGraph checkpointing for persistence
- Tools: LangChain @tool decorated functions
"""

# LangGraph-based agent (recommended)
from agent_service.langgraph_agent import (
    ShoppingAgentLangGraph,
    get_shopping_agent,
    AgentState,
    SHOPPING_TOOLS,
    create_shopping_agent,
)

# Legacy custom implementation (kept for reference)
from agent_service.agent import ShoppingAgent, agent
from agent_service.memory import ConversationMemory, SessionMemory
from agent_service.tools import ToolRegistry, tool_registry

__all__ = [
    # LangGraph agent (primary)
    "ShoppingAgentLangGraph",
    "get_shopping_agent",
    "AgentState",
    "SHOPPING_TOOLS",
    "create_shopping_agent",
    # Legacy (reference)
    "ShoppingAgent",
    "agent",
    "ConversationMemory",
    "SessionMemory", 
    "ToolRegistry",
    "tool_registry",
]

