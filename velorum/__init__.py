"""
Velorum - AI Coding Agent
==========================

A production-ready AI coding agent with Human-in-the-Loop support.

Features:
- Multi-model support (OpenAI, Anthropic, Google, Groq, etc.)
- Human-in-the-Loop for write operations
- File operations, code search, command execution
- Interactive chat and single-task modes

Usage:
    from velorum import CodingAgent

    agent = CodingAgent(model="openai:gpt-4o")
    response = agent.run("List all Python files in this directory")
"""

__version__ = "0.1.0"
__author__ = "Danish"

from velorum.agent import (
    CodingAgent,
    create_coding_agent,
    run_coding_agent,
    chat_with_agent,
    get_llm,
    list_supported_models,
    SUPPORTED_PROVIDERS,
)

from velorum.banner import (
    print_banner,
    print_session_header,
    show_splash,
)

from velorum.tools import (
    read_file,
    write_file,
    edit_file,
    list_directory,
    search_codebase,
    run_command,
    get_file_structure,
    CODING_TOOLS,
    READ_ONLY_TOOLS,
    WRITE_TOOLS,
)

__all__ = [
    # Main classes
    "CodingAgent",
    # Functions
    "create_coding_agent",
    "run_coding_agent", 
    "chat_with_agent",
    "get_llm",
    "list_supported_models",
    "print_banner",
    "print_session_header",
    "show_splash",
    # Tools
    "read_file",
    "write_file",
    "edit_file",
    "list_directory",
    "search_codebase",
    "run_command",
    "get_file_structure",
    "CODING_TOOLS",
    "READ_ONLY_TOOLS",
    "WRITE_TOOLS",
    # Config
    "SUPPORTED_PROVIDERS",
]

