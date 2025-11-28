"""
Velorum CLI
===========

Command-line interface for the Velorum AI coding agent.
"""

import os
import sys

from velorum.agent import (
    run_coding_agent,
    chat_with_agent,
    list_supported_models,
)


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]
    
    # Default settings
    workspace = os.getcwd()
    enable_hitl = True
    model = "openai:gpt-4o"
    api_key = None
    
    # Check for help
    if "--help" in args or "-h" in args:
        print_help()
        return
    
    # Check for version
    if "--version" in args or "-v" in args:
        from velorum import __version__
        print(f"Velorum v{__version__}")
        return
    
    # Check for --list-models flag
    if "--list-models" in args or "--models" in args:
        print(list_supported_models())
        return
    
    # Check for --no-hitl flag
    if "--no-hitl" in args:
        enable_hitl = False
        args.remove("--no-hitl")
    
    # Check for --model flag
    for i, arg in enumerate(args):
        if arg == "--model" and i + 1 < len(args):
            model = args[i + 1]
            args.pop(i)
            args.pop(i)
            break
        elif arg.startswith("--model="):
            model = arg.split("=", 1)[1]
            args.remove(arg)
            break
    
    # Check for --api-key flag
    for i, arg in enumerate(args):
        if arg == "--api-key" and i + 1 < len(args):
            api_key = args[i + 1]
            args.pop(i)
            args.pop(i)
            break
        elif arg.startswith("--api-key="):
            api_key = arg.split("=", 1)[1]
            args.remove(arg)
            break
    
    # Check for --workspace flag
    for i, arg in enumerate(args):
        if arg == "--workspace" and i + 1 < len(args):
            workspace = args[i + 1]
            args.pop(i)
            args.pop(i)
            break
        elif arg.startswith("--workspace="):
            workspace = arg.split("=", 1)[1]
            args.remove(arg)
            break
    
    # Process command
    if args:
        if args[0] == "chat":
            # Interactive mode
            ws = args[1] if len(args) > 1 else workspace
            try:
                chat_with_agent(ws, enable_hitl=enable_hitl, model=model, api_key=api_key)
            except (ValueError, ImportError) as e:
                print(f"\n❌ Error: {e}\n")
                print("Use 'velorum --list-models' to see supported providers.")
                sys.exit(1)
        
        elif args[0] == "run":
            # Single task mode with explicit 'run' command
            if len(args) < 2:
                print("Error: Please provide a task description")
                print("Usage: velorum run \"your task here\"")
                sys.exit(1)
            task = " ".join(args[1:])
            try:
                run_coding_agent(task, workspace, enable_hitl=enable_hitl, model=model, api_key=api_key)
            except (ValueError, ImportError) as e:
                print(f"\n❌ Error: {e}\n")
                sys.exit(1)
        
        elif args[0] == "models":
            print(list_supported_models())
        
        else:
            # Treat as task description
            task = " ".join(args)
            try:
                run_coding_agent(task, workspace, enable_hitl=enable_hitl, model=model, api_key=api_key)
            except (ValueError, ImportError) as e:
                print(f"\n❌ Error: {e}\n")
                sys.exit(1)
    else:
        print_help()


def print_help():
    """Print help message."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🚀 VELORUM                                 ║
║              AI Coding Agent                                  ║
╚══════════════════════════════════════════════════════════════╝

USAGE:
    velorum chat [workspace]           Start interactive chat
    velorum run "task description"     Run a single task
    velorum "task description"         Run a single task (shorthand)
    velorum models                     List supported models

OPTIONS:
    --model <provider:model>    Specify LLM model (default: openai:gpt-4o)
    --api-key <key>             API key (or use environment variable)
    --workspace <path>          Working directory (default: current)
    --no-hitl                   Disable Human-in-the-Loop approval
    --list-models               List all supported models
    --help, -h                  Show this help message
    --version, -v               Show version

SUPPORTED PROVIDERS:
    openai      GPT-4o, GPT-4, GPT-3.5       (env: OPENAI_API_KEY)
    anthropic   Claude 3.5, Claude 3         (env: ANTHROPIC_API_KEY)
    google      Gemini 1.5, Gemini 2         (env: GOOGLE_API_KEY)
    groq        Llama 3.3, Mixtral           (env: GROQ_API_KEY)
    mistral     Mistral Large                (env: MISTRAL_API_KEY)
    together    Llama, Mixtral               (env: TOGETHER_API_KEY)
    deepseek    DeepSeek Chat                (env: DEEPSEEK_API_KEY)

EXAMPLES:
    # Start interactive chat
    velorum chat

    # Use a specific model
    velorum --model anthropic:claude-3-5-sonnet-20241022 chat

    # Run a single task
    velorum "List all Python files in this directory"

    # Use Groq for fast inference
    velorum --model groq:llama-3.3-70b-versatile "Explain this code"

    # Disable approval prompts
    velorum --no-hitl "Create a hello.py file"

For more information, visit: https://github.com/your-repo/velorum
""")


if __name__ == "__main__":
    main()

