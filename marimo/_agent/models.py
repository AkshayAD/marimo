# Copyright 2024 Marimo. All rights reserved.
"""Data models for agent operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from marimo._types.ids import CellId_t


class AgentRole(str, Enum):
    """Agent roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SuggestionType(str, Enum):
    """Types of code suggestions."""
    NEW_CELL = "new_cell"
    MODIFY_CELL = "modify_cell"
    DELETE_CELL = "delete_cell"
    EXECUTE_CELL = "execute_cell"


class ExecutionStatus(str, Enum):
    """Status of execution steps."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class CodeSuggestion:
    """A code suggestion from the agent."""
    type: SuggestionType
    code: str
    cell_id: Optional[CellId_t] = None
    position: Literal["before", "after", "replace"] = "after"
    description: Optional[str] = None
    auto_execute: bool = False


@dataclass
class ExecutionStep:
    """A single step in the execution plan."""
    step_id: str
    description: str
    suggestion: Optional[CodeSuggestion] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class AgentMessage:
    """A message in the agent conversation."""
    role: AgentRole
    content: str
    suggestions: List[CodeSuggestion] = field(default_factory=list)
    timestamp: float = field(default_factory=lambda: 0)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotebookContext:
    """Context about the current notebook state."""
    active_cell_id: Optional[CellId_t] = None
    cell_codes: Dict[CellId_t, str] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    recent_errors: List[Dict[str, Any]] = field(default_factory=list)
    execution_history: List[CellId_t] = field(default_factory=list)


@dataclass
class AgentRequest:
    """Request to the agent."""
    message: str
    context: Optional[NotebookContext] = None
    model: Optional[str] = None
    stream: bool = True
    auto_execute: bool = False
    max_steps: int = 10


@dataclass
class AgentResponse:
    """Response from the agent."""
    message: str
    suggestions: List[CodeSuggestion] = field(default_factory=list)
    execution_plan: List[ExecutionStep] = field(default_factory=list)
    requires_approval: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Configuration for the agent."""
    enabled: bool = True
    default_model: str = "openai/gpt-4"
    auto_execute: bool = False
    max_steps: int = 10
    require_approval: bool = True
    stream_responses: bool = True
    max_context_cells: int = 20
    temperature: float = 0.7
    max_tokens: int = 4096