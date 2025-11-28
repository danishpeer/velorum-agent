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
READ_ONLY_TOOLS = {"read_file", "list_directory", "search_codebase", "get_file_structure"}

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
        return f"✅ Successfully wrote {len(content)} characters to {file_path}"
    
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
        
        return f"✅ Successfully edited {file_path}"
    
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
def search_codebase(directory: str, pattern: str, file_extensions: str = ".py,.js,.ts,.tsx,.jsx") -> str:
    """
    Search for a pattern in the codebase using grep-like functionality.
    
    Args:
        directory: Directory to search in
        pattern: Text pattern to search for (case-insensitive)
        file_extensions: Comma-separated file extensions to search (default: .py,.js,.ts,.tsx,.jsx)
    
    Returns:
        Search results with file paths and line numbers
    """
    try:
        path = Path(directory).expanduser()
        
        if not path.exists():
            return f"Error: Directory not found: {directory}"
        
        extensions = [ext.strip() for ext in file_extensions.split(',')]
        results = []
        
        for ext in extensions:
            for file_path in path.rglob(f"*{ext}"):
                # Skip common non-essential directories
                if any(skip in str(file_path) for skip in ['node_modules', '__pycache__', '.git', 'venv', '.venv']):
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        if pattern.lower() in line.lower():
                            # Truncate long lines
                            display_line = line.strip()[:100]
                            if len(line.strip()) > 100:
                                display_line += "..."
                            results.append(f"{file_path}:{i}: {display_line}")
                
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        if not results:
            return f"No matches found for '{pattern}' in {directory}"
        
        # Limit results
        if len(results) > 50:
            return f"Found {len(results)} matches. Showing first 50:\n\n" + '\n'.join(results[:50])
        
        return f"Found {len(results)} matches:\n\n" + '\n'.join(results)
    
    except Exception as e:
        return f"Error searching codebase: {e}"


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


# Collect all tools
CODING_TOOLS = [
    read_file,
    write_file,
    edit_file,
    list_directory,
    search_codebase,
    run_command,
    get_file_structure,
]

