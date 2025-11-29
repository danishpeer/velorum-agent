"""
Velorum Agent
=============

Main agent module with LLM configuration and StateGraph implementation.
"""

import os
import sys
import threading
import itertools
import time
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.language_models.chat_models import BaseChatModel

from velorum.tools import CODING_TOOLS, READ_ONLY_TOOLS, WRITE_TOOLS
from velorum.banner import print_banner, print_session_header, show_splash


# =============================================================================
# LLM PROVIDER CONFIGURATION
# =============================================================================

SUPPORTED_PROVIDERS = {
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1", "o1-mini", "o1-preview"],
        "default_model": "gpt-4o",
    },
    "anthropic": {
        "env_key": "ANTHROPIC_API_KEY",
        "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "default_model": "claude-sonnet-4-20250514",
    },
    "google": {
        "env_key": "GOOGLE_API_KEY",
        "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-pro"],
        "default_model": "gemini-1.5-pro",
    },
    "groq": {
        "env_key": "GROQ_API_KEY",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
        "default_model": "llama-3.3-70b-versatile",
    },
    "together": {
        "env_key": "TOGETHER_API_KEY",
        "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo", "mistralai/Mixtral-8x22B-Instruct-v0.1"],
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    },
    "fireworks": {
        "env_key": "FIREWORKS_API_KEY",
        "models": ["accounts/fireworks/models/llama-v3p1-70b-instruct", "accounts/fireworks/models/mixtral-8x22b-instruct"],
        "default_model": "accounts/fireworks/models/llama-v3p1-70b-instruct",
    },
    "mistral": {
        "env_key": "MISTRAL_API_KEY",
        "models": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "codestral-latest"],
        "default_model": "mistral-large-latest",
    },
    "deepseek": {
        "env_key": "DEEPSEEK_API_KEY",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "default_model": "deepseek-chat",
    },
}


