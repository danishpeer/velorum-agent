"""
Velorum UI
==========

Terminal UI components and styling for Velorum.
"""

import sys
import shutil
import threading
import itertools
import time
from typing import Optional


# =============================================================================
# TERMINAL COLORS
# =============================================================================

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
GREEN = "\033[1;32m"
RED = "\033[1;31m"
GRAY = "\033[90m"
YELLOW = "\033[1;33m"


# =============================================================================
# TERMINAL UTILITIES
# =============================================================================

def get_terminal_width() -> int:
    """Get terminal width with fallback."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def move_cursor_up(lines: int = 1):
    """Move cursor up n lines."""
    sys.stdout.write(f"\033[{lines}A")
    sys.stdout.flush()


def clear_line():
    """Clear the current line."""
    sys.stdout.write("\033[2K\r")
    sys.stdout.flush()


# =============================================================================
# INPUT BOX
# =============================================================================

def print_input_prompt() -> str:
    """
    Display a full-width input box and get user input.
    Returns the user's input string.
    """
    width = get_terminal_width()
    border = "─" * (width - 2)
    
    # Print top border
    sys.stdout.write(f"{CYAN}╭{border}╮{RESET}\n")
    
    # Print input line with right border, then bottom border
    padding_space = " " * (width - 6)
    sys.stdout.write(f"{CYAN}│{RESET} {BOLD}❯{RESET} {padding_space}{CYAN}│{RESET}\n")
    sys.stdout.write(f"{CYAN}╰{border}╯{RESET}\n")
    
    # Move cursor back up to input line, column 5 (after "│ ❯ ")
    sys.stdout.write(f"\033[2A")  # Move up 2 lines
    sys.stdout.write(f"\033[5G")  # Move to column 5
    sys.stdout.flush()
    
    # Get input
    user_input = input()
    
    # After input, cursor moved down. Move up 2 lines to top border
    sys.stdout.write(f"\033[2A")
    
    # Clear and reprint all 3 lines greyed out
    display_input = user_input[:width - 8] if len(user_input) > width - 8 else user_input
    padding = " " * (width - len(display_input) - 7)
    
    sys.stdout.write(f"\033[2K")  # Clear line
    sys.stdout.write(f"{GRAY}╭{border}╮{RESET}\n")
    sys.stdout.write(f"\033[2K")  # Clear line
    sys.stdout.write(f"{GRAY}│ ❯ {display_input}{padding}│{RESET}\n")
    sys.stdout.write(f"\033[2K")  # Clear line
    sys.stdout.write(f"{GRAY}╰{border}╯{RESET}\n")
    sys.stdout.flush()
    
    return user_input.strip()


def print_approval_prompt() -> str:
    """Display approval prompt and get response."""
    width = get_terminal_width()
    print(f"\n{CYAN}│ Approve? (yes/no):{RESET} ", end="")
    return input().strip()


# =============================================================================
# SPINNER
# =============================================================================

class Spinner:
    """A CLI spinner that shows activity while waiting."""
    
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
            line = f"\r{CYAN}{frame}{RESET} {self.message}"
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
            icon = f"{GREEN}●{RESET}" if success else f"{RED}●{RESET}"
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
            self.current_spinner = None


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def print_tool_result(content: str, max_lines: int = 5, max_chars: int = 200):
    """Print tool result with indentation."""
    lines = content.split("\n")
    if len(lines) > max_lines or len(content) > max_chars:
        line_count = len(lines)
        print(f"{DIM}└  {line_count} lines{RESET}")
    else:
        for line in lines[:max_lines]:
            print(f"{DIM}└  {line}{RESET}")


def print_agent_response(content: str):
    """Print agent's response."""
    print(f"\n{content}\n")


def print_goodbye():
    """Print goodbye message."""
    print(f"\n{DIM}Goodbye!{RESET}")


def print_cleared():
    """Print conversation cleared message."""
    print(f"{DIM}Conversation cleared.{RESET}\n")


def format_tool_display(tool_name: str, args: dict) -> str:
    """Format tool name with key argument for display."""
    if not args:
        return tool_name
    
    if tool_name == "read_file" and "file_path" in args:
        path = args["file_path"]
        filename = path.split("/")[-1] if "/" in path else path
        return f"{tool_name}({filename})"
    elif tool_name == "write_file" and "file_path" in args:
        path = args["file_path"]
        filename = path.split("/")[-1] if "/" in path else path
        return f"{tool_name}({filename})"
    elif tool_name == "list_directory" and "path" in args:
        return f"{tool_name}({args['path']})"
    elif tool_name == "search_codebase" and "query" in args:
        query = args["query"][:20] + "..." if len(args.get("query", "")) > 20 else args.get("query", "")
        return f"{tool_name}(\"{query}\")"
    elif tool_name == "run_command" and "command" in args:
        cmd = args["command"][:25] + "..." if len(args.get("command", "")) > 25 else args.get("command", "")
        return f"{tool_name}({cmd})"
    
    return tool_name

