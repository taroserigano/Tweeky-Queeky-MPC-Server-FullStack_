"""Audit log model for tracking admin operations."""

from beanie import Document, PydanticObjectId
from pydantic import Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any


class AuditLog(Document):
    """
    Tracks all admin operations performed via MCP tools.
    Essential for accountability and debugging in agentic AI workflows.
    """
    
    # Who performed the action
    admin_id: Optional[PydanticObjectId] = Field(None, alias="adminId")
    admin_email: Optional[str] = Field(None, alias="adminEmail")
    
    # What action was performed
    action: str  # e.g., "update_stock", "update_price", "flag_review"
    tool_name: str = Field(alias="toolName")  # MCP tool name
    
    # Target of the action
    target_type: str = Field(alias="targetType")  # e.g., "product", "review", "order"
    target_id: str = Field(alias="targetId")
    target_name: Optional[str] = Field(None, alias="targetName")
    
    # Change details
    old_value: Optional[Dict[str, Any]] = Field(None, alias="oldValue")
    new_value: Optional[Dict[str, Any]] = Field(None, alias="newValue")
    
    # Execution mode
    dry_run: bool = Field(default=False, alias="dryRun")
    
    # Result
    success: bool = True
    error_message: Optional[str] = Field(None, alias="errorMessage")
    
    # Metadata
    reason: Optional[str] = None  # Why the action was taken
    ai_context: Optional[str] = Field(None, alias="aiContext")  # AI conversation context
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)

    class Settings:
        name = "audit_logs"
        use_state_management = True
