"""
ULTRA CODE — Custom Tools for AG Agents
These Python functions are registered as AG custom tools, giving agents
the ability to read, write, search, and execute within the project.
"""

import os
import subprocess
import fnmatch
from pathlib import Path
from typing import Optional
from google.antigravity import ToolContext

from .memory import write_memory, read_memory, search_memory, visualize_memory
from .swarm import run_dynamic_swarm
from .quant_engine import quant_predict, quant_update# ═══════════════════════════════════════════════════════════════════════════════
# FILE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def read_file(file_path: str, start_line: int = 1, end_line: int = -1) -> str:
    """Read the contents of a file. Returns the file content as a string.

    Args:
        file_path: Absolute or relative path to the file to read.
        start_line: First line to read (1-indexed). Defaults to 1.
        end_line: Last line to read (1-indexed, inclusive). -1 means read to end.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        return f"ERROR: File not found: {path}"
    if not path.is_file():
        return f"ERROR: Not a file: {path}"

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        total = len(lines)

        start = max(0, start_line - 1)
        end = total if end_line == -1 else min(end_line, total)

        selected = lines[start:end]
        numbered = [f"{i + start + 1:>4} │ {line}" for i, line in enumerate(selected)]

        header = f"── {path.name} ({total} lines) ──"
        if start > 0 or end < total:
            header += f" [showing lines {start + 1}-{end}]"

        return header + "\n" + "\n".join(numbered)
    except Exception as e:
        return f"ERROR reading {path}: {e}"


def write_file(file_path: str, content: str, create_dirs: bool = True) -> str:
    """Create or overwrite a file with the given content.

    Args:
        file_path: Absolute or relative path to the file to write.
        content: The full content to write to the file.
        create_dirs: Whether to create parent directories if they don't exist.
    """
    path = Path(file_path).resolve()

    # Safety checks
    denied = [".env", ".key", ".pem"]
    if any(path.name.endswith(ext) for ext in denied):
        return f"DENIED: Cannot write to sensitive file: {path.name}"

    if "node_modules" in str(path) or ".git/objects" in str(path):
        return f"DENIED: Cannot write inside protected directory: {path}"

    try:
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        lines = content.count("\n") + 1
        return f"SUCCESS: Wrote {lines} lines to {path}"
    except Exception as e:
        return f"ERROR writing {path}: {e}"


def edit_file(file_path: str, target_content: str, replacement_content: str) -> str:
    """Edit a file by replacing a specific block of text with new content.

    Args:
        file_path: Path to the file to edit.
        target_content: The exact text to find and replace. Must match exactly.
        replacement_content: The new text to replace the target with.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        return f"ERROR: File not found: {path}"

    try:
        original = path.read_text(encoding="utf-8")
        if target_content not in original:
            return f"ERROR: Target content not found in {path.name}. Make sure it matches exactly."

        count = original.count(target_content)
        if count > 1:
            return f"WARNING: Found {count} occurrences. Please provide more specific target content."

        modified = original.replace(target_content, replacement_content, 1)
        path.write_text(modified, encoding="utf-8")

        # Show what changed
        target_lines = target_content.count("\n") + 1
        repl_lines = replacement_content.count("\n") + 1
        return f"SUCCESS: Replaced {target_lines} lines with {repl_lines} lines in {path.name}"
    except Exception as e:
        return f"ERROR editing {path}: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# FILE SEARCH & PROJECT NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

