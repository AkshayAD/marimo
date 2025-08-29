# Copyright 2024 Marimo. All rights reserved.
from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator, Optional, cast

from marimo._ai._convert import (
    convert_to_anthropic_messages,
    convert_to_google_messages,
    convert_to_groq_messages,
    convert_to_openai_messages,
)
from marimo._ai._types import (
    ChatMessage,
    ChatModelConfig,
)
from marimo._dependencies.dependencies import DependencyManager


async def stream_openai(
    messages: list[ChatMessage],
    config: ChatModelConfig,
    model: str,
    system_message: str,
    api_key: str,
    base_url: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream OpenAI chat completion responses."""
    DependencyManager.openai.require(
        "streaming requires openai. `pip install openai`"
    )
    from urllib.parse import parse_qs, urlparse
    from openai import AsyncOpenAI
    try:
        from openai import AsyncAzureOpenAI
    except ImportError:
        # Fallback for older openai versions
        AsyncAzureOpenAI = None

    # Handle Azure OpenAI
    parsed_url = urlparse(base_url) if base_url else None
    if parsed_url and parsed_url.hostname and cast(str, parsed_url.hostname).endswith(
        ".openai.azure.com"
    ):
        if AsyncAzureOpenAI:
            model = cast(str, parsed_url.path).split("/")[3]
            api_version = parse_qs(cast(str, parsed_url.query))["api-version"][0]
            client = AsyncAzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=f"{cast(str, parsed_url.scheme)}://{cast(str, parsed_url.hostname)}",
            )
        else:
            # Fallback - use regular AsyncOpenAI with base_url
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
            )
    else:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or None,
        )

    openai_messages = convert_to_openai_messages(
        [ChatMessage(role="system", content=system_message)] + messages
    )
    
    # No await here - create returns an async iterator directly
    stream = client.chat.completions.create(
        model=model,
        messages=openai_messages,
        max_tokens=config.max_tokens,  # Fixed: use max_tokens
        temperature=config.temperature,
        top_p=config.top_p,
        frequency_penalty=config.frequency_penalty,
        presence_penalty=config.presence_penalty,
        stream=True,
    )

    async for chunk in await stream:  # Need to await the stream
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def stream_anthropic(
    messages: list[ChatMessage],
    config: ChatModelConfig,
    model: str,
    system_message: str,
    api_key: str,
    base_url: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream Anthropic chat completion responses."""
    DependencyManager.anthropic.require(
        "streaming requires anthropic. `pip install anthropic`"
    )
    from anthropic import AsyncAnthropic, NOT_GIVEN

    client = AsyncAnthropic(
        api_key=api_key,
        base_url=base_url,
    )

    anthropic_messages = convert_to_anthropic_messages(messages)
    
    async with client.messages.stream(
        model=model,
        system=system_message,
        max_tokens=config.max_tokens or 4096,
        messages=anthropic_messages,
        top_p=config.top_p if config.top_p is not None else NOT_GIVEN,
        top_k=config.top_k if config.top_k is not None else NOT_GIVEN,
        temperature=config.temperature if config.temperature is not None else NOT_GIVEN,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def stream_google(
    messages: list[ChatMessage],
    config: ChatModelConfig,
    model: str,
    system_message: str,
    api_key: str,
) -> AsyncGenerator[str, None]:
    """Stream Google AI chat completion responses.
    
    Supports Gemini 2.5 models with Deep Think mode and thinking budgets.
    """
    # Try new google-genai SDK first (recommended for Gemini 2.0+)
    try:
        from google import genai
        from google.genai import types
        
        # Initialize client with API key
        client = genai.Client(api_key=api_key)
        
        # Convert messages to Google format
        google_messages = convert_to_google_messages(messages)
        
        # Check for Deep Think mode (Gemini 2.5 Pro only)
        enable_deep_think = (
            "gemini-2.5-pro" in model.lower() and 
            os.getenv("GEMINI_DEEP_THINK", "false").lower() == "true"
        )
        
        # Get thinking budget from environment (for Gemini 2.5 Flash/Pro)
        thinking_budget = None
        if "gemini-2.5" in model.lower():
            thinking_budget = int(os.getenv("GEMINI_THINKING_BUDGET", "0"))
        
        # Create config for generation
        generation_config_dict = {
            "temperature": config.temperature if config.temperature is not None else 0.7,
            "top_p": config.top_p if config.top_p is not None else 0.95,
            "top_k": config.top_k if config.top_k is not None else 40,
            "max_output_tokens": config.max_tokens if config.max_tokens else 2048,
            "system_instruction": system_message if system_message else None,
        }
        
        # Add Deep Think mode if enabled
        if enable_deep_think:
            generation_config_dict["reasoning_mode"] = "deep_think"
            
        # Add thinking budget if specified
        if thinking_budget and thinking_budget > 0:
            generation_config_dict["thinking_budget_tokens"] = thinking_budget
        
        generation_config = types.GenerateContentConfig(**generation_config_dict)
        
        # Stream the response
        try:
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=google_messages,
                config=generation_config,
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            # If streaming fails, fallback to non-streaming
            response = client.models.generate_content(
                model=model,
                contents=google_messages,
                config=generation_config,
            )
            if response.text:
                yield response.text
                
    except ImportError:
        # Fallback to older google-generativeai SDK
        try:
            import google.generativeai as genai
            
            # Configure with API key
            genai.configure(api_key=api_key)
            
            # Create generation config
            generation_config = {
                "temperature": config.temperature if config.temperature is not None else 0.7,
                "top_p": config.top_p if config.top_p is not None else 0.95,
                "top_k": config.top_k if config.top_k is not None else 40,
                "max_output_tokens": config.max_tokens if config.max_tokens else 2048,
            }
            
            # Create model with system instruction
            model_obj = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_message if system_message else None,
            )
            
            # Convert messages
            google_messages = convert_to_google_messages(messages)
            
            # Stream the response
            try:
                response_stream = model_obj.generate_content_stream(google_messages)
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
            except Exception as e:
                # Fallback to non-streaming
                response = model_obj.generate_content(google_messages)
                if response.text:
                    yield response.text
                    
        except ImportError:
            yield "[Error: Please install google-genai or google-generativeai package]"
        except Exception as e:
            yield f"[Error with Google Gemini: {str(e)}]"


async def stream_groq(
    messages: list[ChatMessage],
    config: ChatModelConfig,
    model: str,
    system_message: str,
    api_key: str,
    base_url: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream Groq chat completion responses."""
    DependencyManager.groq.require(
        "streaming requires groq. `pip install groq`"
    )
    from groq import AsyncGroq

    client = AsyncGroq(api_key=api_key, base_url=base_url)

    groq_messages = convert_to_groq_messages(
        [ChatMessage(role="system", content=system_message)] + messages
    )
    
    # No await here - create returns an async iterator
    stream = client.chat.completions.create(
        model=model,
        messages=groq_messages,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        top_p=config.top_p,
        stream=True,
    )

    async for chunk in await stream:  # Need to await the stream
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


# Mapping for streaming functions
STREAMING_PROVIDERS = {
    "openai": stream_openai,
    "anthropic": stream_anthropic,
    "google": stream_google,
    "gemini": stream_google,  # Alias for Google Gemini
    "groq": stream_groq,
}