# Copyright 2024 Marimo. All rights reserved.
"""Agent memory and context management."""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Dict, List, Optional

from marimo._agent.models import (
    AgentMessage,
    AgentRole,
    CodeSuggestion,
    NotebookContext,
)
from marimo._types.ids import CellId_t


class AgentMemory:
    """Manages agent conversation history and context."""

    def __init__(self, max_history: int = 100):
        """Initialize agent memory.
        
        Args:
            max_history: Maximum number of messages to keep in history
        """
        self.conversation_history: deque[AgentMessage] = deque(maxlen=max_history)
        self.notebook_context: Optional[NotebookContext] = None
        self.execution_results: Dict[str, Any] = {}
        self.suggestion_history: List[CodeSuggestion] = []
        
    def add_message(
        self,
        role: AgentRole,
        content: str,
        suggestions: Optional[List[CodeSuggestion]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a message to the conversation history.
        
        Args:
            role: Role of the message sender
            content: Message content
            suggestions: Code suggestions if any
            metadata: Additional metadata
        """
        message = AgentMessage(
            role=role,
            content=content,
            suggestions=suggestions or [],
            timestamp=time.time(),
            metadata=metadata or {},
        )
        self.conversation_history.append(message)
        
        # Track suggestions
        if suggestions:
            self.suggestion_history.extend(suggestions)
    
    def get_conversation_context(self, max_messages: int = 10) -> List[AgentMessage]:
        """Get recent conversation context.
        
        Args:
            max_messages: Maximum number of messages to return
            
        Returns:
            List of recent messages
        """
        return list(self.conversation_history)[-max_messages:]
    
    def update_notebook_context(self, context: NotebookContext) -> None:
        """Update the notebook context.
        
        Args:
            context: Current notebook context
        """
        self.notebook_context = context
    
    def get_relevant_context(self, query: str) -> Dict[str, Any]:
        """Get context relevant to a query.
        
        Args:
            query: User query
            
        Returns:
            Relevant context dictionary
        """
        context = {
            "recent_messages": self.get_conversation_context(),
            "notebook_state": self.notebook_context,
            "recent_suggestions": self.suggestion_history[-5:] if self.suggestion_history else [],
        }
        
        # Add relevant variables if notebook context exists
        if self.notebook_context and self.notebook_context.variables:
            # Filter to most relevant variables (basic heuristic)
            relevant_vars = {}
            for name, value in self.notebook_context.variables.items():
                # Include variables mentioned in query or recently used
                if name.lower() in query.lower() or name.startswith("df"):
                    relevant_vars[name] = value
            context["relevant_variables"] = relevant_vars
        
        return context
    
    def store_execution_result(self, step_id: str, result: Any) -> None:
        """Store the result of an execution step.
        
        Args:
            step_id: Identifier for the execution step
            result: Result of the execution
        """
        self.execution_results[step_id] = {
            "result": result,
            "timestamp": time.time(),
        }
    
    def get_execution_result(self, step_id: str) -> Optional[Any]:
        """Get the result of a previous execution step.
        
        Args:
            step_id: Identifier for the execution step
            
        Returns:
            Execution result if found
        """
        if step_id in self.execution_results:
            return self.execution_results[step_id]["result"]
        return None
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        self.suggestion_history.clear()
        self.execution_results.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the memory state.
        
        Returns:
            Summary dictionary
        """
        return {
            "total_messages": len(self.conversation_history),
            "total_suggestions": len(self.suggestion_history),
            "execution_results": len(self.execution_results),
            "has_notebook_context": self.notebook_context is not None,
        }