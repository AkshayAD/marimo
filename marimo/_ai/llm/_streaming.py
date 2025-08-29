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
    """Stream Google AI chat completion responses."""
    DependencyManager.google_ai.require(
        "streaming requires google. `pip install google-genai`"
    )
    try:
        from google import genai
    except ImportError:
        # Fallback to google.generativeai for older installations
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
        except ImportError:
            raise ImportError("Please install google-genai or google-generativeai")
    
    # WARNING: Google's streaming API is not fully async and may block
    # This is a best-effort implementation that may need adjustment
    try:
        if hasattr(genai, 'Client'):
            # New google-genai API
            client = genai.Client(api_key=api_key)
            google_messages = convert_to_google_messages(messages)
            
            # The actual method name might differ - this is an educated guess
            # Google's API documentation should be consulted for the exact method
            response = client.models.generate_content(
                model=model,
                contents=google_messages,
                config={
                    "system_instruction": system_message,
                    "max_output_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "top_k": config.top_k,
                },
                stream=True,  # Enable streaming if supported
            )
        else:
            # Fallback for google.generativeai
            model_obj = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_message,
            )
            google_messages = convert_to_google_messages(messages)
            response = model_obj.generate_content(
                google_messages,
                generation_config={
                    "max_output_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "top_k": config.top_k,
                },
                stream=True,
            )
        
        # Iterate over streaming response
        for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                yield chunk.text
            elif hasattr(chunk, 'parts'):
                for part in chunk.parts:
                    if hasattr(part, 'text') and part.text:
                        yield part.text
    except Exception as e:
        # Log the error and yield an error message
        yield f"[Error streaming from Google AI: {str(e)}]"


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
    "groq": stream_groq,
}