def search_code(query: str, directory: str = ".", file_pattern: str = "*") -> str:
    """Search for a text pattern across files in a directory using grep.

    Args:
        query: The text or regex pattern to search for.
        directory: The directory to search in. Defaults to current directory.
        file_pattern: Glob pattern to filter files (e.g., '*.py', '*.ts').
    """
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return f"ERROR: Directory not found: {dir_path}"

    try:
        cmd = ["grep", "-rnI", "--include", file_pattern, query, str(dir_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        if not output:
            return f"No matches found for '{query}' in {dir_path}"

        lines = output.split("\n")
        if len(lines) > 50:
            lines = lines[:50]
            lines.append(f"... ({len(output.split(chr(10)))} total matches, showing first 50)")

        return "\n".join(lines)
    except subprocess.TimeoutExpired:
        return "ERROR: Search timed out after 15 seconds."
    except Exception as e:
        return f"ERROR searching: {e}"


def list_directory(directory: str = ".", max_depth: int = 3) -> str:
    """List the contents of a directory in a tree-like format.

    Args:
        directory: The directory to list. Defaults to current directory.
        max_depth: Maximum depth to recurse into subdirectories.
    """
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return f"ERROR: Directory not found: {dir_path}"

    ignore = {".git", "node_modules", "__pycache__", ".next", "dist", "build", ".venv", "venv"}
    lines = [f"📁 {dir_path.name}/"]

    def _walk(path: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return

        dirs = [e for e in entries if e.is_dir() and e.name not in ignore and not e.name.startswith(".")]
        files = [e for e in entries if e.is_file() and not e.name.startswith(".")]

        items = dirs + files
        for i, entry in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "

            if entry.is_dir():
                child_count = sum(1 for _ in entry.iterdir()) if entry.exists() else 0
                lines.append(f"{prefix}{connector}📁 {entry.name}/ ({child_count} items)")
                _walk(entry, prefix + extension, depth + 1)
            else:
                size = entry.stat().st_size
                size_str = _format_size(size)
                lines.append(f"{prefix}{connector}📄 {entry.name} ({size_str})")

    def _format_size(b: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if b < 1024:
                return f"{b:.0f} {unit}" if unit == "B" else f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"

    _walk(dir_path, "", 0)

    if len(lines) > 100:
        lines = lines[:100]
        lines.append("... (truncated at 100 entries)")

    return "\n".join(lines)


def find_files(pattern: str, directory: str = ".") -> str:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern to match (e.g., '*.py', 'test_*.py', '**/*.tsx').
        directory: Root directory to search from.
    """
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return f"ERROR: Directory not found: {dir_path}"

    ignore = {"node_modules", ".git", "__pycache__", ".next", "dist", "build"}
    matches = []

    for match in dir_path.rglob(pattern):
        if any(part in ignore for part in match.parts):
            continue
        rel = match.relative_to(dir_path)
        matches.append(str(rel))

    if not matches:
        return f"No files matching '{pattern}' found in {dir_path}"

    matches.sort()
    if len(matches) > 50:
        return "\n".join(matches[:50]) + f"\n... ({len(matches)} total, showing first 50)"

    return "\n".join(matches)


# ═══════════════════════════════════════════════════════════════════════════════
# SHELL EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def run_shell(command: str, working_dir: str = ".", timeout: int = 30) -> str:
    """Execute a shell command and return the output.

    Args:
        command: The shell command to execute.
        working_dir: Working directory for the command.
        timeout: Maximum execution time in seconds.
    """
    # Safety: block obviously dangerous commands
    dangerous = ["rm -rf /", "rm -rf ~", "mkfs", "dd if=", ": > /dev/sda", "chmod -R 777 /"]
    for d in dangerous:
        if d in command:
            return f"BLOCKED: Command contains dangerous pattern: {d}"

    cwd = Path(working_dir).resolve()
    if not cwd.exists():
        return f"ERROR: Working directory not found: {cwd}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=timeout,
            env={**os.environ, "PAGER": "cat"},
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}" if output else result.stderr

        output = output.strip()
        if not output:
            output = f"(command completed with exit code {result.returncode})"

        # Truncate very long output
        if len(output) > 10000:
            output = output[:10000] + "\n... (output truncated at 10,000 chars)"

        return f"[Exit {result.returncode}]\n{output}"
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"ERROR running command: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# GIT OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def git_status(directory: str = ".") -> str:
    """Get the current git status of the repository.

    Args:
        directory: Path to the git repository.
    """
    return run_shell("git status --short --branch", directory)


def git_diff(file_path: str = "", staged: bool = False, directory: str = ".") -> str:
    """Show git diff for changes.

    Args:
        file_path: Specific file to diff. Empty string for all changes.
        staged: If True, show staged changes. If False, show unstaged.
        directory: Path to the git repository.
    """
    cmd = "git diff"
    if staged:
        cmd += " --staged"
    if file_path:
        cmd += f" -- {file_path}"
    return run_shell(cmd, directory)


def git_log(count: int = 10, directory: str = ".") -> str:
    """Show recent git commit history.

    Args:
        count: Number of recent commits to show.
        directory: Path to the git repository.
    """
    return run_shell(f"git log --oneline --graph -n {count}", directory)


def git_commit(message: str, directory: str = ".") -> str:
    """Stage all changes and create a git commit.

    Args:
        message: The commit message.
        directory: Path to the git repository.
    """
    stage_result = run_shell("git add -A", directory)
    commit_result = run_shell(f'git commit -m "{message}"', directory)
    return f"{stage_result}\n{commit_result}"


# ═══════════════════════════════════════════════════════════════════════════════
# TASK MANAGEMENT (inter-agent communication via ToolContext)
# ═══════════════════════════════════════════════════════════════════════════════

def report_progress(status: str, details: str, ctx: ToolContext) -> str:
    """Report the current progress of the agent's task back to the orchestrator.

    Args:
        status: Current status: 'in_progress', 'completed', 'blocked', 'failed'.
        details: Human-readable description of what was done or what's blocking.
        ctx: Tool context for state management.
    """
    progress = ctx.get_state("progress_log", [])
    progress.append({
        "status": status,
        "details": details,
    })
    ctx.set_state("progress_log", progress)
    return f"Progress reported: [{status}] {details}"


def get_project_context(directory: str = ".") -> str:
    """Analyze the project structure and return a summary of the codebase.

    Args:
        directory: Root directory of the project to analyze.
    """
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return f"ERROR: Directory not found: {dir_path}"

    # Detect project type
    indicators = {
        "package.json": "Node.js/JavaScript",
        "pyproject.toml": "Python",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "pom.xml": "Java (Maven)",
        "build.gradle": "Java/Kotlin (Gradle)",
        "Gemfile": "Ruby",
        "Package.swift": "Swift",
        "CMakeLists.txt": "C/C++",
    }

    project_type = "Unknown"
    for file, lang in indicators.items():
        if (dir_path / file).exists():
            project_type = lang
            break

    # Count files by extension
    ext_counts: dict[str, int] = {}
    ignore = {"node_modules", ".git", "__pycache__", ".next", "dist", "build", ".venv"}
    total_files = 0
    for f in dir_path.rglob("*"):
        if any(part in ignore for part in f.parts):
            continue
        if f.is_file():
            total_files += 1
            ext = f.suffix.lower() or "(no ext)"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

    top_exts = sorted(ext_counts.items(), key=lambda x: -x[1])[:10]

    # Read key config files
    config_content = ""
    for config_file in ["package.json", "pyproject.toml", "README.md"]:
        cfg_path = dir_path / config_file
        if cfg_path.exists():
            content = cfg_path.read_text(encoding="utf-8", errors="replace")[:2000]
            config_content += f"\n─── {config_file} ───\n{content}\n"

    summary = f"""PROJECT ANALYSIS: {dir_path.name}
Type: {project_type}
Total files: {total_files}
File distribution: {', '.join(f'{ext}: {cnt}' for ext, cnt in top_exts)}
{config_content}"""

    return summary


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY — grouped by agent capability level
# ═══════════════════════════════════════════════════════════════════════════════

# Read-only tools (safe for all agents)
READ_TOOLS = [read_file, search_code, list_directory, find_files, get_project_context]

# Write tools (need permission)
WRITE_TOOLS = [write_file, edit_file]

# Shell tools (need permission)
SHELL_TOOLS = [run_shell]

# Git tools
GIT_TOOLS = [git_status, git_diff, git_log, git_commit]

# State tools
STATE_TOOLS = [report_progress]

# Memory tools
MEMORY_TOOLS = [write_memory, read_memory, search_memory, visualize_memory]

# Swarm tools
SWARM_TOOLS = [run_dynamic_swarm]

# Quant tools
QUANT_TOOLS = [quant_predict, quant_update]

# Full toolkit
ALL_TOOLS = READ_TOOLS + WRITE_TOOLS + SHELL_TOOLS + GIT_TOOLS + STATE_TOOLS + MEMORY_TOOLS + SWARM_TOOLS + QUANT_TOOLS
