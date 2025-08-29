#!/usr/bin/env python3
"""Test script for Google Gemini agent integration."""

import marimo

__generated_with = "0.15.0"
app = marimo.App()


@app.cell
def __(mo):
    mo.md(
        r"""
        # 🤖 Google Gemini Agent Test
        
        This notebook tests the Marimo AI Agent with **Google Gemini 2.0 Flash**.
        
        ## Setup Instructions
        
        1. **Get your Google AI API key** (FREE):
           - Visit: https://makersuite.google.com/app/apikey
           - Or: https://aistudio.google.com/app/apikey
           - Click "Create API key"
        
        2. **Set the API key**:
           ```bash
           export GOOGLE_AI_API_KEY="your-key-here"
           ```
           Or create a `.env` file with:
           ```
           GOOGLE_AI_API_KEY=your-key-here
           ```
        
        3. **Start Marimo**:
           ```bash
           marimo edit test_gemini_agent.py
           ```
        """
    )
    return


@app.cell
def __():
    import marimo as mo
    import os
    import pandas as pd
    import numpy as np
    return mo, np, os, pd


@app.cell
def __(mo, os):
    # Check API key status
    api_key_set = bool(os.getenv("GOOGLE_AI_API_KEY"))
    
    if api_key_set:
        mo.md("""
        ✅ **Google AI API key is configured!**
        
        The agent is ready to use with Gemini models.
        """).callout(kind="success")
    else:
        mo.md("""
        ⚠️ **Google AI API key not found!**
        
        Please set your GOOGLE_AI_API_KEY environment variable:
        ```bash
        export GOOGLE_AI_API_KEY="your-key-here"
        ```
        
        Get a free key at: https://makersuite.google.com/app/apikey
        """).callout(kind="warn")
    return api_key_set,


@app.cell
def __(mo):
    mo.md(
        r"""
        ## Sample Data for Testing
        
        Let's create a sample dataset that the agent can work with:
        """
    )
    return


@app.cell
def __(mo, np, pd):
    # Create sample sales data
    np.random.seed(42)
    
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    products = ['Widget A', 'Widget B', 'Widget C', 'Gadget X', 'Gadget Y']
    regions = ['North', 'South', 'East', 'West']
    
    sales_data = {
        'date': np.repeat(dates, 5),
        'product': np.tile(products, 100),
        'region': np.random.choice(regions, 500),
        'units_sold': np.random.randint(10, 100, 500),
        'revenue': np.random.uniform(100, 1000, 500).round(2),
        'cost': np.random.uniform(50, 500, 500).round(2),
    }
    
    df = pd.DataFrame(sales_data)
    df['profit'] = df['revenue'] - df['cost']
    df['profit_margin'] = (df['profit'] / df['revenue'] * 100).round(2)
    
    mo.md(f"""
    **Sample Sales Dataset Created:**
    - Shape: {df.shape}
    - Columns: {', '.join(df.columns)}
    - Date range: {df['date'].min().date()} to {df['date'].max().date()}
    - Products: {', '.join(df['product'].unique())}
    - Regions: {', '.join(df['region'].unique())}
    
    First few rows:
    {df.head()}
    """)
    return dates, df, products, regions, sales_data


@app.cell
def __(mo):
    mo.md(
        r"""
        ## 🧪 Test the Gemini Agent
        
        **Click the bot icon (🤖) in the bottom-right corner to open the agent panel.**
        
        The agent should show:
        - **Connected (Gemini 2.0 Flash)** status
        - Streaming responses as text appears
        
        ### Try These Prompts:
        
        #### 📊 Data Analysis:
        - "Show me summary statistics for the revenue column"
        - "What's the average profit margin by product?"
        - "Find the top 5 days with highest revenue"
        - "Calculate total sales by region"
        
        #### 📈 Visualizations:
        - "Create a line chart of revenue over time"
        - "Make a bar chart comparing profit margins by product"
        - "Show me a heatmap of sales by region and product"
        - "Create a scatter plot of revenue vs profit with color by region"
        
        #### 🔧 Data Manipulation:
        - "Add a column for revenue per unit (revenue/units_sold)"
        - "Create a function to categorize products as high/medium/low margin"
        - "Filter the data to show only profitable sales"
        - "Group by month and calculate monthly totals"
        
        #### 💡 Advanced Analysis:
        - "Perform a comprehensive analysis of this sales data including trends, patterns, and actionable insights"
        - "Build a simple forecast model for next month's revenue"
        - "Identify which product-region combinations are most profitable"
        - "Create an interactive dashboard to explore the data"
        
        ### Expected Behavior:
        
        1. **Streaming**: You should see the response appear character-by-character
        2. **Context Aware**: The agent knows about the `df` variable
        3. **Code Generation**: Generated code should work immediately
        4. **Safety**: Any risky operations should show warnings
        
        ### Troubleshooting:
        
        - **"Disconnected" status**: Check your API key is set correctly
        - **No streaming**: Ensure "Stream Responses" is enabled in settings
        - **Errors**: Check the browser console (F12) for details
        - **Model not found**: Try using `google/gemini-1.5-flash` instead
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        r"""
        ## 🎯 Testing Gemini-Specific Features
        
        Google Gemini models have some unique capabilities:
        
        1. **Long Context**: Can handle up to 1M tokens
        2. **Fast Inference**: Gemini Flash models are optimized for speed
        3. **Multimodal**: Can process text, code, and images (in supported versions)
        4. **Free Tier**: Generous free API limits
        
        ### Performance Comparison:
        
        | Model | Speed | Quality | Cost |
        |-------|-------|---------|------|
        | Gemini 2.0 Flash | ⚡⚡⚡ | ⭐⭐⭐ | Free* |
        | Gemini 1.5 Flash | ⚡⚡⚡ | ⭐⭐ | Free* |
        | Gemini 1.5 Flash-8B | ⚡⚡⚡⚡ | ⭐⭐ | Free* |
        | Gemini 1.5 Pro | ⚡⚡ | ⭐⭐⭐⭐ | Free* |
        
        *Free tier has rate limits
        
        ### Custom Model Test:
        
        You can also test custom model names using the settings panel:
        1. Click Settings in the agent panel
        2. Select "Custom Model..."
        3. Enter: `google/gemini-2.0-flash-001` or any other variant
        4. The agent will use your custom model
        """
    )
    return


@app.cell
def __(mo):
    # Create an info box with current configuration
    mo.md("""
    ## Current Configuration
    
    ```python
    # Agent is configured to use:
    Provider: Google Gemini
    Default Model: gemini-2.0-flash-exp
    Streaming: Enabled
    Safety Mode: Balanced
    Auto Execute: Disabled
    
    # To change settings:
    # 1. Open agent panel (bot icon)
    # 2. Click settings gear
    # 3. Adjust as needed
    ```
    """).callout(kind="info")
    return


if __name__ == "__main__":
    app.run()