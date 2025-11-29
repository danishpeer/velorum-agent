"""
Velorum Tools
=============

Tools that the coding agent can use to interact with the codebase.
"""

import subprocess
from pathlib import Path
from langchain_core.tools import tool


# =============================================================================
# TOOL CLASSIFICATION
# =============================================================================

# Tools that only read data - no approval needed
READ_ONLY_TOOLS = {"read_file", "list_directory", "get_file_structure", "grep"}

# Tools that modify state - require human approval
WRITE_TOOLS = {"write_file", "edit_file", "run_command"}


# =============================================================================
# TOOLS DEFINITION
# =============================================================================

@tool
def read_file(file_path: str) -> str:
    """
    Read the contents of a file from the codebase.
    
    Args:
        file_path: Path to the file (relative or absolute)
    
    Returns:
        The file contents with line numbers, or an error message
    """
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return f"Error: File not found: {file_path}"
        
        if not path.is_file():
            return f"Error: Path is not a file: {file_path}"
        
        content = path.read_text(encoding='utf-8')
        
        # Add line numbers for easier reference
        lines = content.split('\n')
        numbered_lines = [f"{i+1:4}| {line}" for i, line in enumerate(lines)]
        return '\n'.join(numbered_lines)
    
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file. Creates the file if it doesn't exist.
    Creates parent directories if needed.
    
    Args:
        file_path: Path to the file (relative or absolute)
        content: The content to write to the file
    
    Returns:
        Success message or error
    """
    try:
        path = Path(file_path).expanduser()
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        path.write_text(content, encoding='utf-8')
        return f"Wrote {len(content)} characters to {file_path}"
    
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def edit_file(file_path: str, old_content: str, new_content: str) -> str:
    """
    Edit a file by replacing old_content with new_content.
    This is safer than overwriting the entire file.
    
    Args:
        file_path: Path to the file
        old_content: The exact content to find and replace
        new_content: The content to replace it with
    
    Returns:
        Success message or error
    """
    try:
        path = Path(file_path).expanduser()
        
        if not path.exists():
            return f"Error: File not found: {file_path}"
        
        content = path.read_text(encoding='utf-8')
        
        if old_content not in content:
            return f"Error: Could not find the specified content in {file_path}. Make sure you're using the exact text."
        
        # Count occurrences
        count = content.count(old_content)
        if count > 1:
            return f"Warning: Found {count} occurrences of the content. Please provide more context to make it unique."
        
        new_file_content = content.replace(old_content, new_content, 1)
        path.write_text(new_file_content, encoding='utf-8')
        
        return f"Edited {file_path}"
    
    except Exception as e:
        return f"Error editing file: {e}"


@tool
def list_directory(directory_path: str, pattern: str = "*") -> str:
    """
    List files and directories in a given path.
    
    Args:
        directory_path: Path to the directory
        pattern: Glob pattern to filter results (default: "*")
    
    Returns:
        List of files and directories
    """
    try:
        path = Path(directory_path).expanduser()
        
        if not path.exists():
            return f"Error: Directory not found: {directory_path}"
        
        if not path.is_dir():
            return f"Error: Path is not a directory: {directory_path}"
        
        items = []
        for item in sorted(path.glob(pattern)):
            if item.name.startswith('.'):
                continue  # Skip hidden files
            
            item_type = "📁" if item.is_dir() else "📄"
            size = ""
            if item.is_file():
                size_bytes = item.stat().st_size
                if size_bytes < 1024:
                    size = f" ({size_bytes}B)"
                elif size_bytes < 1024 * 1024:
                    size = f" ({size_bytes // 1024}KB)"
                else:
                    size = f" ({size_bytes // (1024*1024)}MB)"
            
            items.append(f"{item_type} {item.name}{size}")
        
        if not items:
            return f"Directory is empty or no matches for pattern '{pattern}'"
        
        return f"Contents of {directory_path}:\n" + '\n'.join(items)
    
    except Exception as e:
        return f"Error listing directory: {e}"


@tool
def run_command(command: str, working_directory: str = ".") -> str:
    """
    Execute a shell command and return its output.
    
    ⚠️ SECURITY: Only use for safe, read-only commands like:
    - Running tests
    - Linting
    - Type checking
    - Git status
    
    Args:
        command: The shell command to execute
        working_directory: Directory to run the command in
    
    Returns:
        Command output (stdout + stderr) or error message
    """
    # Block dangerous commands
    dangerous_patterns = [
        'rm -rf', 'rm -r', 'rmdir', 'del /f', 'format',
        'sudo', 'chmod 777', 'curl | bash', 'wget | bash',
        '> /dev/', 'dd if=', 'mkfs', ':(){:|:&};:'
    ]
    
    for pattern in dangerous_patterns:
        if pattern in command.lower():
            return f"⛔ Blocked potentially dangerous command containing: {pattern}"
    
    try:
        path = Path(working_directory).expanduser()
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        
        output += f"\nExit code: {result.returncode}"
        
        return output if output.strip() else "Command completed with no output"
    
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds"
    except Exception as e:
        return f"Error executing command: {e}"


@tool
def get_file_structure(directory: str, max_depth: int = 3) -> str:
    """
    Get a tree-like structure of the project directory.
    
    Args:
        directory: Root directory to map
        max_depth: Maximum depth to traverse (default: 3)
    
    Returns:
        Tree structure of the project
    """
    try:
        path = Path(directory).expanduser()
        
        if not path.exists():
            return f"Error: Directory not found: {directory}"
        
        skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 
                     '.idea', '.vscode', 'dist', 'build', '.next', 'coverage'}
        
        def build_tree(current_path: Path, prefix: str = "", depth: int = 0) -> list[str]:
            if depth >= max_depth:
                return [f"{prefix}..."]
            
            items = []
            try:
                entries = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                return [f"{prefix}[Permission Denied]"]
            
            # Filter entries
            entries = [e for e in entries if not e.name.startswith('.') and e.name not in skip_dirs]
            
            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                connector = "└── " if is_last else "├── "
                
                if entry.is_dir():
                    items.append(f"{prefix}{connector}📁 {entry.name}/")
                    extension = "    " if is_last else "│   "
                    items.extend(build_tree(entry, prefix + extension, depth + 1))
                else:
                    items.append(f"{prefix}{connector}📄 {entry.name}")
            
            return items
        
        tree_lines = [f"📁 {path.name}/"] + build_tree(path)
        return '\n'.join(tree_lines)
    
    except Exception as e:
        return f"Error building file structure: {e}"


@tool
def grep(pattern: str, path: str, ignore_case: bool = True, context_lines: int = 0, file_pattern: str = "") -> str:
    """
    Search for a regex pattern in files using grep/ripgrep.
    
    This is a powerful search tool that supports regular expressions.
    Use this for precise pattern matching in the codebase.
    
    Args:
        pattern: Regular expression pattern to search for
        path: File or directory path to search in
        ignore_case: Whether to ignore case (default: True)
        context_lines: Number of lines to show before/after match (default: 0)
        file_pattern: Glob pattern for files to include (e.g., "*.py", "*.js")
    
    Returns:
        Matching lines with file paths and line numbers
    
    Examples:
        - grep("def.*init", "./src") - Find all __init__ methods
        - grep("import.*react", "./", file_pattern="*.tsx") - Find React imports in TSX files
        - grep("TODO|FIXME", "./") - Find all TODOs and FIXMEs
    """
    try:
        search_path = Path(path).expanduser()
        
        if not search_path.exists():
            return f"Error: Path not found: {path}"
        
        # Try ripgrep first (faster), fall back to grep
        rg_available = subprocess.run(
            ["which", "rg"], 
            capture_output=True, 
            text=True
        ).returncode == 0
        
        if rg_available:
            cmd = ["rg", "--line-number", "--no-heading", "--color=never"]
            
            if ignore_case:
                cmd.append("--ignore-case")
            
            if context_lines > 0:
                cmd.extend(["-C", str(context_lines)])
            
            if file_pattern:
                cmd.extend(["--glob", file_pattern])
            
            # Always ignore common directories
            cmd.extend([
                "--glob", "!node_modules",
                "--glob", "!__pycache__",
                "--glob", "!.git",
                "--glob", "!venv",
                "--glob", "!.venv",
                "--glob", "!dist",
                "--glob", "!build"
            ])
            
            cmd.append(pattern)
            cmd.append(str(search_path))
        else:
            # Fall back to grep
            cmd = ["grep", "-rn"]
            
            if ignore_case:
                cmd.append("-i")
            
            if context_lines > 0:
                cmd.extend(["-C", str(context_lines)])
            
            if file_pattern:
                cmd.extend(["--include", file_pattern])
            
            # Exclude common directories
            cmd.extend([
                "--exclude-dir=node_modules",
                "--exclude-dir=__pycache__",
                "--exclude-dir=.git",
                "--exclude-dir=venv",
                "--exclude-dir=.venv"
            ])
            
            cmd.append(pattern)
            cmd.append(str(search_path))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout.strip()
        
        if not output:
            return f"No matches found for pattern '{pattern}' in {path}"
        
        # Count and potentially limit results
        lines = output.split('\n')
        if len(lines) > 100:
            return f"Found {len(lines)} matches. Showing first 100:\n\n" + '\n'.join(lines[:100])
        
        return f"Found {len(lines)} matches:\n\n" + output
    
    except subprocess.TimeoutExpired:
        return "Error: Search timed out after 30 seconds"
    except FileNotFoundError:
        # Neither rg nor grep available, use Python fallback
        return _python_grep(pattern, path, ignore_case, file_pattern)
    except Exception as e:
        return f"Error during grep: {e}"


def _python_grep(pattern: str, path: str, ignore_case: bool, file_pattern: str) -> str:
    """Python fallback for grep when rg/grep are not available."""
    import re
    
    try:
        search_path = Path(path).expanduser()
        flags = re.IGNORECASE if ignore_case else 0
        regex = re.compile(pattern, flags)
        
        results = []
        skip_dirs = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'dist', 'build'}
        
        if search_path.is_file():
            files = [search_path]
        else:
            if file_pattern:
                files = search_path.rglob(file_pattern)
            else:
                files = search_path.rglob("*")
        
        for file_path in files:
            if any(skip in str(file_path) for skip in skip_dirs):
                continue
            
            if not file_path.is_file():
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
                for i, line in enumerate(content.split('\n'), 1):
                    if regex.search(line):
                        display = line.strip()[:150]
                        if len(line.strip()) > 150:
                            display += "..."
                        results.append(f"{file_path}:{i}: {display}")
            except (UnicodeDecodeError, PermissionError):
                continue
        
        if not results:
            return f"No matches found for pattern '{pattern}' in {path}"
        
        if len(results) > 100:
            return f"Found {len(results)} matches. Showing first 100:\n\n" + '\n'.join(results[:100])
        
        return f"Found {len(results)} matches:\n\n" + '\n'.join(results)
    
    except re.error as e:
        return f"Error: Invalid regex pattern - {e}"
    except Exception as e:
        return f"Error during search: {e}"


# Collect all tools
CODING_TOOLS = [
    read_file,
    write_file,
    edit_file,
    list_directory,
    grep,
    run_command,
    get_file_structure,
]

