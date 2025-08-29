# Marimo AI Agent - Enhanced Setup Guide

This guide explains how to set up and use the enhanced AI Agent capabilities in Marimo with multiple LLM providers, streaming responses, and safety controls.

## 🚀 Quick Start

### 1. Install Dependencies

The required dependencies are already included in the main Marimo installation:

```bash
# Core dependencies (already included)
pip install openai anthropic google-genai groq boto3

# Optional: For local models
pip install ollama-python
```

### 2. Configure API Keys

Create a `.env` file in your project root (copy from `.env.example`):

```bash
# OpenAI (recommended for best performance)
OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic Claude (excellent for code generation)  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Google AI (good for general tasks)
GOOGLE_AI_API_KEY=your-google-ai-key-here

# Groq (fast inference)
GROQ_API_KEY=gsk_your-groq-key-here

# Agent Settings
MARIMO_AGENT_DEFAULT_MODEL=openai/gpt-4o
MARIMO_AGENT_STREAM_RESPONSES=true
MARIMO_AGENT_SAFETY_MODE=balanced
```

### 3. Start Marimo

```bash
source venv/bin/activate  # if using virtual environment
marimo edit --port 8080
```

### 4. Test the Agent

Open the test notebook:
```bash
marimo edit test_agent.py
```

## 🤖 Using the Agent

### Opening the Agent Panel

1. Look for the bot icon (🤖) in the bottom-right corner of the Marimo editor
2. Click to open the agent panel
3. The panel shows connection status and active model

### Basic Usage

**Simple requests:**
- "Create a scatter plot of x vs y"
- "Calculate the mean of column 'sales'"
- "Add a new column with random numbers"

**Complex analysis:**
- "Perform a comprehensive analysis of this dataset including statistics, correlations, and visualizations"
- "Build a machine learning model to predict sales based on other features"
- "Create an interactive dashboard for exploring the data"

**Code assistance:**
- "Debug this error in my code"
- "Optimize this function for better performance" 
- "Add error handling to my data processing pipeline"

## ⚙️ Configuration Options

### Model Selection

Choose from multiple providers in the agent settings:

**OpenAI Models:**
- `openai/gpt-4o` - Latest and most capable
- `openai/gpt-4o-mini` - Faster and cheaper
- `openai/gpt-3.5-turbo` - Good balance of speed/cost

**Anthropic Models:**
- `anthropic/claude-3-5-sonnet-20241022` - Excellent for coding
- `anthropic/claude-3-haiku-20240307` - Fast responses

**Google Models:**
- `google/gemini-1.5-pro` - Long context support
- `google/gemini-1.5-flash` - Fast inference

**Groq (Fast inference):**
- `groq/llama-3.1-70b-versatile` - Good open-source option

### Safety Modes

- **Strict**: Maximum safety, blocks file system and network operations
- **Balanced**: Reasonable safety with warnings for risky operations
- **Permissive**: Minimal restrictions, only blocks truly dangerous code

### Streaming Options

- **Stream Responses**: See responses generated character by character
- **Auto Execute**: Automatically run generated code (use with caution)
- **Require Approval**: Ask before executing suggestions

## 🔧 Advanced Features

### Environment Variables

Control agent behavior via environment variables:

```bash
MARIMO_AGENT_DEFAULT_MODEL=anthropic/claude-3-5-sonnet-20241022
MARIMO_AGENT_AUTO_EXECUTE=false
MARIMO_AGENT_REQUIRE_APPROVAL=true
MARIMO_AGENT_MAX_STEPS=10
MARIMO_AGENT_STREAM_RESPONSES=true
MARIMO_AGENT_SAFETY_MODE=balanced
```

### Custom Models

You can use custom or local models by specifying the full model identifier:

```bash
# Custom OpenAI-compatible endpoint
OPENAI_BASE_URL=https://your-custom-endpoint.com/v1
OPENAI_API_KEY=your-custom-key

# Then use in agent settings:
# Model: openai/your-custom-model-name
```

### WebSocket API

The agent uses WebSocket for real-time communication:

```javascript
// Connect to agent WebSocket
const ws = new WebSocket('ws://localhost:8080/api/agent/stream');

// Send chat message
ws.send(JSON.stringify({
  type: "chat",
  message: "Create a visualization",
  stream: true
}));

// Handle streaming response
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "stream_chunk") {
    console.log(data.chunk); // Real-time text
  }
};
```

## 🛡️ Safety Features

### Code Safety Checking

The agent automatically checks generated code for:

- File system operations (reading/writing files)
- Network requests and API calls
- Shell command execution
- Potentially dangerous imports
- Eval/exec statements

### Safety Warnings

Unsafe code includes warning comments:

```python
# SAFETY WARNING: Network operation detected: requests.get
# NOTE: Consider the security implications
import requests
response = requests.get("https://api.example.com")
```

### Approval Workflows

With "Require Approval" enabled:

1. Agent generates code suggestions
2. User reviews the code
3. User clicks "Apply" to execute
4. Agent provides feedback on results

## 🔍 Troubleshooting

### Common Issues

**"API key not found"**
- Check that environment variables are set correctly
- Verify API key format (should start with proper prefix)
- Restart Marimo server after setting new environment variables

**"Connection error"**
- Check internet connection
- Verify API endpoints are accessible
- Check for rate limiting or quota issues

**"WebSocket disconnected"**
- Network connectivity issues
- Server restart required
- Check browser console for errors

### Debug Mode

Enable detailed logging:

```bash
MARIMO_AGENT_LOG_LEVEL=DEBUG marimo edit
```

### Reset Agent Memory

Clear conversation history:
- Open agent panel
- Use settings menu → Clear Memory
- Or restart the Marimo server

## 📊 Performance Tips

### Model Selection

- **GPT-4o**: Best for complex reasoning and code generation
- **Claude Sonnet**: Excellent for coding tasks and safety
- **GPT-4o-mini**: Faster responses for simple tasks
- **Groq models**: Fastest inference but may be less capable

### Streaming Settings

- Enable streaming for better UX on long responses
- Disable for faster processing of simple requests
- Adjust max tokens based on your needs (512-8192)

### Safety vs Speed

- **Strict mode**: Safest but may block legitimate operations
- **Balanced mode**: Good default with reasonable safety
- **Permissive mode**: Fastest but requires more user vigilance

## 🔗 Integration Examples

### Jupyter Migration

Convert existing Jupyter notebooks:

```bash
marimo convert notebook.ipynb > notebook.py
# Then use agent to enhance/debug the converted code
```

### Data Science Workflow

1. Load data with agent assistance
2. Use agent for exploratory data analysis
3. Generate visualizations and models
4. Get help with interpretation and next steps

### Code Review

- Paste problematic code and ask for debugging help
- Request performance optimizations
- Get suggestions for better practices
- Automated testing recommendations

## 📚 Additional Resources

- [Marimo Documentation](https://docs.marimo.io)
- [Agent API Reference](https://docs.marimo.io/api/agent)
- [Example Notebooks](./examples/)
- [Community Discord](https://discord.gg/marimo)

## 🤝 Contributing

To improve the agent system:

1. Check issues with "agent" label
2. Test with different model providers
3. Suggest new safety features
4. Report bugs or edge cases

---

**Happy coding with your AI-powered Marimo agent! 🚀**