# Google Gemini 2.5 Integration in Marimo

## Overview

Marimo now fully supports Google Gemini 2.5 models, the latest thinking models from Google with enhanced reasoning capabilities, multimodal support, and cost optimization features.

## Available Models

### Gemini 2.5 Flash (Default)
- **Model ID**: `google/gemini-2.5-flash`
- **Description**: Best price-performance ratio with thinking capabilities
- **Features**: 
  - Fast inference with reasoning abilities
  - Thinking budget control for cost optimization
  - Well-rounded capabilities for most tasks
  - First Flash model with thinking features

### Gemini 2.5 Pro
- **Model ID**: `google/gemini-2.5-pro`
- **Description**: World-leading performance with Deep Think mode
- **Features**:
  - Deep Think mode for complex reasoning
  - Multi-hypothesis parallel thinking
  - Superior performance on math (USAMO), coding (LiveCodeBench), and multimodal tasks (MMMU)
  - Enhanced reasoning with reinforcement learning techniques

### Gemini 2.5 Flash Image
- **Model ID**: `google/gemini-2.5-flash-image`
- **Description**: State-of-the-art image generation and editing
- **Features**:
  - Blend multiple images seamlessly
  - Character consistency across generations
  - Natural language-based targeted transformations
  - $0.039 per image (1290 tokens)

## Configuration

### Environment Variables

```bash
# Basic Configuration
GOOGLE_AI_API_KEY=your-api-key-here
MARIMO_AGENT_DEFAULT_MODEL=google/gemini-2.5-flash

# Gemini 2.5 Specific Settings
GEMINI_DEEP_THINK=false  # Set to true to enable Deep Think for 2.5 Pro
GEMINI_THINKING_BUDGET=0  # Token budget (0 = automatic)
```

### Frontend Settings

The agent settings UI automatically detects Gemini 2.5 models and shows:
- Deep Think toggle (Gemini 2.5 Pro only)
- Thinking budget control (all Gemini 2.5 models)

## Deep Think Mode

Deep Think is an experimental enhanced reasoning mode for Gemini 2.5 Pro that:
- Considers multiple hypotheses before responding
- Uses parallel thinking to explore different solution paths
- Employs reinforcement learning for improved problem-solving
- Significantly improves performance on complex tasks

### Enabling Deep Think

1. Select `google/gemini-2.5-pro` as your model
2. Set `GEMINI_DEEP_THINK=true` in your environment
3. Or toggle "Deep Think Mode" in the agent settings UI

### Performance Benchmarks with Deep Think

- **USAMO 2025**: Impressive score on advanced mathematics
- **LiveCodeBench**: Leading performance on competition-level coding
- **MMMU**: 84.0% on multimodal reasoning tasks

## Thinking Budgets

Thinking budgets give you control over the cost-quality tradeoff:

```python
# Set via environment variable
GEMINI_THINKING_BUDGET=5000  # Use up to 5000 tokens for thinking

# Or via UI
# Agent Settings > Thinking Budget
```

- **0 (default)**: Automatic budget selection
- **1-1000**: Quick responses with basic reasoning
- **1000-5000**: Balanced reasoning and response time
- **5000-10000**: Deep reasoning for complex problems

## Usage Examples

### Basic Usage

```python
# In a Marimo cell
mo.ai.chat("Explain quantum entanglement")
```

### Complex Reasoning with Deep Think

```python
# Enable Deep Think for complex problems
import os
os.environ["GEMINI_DEEP_THINK"] = "true"

mo.ai.chat("""
Solve this optimization problem:
Find the minimum value of f(x,y) = x^2 + y^2 - 2x - 4y + 5
subject to the constraint x + y ≤ 3
""")
```

### Controlled Thinking Budget

```python
# Set thinking budget for cost control
os.environ["GEMINI_THINKING_BUDGET"] = "2000"

mo.ai.chat("Design a distributed cache system")
```

## API Integration

The streaming client automatically handles Gemini 2.5 features:

```python
from marimo._ai.llm._streaming import stream_google

# Automatic Deep Think and budget handling
async for chunk in stream_google(
    messages=messages,
    config=config,
    model="google/gemini-2.5-pro",
    system_message="You are a helpful assistant",
    api_key=api_key
):
    print(chunk, end="")
```

## Best Practices

### Model Selection
- **Gemini 2.5 Flash**: Default choice for most tasks
- **Gemini 2.5 Pro**: Complex reasoning, math, advanced coding
- **Gemini 2.5 Flash Image**: Image generation and editing

### Cost Optimization
1. Start with Gemini 2.5 Flash for general tasks
2. Use thinking budgets to control costs
3. Enable Deep Think only for complex problems
4. Monitor token usage in production

### Performance Tips
- Stream responses for better UX
- Use appropriate thinking budgets
- Cache responses for repeated queries
- Batch similar requests when possible

## Migration from Gemini 2.0

### Key Improvements
- Native thinking capabilities in all models
- Deep Think mode for enhanced reasoning
- Thinking budget control
- Better performance across all benchmarks
- Improved multimodal understanding

### Code Changes
```python
# Old (Gemini 2.0)
config.default_model = "google/gemini-2.0-flash-exp"

# New (Gemini 2.5)
config.default_model = "google/gemini-2.5-flash"
config.enable_deep_think = True  # For 2.5 Pro
config.thinking_budget = 3000  # Control costs
```

## Pricing

### Gemini 2.5 Flash
- Input: Competitive with 2.0 Flash
- Output: Slightly higher due to thinking tokens
- Best value for most use cases

### Gemini 2.5 Pro
- Input: Premium pricing
- Output: Premium pricing + thinking tokens
- Deep Think: Additional cost for enhanced reasoning

### Gemini 2.5 Flash Image
- Fixed: $0.039 per image (1290 tokens)
- No additional thinking costs

## Troubleshooting

### Deep Think Not Working
- Ensure you're using `gemini-2.5-pro` model
- Check `GEMINI_DEEP_THINK=true` is set
- Verify API key has access to 2.5 Pro

### High Token Usage
- Reduce thinking budget
- Use Gemini 2.5 Flash instead of Pro
- Enable streaming to see progress

### API Errors
- Update to latest Google AI SDK
- Check API key permissions
- Verify model availability in your region

## Future Roadmap

- Native audio output support (coming soon)
- Model Context Protocol (MCP) integration
- Project Mariner computer use capabilities
- Enhanced multimodal features
- Live API with audio-visual input

## Resources

- [Google AI Studio](https://aistudio.google.com)
- [Gemini API Documentation](https://ai.google.dev)
- [Vertex AI Gemini](https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini)
- [Pricing Calculator](https://cloud.google.com/vertex-ai/pricing)