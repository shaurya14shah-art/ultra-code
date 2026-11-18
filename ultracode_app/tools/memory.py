import os
import re
from pathlib import Path
from typing import Optional

MEMORY_DIR = Path(".ultra_memory")

def _ensure_memory_dir():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

def write_memory(topic: str, content: str) -> str:
    """Create or update a memory note on a specific topic.
    
    Args:
        topic: The title or subject of the memory (e.g., 'auth_flow', 'project_goals'). 
               This will be used as the filename (topic.md).
        content: The detailed markdown content to store.
    """
    _ensure_memory_dir()
    
    # Sanitize topic name
    safe_topic = re.sub(r'[^a-zA-Z0-9_\-]', '_', topic.lower().replace(' ', '_'))
    file_path = MEMORY_DIR / f"{safe_topic}.md"
    
    try:
        file_path.write_text(content, encoding="utf-8")
        return f"SUCCESS: Memory saved to {file_path}"
    except Exception as e:
        return f"ERROR saving memory: {e}"

def read_memory(topic: str) -> str:
    """Read the contents of a specific memory note.
    
    Args:
        topic: The title of the memory to read.
    """
    _ensure_memory_dir()
    safe_topic = re.sub(r'[^a-zA-Z0-9_\-]', '_', topic.lower().replace(' ', '_'))
    file_path = MEMORY_DIR / f"{safe_topic}.md"
    
    if not file_path.exists():
        return f"ERROR: Memory '{topic}' not found."
        
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"ERROR reading memory: {e}"

def search_memory(query: str) -> str:
    """Search across all memory notes for a specific query.
    
    Args:
        query: The search term or phrase to look for.
    """
    _ensure_memory_dir()
    results = []
    
    for md_file in MEMORY_DIR.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if query.lower() in content.lower():
                results.append(f"- [{md_file.stem}] Match found.")
        except Exception:
            continue
            
    if not results:
        return f"No memories found matching '{query}'"
        
    return "Search Results:\n" + "\n".join(results)

def visualize_memory() -> str:
    """Visualize the structural map of the memory vault.
    Returns a textual tree representation of all stored memories.
    """
    _ensure_memory_dir()
    files = list(MEMORY_DIR.glob("*.md"))
    
    if not files:
        return "The memory vault is currently empty."
        
    lines = ["🧠 Ultra Code Memory Vault:"]
    
    for i, md_file in enumerate(sorted(files)):
        prefix = "└── " if i == len(files) - 1 else "├── "
        try:
            # Try to grab the first line as a title
            content = md_file.read_text(encoding="utf-8").strip().splitlines()
            title = content[0][:50] + "..." if content and len(content[0]) > 50 else (content[0] if content else "(Empty)")
            lines.append(f"{prefix}{md_file.name} - {title}")
        except Exception:
            lines.append(f"{prefix}{md_file.name}")
            
    return "\n".join(lines)
