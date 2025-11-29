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
from typing import Optional, List, Dict, Any


# =============================================================================
# TERMINAL COLORS
# =============================================================================

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
GREEN = "\033[1;32m"
RED = "\033[1;31m"
GRAY = "\033[90m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
WHITE = "\033[1;37m"

# Gradient colors for styled elements
GRADIENT = [
    "\033[1;96m",  # Bright Cyan
    "\033[1;94m",  # Bright Blue
    "\033[1;95m",  # Bright Magenta
]


# =============================================================================
# TERMINAL UTILITIES
# =============================================================================

def get_terminal_width() -> int:
    """Get terminal width with fallback."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def get_visual_width(text: str) -> int:
    """
    Calculate visual width of text, accounting for:
    - ANSI escape codes (0 width)
    - Wide characters/Emojis (2 width)
    - Simple heuristic: len() + 1 for every Wide/Fullwidth char
    """
    import unicodedata
    import re
    
    # Strip ANSI codes
    text = re.sub(r'\033\[[0-9;]*m', '', text)
    
    width = len(text)
    for char in text:
        if unicodedata.east_asian_width(char) in ('W', 'F'):
            width += 1
            
    return width


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
    """Display styled approval prompt and get response."""
    width = get_terminal_width()
    border = "─" * (width - 2)
    
    # Bottom section with approval input
    print(f"\n{GRADIENT[0]}╭{border}╮{RESET}")
    
    # Prompt line
    padding_space = " " * (width - 27)
    print(f"{GRADIENT[0]}│{RESET} {WHITE}Approve?{RESET} {DIM}(y/yes or n/no){RESET}{padding_space}{GRADIENT[0]}│{RESET}")
    
    # Input line
    # "│ › " is 4 chars. Right border is 1. Total 5.
    padding_space = " " * (width - 5)
    print(f"{GRADIENT[0]}│{RESET} {BOLD}›{RESET} {padding_space}{GRADIENT[0]}│{RESET}")
    print(f"{GRADIENT[0]}╰{border}╯{RESET}")
    
    # Move cursor back to input line
    sys.stdout.write(f"\033[2A")  # Move up 2 lines
    sys.stdout.write(f"\033[5G")  # Move to column 5
    sys.stdout.flush()
    
    # Get input
    user_input = input()
    
    # After input, move up and grey out the box
    sys.stdout.write(f"\033[3A")
    
    display_input = user_input[:width - 8] if len(user_input) > width - 8 else user_input
    padding = " " * (width - len(display_input) - 7)
    
    # Reprint as greyed out
    print(f"\033[2K{GRAY}╭{border}╮{RESET}")
    print(f"\033[2K{GRAY}│ Approve? (y/yes or n/no){' ' * (width - 29)}│{RESET}")
    print(f"\033[2K{GRAY}│ › {display_input}{padding}│{RESET}")
    print(f"\033[2K{GRAY}╰{border}╯{RESET}")
    
    return user_input.strip()


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


# =============================================================================
# HUMAN APPROVAL UI
# =============================================================================

def _wrap_text(text: str, max_width: int, indent: str = "") -> List[str]:
    """Wrap text to fit within max_width."""
    lines = []
    for line in text.split('\n'):
        while len(line) > max_width:
            # Find last space before max_width
            break_at = line[:max_width].rfind(' ')
            if break_at <= 0:
                break_at = max_width
            lines.append(indent + line[:break_at].strip())
            line = line[break_at:].strip()
        lines.append(indent + line)
    return lines


def _print_box_line(content: str, width: int, left_char: str = "│", right_char: str = "│", color: str = GRADIENT[1]):
    """Print a single line within a box."""
    # Strip ANSI codes for length calculation
    import re
    visible_content = re.sub(r'\033\[[0-9;]*m', '', content)
    vis_width = get_visual_width(content)
    
    padding_needed = width - vis_width - 4
    if padding_needed < 0:
        # Truncate if too long
        content = content[:width - 7] + "..."
        vis_width = get_visual_width(content)
        padding_needed = width - vis_width - 4
    padding = " " * max(0, padding_needed)
    print(f"{color}{left_char}{RESET} {content}{padding} {color}{right_char}{RESET}")


def format_operation_for_approval(tool_name: str, args: Dict[str, Any], width: int) -> List[str]:
    """
    Format a tool operation for the approval dialog.
    
    Returns a list of formatted lines for display.
    """
    lines = []
    content_width = width - 8  # Account for box borders and padding
    
    if tool_name == "write_file":
        file_path = args.get('file_path', 'unknown')
        content = args.get('content', '')
        
        lines.append(f"{MAGENTA}╭─{RESET} {WHITE}{BOLD}WRITE FILE{RESET}")
        lines.append(f"{MAGENTA}│{RESET}  {DIM}Path:{RESET} {CYAN}{file_path}{RESET}")
        
        # Preview content (first few lines)
        preview_lines = content.split('\n')[:6]
        if preview_lines:
            lines.append(f"{MAGENTA}│{RESET}  {DIM}Content:{RESET}")
            for i, line in enumerate(preview_lines):
                truncated = line[:content_width - 10] if len(line) > content_width - 10 else line
                lines.append(f"{MAGENTA}│{RESET}    {DIM}{truncated}{RESET}")
            if len(content.split('\n')) > 6:
                lines.append(f"{MAGENTA}│{RESET}    {DIM}... ({len(content.split(chr(10)))} lines total){RESET}")
        lines.append(f"{MAGENTA}╰{'─' * content_width}{RESET}")
        
    elif tool_name == "edit_file":
        file_path = args.get('file_path', 'unknown')
        old_content = args.get('old_content', '')[:80]
        new_content = args.get('new_content', '')[:80]
        
        lines.append(f"{BLUE}╭─{RESET} {WHITE}{BOLD}EDIT FILE{RESET}")
        lines.append(f"{BLUE}│{RESET}  {DIM}Path:{RESET} {CYAN}{file_path}{RESET}")
        lines.append(f"{BLUE}│{RESET}  {RED}- {old_content}{'...' if len(args.get('old_content', '')) > 80 else ''}{RESET}")
        lines.append(f"{BLUE}│{RESET}  {GREEN}+ {new_content}{'...' if len(args.get('new_content', '')) > 80 else ''}{RESET}")
        lines.append(f"{BLUE}╰{'─' * content_width}{RESET}")
        
    elif tool_name == "run_command":
        command = args.get('command', 'unknown')
        working_dir = args.get('working_directory', '.')
        
        lines.append(f"{GREEN}╭─{RESET} {WHITE}{BOLD}RUN COMMAND{RESET}")
        lines.append(f"{GREEN}│{RESET}  {DIM}Directory:{RESET} {CYAN}{working_dir}{RESET}")
        lines.append(f"{GREEN}│{RESET}  {DIM}Command:{RESET}")
        
        # Wrap long commands
        wrapped = _wrap_text(command, content_width - 8, "")
        for line in wrapped[:5]:
            lines.append(f"{GREEN}│{RESET}    {WHITE}${RESET} {line}")
        if len(wrapped) > 5:
            lines.append(f"{GREEN}│{RESET}    {DIM}... (truncated){RESET}")
        lines.append(f"{GREEN}╰{'─' * content_width}{RESET}")
        
    else:
        # Generic format for unknown operations
        lines.append(f"{CYAN}╭─{RESET} {WHITE}{BOLD}{tool_name.upper()}{RESET}")
        for key, value in list(args.items())[:5]:
            val_str = str(value)[:60]
            if len(str(value)) > 60:
                val_str += "..."
            lines.append(f"{CYAN}│{RESET}  {DIM}{key}:{RESET} {val_str}")
        lines.append(f"{CYAN}╰{'─' * content_width}{RESET}")
    
    return lines


def print_approval_dialog(operations: List[Dict[str, Any]]) -> None:
    """
    Print the styled human approval dialog box.
    
    Args:
        operations: List of dicts with 'name' and 'args' keys for each operation
    """
    width = get_terminal_width()
    border = "═" * (width - 2)
    thin_border = "─" * (width - 2)
    
    print()
    
    # Top border with title
    print(f"{GRADIENT[0]}╔{border}╗{RESET}")
    
    # Title section
    title = "APPROVAL REQUIRED"
    vis_title_width = get_visual_width(title)
    title_padding = (width - vis_title_width - 4) // 2
    right_padding = width - vis_title_width - title_padding - 2
    print(f"{GRADIENT[0]}║{RESET}{' ' * title_padding}{YELLOW}{BOLD}{title}{RESET}{' ' * right_padding}{GRADIENT[0]}║{RESET}")
    
    # Subtitle
    subtitle = "The agent wants to perform the following operation(s)"
    vis_sub_width = get_visual_width(subtitle)
    sub_padding = (width - vis_sub_width - 4) // 2
    right_sub_padding = width - vis_sub_width - sub_padding - 2
    print(f"{GRADIENT[0]}║{RESET}{' ' * sub_padding}{DIM}{subtitle}{RESET}{' ' * right_sub_padding}{GRADIENT[0]}║{RESET}")
    
    # Separator
    print(f"{GRADIENT[0]}╟{RESET}{GRAY}{thin_border}{RESET}{GRADIENT[0]}╢{RESET}")
    
    # Operations
    for i, op in enumerate(operations):
        if i > 0:
            print(f"{GRADIENT[0]}║{RESET}{' ' * (width - 4)}{GRADIENT[0]}║{RESET}")
        
        op_lines = format_operation_for_approval(op['name'], op['args'], width)
        for line in op_lines:
            _print_box_line(line, width, "║", "║", GRADIENT[0])
    
    # Separator
    print(f"{GRADIENT[0]}╟{RESET}{GRAY}{thin_border}{RESET}{GRADIENT[0]}╢{RESET}")
    
    # Instructions
    inst_line = f"{DIM}Type{RESET} {GREEN}y{RESET}{DIM}/{RESET}{GREEN}yes{RESET} {DIM}to approve or{RESET} {RED}n{RESET}{DIM}/{RESET}{RED}no{RESET} {DIM}to reject{RESET}"
    _print_box_line(inst_line, width, "║", "║", GRADIENT[0])
    
    # Bottom border
    print(f"{GRADIENT[0]}╚{border}╝{RESET}")


def build_approval_request(tool_calls: List[Dict[str, Any]]) -> str:
    """
    Build the approval request string for interrupt.
    This is the value that gets passed to the interrupt() call.
    
    Args:
        tool_calls: List of tool call dicts with 'name' and 'args'
    
    Returns:
        A marker string (the actual display is handled by print_approval_dialog)
    """
    # Return a simple marker - the actual display is handled separately
    return "__VELORUM_APPROVAL_REQUEST__"


def display_approval_request_and_prompt(operations: List[Dict[str, Any]]) -> str:
    """
    Display the full approval request dialog and get user input.
    
    Args:
        operations: List of operations needing approval
    
    Returns:
        User's approval response
    """
    print_approval_dialog(operations)
    return print_approval_prompt()