def get_llm(
    model: str = "openai:gpt-4o",
    temperature: float = 0,
    api_key: Optional[str] = None,
) -> BaseChatModel:
    """
    Get an LLM instance based on the model string.
    
    Args:
        model: Model string in format "provider:model_name" or "provider/model_name"
               Examples: "openai:gpt-4o", "anthropic:claude-3-5-sonnet-20241022"
        temperature: Model temperature (0-1)
        api_key: Optional API key (if not provided, uses environment variable)
    
    Returns:
        Configured LLM instance
    
    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    # Parse model string
    if ":" in model:
        provider, model_name = model.split(":", 1)
    elif "/" in model and model.split("/")[0] in SUPPORTED_PROVIDERS:
        provider, model_name = model.split("/", 1)
    elif model in SUPPORTED_PROVIDERS:
        provider = model
        model_name = SUPPORTED_PROVIDERS[provider]["default_model"]
    else:
        provider = "openai"
        model_name = model
    
    provider = provider.lower()
    
    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(SUPPORTED_PROVIDERS.keys())
        raise ValueError(f"Unsupported provider: {provider}. Supported: {supported}")
    
    config = SUPPORTED_PROVIDERS[provider]
    if api_key is None:
        api_key = os.getenv(config["env_key"])
    
    if not api_key:
        raise ValueError(
            f"API key required for {provider}. "
            f"Set {config['env_key']} environment variable or pass api_key parameter."
        )
    
    try:
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)
        
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=model_name, temperature=temperature, api_key=api_key)
        
        elif provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=api_key)
        
        elif provider == "groq":
            from langchain_groq import ChatGroq
            return ChatGroq(model=model_name, temperature=temperature, api_key=api_key)
        
        elif provider == "together":
            from langchain_together import ChatTogether
            return ChatTogether(model=model_name, temperature=temperature, api_key=api_key)
        
        elif provider == "fireworks":
            from langchain_fireworks import ChatFireworks
            return ChatFireworks(model=model_name, temperature=temperature, api_key=api_key)
        
        elif provider == "mistral":
            from langchain_mistralai import ChatMistralAI
            return ChatMistralAI(model=model_name, temperature=temperature, api_key=api_key)
        
        elif provider == "deepseek":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_name, temperature=temperature, api_key=api_key,
                base_url="https://api.deepseek.com/v1"
            )
        
        else:
            raise ValueError(f"Provider {provider} not implemented")
    
    except ImportError as e:
        package_map = {
            "openai": "langchain-openai",
            "anthropic": "langchain-anthropic",
            "google": "langchain-google-genai",
            "groq": "langchain-groq",
            "together": "langchain-together",
            "fireworks": "langchain-fireworks",
            "mistral": "langchain-mistralai",
        }
        package = package_map.get(provider, f"langchain-{provider}")
        raise ImportError(f"Install with: pip install {package}\nOriginal error: {e}")


def resolve_model_string(model: str) -> str:
    """
    Resolve a model string to its full 'provider:model_name' format.
    
    Args:
        model: Model string (e.g., "openai", "openai:gpt-4o", "gpt-4o")
    
    Returns:
        Full model string in 'provider:model_name' format
    """
    if ":" in model:
        provider, model_name = model.split(":", 1)
    elif "/" in model and model.split("/")[0] in SUPPORTED_PROVIDERS:
        provider, model_name = model.split("/", 1)
    elif model in SUPPORTED_PROVIDERS:
        provider = model
        model_name = SUPPORTED_PROVIDERS[provider]["default_model"]
    else:
        provider = "openai"
        model_name = model
    
    return f"{provider}:{model_name}"


def list_supported_models() -> str:
    """Return a formatted string listing all supported providers and models."""
    lines = ["Supported LLM Providers and Models:", "=" * 50]
    
    for provider, config in SUPPORTED_PROVIDERS.items():
        env_key = config["env_key"]
        has_key = "✅" if os.getenv(env_key) else "❌"
        lines.append(f"\n{provider.upper()} {has_key} (env: {env_key})")
        lines.append(f"  Default: {config['default_model']}")
        lines.append(f"  Models:")
        for model in config["models"]:
            lines.append(f"    - {provider}:{model}")
    
    return "\n".join(lines)


# =============================================================================
# SPINNER UTILITY
# =============================================================================

class Spinner:
    """A simple CLI spinner that shows activity while waiting."""
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, message: str = "", delay: float = 0.1):
        self.message = message
        self.delay = delay
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_line_length = 0
    
    def _spin(self):
        for frame in itertools.cycle(self.FRAMES):
            if self._stop_event.is_set():
                break
            line = f"\r{frame} {self.message}"
            sys.stdout.write(line)
            sys.stdout.flush()
            self._last_line_length = len(line)
            time.sleep(self.delay)
    
    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
    
    def stop(self, success: bool = True, final_message: str = None):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        sys.stdout.write("\r" + " " * (self._last_line_length + 10) + "\r")
        if final_message:
            icon = "✅" if success else "❌"
            sys.stdout.write(f"{icon} {final_message}\n")
        sys.stdout.flush()


class StepTracker:
    """Tracks and displays steps with spinners and completion status."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.current_spinner: Optional[Spinner] = None
    
    def start_step(self, message: str):
        if not self.verbose:
            return
        if self.current_spinner:
            self.current_spinner.stop(success=True, final_message=None)
        self.current_spinner = Spinner(message)
        self.current_spinner.start()
    
    def complete_step(self, message: str = None, success: bool = True):
        if not self.verbose:
            return
        if self.current_spinner:
            final_msg = message or self.current_spinner.message
            self.current_spinner.stop(success=success, final_message=final_msg)
            self.current_spinner = None
    
    def cleanup(self):
        if self.current_spinner:
            self.current_spinner.stop(success=True, final_message=None)


# =============================================================================
# STATE DEFINITION
# =============================================================================

class AgentState(BaseModel):
    """The state that flows through the coding agent graph."""
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    current_task: str = ""
    workspace_path: str = ""
    files_context: dict[str, str] = Field(default_factory=dict)
    pending_approval: Optional[dict] = None
    human_approved: Optional[bool] = None
    execution_count: int = 0
    max_iterations: int = 25


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are an expert AI coding assistant with deep knowledge of software engineering.

## Capabilities
- 📖 Read files from the codebase
- ✏️ Write new files or edit existing ones (requires human approval)
- 🔍 Search through code
- 📂 Explore directory structures
- ⚡ Run shell commands (requires human approval)

