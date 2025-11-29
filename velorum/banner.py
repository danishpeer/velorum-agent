"""
Velorum Banner
==============

ASCII art banner and animated splash screen for Velorum.
"""

import sys
import time
import math
import shutil
from typing import Optional


# Bold ASCII Art for VELORUM using block characters
VELORUM_ART = [
    "██     ██  ███████  ██        ██████   ██████   ██    ██  ██     ██",
    "██     ██  ██       ██       ██    ██  ██   ██  ██    ██  ███   ███",
    "██     ██  █████    ██       ██    ██  ██████   ██    ██  █████████",
    " ██   ██   ██       ██       ██    ██  ██   ██  ██    ██  ██  █  ██",
    "  █████    ███████  ███████   ██████   ██   ██   ██████   ██     ██"
]

# Smaller version for narrow terminals
VELORUM_ART_SMALL = [
    "█   █ █▀▀ █   ▄▀▀▄ █▀▀▄ █  █ █▄ ▄█",
    "█   █ █▀  █   █  █ █▄▄▀ █  █ █ █ █",
    " ▀▄▀  ▀▀▀ ▀▀▀  ▀▀  ▀  ▀  ▀▀  ▀   ▀"
]

# Planet sprite for animation
PLANET_ART = [
    "   .   ",
    ".-(_)-.",
    " '   ' "
]

# Gradient colors (cyan -> blue -> magenta -> blue -> cyan)
GRADIENT_COLORS = [
    "\033[1;96m",  # Bright Cyan
    "\033[1;94m",  # Bright Blue
    "\033[1;95m",  # Bright Magenta
    "\033[1;94m",  # Bright Blue
    "\033[1;96m",  # Bright Cyan
]

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
YELLOW = "\033[1;33m"
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
GREEN = "\033[1;32m"
WHITE = "\033[1;37m"
GRAY = "\033[90m"


