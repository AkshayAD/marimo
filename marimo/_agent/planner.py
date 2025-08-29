# Copyright 2024 Marimo. All rights reserved.
"""Task planning and decomposition for agent execution."""

from __future__ import annotations

import re
from typing import List, Optional
from uuid import uuid4

from marimo._agent.models import (
    CodeSuggestion,
    ExecutionStep,
    ExecutionStatus,
    NotebookContext,
    SuggestionType,
)
from marimo import _loggers

LOGGER = _loggers.marimo_logger()


class TaskPlanner:
    """Plans and decomposes user requests into executable steps."""
    
    def __init__(self):
        """Initialize task planner."""
        self.current_plan: List[ExecutionStep] = []
        
    def create_plan(
        self,
        user_request: str,
        context: Optional[NotebookContext] = None,
    ) -> List[ExecutionStep]:
        """Create an execution plan from a user request.
        
        Args:
            user_request: Natural language request from user
            context: Current notebook context
            
        Returns:
            List of execution steps
        """
        steps = []
        
        # Parse the request to identify intent
        intent = self._identify_intent(user_request)
        
        if intent == "create_function":
            steps.append(self._create_function_step(user_request, context))
        elif intent == "analyze_data":
            steps.append(self._create_analysis_step(user_request, context))
        elif intent == "visualize":
            steps.append(self._create_visualization_step(user_request, context))
        elif intent == "debug":
            steps.append(self._create_debug_step(user_request, context))
        elif intent == "modify":
            steps.append(self._create_modification_step(user_request, context))
        else:
            # Default: create a general code generation step
            steps.append(self._create_general_step(user_request, context))
        
        self.current_plan = steps
        return steps
    
    def _identify_intent(self, request: str) -> str:
        """Identify the intent of a user request.
        
        Args:
            request: User request text
            
        Returns:
            Intent category
        """
        request_lower = request.lower()
        
        # Simple keyword-based intent detection
        if any(word in request_lower for word in ["function", "def", "method"]):
            return "create_function"
        elif any(word in request_lower for word in ["analyze", "analysis", "explore"]):
            return "analyze_data"
        elif any(word in request_lower for word in ["plot", "visualize", "chart", "graph"]):
            return "visualize"
        elif any(word in request_lower for word in ["debug", "error", "fix", "wrong"]):
            return "debug"
        elif any(word in request_lower for word in ["modify", "change", "update", "edit"]):
            return "modify"
        else:
            return "general"
    
    def _create_function_step(
        self,
        request: str,
        context: Optional[NotebookContext],
    ) -> ExecutionStep:
        """Create a step for function creation.
        
        Args:
            request: User request
            context: Notebook context
            
        Returns:
            Execution step
        """
        step_id = str(uuid4())
        
        # Extract function details from request
        function_name = self._extract_function_name(request)
        
        description = f"Create function {function_name}" if function_name else "Create new function"
        
        return ExecutionStep(
            step_id=step_id,
            description=description,
            status=ExecutionStatus.PENDING,
        )
    
    def _create_analysis_step(
        self,
        request: str,
        context: Optional[NotebookContext],
    ) -> ExecutionStep:
        """Create a step for data analysis.
        
        Args:
            request: User request
            context: Notebook context
            
        Returns:
            Execution step
        """
        step_id = str(uuid4())
        
        # Check for dataframes in context
        df_name = None
        if context and context.variables:
            for var_name in context.variables:
                if "df" in var_name.lower() or "data" in var_name.lower():
                    df_name = var_name
                    break
        
        description = f"Analyze {df_name}" if df_name else "Perform data analysis"
        
        return ExecutionStep(
            step_id=step_id,
            description=description,
            status=ExecutionStatus.PENDING,
        )
    
    def _create_visualization_step(
        self,
        request: str,
        context: Optional[NotebookContext],
    ) -> ExecutionStep:
        """Create a step for visualization.
        
        Args:
            request: User request
            context: Notebook context
            
        Returns:
            Execution step
        """
        step_id = str(uuid4())
        
        # Identify visualization type
        viz_type = "plot"
        if "bar" in request.lower():
            viz_type = "bar chart"
        elif "scatter" in request.lower():
            viz_type = "scatter plot"
        elif "line" in request.lower():
            viz_type = "line chart"
        elif "histogram" in request.lower():
            viz_type = "histogram"
        
        return ExecutionStep(
            step_id=step_id,
            description=f"Create {viz_type}",
            status=ExecutionStatus.PENDING,
        )
    
    def _create_debug_step(
        self,
        request: str,
        context: Optional[NotebookContext],
    ) -> ExecutionStep:
        """Create a step for debugging.
        
        Args:
            request: User request
            context: Notebook context
            
        Returns:
            Execution step
        """
        step_id = str(uuid4())
        
        # Check for recent errors in context
        has_errors = context and context.recent_errors
        
        description = "Debug recent error" if has_errors else "Debug code"
        
        return ExecutionStep(
            step_id=step_id,
            description=description,
            status=ExecutionStatus.PENDING,
        )
    
    def _create_modification_step(
        self,
        request: str,
        context: Optional[NotebookContext],
    ) -> ExecutionStep:
        """Create a step for code modification.
        
        Args:
            request: User request
            context: Notebook context
            
        Returns:
            Execution step
        """
        step_id = str(uuid4())
        
        # Check if active cell is specified
        target = "active cell" if context and context.active_cell_id else "code"
        
        return ExecutionStep(
            step_id=step_id,
            description=f"Modify {target}",
            status=ExecutionStatus.PENDING,
        )
    
    def _create_general_step(
        self,
        request: str,
        context: Optional[NotebookContext],
    ) -> ExecutionStep:
        """Create a general execution step.
        
        Args:
            request: User request
            context: Notebook context
            
        Returns:
            Execution step
        """
        step_id = str(uuid4())
        
        # Use first 50 chars of request as description
        description = request[:50] + "..." if len(request) > 50 else request
        
        return ExecutionStep(
            step_id=step_id,
            description=description,
            status=ExecutionStatus.PENDING,
        )
    
    def _extract_function_name(self, request: str) -> Optional[str]:
        """Extract function name from request.
        
        Args:
            request: User request
            
        Returns:
            Function name if found
        """
        # Look for patterns like "function called X" or "X function"
        patterns = [
            r"function (?:called |named )?(\w+)",
            r"(\w+) function",
            r"def (\w+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def update_step_status(
        self,
        step_id: str,
        status: ExecutionStatus,
        result: Optional[any] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update the status of an execution step.
        
        Args:
            step_id: ID of the step
            status: New status
            result: Execution result if any
            error: Error message if any
        """
        for step in self.current_plan:
            if step.step_id == step_id:
                step.status = status
                if result is not None:
                    step.result = result
                if error is not None:
                    step.error = error
                break
    
    def get_next_pending_step(self) -> Optional[ExecutionStep]:
        """Get the next pending step in the plan.
        
        Returns:
            Next pending step or None
        """
        for step in self.current_plan:
            if step.status == ExecutionStatus.PENDING:
                return step
        return None
    
    def is_plan_complete(self) -> bool:
        """Check if all steps in the plan are complete.
        
        Returns:
            True if all steps are complete or errored
        """
        for step in self.current_plan:
            if step.status in [ExecutionStatus.PENDING, ExecutionStatus.EXECUTING]:
                return False
        return True
    
    def get_plan_summary(self) -> dict:
        """Get a summary of the current plan.
        
        Returns:
            Summary dictionary
        """
        total = len(self.current_plan)
        complete = sum(1 for s in self.current_plan if s.status == ExecutionStatus.COMPLETE)
        errors = sum(1 for s in self.current_plan if s.status == ExecutionStatus.ERROR)
        
        return {
            "total_steps": total,
            "completed": complete,
            "errors": errors,
            "progress": complete / total if total > 0 else 0,
        }