## Approach
1. **Understand First**: Read and understand relevant code before making changes
2. **Plan**: Think step-by-step about what needs to be done
3. **Execute Carefully**: Make precise, minimal changes
4. **Verify**: Run tests or checks when appropriate

## Best Practices
- Always read a file before editing it
- Make small, focused changes
- Follow existing code style and patterns
- If unsure, ask clarifying questions
"""


# =============================================================================
# GRAPH NODES
# =============================================================================

def create_agent_node(model: BaseChatModel):
    """Create the main agent reasoning node."""
    model_with_tools = model.bind_tools(CODING_TOOLS)
    
    def agent_node(state: AgentState) -> dict:
        if state.execution_count >= state.max_iterations:
            return {
                "messages": [AIMessage(content="Reached maximum iterations.")],
                "execution_count": state.execution_count
            }
        
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state.messages)
        response = model_with_tools.invoke(messages)
        
        return {
            "messages": [response],
            "execution_count": state.execution_count + 1
        }
    
    return agent_node


def should_continue(state: AgentState) -> Literal["tools", "human_approval", "end"]:
    """Determine whether to continue to tools, request approval, or end."""
    messages = state.messages
    last_message = messages[-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            if tool_call['name'] in WRITE_TOOLS:
                return "human_approval"
        return "tools"
    
    return "end"


def format_tool_call_for_approval(tool_call: dict) -> str:
    """Format a tool call for human-readable approval request."""
    name = tool_call['name']
    args = tool_call['args']
    
    if name == "write_file":
        content_preview = args.get('content', '')[:200]
        if len(args.get('content', '')) > 200:
            content_preview += "..."
        return f"""
📝 WRITE FILE
   Path: {args.get('file_path', 'unknown')}
   Content Preview:
   {content_preview}
"""
    elif name == "edit_file":
        return f"""
✏️ EDIT FILE
   Path: {args.get('file_path', 'unknown')}
   Replace: {args.get('old_content', '')[:100]}...
   With: {args.get('new_content', '')[:100]}...
"""
    elif name == "run_command":
        return f"""
⚡ RUN COMMAND
   Command: {args.get('command', 'unknown')}
   Directory: {args.get('working_directory', '.')}
"""
    return f"""
🔧 {name.upper()}
   Args: {args}
