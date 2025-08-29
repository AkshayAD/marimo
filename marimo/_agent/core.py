# Copyright 2024 Marimo. All rights reserved.
"""Core agent implementation for Marimo notebooks."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from uuid import uuid4

from marimo import _loggers
from marimo._agent.executor import ExecutionContext
from marimo._agent.memory import AgentMemory
from marimo._agent.models import (
    AgentConfig,
    AgentMessage,
    AgentRequest,
    AgentResponse,
    AgentRole,
    CodeSuggestion,
    ExecutionStatus,
    ExecutionStep,
    NotebookContext,
    SuggestionType,
)
from marimo._agent.planner import TaskPlanner
from marimo._agent.prompts import (
    SYSTEM_PROMPT,
    build_code_generation_prompt,
    build_modification_prompt,
    extract_code_from_response,
    format_conversation_for_llm,
)
from marimo._ai._types import ChatMessage, ChatModelConfig
from marimo._dependencies.dependencies import DependencyManager

LOGGER = _loggers.marimo_logger()


class AgentCore:
    """Core agent for executing tasks in Marimo notebooks."""
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        model: Optional[Any] = None,
    ):
        """Initialize the agent.
        
        Args:
            config: Agent configuration
            model: LLM model to use (optional)
        """
        self.config = config or AgentConfig()
        self.memory = AgentMemory()
        self.executor = ExecutionContext()
        self.planner = TaskPlanner()
        self._model = model
        self._session_id = str(uuid4())
        
    def _get_model(self):
        """Get the LLM model instance."""
        if self._model:
            return self._model
            
        # Import based on config
        model_name = self.config.default_model
        
        if model_name.startswith("openai/"):
            from marimo._ai.llm import openai
            model = model_name.replace("openai/", "")
            return openai(model=model)
            
        elif model_name.startswith("anthropic/"):
            from marimo._ai.llm import anthropic
            model = model_name.replace("anthropic/", "")
            return anthropic(model=model)
            
        elif model_name.startswith("google/"):
            from marimo._ai.llm import google
            model = model_name.replace("google/", "")
            return google(model=model)
            
        elif model_name.startswith("bedrock/"):
            from marimo._ai.llm import bedrock
            model = model_name.replace("bedrock/", "")
            return bedrock(model=model)
            
        else:
            raise ValueError(f"Unknown model provider: {model_name}")
    
    async def process_request(
        self,
        request: AgentRequest,
    ) -> AgentResponse:
        """Process a user request.
        
        Args:
            request: User request
            
        Returns:
            Agent response with suggestions and execution plan
        """
        # Add user message to memory
        self.memory.add_message(
            role=AgentRole.USER,
            content=request.message,
        )
        
        # Update context if provided
        if request.context:
            self.memory.update_notebook_context(request.context)
        
        # Create execution plan
        plan = self.planner.create_plan(request.message, request.context)
        
        # Generate code suggestions
        suggestions = await self._generate_suggestions(request, plan)
        
        # Build response message
        response_message = await self._generate_response_message(
            request.message,
            suggestions,
            plan,
        )
        
        # Add assistant message to memory
        self.memory.add_message(
            role=AgentRole.ASSISTANT,
            content=response_message,
            suggestions=suggestions,
        )
        
        return AgentResponse(
            message=response_message,
            suggestions=suggestions,
            execution_plan=plan,
            requires_approval=self.config.require_approval and not request.auto_execute,
        )
    
    async def _generate_suggestions(
        self,
        request: AgentRequest,
        plan: List[ExecutionStep],
    ) -> List[CodeSuggestion]:
        """Generate code suggestions based on request and plan.
        
        Args:
            request: User request
            plan: Execution plan
            
        Returns:
            List of code suggestions
        """
        suggestions = []
        
        for step in plan:
            # Generate code for this step
            code = await self._generate_code_for_step(request, step)
            
            if code:
                # Determine suggestion type based on context
                suggestion_type = self._determine_suggestion_type(request, step)
                
                suggestion = CodeSuggestion(
                    type=suggestion_type,
                    code=code,
                    cell_id=request.context.active_cell_id if request.context else None,
                    description=step.description,
                    auto_execute=request.auto_execute,
                )
                
                suggestions.append(suggestion)
                step.suggestion = suggestion
        
        return suggestions
    
    async def _generate_code_for_step(
        self,
        request: AgentRequest,
        step: ExecutionStep,
    ) -> Optional[str]:
        """Generate code for a specific execution step.
        
        Args:
            request: User request
            step: Execution step
            
        Returns:
            Generated code or None
        """
        # Build prompt based on step type
        if "modify" in step.description.lower():
            if request.context and request.context.active_cell_id:
                current_code = request.context.cell_codes.get(
                    request.context.active_cell_id, ""
                )
                prompt = build_modification_prompt(request.message, current_code)
            else:
                prompt = build_code_generation_prompt(request.message, request.context)
        else:
            prompt = build_code_generation_prompt(request.message, request.context)
        
        # Get LLM response
        try:
            model = self._get_model()
            config = ChatModelConfig(
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            
            # Create chat messages
            messages = [
                ChatMessage(role="system", content=SYSTEM_PROMPT),
                ChatMessage(role="user", content=prompt),
            ]
            
            response = model(messages, config)
            
            # Extract code from response
            code = extract_code_from_response(str(response))
            return code
            
        except Exception as e:
            LOGGER.error(f"Error generating code: {e}")
            return None
    
    def _determine_suggestion_type(
        self,
        request: AgentRequest,
        step: ExecutionStep,
    ) -> SuggestionType:
        """Determine the type of suggestion based on context.
        
        Args:
            request: User request
            step: Execution step
            
        Returns:
            Suggestion type
        """
        desc_lower = step.description.lower()
        
        if "modify" in desc_lower or "edit" in desc_lower or "change" in desc_lower:
            return SuggestionType.MODIFY_CELL
        elif "delete" in desc_lower or "remove" in desc_lower:
            return SuggestionType.DELETE_CELL
        elif "execute" in desc_lower or "run" in desc_lower:
            return SuggestionType.EXECUTE_CELL
        else:
            return SuggestionType.NEW_CELL
    
    async def _generate_response_message(
        self,
        request: str,
        suggestions: List[CodeSuggestion],
        plan: List[ExecutionStep],
    ) -> str:
        """Generate a response message for the user.
        
        Args:
            request: Original request
            suggestions: Generated suggestions
            plan: Execution plan
            
        Returns:
            Response message
        """
        if not suggestions:
            return "I couldn't generate any code suggestions for your request. Could you provide more details?"
        
        # Build response based on number of suggestions
        if len(suggestions) == 1:
            suggestion = suggestions[0]
            if suggestion.type == SuggestionType.NEW_CELL:
                return f"I've created code to {plan[0].description}. Click 'Apply' to add it to your notebook."
            elif suggestion.type == SuggestionType.MODIFY_CELL:
                return f"I've modified the code to {plan[0].description}. Click 'Apply' to update the cell."
            else:
                return f"I've prepared an action to {plan[0].description}."
        else:
            steps_desc = ", ".join(step.description for step in plan[:3])
            if len(plan) > 3:
                steps_desc += f" and {len(plan) - 3} more steps"
            return f"I've created a plan with {len(suggestions)} steps: {steps_desc}. Review and apply the suggestions."
    
    async def execute_suggestion(
        self,
        suggestion: CodeSuggestion,
    ) -> Dict[str, Any]:
        """Execute a code suggestion.
        
        Args:
            suggestion: Code suggestion to execute
            
        Returns:
            Execution result
        """
        try:
            cell_id = await self.executor.apply_suggestion(suggestion)
            
            if suggestion.auto_execute or suggestion.type == SuggestionType.EXECUTE_CELL:
                results = await self.executor.execute_cells([cell_id])
                return {
                    "status": "success",
                    "cell_id": cell_id,
                    "results": results,
                }
            else:
                return {
                    "status": "success",
                    "cell_id": cell_id,
                    "executed": False,
                }
                
        except Exception as e:
            LOGGER.error(f"Error executing suggestion: {e}")
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def execute_plan(
        self,
        plan: List[ExecutionStep],
        auto_execute: bool = False,
    ) -> Dict[str, Any]:
        """Execute a complete plan.
        
        Args:
            plan: Execution plan
            auto_execute: Whether to auto-execute cells
            
        Returns:
            Execution results
        """
        results = []
        
        for step in plan:
            # Update status
            self.planner.update_step_status(step.step_id, ExecutionStatus.EXECUTING)
            
            try:
                if step.suggestion:
                    result = await self.execute_suggestion(step.suggestion)
                    results.append(result)
                    
                    # Store result in memory
                    self.memory.store_execution_result(step.step_id, result)
                    
                    # Update status based on result
                    if result.get("status") == "success":
                        self.planner.update_step_status(
                            step.step_id,
                            ExecutionStatus.COMPLETE,
                            result=result,
                        )
                    else:
                        self.planner.update_step_status(
                            step.step_id,
                            ExecutionStatus.ERROR,
                            error=result.get("error"),
                        )
                else:
                    self.planner.update_step_status(
                        step.step_id,
                        ExecutionStatus.ERROR,
                        error="No suggestion generated for step",
                    )
                    
            except Exception as e:
                LOGGER.error(f"Error executing step {step.step_id}: {e}")
                self.planner.update_step_status(
                    step.step_id,
                    ExecutionStatus.ERROR,
                    error=str(e),
                )
        
        return {
            "results": results,
            "summary": self.planner.get_plan_summary(),
        }
    
    def clear_memory(self) -> None:
        """Clear agent memory and conversation history."""
        self.memory.clear_history()
        self.planner.current_plan.clear()
        LOGGER.info(f"Cleared memory for agent session {self._session_id}")