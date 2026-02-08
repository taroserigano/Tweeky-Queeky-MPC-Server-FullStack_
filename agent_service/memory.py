"""
Conversation and Session Memory

Manages agent memory for:
- Conversation history within a session
- User preferences and context
- Short-term working memory for multi-step tasks
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import json


@dataclass
class Message:
    """A single message in conversation history"""
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    def to_llm_message(self) -> Dict[str, str]:
        """Convert to format expected by LLM APIs"""
        return {"role": self.role, "content": self.content}


class ConversationMemory:
    """
    Manages conversation history for an agent session.
    
    Features:
    - Rolling window of recent messages
    - Summary of older messages
    - Token-aware truncation
    """
    
    def __init__(
        self,
        max_messages: int = 20,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None,
    ):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.messages: deque[Message] = deque(maxlen=max_messages)
        self.system_prompt = system_prompt
        self._summary: Optional[str] = None
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a message to conversation history"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(message)
    
    def add_user_message(self, content: str) -> None:
        """Add a user message"""
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message"""
        self.add_message("assistant", content)
    
    def add_tool_result(self, tool_name: str, result: Any) -> None:
        """Add a tool execution result"""
        content = f"Tool '{tool_name}' returned: {json.dumps(result, default=str)[:1000]}"
        self.add_message("tool", content, {"tool_name": tool_name})
    
    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Get messages formatted for LLM API"""
        messages = []
        
        # Add system prompt if set
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        # Add summary of older messages if available
        if self._summary:
            messages.append({
                "role": "system",
                "content": f"Summary of earlier conversation: {self._summary}"
            })
        
        # Add recent messages
        for msg in self.messages:
            # Convert tool messages to assistant for APIs that don't support tool role
            role = "assistant" if msg.role == "tool" else msg.role
            messages.append({"role": role, "content": msg.content})
        
        return messages
    
    def get_recent_context(self, n: int = 5) -> str:
        """Get recent messages as a string for context"""
        recent = list(self.messages)[-n:]
        lines = []
        for msg in recent:
            prefix = {"user": "User", "assistant": "Assistant", "tool": "Tool"}.get(msg.role, msg.role)
            lines.append(f"{prefix}: {msg.content[:200]}")
        return "\n".join(lines)
    
    def clear(self) -> None:
        """Clear conversation history"""
        self.messages.clear()
        self._summary = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory state"""
        return {
            "messages": [m.to_dict() for m in self.messages],
            "summary": self._summary,
            "system_prompt": self.system_prompt,
        }


class SessionMemory:
    """
    Session-level memory for user context and preferences.
    
    Stores:
    - User preferences (budget, categories of interest)
    - Cart/wishlist state
    - Recently viewed products
    - Task context for multi-step workflows
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_id()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # User preferences
        self.preferences: Dict[str, Any] = {
            "budget_min": None,
            "budget_max": None,
            "preferred_categories": [],
            "preferred_brands": [],
        }
        
        # Recently viewed items
        self.recently_viewed: deque[str] = deque(maxlen=20)
        
        # Current task context
        self.task_context: Dict[str, Any] = {}
        
        # Working memory for current task
        self.working_memory: Dict[str, Any] = {}
    
    @staticmethod
    def _generate_id() -> str:
        """Generate a unique session ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference"""
        self.preferences[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self.preferences.get(key, default)
    
    def add_viewed_product(self, product_id: str) -> None:
        """Track a viewed product"""
        if product_id in self.recently_viewed:
            self.recently_viewed.remove(product_id)
        self.recently_viewed.append(product_id)
        self.updated_at = datetime.utcnow()
    
    def get_recently_viewed(self, limit: int = 10) -> List[str]:
        """Get recently viewed product IDs"""
        return list(self.recently_viewed)[-limit:]
    
    def set_task_context(self, task_type: str, context: Dict[str, Any]) -> None:
        """Set context for current task"""
        self.task_context = {
            "type": task_type,
            "started_at": datetime.utcnow().isoformat(),
            **context,
        }
        self.updated_at = datetime.utcnow()
    
    def clear_task_context(self) -> None:
        """Clear current task context"""
        self.task_context = {}
        self.working_memory = {}
    
    def store(self, key: str, value: Any) -> None:
        """Store a value in working memory"""
        self.working_memory[key] = value
    
    def retrieve(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from working memory"""
        return self.working_memory.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize session state"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "preferences": self.preferences,
            "recently_viewed": list(self.recently_viewed),
            "task_context": self.task_context,
        }
    
    def get_context_summary(self) -> str:
        """Get a summary of session context for the agent"""
        parts = []
        
        if self.preferences.get("budget_max"):
            parts.append(f"Budget: up to ${self.preferences['budget_max']}")
        
        if self.preferences.get("preferred_categories"):
            parts.append(f"Interested in: {', '.join(self.preferences['preferred_categories'])}")
        
        if self.recently_viewed:
            parts.append(f"Recently viewed {len(self.recently_viewed)} products")
        
        if self.task_context:
            parts.append(f"Current task: {self.task_context.get('type', 'unknown')}")
        
        return " | ".join(parts) if parts else "New session"
