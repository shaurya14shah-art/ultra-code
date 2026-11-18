"""
ULTRA CODE — Agent Persona Definitions
Each agent has a specialized system instruction, tool set, and safety policy.
These are used to create AG Agent instances via LocalAgentConfig.
"""

from dataclasses import dataclass, field
from typing import Callable

from ..tools.tools import (
    READ_TOOLS, WRITE_TOOLS, SHELL_TOOLS, GIT_TOOLS, STATE_TOOLS, ALL_TOOLS,
    MEMORY_TOOLS, SWARM_TOOLS, QUANT_TOOLS,
    read_file, write_file, edit_file, search_code, list_directory, find_files,
    run_shell, git_status, git_diff, git_log, git_commit,
    get_project_context, report_progress,
)


@dataclass
class AgentPersona:
    """Defines an agent's identity, tools, and behavior."""
    name: str
    emoji: str
    role: str
    system_instructions: str
    tools: list[Callable] = field(default_factory=list)
    enable_subagents: bool = False
    enable_shell: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT REGISTRY - GODMODE ULTRACODE
# ═══════════════════════════════════════════════════════════════════════════════

from .god_mode_personas import GOD_MODE_AGENTS

AGENT_REGISTRY: dict[str, AgentPersona] = GOD_MODE_AGENTS
ALL_AGENT_NAMES = list(AGENT_REGISTRY.keys())
