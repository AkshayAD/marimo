#!/bin/bash
# Quick Start Script for Marimo AI Agent with Google Gemini

set -e

echo "🚀 Marimo AI Agent Quick Start Setup"
echo "===================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Check for Google API key
if [ -z "$GOOGLE_AI_API_KEY" ]; then
    echo ""
    echo "🔑 Google AI API Key Setup"
    echo "-------------------------"
    echo "You need a Google AI API key to use the agent."
    echo ""
    echo "Get your FREE key at:"
    echo "👉 https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Enter your Google AI API key: " api_key
    
    if [ ! -z "$api_key" ]; then
        # Update .env file
        sed -i.bak "s/GOOGLE_AI_API_KEY=.*/GOOGLE_AI_API_KEY=$api_key/" .env
        # Also export for current session
        export GOOGLE_AI_API_KEY=$api_key
        echo "✅ API key configured!"
    else
        echo "⚠️  No API key provided. You'll need to set it manually in .env"
    fi
else
    echo "✅ Google AI API key already configured"
fi

# Check Python version
echo ""
echo "🐍 Checking Python installation..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version | cut -d' ' -f2)
    echo "✅ Python $python_version found"
else
    echo "❌ Python 3 not found. Please install Python 3.9 or later."
    exit 1
fi

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo ""
    echo "🔧 Setting up virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Virtual environment created"
    fi
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Install/upgrade pip
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1

# Install Marimo and AI dependencies
echo "Installing Marimo..."
pip install -e ".[recommended]" > /dev/null 2>&1 || pip install marimo[recommended]

echo "Installing AI providers..."
pip install google-genai > /dev/null 2>&1 || pip install google-generativeai
pip install openai anthropic groq > /dev/null 2>&1 || true

echo "✅ Dependencies installed"

# Check Node.js for frontend
echo ""
echo "🎨 Checking frontend setup..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "✅ Node.js $node_version found"
    
    # Install pnpm if needed
    if ! command -v pnpm &> /dev/null; then
        echo "Installing pnpm..."
        npm install -g pnpm > /dev/null 2>&1
    fi
    
    # Install frontend dependencies
    if [ -f "pnpm-lock.yaml" ]; then
        echo "Installing frontend dependencies..."
        pnpm install > /dev/null 2>&1
        echo "✅ Frontend dependencies installed"
    fi
else
    echo "⚠️  Node.js not found. Frontend development features may be limited."
fi

# Create test notebook if it doesn't exist
if [ ! -f "test_gemini_agent.py" ]; then
    echo ""
    echo "📓 Test notebook already exists"
fi

# Final instructions
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "To start Marimo with the AI Agent:"
echo ""
echo "  marimo edit test_gemini_agent.py"
echo ""
echo "Or create a new notebook:"
echo ""
echo "  marimo edit my_notebook.py"
echo ""
echo "The agent will use Google Gemini 2.0 Flash by default."
echo "Click the bot icon (🤖) in the bottom-right to open the agent."
echo ""
echo "Happy coding with your AI assistant! 🚀"

# Optionally start Marimo
echo ""
read -p "Would you like to start Marimo now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting Marimo..."
    marimo edit test_gemini_agent.py
fi