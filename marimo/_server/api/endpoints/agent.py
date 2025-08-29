# Copyright 2024 Marimo. All rights reserved.
"""Agent API endpoints for Marimo."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import uuid4

from starlette.authentication import requires
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from marimo import _loggers
from marimo._agent.core import AgentCore
from marimo._agent.models import (
    AgentConfig,
    AgentRequest,
    CodeSuggestion,
    NotebookContext,
)
from marimo._messaging.ops import (
    AgentExecutionOp,
    AgentMessageOp,
    AgentSuggestionOp,
)
from marimo._runtime.context import get_context
from marimo._runtime.context.types import ContextNotInitializedError
from marimo._server.api.deps import AppState
from marimo._server.api.utils import parse_request
from marimo._server.models.models import BaseResponse, SuccessResponse
from marimo._server.router import APIRouter
from marimo._types.ids import CellId_t

if TYPE_CHECKING:
    from starlette.requests import Request

LOGGER = _loggers.marimo_logger()

# Router for agent endpoints
router = APIRouter()

# Store agent instances per session
AGENT_SESSIONS: Dict[str, AgentCore] = {}


def get_or_create_agent(session_id: str, config: Optional[AgentConfig] = None) -> AgentCore:
    """Get or create an agent for a session.
    
    Args:
        session_id: Session identifier
        config: Agent configuration
        
    Returns:
        Agent instance
    """
    if session_id not in AGENT_SESSIONS:
        AGENT_SESSIONS[session_id] = AgentCore(config=config)
    return AGENT_SESSIONS[session_id]


@router.post("/agent/chat")
async def agent_chat(
    *,
    request: Request,
) -> JSONResponse:
    """Handle agent chat request.
    
    requestBody:
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        message:
                            type: string
                        context:
                            type: object
                        auto_execute:
                            type: boolean
                        model:
                            type: string
    responses:
        200:
            description: Agent response with suggestions
    """
    app_state = AppState(request)
    session_id = app_state.require_current_session_id()
    
    body = await request.json()
    message = body.get("message", "")
    context_data = body.get("context", {})
    auto_execute = body.get("auto_execute", False)
    model = body.get("model")
    
    # Build notebook context
    context = None
    if context_data:
        context = NotebookContext(
            active_cell_id=context_data.get("active_cell_id"),
            cell_codes=context_data.get("cell_codes", {}),
            variables=context_data.get("variables", {}),
            recent_errors=context_data.get("recent_errors", []),
            execution_history=context_data.get("execution_history", []),
        )
    
    # Get or create agent
    agent = get_or_create_agent(session_id)
    
    # Create request
    agent_request = AgentRequest(
        message=message,
        context=context,
        model=model,
        auto_execute=auto_execute,
    )
    
    # Process request
    try:
        response = await agent.process_request(agent_request)
        
        # Broadcast to frontend via WebSocket
        AgentMessageOp(
            message=response.message,
            role="assistant",
            suggestions=[s.__dict__ for s in response.suggestions],
        ).broadcast()
        
        return JSONResponse({
            "message": response.message,
            "suggestions": [s.__dict__ for s in response.suggestions],
            "execution_plan": [s.__dict__ for s in response.execution_plan],
            "requires_approval": response.requires_approval,
        })
        
    except Exception as e:
        LOGGER.error(f"Error processing agent request: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500,
        )


@router.post("/agent/execute")
async def agent_execute(
    *,
    request: Request,
) -> JSONResponse:
    """Execute agent suggestions.
    
    requestBody:
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        suggestion_id:
                            type: string
                        suggestion:
                            type: object
    responses:
        200:
            description: Execution result
    """
    app_state = AppState(request)
    session_id = app_state.require_current_session_id()
    
    body = await request.json()
    suggestion_data = body.get("suggestion", {})
    
    # Get agent
    agent = get_or_create_agent(session_id)
    
    # Create suggestion object
    suggestion = CodeSuggestion(
        type=suggestion_data.get("type"),
        code=suggestion_data.get("code"),
        cell_id=suggestion_data.get("cell_id"),
        position=suggestion_data.get("position", "after"),
        description=suggestion_data.get("description"),
        auto_execute=suggestion_data.get("auto_execute", False),
    )
    
    # Execute suggestion
    try:
        result = await agent.execute_suggestion(suggestion)
        
        # Broadcast execution status
        AgentExecutionOp(
            step_id=str(uuid4()),
            description=suggestion.description or "Executing code",
            status="complete" if result.get("status") == "success" else "error",
            result=result,
        ).broadcast()
        
        return JSONResponse(result)
        
    except Exception as e:
        LOGGER.error(f"Error executing suggestion: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500,
        )


@router.post("/agent/clear")
async def agent_clear(
    *,
    request: Request,
) -> BaseResponse:
    """Clear agent memory and conversation.
    
    responses:
        200:
            description: Success
    """
    app_state = AppState(request)
    session_id = app_state.require_current_session_id()
    
    if session_id in AGENT_SESSIONS:
        AGENT_SESSIONS[session_id].clear_memory()
    
    return SuccessResponse()


@router.get("/agent/config")
async def get_agent_config(
    *,
    request: Request,
) -> JSONResponse:
    """Get agent configuration.
    
    responses:
        200:
            description: Agent configuration
    """
    app_state = AppState(request)
    
    # Get config from context or use defaults
    try:
        ctx = get_context()
        config = ctx.marimo_config.get("agent", {})
    except ContextNotInitializedError:
        config = {}
    
    # Use defaults if not configured
    default_config = AgentConfig()
    
    return JSONResponse({
        "enabled": config.get("enabled", default_config.enabled),
        "default_model": config.get("default_model", default_config.default_model),
        "auto_execute": config.get("auto_execute", default_config.auto_execute),
        "require_approval": config.get("require_approval", default_config.require_approval),
        "max_steps": config.get("max_steps", default_config.max_steps),
        "stream_responses": config.get("stream_responses", default_config.stream_responses),
    })


@router.websocket("/agent/stream")
async def agent_stream_ws(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming agent responses.
    
    This allows for real-time streaming of LLM responses and execution updates.
    """
    await websocket.accept()
    
    session_id = str(uuid4())  # Create unique session for this connection
    agent = None
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data.get("type") == "init":
                # Initialize agent with config
                config_data = data.get("config", {})
                config = AgentConfig(**config_data) if config_data else None
                agent = get_or_create_agent(session_id, config)
                
                await websocket.send_json({
                    "type": "init_complete",
                    "session_id": session_id,
                })
                
            elif data.get("type") == "chat":
                if not agent:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Agent not initialized",
                    })
                    continue
                
                # Process chat message
                message = data.get("message", "")
                context_data = data.get("context", {})
                
                # Build context
                context = None
                if context_data:
                    context = NotebookContext(
                        active_cell_id=context_data.get("active_cell_id"),
                        cell_codes=context_data.get("cell_codes", {}),
                        variables=context_data.get("variables", {}),
                        recent_errors=context_data.get("recent_errors", []),
                        execution_history=context_data.get("execution_history", []),
                    )
                
                # Create request
                agent_request = AgentRequest(
                    message=message,
                    context=context,
                    stream=True,
                )
                
                # Process and stream response
                try:
                    # For now, send complete response
                    # In future, implement streaming from LLM
                    response = await agent.process_request(agent_request)
                    
                    await websocket.send_json({
                        "type": "response",
                        "message": response.message,
                        "suggestions": [s.__dict__ for s in response.suggestions],
                        "execution_plan": [s.__dict__ for s in response.execution_plan],
                        "requires_approval": response.requires_approval,
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                    })
                    
            elif data.get("type") == "execute":
                if not agent:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Agent not initialized",
                    })
                    continue
                
                # Execute suggestion
                suggestion_data = data.get("suggestion", {})
                suggestion = CodeSuggestion(**suggestion_data)
                
                try:
                    result = await agent.execute_suggestion(suggestion)
                    
                    await websocket.send_json({
                        "type": "execution_result",
                        "result": result,
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                    })
                    
            elif data.get("type") == "clear":
                if agent:
                    agent.clear_memory()
                    await websocket.send_json({
                        "type": "cleared",
                    })
                    
    except WebSocketDisconnect:
        LOGGER.info(f"Agent WebSocket disconnected for session {session_id}")
    except Exception as e:
        LOGGER.error(f"Error in agent WebSocket: {e}")
    finally:
        # Clean up session
        if session_id in AGENT_SESSIONS:
            del AGENT_SESSIONS[session_id]