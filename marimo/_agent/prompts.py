# Copyright 2024 Marimo. All rights reserved.
"""System prompts and templates for agent LLM interactions."""

from typing import Dict, List, Optional

from marimo._agent.models import AgentMessage, NotebookContext


SYSTEM_PROMPT = """You are an AI assistant integrated into Marimo, a reactive Python notebook. 
Your role is to help users write, execute, and debug Python code in their notebooks.

Key capabilities:
1. Generate Python code based on natural language requests
2. Modify existing cells based on user instructions
3. Analyze data and suggest visualizations
4. Debug errors and propose fixes
5. Explain code and provide documentation

Important context about Marimo:
- Cells automatically re-run when their dependencies change (reactive)
- Variables are shared across all cells
- The notebook is stored as a pure Python file
- UI elements can be created with mo.ui components
- SQL cells are supported with mo.sql

When generating code:
- Write clean, readable Python code
- Use appropriate variable names
- Add brief comments for complex logic
- Import necessary libraries at the cell level
- Consider the reactive nature of the notebook

When suggesting modifications:
- Preserve existing variable names when possible
- Maintain compatibility with dependent cells
- Explain the changes being made

Always be helpful, accurate, and concise in your responses."""


CODE_GENERATION_PROMPT = """Generate Python code for the following request:
{request}

Current notebook context:
- Active variables: {variables}
- Recent cells: {recent_cells}

Requirements:
- Write complete, executable Python code
- Include necessary imports
- Use descriptive variable names
- Add comments for clarity
- Consider existing variables in scope"""


CODE_MODIFICATION_PROMPT = """Modify the following Python code based on the user's request:

Current code:
```python
{current_code}
```

User request: {request}

Requirements:
- Preserve functionality unless explicitly asked to change
- Maintain variable names that other cells might depend on
- Explain what changes were made
- Keep the code style consistent"""


DATA_ANALYSIS_PROMPT = """Analyze the data and provide insights:

Available data: {data_info}
User request: {request}

Provide:
1. Summary statistics or key findings
2. Python code to perform the analysis
3. Suggestions for visualizations
4. Any data quality issues noticed"""


DEBUGGING_PROMPT = """Debug the following error:

Error message:
{error_message}

Code that caused the error:
```python
{error_code}
```

Context: {context}

Provide:
1. Explanation of what caused the error
2. Fixed code
3. Tips to avoid similar errors"""


VISUALIZATION_PROMPT = """Create a visualization based on the request:

Data available: {data_info}
Request: {request}

Generate Python code that:
1. Creates the requested visualization
2. Uses appropriate library (matplotlib, plotly, altair, etc.)
3. Includes proper labels and formatting
4. Handles edge cases in the data"""


def build_code_generation_prompt(
    request: str,
    context: Optional[NotebookContext] = None,
) -> str:
    """Build a prompt for code generation.
    
    Args:
        request: User's request
        context: Current notebook context
        
    Returns:
        Formatted prompt string
    """
    variables = []
    recent_cells = []
    
    if context:
        if context.variables:
            variables = list(context.variables.keys())[:10]  # Limit to 10 vars
        if context.cell_codes:
            # Get last 3 cells
            for cell_id in list(context.execution_history[-3:]):
                if cell_id in context.cell_codes:
                    code = context.cell_codes[cell_id]
                    # Truncate long code
                    if len(code) > 200:
                        code = code[:200] + "..."
                    recent_cells.append(code)
    
    return CODE_GENERATION_PROMPT.format(
        request=request,
        variables=", ".join(variables) if variables else "None",
        recent_cells="\n\n".join(recent_cells) if recent_cells else "None",
    )


def build_modification_prompt(
    request: str,
    current_code: str,
) -> str:
    """Build a prompt for code modification.
    
    Args:
        request: User's modification request
        current_code: Current cell code
        
    Returns:
        Formatted prompt string
    """
    return CODE_MODIFICATION_PROMPT.format(
        current_code=current_code,
        request=request,
    )


def build_debugging_prompt(
    error_message: str,
    error_code: str,
    context: Optional[Dict] = None,
) -> str:
    """Build a prompt for debugging.
    
    Args:
        error_message: The error message
        error_code: Code that caused the error
        context: Additional context
        
    Returns:
        Formatted prompt string
    """
    context_str = str(context) if context else "No additional context"
    
    return DEBUGGING_PROMPT.format(
        error_message=error_message,
        error_code=error_code,
        context=context_str,
    )


def build_analysis_prompt(
    request: str,
    data_info: Dict,
) -> str:
    """Build a prompt for data analysis.
    
    Args:
        request: Analysis request
        data_info: Information about available data
        
    Returns:
        Formatted prompt string
    """
    return DATA_ANALYSIS_PROMPT.format(
        data_info=str(data_info),
        request=request,
    )


def build_visualization_prompt(
    request: str,
    data_info: Dict,
) -> str:
    """Build a prompt for visualization.
    
    Args:
        request: Visualization request
        data_info: Information about available data
        
    Returns:
        Formatted prompt string
    """
    return VISUALIZATION_PROMPT.format(
        data_info=str(data_info),
        request=request,
    )


def format_conversation_for_llm(
    messages: List[AgentMessage],
    system_prompt: str = SYSTEM_PROMPT,
) -> List[Dict[str, str]]:
    """Format conversation history for LLM input.
    
    Args:
        messages: List of agent messages
        system_prompt: System prompt to prepend
        
    Returns:
        List of formatted messages
    """
    formatted = [{"role": "system", "content": system_prompt}]
    
    for msg in messages:
        formatted.append({
            "role": msg.role.value,
            "content": msg.content,
        })
    
    return formatted


def extract_code_from_response(response: str) -> Optional[str]:
    """Extract Python code from LLM response.
    
    Args:
        response: LLM response text
        
    Returns:
        Extracted code or None
    """
    # Look for code blocks
    import re
    
    # Try to find ```python blocks first
    python_blocks = re.findall(r'```python\n(.*?)\n```', response, re.DOTALL)
    if python_blocks:
        return python_blocks[0]
    
    # Try generic code blocks
    code_blocks = re.findall(r'```\n(.*?)\n```', response, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    
    # If no code blocks, check if the entire response looks like code
    lines = response.strip().split('\n')
    if lines and any(
        line.strip().startswith(keyword)
        for line in lines
        for keyword in ['import ', 'from ', 'def ', 'class ', 'if ', 'for ', 'while ']
    ):
        return response.strip()
    
    return None