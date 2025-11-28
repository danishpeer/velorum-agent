# 🚀 Velorum

**AI Coding Agent with Human-in-the-Loop Support**

Velorum is a production-ready AI coding agent built with LangGraph that can read, write, and edit files, search codebases, and execute commands — with human approval for sensitive operations.

## ✨ Features

- 🧠 **Multi-Model Support** - OpenAI, Anthropic, Google, Groq, Mistral, and more
- 🛡️ **Human-in-the-Loop** - Approval required for write operations
- 📁 **File Operations** - Read, write, edit files with safety checks
- 🔍 **Code Search** - Grep-like search across your codebase
- ⚡ **Command Execution** - Run shell commands with dangerous pattern blocking
- 💬 **Interactive Chat** - Conversational interface with memory
- 🎡 **Progress Indicators** - Spinners and status updates

## 📦 Installation

```bash
# Basic installation (OpenAI support)
pip install velorum

# With Anthropic support
pip install velorum[anthropic]

# With all providers
pip install velorum[all]
```

## 🚀 Quick Start

### Command Line

```bash
# Start interactive chat
velorum chat

# Run a single task
velorum "List all Python files and summarize them"

# Use a specific model
velorum --model anthropic:claude-3-5-sonnet-20241022 chat

# Use Groq for fast inference
velorum --model groq:llama-3.3-70b-versatile "Explain this code"

# Disable approval prompts
velorum --no-hitl "Create a hello.py file"
```

### Python API

```python
from velorum import CodingAgent

# Create an agent
agent = CodingAgent(model="openai:gpt-4o")

# Run a task
response = agent.run("List all Python files in this directory")

# Start interactive chat
agent.chat()
```

### Using Different Models

```python
from velorum import CodingAgent

# OpenAI
agent = CodingAgent(model="openai:gpt-4o")

# Anthropic Claude
agent = CodingAgent(model="anthropic:claude-3-5-sonnet-20241022")

# Google Gemini
agent = CodingAgent(model="google:gemini-1.5-pro")

# Groq (fast inference)
agent = CodingAgent(model="groq:llama-3.3-70b-versatile")

# With custom API key
agent = CodingAgent(
    model="openai:gpt-4o",
    api_key="sk-..."
)
```

## 🔧 Supported Providers

| Provider | Environment Variable | Example Models |
|----------|---------------------|----------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o`, `gpt-4o-mini`, `o1` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229` |
| Google | `GOOGLE_API_KEY` | `gemini-1.5-pro`, `gemini-2.0-flash-exp` |
| Groq | `GROQ_API_KEY` | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768` |
| Mistral | `MISTRAL_API_KEY` | `mistral-large-latest`, `codestral-latest` |
| Together | `TOGETHER_API_KEY` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat`, `deepseek-reasoner` |

List all models:
```bash
velorum --list-models
```

## 🛡️ Human-in-the-Loop

By default, Velorum requires human approval for operations that modify files or run commands:

**Auto-approved (Read-only):**
- `read_file` - Read file contents
- `list_directory` - List directory contents
- `search_codebase` - Search for patterns
- `get_file_structure` - Get directory tree

**Requires Approval:**
- `write_file` - Create or overwrite files
- `edit_file` - Modify existing files
- `run_command` - Execute shell commands

Disable with `--no-hitl` or `enable_hitl=False`.

## 📖 Advanced Usage

### Low-level API

```python
from velorum import create_coding_agent, get_llm, CODING_TOOLS

# Create a custom LLM
llm = get_llm("anthropic:claude-3-5-sonnet-20241022", temperature=0.5)

# Create the agent graph
agent = create_coding_agent(
    model="openai:gpt-4o",
    enable_hitl=True,
    enable_memory=True
)

# Stream responses
from langchain_core.messages import HumanMessage

config = {"configurable": {"thread_id": "my-session"}}
for event in agent.stream(
    {"messages": [HumanMessage(content="Hello!")]},
    config,
    stream_mode="values"
):
    print(event)
```

### Custom Tools

```python
from langchain_core.tools import tool
from velorum import create_coding_agent, CODING_TOOLS

@tool
def my_custom_tool(query: str) -> str:
    """My custom tool description."""
    return f"Result for: {query}"

# Add to existing tools
all_tools = CODING_TOOLS + [my_custom_tool]
```

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│                 VELORUM AGENT                    │
├──────────────────────────────────────────────────┤
│                                                  │
│   START → AGENT → should_continue?              │
│              │         │                        │
│              │    ┌────┴────┐                   │
│              │    ▼         ▼                   │
│              │  READ     WRITE                  │
│              │  TOOLS    TOOLS                  │
│              │    │         │                   │
│              │    │    HUMAN APPROVAL           │
│              │    │         │                   │
│              │    └────┬────┘                   │
│              │         ▼                        │
│              └──── TOOLS NODE ──→ END           │
│                                                  │
└──────────────────────────────────────────────────┘
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