"""


def human_approval_node(state: AgentState) -> dict:
    """Node that requests human approval for write operations."""
    messages = state.messages
    last_message = messages[-1]
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {}
    
    write_calls = [tc for tc in last_message.tool_calls if tc['name'] in WRITE_TOOLS]
    
    if not write_calls:
        return {}
    
    approval_request = "\n" + "="*60 + "\n"
    approval_request += "🛑 HUMAN APPROVAL REQUIRED\n"
    approval_request += "="*60 + "\n"
    approval_request += "The agent wants to perform the following operation(s):\n"
    
    for tc in write_calls:
        approval_request += format_tool_call_for_approval(tc)
    
    approval_request += "\n" + "-"*60
    
    human_response = interrupt(approval_request)
    approved = human_response.lower().strip() in ['y', 'yes', 'approve', 'ok', 'proceed', '1', 'true']
    
    if approved:
        return {"human_approved": True}
    else:
        rejection_message = ToolMessage(
            content=f"❌ Human rejected the operation. Reason: {human_response}",
            tool_call_id=write_calls[0]['id'] if write_calls else "rejected"
        )
        return {"human_approved": False, "messages": [rejection_message]}


def route_after_approval(state: AgentState) -> Literal["tools", "agent"]:
    """Route after human approval decision."""
    return "tools" if state.human_approved else "agent"


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def create_coding_agent(
    model: str = "openai:gpt-4o",
    temperature: float = 0,
    api_key: Optional[str] = None,
    enable_memory: bool = True,
    enable_hitl: bool = True
) -> StateGraph:
    """
    Create the coding agent StateGraph.
    
    Args:
        model: Model string (e.g., "openai:gpt-4o", "anthropic:claude-3-5-sonnet-20241022")
        temperature: Model temperature (0 for deterministic)
        api_key: Optional API key
        enable_memory: Whether to enable conversation memory
        enable_hitl: Whether to enable Human-in-the-Loop
    
    Returns:
        Compiled StateGraph ready for use
    """
    llm = get_llm(model=model, temperature=temperature, api_key=api_key)
    graph_builder = StateGraph(AgentState)
    
    graph_builder.add_node("agent", create_agent_node(llm))
    graph_builder.add_node("tools", ToolNode(CODING_TOOLS))
    
    if enable_hitl:
        graph_builder.add_node("human_approval", human_approval_node)
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges(
            "agent", should_continue,
            {"tools": "tools", "human_approval": "human_approval", "end": END}
        )
        graph_builder.add_conditional_edges(
            "human_approval", route_after_approval,
            {"tools": "tools", "agent": "agent"}
        )
        graph_builder.add_edge("tools", "agent")
    else:
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges(
            "agent",
            lambda s: "tools" if hasattr(s.messages[-1], 'tool_calls') and s.messages[-1].tool_calls else "end",
            {"tools": "tools", "end": END}
        )
        graph_builder.add_edge("tools", "agent")
    
    if enable_memory or enable_hitl:
        return graph_builder.compile(checkpointer=MemorySaver())
    return graph_builder.compile()


# =============================================================================
# CODING AGENT CLASS
# =============================================================================

class CodingAgent:
    """
    High-level wrapper for the coding agent.
    
    Usage:
        agent = CodingAgent(model="openai:gpt-4o")
        response = agent.run("List all Python files")
        
        # Or with custom settings
        agent = CodingAgent(
            model="anthropic:claude-3-5-sonnet-20241022",
            enable_hitl=False
        )
    """
    
    def __init__(
        self,
        model: str = "openai:gpt-4o",
        temperature: float = 0,
        api_key: Optional[str] = None,
        enable_hitl: bool = True,
        workspace_path: str = "."
    ):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.enable_hitl = enable_hitl
        self.workspace_path = workspace_path
        self._agent = None
        self._thread_id = f"velorum-{int(time.time())}"
    
    @property
    def agent(self):
        if self._agent is None:
            self._agent = create_coding_agent(
                model=self.model,
                temperature=self.temperature,
                api_key=self.api_key,
                enable_hitl=self.enable_hitl
            )
        return self._agent
    
    def run(self, task: str, verbose: bool = True) -> str:
        """Run a single task and return the response."""
        return run_coding_agent(
            task=task,
            workspace_path=self.workspace_path,
            verbose=verbose,
            enable_hitl=self.enable_hitl,
            model=self.model,
            api_key=self.api_key
        )
    
    def chat(self):
        """Start an interactive chat session."""
        chat_with_agent(
            workspace_path=self.workspace_path,
            enable_hitl=self.enable_hitl,
            model=self.model,
            api_key=self.api_key
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def run_coding_agent(
    task: str,
    workspace_path: str = ".",
    thread_id: str = "default",
    verbose: bool = True,
    enable_hitl: bool = True,
    model: str = "openai:gpt-4o",
    api_key: Optional[str] = None
) -> str:
    """Run the coding agent on a task."""
    agent = create_coding_agent(model=model, api_key=api_key, enable_hitl=enable_hitl)
    tracker = StepTracker(verbose=verbose)
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "messages": [HumanMessage(content=task)],
        "workspace_path": workspace_path,
        "current_task": task,
    }
    
    if verbose:
        # Show ASCII art banner as title
        print_session_header(
            mode="Task",
            workspace=workspace_path,
            model=resolve_model_string(model),
            hitl_enabled=enable_hitl
        )
        print(f"📋 Task: {task}\n")
    
    final_response = None
    current_input = initial_state
    current_tool_name = None
    
    try:
        while True:
            tracker.start_step("Thinking...")
            
            for event in agent.stream(current_input, config, stream_mode="values"):
                if "messages" in event:
                    last_message = event["messages"][-1]
                    
                    if isinstance(last_message, AIMessage):
                        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            tracker.complete_step("Analyzed task", success=True)
                            for tc in last_message.tool_calls:
                                current_tool_name = tc['name']
                                tracker.start_step(f"Running {tc['name']}...")
                        elif last_message.content:
                            tracker.cleanup()
                            print(f"\n🤖 Agent: {last_message.content}\n")
                            final_response = last_message.content
                    
                    elif isinstance(last_message, ToolMessage):
                        tool_name = last_message.name or current_tool_name or "tool"
                        is_success = not last_message.content.startswith("Error")
                        tracker.complete_step(f"{tool_name}", success=is_success)
                        
                        if verbose:
                            content = last_message.content
                            if len(content) > 300:
                                content = content[:300] + "\n   ... [truncated]"
                            indented = "\n".join(f"   {line}" for line in content.split("\n")[:10])
                            print(f"   📤 {indented}\n")
            
            state = agent.get_state(config)
            
            if state.next and "human_approval" in state.next:
                tracker.cleanup()
                if state.tasks:
                    for task_obj in state.tasks:
                        if hasattr(task_obj, 'interrupts') and task_obj.interrupts:
                            for intr in task_obj.interrupts:
                                print(intr.value)
                
                print("\n" + "-"*60)
                print("Do you approve this operation? (yes/no): ", end="")
                human_input = input().strip()
                print("-"*60 + "\n")
                current_input = Command(resume=human_input)
            else:
                break
    finally:
        tracker.cleanup()
    
    return final_response


def chat_with_agent(
    workspace_path: str = ".",
    enable_hitl: bool = True,
    model: str = "openai:gpt-4o",
    api_key: Optional[str] = None
):
    """Interactive chat session with the coding agent."""
    agent = create_coding_agent(model=model, api_key=api_key, enable_hitl=enable_hitl)
    thread_id = f"interactive-session-{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}
    tracker = StepTracker(verbose=True)
    
    # Show ASCII art banner as title
    print_session_header(
        mode="Interactive",
        workspace=workspace_path,
        model=resolve_model_string(model),
        hitl_enabled=enable_hitl
    )
    
    messages = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'clear':
                messages = []
                thread_id = f"interactive-session-{int(time.time())}"
                config = {"configurable": {"thread_id": thread_id}}
                print("🔄 Conversation cleared!\n")
                continue
            
            messages.append(HumanMessage(content=user_input))
            current_input = {"messages": messages, "workspace_path": workspace_path}
            
            print()
            current_tool_name = None
            
            try:
                while True:
                    tracker.start_step("Thinking...")
                    
                    for event in agent.stream(current_input, config, stream_mode="values"):
                        if "messages" in event:
                            last_message = event["messages"][-1]
                            
                            if isinstance(last_message, AIMessage):
                                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                                    tracker.complete_step("Analyzed", success=True)
                                    for tc in last_message.tool_calls:
                                        current_tool_name = tc['name']
                                        tracker.start_step(f"Running {tc['name']}...")
                                elif last_message.content:
                                    tracker.cleanup()
                                    print(f"🤖 Agent: {last_message.content}")
                                    messages.append(last_message)
                            
                            elif isinstance(last_message, ToolMessage):
                                tool_name = last_message.name or current_tool_name or "tool"
                                is_success = not last_message.content.startswith("Error")
                                tracker.complete_step(f"{tool_name}", success=is_success)
                                
                                content = last_message.content
                                if len(content) > 200:
                                    content = content[:200] + "..."
                                indented = "\n".join(f"   {line}" for line in content.split("\n")[:5])
                                print(f"   📤 {indented}")
                    
                    state = agent.get_state(config)
                    
                    if state.next and "human_approval" in state.next:
                        tracker.cleanup()
                        if state.tasks:
                            for task_obj in state.tasks:
                                if hasattr(task_obj, 'interrupts') and task_obj.interrupts:
                                    for intr in task_obj.interrupts:
                                        print(intr.value)
                        
                        print("Do you approve? (yes/no): ", end="")
                        approval = input().strip()
                        print()
                        current_input = Command(resume=approval)
                    else:
                        break
            finally:
                tracker.cleanup()
            
            print()
            
        except KeyboardInterrupt:
            tracker.cleanup()
            print("\n\n👋 Goodbye!")
            break

