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
    from openai import AsyncOpenAI, AzureOpenAI

    # Handle Azure OpenAI
    parsed_url = urlparse(base_url) if base_url else None
    if parsed_url and parsed_url.hostname and cast(str, parsed_url.hostname).endswith(
        ".openai.azure.com"
    ):
        model = cast(str, parsed_url.path).split("/")[3]
        api_version = parse_qs(cast(str, parsed_url.query))["api-version"][0]
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=f"{cast(str, parsed_url.scheme)}://{cast(str, parsed_url.hostname)}",
        )
    else:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or None,
        )

    openai_messages = convert_to_openai_messages(
        [ChatMessage(role="system", content=system_message)] + messages
    )
    
    stream = await client.chat.completions.create(
        model=model,
        messages=openai_messages,
        max_completion_tokens=config.max_tokens,
        temperature=config.temperature,
        top_p=config.top_p,
        frequency_penalty=config.frequency_penalty,
        presence_penalty=config.presence_penalty,
        stream=True,
    )

    async for chunk in stream:
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
    from google import genai

    client = genai.Client(api_key=api_key)
    google_messages = convert_to_google_messages(messages)
    
    # Note: Google's streaming API might be different - this is a placeholder
    # You might need to adjust based on the actual Google genai streaming API
    response = client.models.generate_content_stream(
        model=model,
        contents=google_messages,
        config={
            "system_instruction": system_message,
            "max_output_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
        },
    )

    for chunk in response:
        if hasattr(chunk, 'text') and chunk.text:
            yield chunk.text


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
    
    stream = await client.chat.completions.create(
        model=model,
        messages=groq_messages,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        top_p=config.top_p,
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


# Mapping for streaming functions
STREAMING_PROVIDERS = {
    "openai": stream_openai,
    "anthropic": stream_anthropic,
    "google": stream_google,
    "groq": stream_groq,
}