def get_terminal_width() -> int:
    """Get terminal width, with fallback."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def print_banner(subtitle: str = "", show_border: bool = True) -> None:
    """
    Print the VELORUM ASCII art banner as a header.
    
    Args:
        subtitle: Optional subtitle to display below the banner
        show_border: Whether to show decorative borders
    """
    width = get_terminal_width()
    art = VELORUM_ART if width >= 75 else VELORUM_ART_SMALL
    art_width = len(art[0])
    
    # Calculate padding for centering
    padding = max(0, (width - art_width) // 2)
    pad_str = " " * padding
    
    print()
    
    if show_border:
        border = "═" * min(width - 2, art_width + 4)
        print(f"{CYAN}{pad_str[:-2]}╔{border}╗{RESET}")
    
    # Print ASCII art with gradient colors
    for i, line in enumerate(art):
        color = GRADIENT_COLORS[i % len(GRADIENT_COLORS)]
        if show_border:
            print(f"{CYAN}{pad_str[:-2]}║{RESET} {color}{line}{RESET} {CYAN}║{RESET}")
        else:
            print(f"{pad_str}{color}{line}{RESET}")
    
    if show_border:
        print(f"{CYAN}{pad_str[:-2]}╚{border}╝{RESET}")
    
    # Print subtitle if provided
    if subtitle:
        sub_padding = max(0, (width - len(subtitle)) // 2)
        print(f"{' ' * sub_padding}{DIM}{subtitle}{RESET}")
    
    print()


def print_session_header(
    mode: str = "Interactive",
    workspace: str = ".",
    model: str = "openai:gpt-4o",
    hitl_enabled: bool = True
) -> None:
    """
    Print the full session header with banner and info.
    
    Args:
        mode: Session mode ("Interactive" or "Task")
        workspace: Workspace path
        model: Model being used
        hitl_enabled: Whether HITL is enabled
    """
    hitl_text = "(HITL Enabled)" if hitl_enabled else ""
    subtitle = f"AI Coding Agent • {mode} Mode {hitl_text}"
    
    print_banner(subtitle=subtitle)
    
    width = get_terminal_width()
    info_width = min(70, width - 4)
    
    # Calculate max value width (box width - borders - icon - label - padding)
    # Format: "│ ▸ Label   value" = 1 + 1 + 1 + 1 + label_len + 2 + value
    max_label_len = 9  # "Workspace" is the longest label
    max_value_width = info_width - 7 - max_label_len
    
    # Truncate workspace path if too long
    def truncate_path(path: str, max_len: int) -> str:
        if len(path) <= max_len:
            return path
        # Show .../ + last parts of path
        parts = path.split('/')
        result = parts[-1]  # Start with filename/last dir
        for part in reversed(parts[:-1]):
            candidate = f"{part}/{result}"
            if len(candidate) + 4 > max_len:  # 4 for ".../"
                break
            result = candidate
        return f".../{result}" if len(result) < len(path) else path[:max_len-3] + "..."
    
    workspace_display = truncate_path(workspace, max_value_width)
    
    # Build info lines
    info_lines = []
    
    # Workspace
    info_lines.append((f"{GRADIENT_COLORS[0]}▸{RESET}", "Workspace", workspace_display))
    
    # Model
    info_lines.append((f"{GRADIENT_COLORS[1]}▸{RESET}", "Model", model))
    
    # Mode indicator
    mode_color = GREEN if mode == "Interactive" else MAGENTA
    info_lines.append((f"{GRADIENT_COLORS[2]}▸{RESET}", "Mode", f"{mode_color}{mode}{RESET}"))
    
    # HITL status
    if hitl_enabled:
        info_lines.append((f"{GRADIENT_COLORS[1]}▸{RESET}", "Safety", f"{GREEN}HITL Enabled{RESET} {DIM}(write ops require approval){RESET}"))
    else:
        info_lines.append((f"{GRADIENT_COLORS[1]}▸{RESET}", "Safety", f"{YELLOW}HITL Disabled{RESET}"))
    
    # Calculate the longest label for alignment
    label_len = max(len(label) for _, label, _ in info_lines)
    
    # Print styled info box
    border_char = "─"
    corner_tl, corner_tr = "╭", "╮"
    corner_bl, corner_br = "╰", "╯"
    side = "│"
    
    # Calculate center padding
    center_pad = " " * max(0, (width - info_width) // 2)
    
    # Helper to calculate visible length (strips ANSI codes)
    import re
    def visible_len(s: str) -> int:
        return len(re.sub(r'\033\[[0-9;]*m', '', s))
    
    # Helper to pad line to fit box with right border
    def box_line(content: str) -> str:
        vis_len = visible_len(content)
        padding = info_width - 2 - vis_len  # -2 for left and right borders
        if padding < 0:
            padding = 0
        return f"{center_pad}{GRAY}{side}{RESET}{content}{' ' * padding}{GRAY}{side}{RESET}"
    
    # Top border
    print(f"{center_pad}{GRAY}{corner_tl}{border_char * (info_width - 2)}{corner_tr}{RESET}")
    
    # Content lines
    for icon, label, value in info_lines:
        label_padded = label.ljust(label_len)
        line_content = f" {icon} {DIM}{label_padded}{RESET}  {value}"
        print(box_line(line_content))
    
    # Separator before hints (if interactive mode)
    if mode == "Interactive":
        print(box_line(""))
        hint_content = f"   {DIM}Commands:{RESET} {CYAN}quit{RESET}{DIM}/{RESET}{CYAN}exit{RESET} {DIM}to end{RESET}  {DIM}•{RESET}  {CYAN}clear{RESET} {DIM}for new conversation{RESET}"
        print(box_line(hint_content))
    
    # Bottom border
    print(f"{center_pad}{GRAY}{corner_bl}{border_char * (info_width - 2)}{corner_br}{RESET}")
    print()


class VelorumSplash:
    """Animated VELORUM title with orbiting planet."""
    
    def __init__(self):
        self.running = True
        self.text_height = len(VELORUM_ART)
        self.text_width = len(VELORUM_ART[0])
        self.planet_h = len(PLANET_ART)
        self.planet_w = len(PLANET_ART[0])
    
    def _hide_cursor(self):
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
    
    def _show_cursor(self):
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
    
    def show(self, duration: float = 2.5):
        """Display the animated splash screen for a given duration."""
        # Check if we're in a terminal that supports the animation
        if not sys.stdout.isatty():
            print_banner()
            return
        
        try:
            cols, lines = shutil.get_terminal_size()
            # If terminal is too small, show static version
            if cols < self.text_width + 25 or lines < self.text_height + 10:
                print_banner()
                return
        except Exception:
            print_banner()
            return
        
        # Orbit settings
        radius_x = (self.text_width // 2) + 10
        radius_y = (self.text_height // 2) + 3
        speed = 0.12
        angle = 3.14  # Start from the back
        
        start_time = time.time()
        
        self._hide_cursor()
        sys.stdout.write("\033[2J")  # Clear screen
        
        try:
            while self.running and (time.time() - start_time) < duration:
                cols, lines = shutil.get_terminal_size()
                cx, cy = cols // 2, lines // 2
                
                # Grid: (y, x) -> (char, z_index, style)
                grid = {}
                
                # 1. Calculate Planet position
                px_center = cx + int(radius_x * math.cos(angle))
                py_center = cy + int(radius_y * math.sin(angle))
                
                is_front = math.sin(angle) > 0
                planet_z = 2 if is_front else -1
                
                # 2. Draw Text (Z = 1)
                start_y = cy - (self.text_height // 2)
                start_x = cx - (self.text_width // 2)
                
                for r, line in enumerate(VELORUM_ART):
                    y = start_y + r
                    text_style = GRADIENT_COLORS[r % len(GRADIENT_COLORS)]
                    for c, char in enumerate(line):
                        if char != " ":
                            x = start_x + c
                            grid[(y, x)] = (char, 1, text_style)
                
                # 3. Draw Planet
                p_start_y = py_center - (self.planet_h // 2)
                p_start_x = px_center - (self.planet_w // 2)
                
                planet_style = YELLOW
                
                for r, line in enumerate(PLANET_ART):
                    y = p_start_y + r
                    for c, char in enumerate(line):
                        if char != " ":
                            x = p_start_x + c
                            current = grid.get((y, x), (None, -99, ""))
                            current_z = current[1]
                            
                            if planet_z > current_z:
                                grid[(y, x)] = (char, planet_z, planet_style)
                
                # 4. Render
                min_y = min(start_y, cy - radius_y - 3)
                max_y = max(start_y + self.text_height, cy + radius_y + 3)
                
                output_buffer = []
                
                for y in range(int(min_y), int(max_y) + 1):
                    if 0 <= y < lines:
                        output_buffer.append(f"\033[{y+1};1H")
                        
                        line_chars = []
                        current_style = ""
                        
                        for x in range(cols):
                            cell = grid.get((y, x))
                            if cell:
                                char, z, style = cell
                                if style != current_style:
                                    line_chars.append(style)
                                    current_style = style
                                line_chars.append(char)
                            else:
                                if current_style != "":
                                    line_chars.append(RESET)
                                    current_style = ""
                                line_chars.append(" ")
                        
                        if current_style != "":
                            line_chars.append(RESET)
                        
                        output_buffer.append("".join(line_chars))
                
                sys.stdout.write("".join(output_buffer))
                sys.stdout.flush()
                
                angle += speed
                time.sleep(0.05)
        
        except (KeyboardInterrupt, Exception):
            pass
        finally:
            self._show_cursor()
            sys.stdout.write("\033[2J")  # Clear screen
            sys.stdout.write("\033[H")   # Move to top
            sys.stdout.write(RESET)      # Reset colors
            sys.stdout.flush()


def show_splash(duration: float = 2.5):
    """Show the animated Velorum splash screen."""
    splash = VelorumSplash()
    splash.show(duration)

