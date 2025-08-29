# Marimo - Reactive Python Notebook

## Overview

Marimo is a reactive Python notebook that's reproducible, git-friendly, and deployable as scripts or apps. It's a modern alternative to Jupyter notebooks with a focus on reactivity, reproducibility, and interactivity.

## Core Features

- **Reactive Programming**: Automatically updates dependent cells when inputs change
- **Git-Friendly**: Notebooks are stored as pure Python files
- **Interactive UI**: Built-in UI components that bind to Python without callbacks
- **Deployable**: Can be executed as scripts or deployed as web apps
- **SQL Support**: First-class SQL cells that integrate with Python
- **AI-Native**: Code generation capabilities tailored for data work
- **Testing Support**: Run pytest on notebooks
- **Package Management**: Built-in dependency management with uv

## Codebase Structure

### Backend (Python)
- `marimo/`: Main Python package
  - `_ast/`: Abstract syntax tree handling for cell dependencies
  - `_cli/`: Command-line interface
  - `_config/`: Configuration management
  - `_runtime/`: Execution runtime and dataflow engine
  - `_server/`: Web server (Starlette/Uvicorn based)
  - `_plugins/`: UI component plugins
  - `_sql/`: SQL cell implementation
  - `_output/`: Output formatting and display
  - `_messaging/`: WebSocket messaging system
  - `_save/`: Caching and persistence
  - `_ai/`: AI/LLM integration for code generation

### Frontend (TypeScript/React)
- `frontend/`: React-based web interface
  - `src/core/`: Core functionality (cells, network, runtime)
  - `src/components/`: React components
  - `src/plugins/`: UI plugin implementations
  - `src/utils/`: Utility functions
  - `src/hooks/`: React hooks

### Key Technologies

#### Backend Dependencies
- **Web Framework**: Starlette + Uvicorn
- **Code Analysis**: Jedi (code completion), AST parsing
- **Markdown**: markdown + pymdown-extensions + pygments
- **Data**: narwhals (dataframe abstraction), DuckDB (SQL)
- **Config**: tomlkit, pyyaml
- **System**: psutil (resource monitoring)

#### Frontend Dependencies
- **Framework**: React 18 with TypeScript
- **Editor**: CodeMirror 6 with Python/SQL support
- **UI Components**: Radix UI, Tailwind CSS
- **State Management**: Zustand, Jotai
- **Visualization**: Plotly, Vega-Lite
- **Data Grid**: Glide Data Grid
- **Build Tools**: Vite, pnpm, Turbo

## Architecture

### Reactive Execution Model
1. Cells are Python code blocks with dependency tracking
2. AST analysis determines variable dependencies between cells
3. When a cell runs, dependent cells automatically re-execute
4. Dataflow graph ensures consistent state

### Client-Server Communication
- WebSocket connection for bidirectional communication
- JSON-RPC style message passing
- Operations include: run_cell, interrupt, code_completion, etc.

### Cell Lifecycle
1. Parse cell code and extract dependencies
2. Check for cycles in dependency graph
3. Execute cells in topological order
4. Stream outputs back to frontend
5. Update UI state reactively

## Telemetry & Analytics Status

### Documentation Website
- **PostHog Analytics**: Active on docs.marimo.io
- **Kapa AI Widget**: Chat support with analytics

### Application Core
- **No User Tracking**: Main application has no telemetry
- **Local Tracing Only**: OpenTelemetry for development (disabled by default)
- **Privacy-First**: All data stays local to user's machine

## Development Workflow

### Setup
```bash
# Install dependencies
pip install -e ".[dev]"
pnpm install

# Run development server
marimo edit --sandbox

# Run frontend dev server
pnpm run dev
```

### Testing
```bash
# Python tests
pytest

# Frontend tests
pnpm test

# E2E tests
pnpm run e2e
```

### Build
```bash
# Build frontend
pnpm run build

# Build Python package
python -m build
```

## Key Files

- `marimo/_server/main.py`: Server entry point
- `marimo/_runtime/runtime.py`: Execution engine
- `marimo/_ast/visitor.py`: Dependency analysis
- `frontend/src/core/cells/cells.ts`: Cell management
- `frontend/src/components/editor/cell/`: Cell UI components

## Configuration

User configuration stored in `~/.marimo/marimo.toml`:
- Completion settings (copilot, codeium)
- Formatting preferences
- Runtime options
- UI theme

## Security Considerations

- CSRF protection via server tokens
- Sandboxed execution option available
- No external data transmission (except docs site)
- Local-only file access