"""
ULTRA CODE — Configuration Module
Centralizes all settings, paths, and environment config.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv


@dataclass
class UltraCodeConfig:
    """Central configuration for ULTRA CODE."""

    # ─── Working Directory ────────────────────────────────────────────────
    working_dir: str = field(default_factory=os.getcwd)

    # ─── Model Settings ──────────────────────────────────────────────────
    # AG SDK handles model routing; these are hints for system instructions
    model: str = "gemini-3.1-pro"
    heavy_model: str = "gemini-3.1-pro"

    # ─── Agent Settings ──────────────────────────────────────────────────
    max_concurrent_agents: int = 3
    enabled_agents: list[str] = field(default_factory=lambda: [
        "ideator", "architect", "planner", "coder", "debugger", "tester",
        "reviewer", "refactorer", "docwriter", "security", "designer", "devops"
    ])

    # ─── Permission Defaults ─────────────────────────────────────────────
    auto_approve_reads: bool = True
    auto_approve_safe_commands: bool = True
    denied_file_patterns: list[str] = field(default_factory=lambda: [
        "**/.env*", "**/*.key", "**/*.pem", "**/node_modules/**", "**/.git/objects/**"
    ])

    # ─── Persistence ─────────────────────────────────────────────────────
    save_dir: Optional[str] = None
    app_data_dir: Optional[str] = None

    # ─── UI ──────────────────────────────────────────────────────────────
    stream_output: bool = True
    show_agent_panel: bool = True
    verbose: bool = False

    # ─── API Key Rotation ────────────────────────────────────────────────
    api_key_pool: list[str] = field(default_factory=list)
    current_key_idx: int = 0

    @classmethod
    def load(cls, working_dir: Optional[str] = None) -> "UltraCodeConfig":
        """Load config from .ultracode.json in the working directory, then home, then env."""
        # Load environment variables from .env file (if present)
        load_dotenv()
        
        cfg = cls()
        if working_dir:
            cfg.working_dir = working_dir

        # Load project-level config
        project_config = Path(cfg.working_dir) / ".ultracode.json"
        if project_config.exists():
            try:
                data = json.loads(project_config.read_text())
                for key, value in data.items():
                    if hasattr(cfg, key):
                        setattr(cfg, key, value)
            except (json.JSONDecodeError, OSError):
                pass

        # Load home-level config (lower priority)
        home_config = Path.home() / ".ultracode.json"
        if home_config.exists():
            try:
                data = json.loads(home_config.read_text())
                for key, value in data.items():
                    if hasattr(cfg, key) and getattr(cfg, key) == getattr(cls(), key):
                        setattr(cfg, key, value)
            except (json.JSONDecodeError, OSError):
                pass

        # Environment overrides
        if os.environ.get("ULTRACODE_MODEL"):
            cfg.model = os.environ["ULTRACODE_MODEL"]
        if os.environ.get("ULTRACODE_VERBOSE"):
            cfg.verbose = True

        # Parse API key pool
        if os.environ.get("GEMINI_API_KEYS"):
            keys = [k.strip() for k in os.environ["GEMINI_API_KEYS"].split(",") if k.strip()]
            cfg.api_key_pool = keys
            
        # Ensure the main GEMINI_API_KEY is always first in the pool
        main_key = os.environ.get("GEMINI_API_KEY")
        if main_key:
            if main_key in cfg.api_key_pool:
                cfg.api_key_pool.remove(main_key)
            cfg.api_key_pool.insert(0, main_key)

        return cfg

    def is_agent_enabled(self, name: str) -> bool:
        return name.lower() in self.enabled_agents

    def get_key_count(self) -> int:
        return max(1, len(self.api_key_pool))
        
    def rotate_key(self) -> str:
        """Rotates to the next API key and sets it in the environment."""
        if not self.api_key_pool:
            return ""
            
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_key_pool)
        next_key = self.api_key_pool[self.current_key_idx]
        os.environ["GEMINI_API_KEY"] = next_key
        return next_key
