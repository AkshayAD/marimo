# Copyright 2024 Marimo. All rights reserved.
"""Core agent implementation for Marimo notebooks."""

from __future__ import annotations

import asyncio
import os
from typing import Any, AsyncGenerator, Dict, List, Optional
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
from marimo._ai.llm._streaming import STREAMING_PROVIDERS
from marimo._ai._types import ChatMessage, ChatModelConfig
from marimo._agent.safety import SafetyChecker
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
        self.safety_checker = SafetyChecker(getattr(self.config, 'safety_mode', 'balanced'))
        self._model = model
        self._session_id = str(uuid4())
        
    def _get_model(self):
        """Get the LLM model instance."""
        if self._model:
            return self._model
            
        # Import based on config - use active_model property
        model_name = self.config.active_model
        
        if model_name.startswith("openai/"):
            from marimo._ai.llm import openai
            model = model_name.replace("openai/", "")
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")
            return openai(model=model, api_key=api_key, base_url=base_url)
            
        elif model_name.startswith("anthropic/"):
            from marimo._ai.llm import anthropic
            model = model_name.replace("anthropic/", "")
            api_key = os.getenv("ANTHROPIC_API_KEY")
            base_url = os.getenv("ANTHROPIC_BASE_URL")
            return anthropic(model=model, api_key=api_key, base_url=base_url)
            
        elif model_name.startswith("google/") or model_name.startswith("gemini/"):
            from marimo._ai.llm import google
            # Handle both google/ and gemini/ prefixes
            if model_name.startswith("google/"):
                model = model_name.replace("google/", "")
            else:
                model = model_name.replace("gemini/", "")
            api_key = os.getenv("GOOGLE_AI_API_KEY")
            return google(model=model, api_key=api_key)
            
        elif model_name.startswith("groq/"):
            from marimo._ai.llm import groq
            model = model_name.replace("groq/", "")
            api_key = os.getenv("GROQ_API_KEY")
            return groq(model=model, api_key=api_key)
            
        elif model_name.startswith("bedrock/"):
            from marimo._ai.llm import bedrock
            model = model_name.replace("bedrock/", "")
            return bedrock(
                model=model,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            )
            
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
            
            # Check code safety
            if code:
                is_safe, warnings = self.safety_checker.check_code(code)
                if not is_safe:
                    LOGGER.warning(f"Generated unsafe code: {warnings}")
                    # Add safety warnings as comments
                    warning_comments = "\n".join([f"# SAFETY WARNING: {w}" for w in warnings])
                    code = f"{warning_comments}\n\n{code}"
                elif warnings:
                    # Add warnings as comments for user awareness
                    warning_comments = "\n".join([f"# NOTE: {w}" for w in warnings[:3]])  # Limit to first 3
                    code = f"{warning_comments}\n\n{code}"
            
            return code
            
        except Exception as e:
            LOGGER.error(f"Error generating code: {e}")
            # Try to provide helpful error message based on the error
            error_str = str(e)
            if "API key" in error_str or "authentication" in error_str.lower():
                return f"# Error: Please check your API key configuration\n# {error_str}"
            elif "rate limit" in error_str.lower():
                return f"# Error: Rate limit exceeded, please try again later\n# {error_str}"
            else:
                return f"# Error generating code: {error_str}"
    
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
    
    async def stream_response(
        self,
        request: AgentRequest,
    ) -> AsyncGenerator[str, None]:
        """Stream agent response in real-time.
        
        Args:
            request: User request
            
        Yields:
            Chunks of the response message
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
        
        # Stream the response generation
        async for chunk in self._stream_code_generation(request, plan):
            yield chunk
    
    async def _stream_code_generation(
        self,
        request: AgentRequest,
        plan: List[ExecutionStep],
    ) -> AsyncGenerator[str, None]:
        """Stream code generation for execution plan.
        
        Args:
            request: User request
            plan: Execution plan
            
        Yields:
            Chunks of generated response
        """
        if not plan:
            yield "I couldn't create a plan for your request. Could you provide more details?"
            return
            
        # Get model information for streaming
        model_name = self.config.active_model
        provider = model_name.split("/")[0]
        # Normalize gemini to google for provider lookup
        if provider == "gemini":
            provider = "google"
        model = model_name.split("/", 1)[1] if "/" in model_name else model_name
        
        if provider not in STREAMING_PROVIDERS:
            # Fallback to non-streaming for unsupported providers
            response = await self.process_request(request)
            yield response.message
            return
            
        # Build streaming prompt
        step = plan[0]  # For now, stream the first step
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
            
        # Get API credentials
        api_key = self._get_api_key_for_provider(provider)
        base_url = self._get_base_url_for_provider(provider)
        
        # Create chat messages
        messages = [
            ChatMessage(role="user", content=prompt)
        ]
        
        config = ChatModelConfig(
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        
        # Stream the response
        stream_func = STREAMING_PROVIDERS[provider]
        try:
            async for chunk in stream_func(
                messages=messages,
                config=config,
                model=model,
                system_message=SYSTEM_PROMPT,
                api_key=api_key,
                base_url=base_url,
            ):
                yield chunk
        except Exception as e:
            LOGGER.error(f"Error streaming response: {e}")
            yield f"\n\nError generating response: {str(e)}"
    
    def _get_api_key_for_provider(self, provider: str) -> str:
        """Get API key for a specific provider."""
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY", 
            "google": "GOOGLE_AI_API_KEY",
            "gemini": "GOOGLE_AI_API_KEY",  # Alias for Google
            "groq": "GROQ_API_KEY",
        }
        
        env_var = key_map.get(provider)
        if not env_var:
            raise ValueError(f"No API key environment variable defined for provider: {provider}")
            
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {env_var}")
            
        return api_key
    
    def _get_base_url_for_provider(self, provider: str) -> Optional[str]:
        """Get base URL for a specific provider."""
        url_map = {
            "openai": "OPENAI_BASE_URL",
            "anthropic": "ANTHROPIC_BASE_URL",
        }
        
        env_var = url_map.get(provider)
        return os.getenv(env_var) if env_var else None

    @classmethod
    def from_env(cls, **overrides) -> "AgentCore":
        """Create AgentCore with configuration from environment variables.
        
        Args:
            **overrides: Override specific config values
            
        Returns:
            Configured AgentCore instance
        """
        config = AgentConfig(
            enabled=os.getenv("MARIMO_AGENT_ENABLED", "true").lower() == "true",
            default_model=os.getenv("MARIMO_AGENT_DEFAULT_MODEL", "openai/gpt-4o"),
            auto_execute=os.getenv("MARIMO_AGENT_AUTO_EXECUTE", "false").lower() == "true",
            require_approval=os.getenv("MARIMO_AGENT_REQUIRE_APPROVAL", "true").lower() == "true",
            max_steps=int(os.getenv("MARIMO_AGENT_MAX_STEPS", "10")),
            stream_responses=os.getenv("MARIMO_AGENT_STREAM_RESPONSES", "true").lower() == "true",
            **overrides
        )
        return cls(config=config)
    
    def clear_memory(self) -> None:
        """Clear agent memory and conversation history."""
        self.memory.clear_history()
        self.planner.current_plan.clear()
        LOGGER.info(f"Cleared memory for agent session {self._session_id}")