# Copyright 2024 Marimo. All rights reserved.
"""Safety checks and controls for agent operations."""

from __future__ import annotations

import ast
import re
from typing import List, Optional, Set, Tuple

from marimo import _loggers

LOGGER = _loggers.marimo_logger()

# Dangerous operations that should be controlled
DANGEROUS_IMPORTS = {
    "os",
    "subprocess", 
    "sys",
    "shutil",
    "pathlib",
    "glob",
    "socket",
    "urllib",
    "requests",
    "http",
    "ftplib",
    "smtplib",
    "telnetlib",
    "webbrowser",
}

DANGEROUS_FUNCTIONS = {
    "exec",
    "eval", 
    "compile",
    "__import__",
    "open",
    "input",
    "raw_input",
    "exit",
    "quit",
}

FILE_OPERATIONS = {
    "open",
    "read", 
    "write",
    "remove",
    "delete",
    "unlink",
    "rmdir",
    "mkdir",
    "makedirs",
}

NETWORK_OPERATIONS = {
    "urlopen",
    "request",
    "get",
    "post",
    "put",
    "delete",
    "connect",
    "send",
    "recv",
}


class SafetyChecker:
    """Checks code for potentially dangerous operations."""
    
    def __init__(self, safety_mode: str = "balanced"):
        """Initialize safety checker.
        
        Args:
            safety_mode: "strict", "balanced", or "permissive"
        """
        self.safety_mode = safety_mode
        
    def check_code(self, code: str) -> Tuple[bool, List[str]]:
        """Check code for safety issues.
        
        Args:
            code: Python code to check
            
        Returns:
            Tuple of (is_safe, list_of_warnings)
        """
        warnings = []
        
        try:
            # Parse the code to check for dangerous patterns
            tree = ast.parse(code)
            visitor = SafetyVisitor(self.safety_mode)
            visitor.visit(tree)
            warnings.extend(visitor.warnings)
            
        except SyntaxError as e:
            warnings.append(f"Syntax error in code: {e}")
            
        # Additional regex-based checks for patterns that might be missed
        regex_warnings = self._check_regex_patterns(code)
        warnings.extend(regex_warnings)
        
        # Determine if code is safe based on safety mode
        is_safe = self._is_code_safe(warnings)
        
        return is_safe, warnings
    
    def _check_regex_patterns(self, code: str) -> List[str]:
        """Check for dangerous patterns using regex."""
        warnings = []
        
        # Check for shell command execution
        shell_patterns = [
            r'os\.system\s*\(',
            r'subprocess\.(run|call|check_output|Popen)',
            r'!\s*[a-zA-Z]',  # Shell commands in notebooks
        ]
        
        for pattern in shell_patterns:
            if re.search(pattern, code):
                warnings.append(f"Potential shell command execution detected: {pattern}")
        
        # Check for file system operations
        if self.safety_mode == "strict":
            file_patterns = [
                r'open\s*\(',
                r'with\s+open\s*\(',
                r'\.write\s*\(',
                r'\.read\s*\(',
                r'os\.remove\s*\(',
                r'shutil\.',
            ]
            
            for pattern in file_patterns:
                if re.search(pattern, code):
                    warnings.append(f"File system operation detected: {pattern}")
        
        # Check for network operations
        if self.safety_mode in ["strict", "balanced"]:
            network_patterns = [
                r'requests\.',
                r'urllib\.',
                r'http\.',
                r'socket\.',
                r'urlopen\s*\(',
            ]
            
            for pattern in network_patterns:
                if re.search(pattern, code):
                    warnings.append(f"Network operation detected: {pattern}")
        
        return warnings
    
    def _is_code_safe(self, warnings: List[str]) -> bool:
        """Determine if code is safe based on warnings and safety mode."""
        if not warnings:
            return True
            
        if self.safety_mode == "permissive":
            # Only block truly dangerous operations
            dangerous_keywords = ["system", "exec", "eval", "__import__"]
            for warning in warnings:
                if any(keyword in warning.lower() for keyword in dangerous_keywords):
                    return False
            return True
            
        elif self.safety_mode == "balanced":
            # Block moderate risk operations
            return len(warnings) == 0
            
        else:  # strict
            # Block anything that raises a warning
            return False
    
    def get_safety_prompt_addition(self) -> str:
        """Get additional prompt text based on safety mode."""
        if self.safety_mode == "strict":
            return (
                "\n\nIMPORTANT SAFETY GUIDELINES:\n"
                "- Do not generate code that accesses the file system\n"
                "- Do not generate code that makes network requests\n"
                "- Do not generate code that executes shell commands\n"
                "- Focus on data analysis and visualization only\n"
                "- Use only safe, read-only operations"
            )
        elif self.safety_mode == "balanced":
            return (
                "\n\nSAFETY GUIDELINES:\n"
                "- Avoid shell command execution unless specifically requested\n"
                "- Be cautious with file system operations\n"
                "- Prefer safe data manipulation and analysis operations\n"
                "- Ask for confirmation before risky operations"
            )
        else:  # permissive
            return (
                "\n\nGENERAL SAFETY:\n"
                "- Be thoughtful about potentially destructive operations\n"
                "- Consider the security implications of generated code"
            )


class SafetyVisitor(ast.NodeVisitor):
    """AST visitor to check for dangerous operations."""
    
    def __init__(self, safety_mode: str):
        self.safety_mode = safety_mode
        self.warnings = []
        self.imported_modules = set()
        
    def visit_Import(self, node: ast.Import) -> None:
        """Check import statements."""
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            self.imported_modules.add(module_name)
            
            if module_name in DANGEROUS_IMPORTS:
                self.warnings.append(f"Potentially dangerous import: {module_name}")
                
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check from X import Y statements."""
        if node.module:
            module_name = node.module.split('.')[0]
            self.imported_modules.add(module_name)
            
            if module_name in DANGEROUS_IMPORTS:
                self.warnings.append(f"Potentially dangerous import from: {module_name}")
                
        self.generic_visit(node)
        
    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls."""
        func_name = None
        
        # Extract function name
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            
        if func_name and func_name in DANGEROUS_FUNCTIONS:
            self.warnings.append(f"Potentially dangerous function call: {func_name}")
            
        # Check for specific dangerous patterns
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                if module_name == "os" and func_name == "system":
                    self.warnings.append("Shell command execution via os.system()")
                elif module_name == "subprocess":
                    self.warnings.append(f"Subprocess call: subprocess.{func_name}()")
                    
        self.generic_visit(node)
        
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check attribute access."""
        if isinstance(node.value, ast.Name):
            if node.value.id in self.imported_modules:
                if node.attr in FILE_OPERATIONS and self.safety_mode == "strict":
                    self.warnings.append(f"File operation: {node.value.id}.{node.attr}")
                elif node.attr in NETWORK_OPERATIONS and self.safety_mode in ["strict", "balanced"]:
                    self.warnings.append(f"Network operation: {node.value.id}.{node.attr}")
                    
        self.generic_visit(node)


def create_safety_checker(safety_mode: str = "balanced") -> SafetyChecker:
    """Create a safety checker with the specified mode.
    
    Args:
        safety_mode: "strict", "balanced", or "permissive"
        
    Returns:
        SafetyChecker instance
    """
    return SafetyChecker(safety_mode)


def check_code_safety(code: str, safety_mode: str = "balanced") -> Tuple[bool, List[str]]:
    """Quick function to check code safety.
    
    Args:
        code: Python code to check
        safety_mode: Safety mode to use
        
    Returns:
        Tuple of (is_safe, warnings)
    """
    checker = create_safety_checker(safety_mode)
    return checker.check_code(code)