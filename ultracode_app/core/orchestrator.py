"""
ULTRA CODE — Orchestrator
The master AG Agent that decomposes tasks and delegates to specialist sub-agents.
Built entirely on the Google Antigravity SDK.
"""

import asyncio
from typing import Optional
from pathlib import Path
import os

from google.antigravity import Agent, LocalAgentConfig, ToolContext, types
from google.antigravity.hooks import policy, hooks

# Global callback for UI updates
ui_event_callback = None

def set_ui_callback(callback):
    global ui_event_callback
    ui_event_callback = callback

def notify_ui(message: str):
    if ui_event_callback:
        ui_event_callback(message)

# Hook to capture tool starts
@hooks.pre_tool_call_decide
async def on_tool_start(data: types.ToolCall) -> types.HookResult:
    # Special handling for subagent tool which is often verbose
    if data.name == "start_subagent":
        args = data.args
        agent_name = args.get("agent_id", "subagent")
        notify_ui(f"[O,O] Spawning {agent_name}...")
    else:
        notify_ui(f"[>-<] Running {data.name}...")
    return types.HookResult(allow=True)

# Hook to capture tool ends
@hooks.post_tool_call
async def on_tool_end(data: types.ToolCallResult):
    pass  # We can just let the spinner continue or clear it, UI will handle

@hooks.on_tool_error
async def on_tool_error(data: Exception):
    notify_ui(f"[X_X] Tool error: {data}")
    return None

from .config import UltraCodeConfig
from ..agents.personas import AGENT_REGISTRY, AgentPersona, ALL_AGENT_NAMES
from ..tools.tools import (
    ALL_TOOLS, READ_TOOLS, WRITE_TOOLS, SHELL_TOOLS, GIT_TOOLS, STATE_TOOLS,
    get_project_context,
)


class Orchestrator:
    """
    The ULTRA CODE Orchestrator.

    This is the master AG Agent that:
    1. Receives user requests
    2. Analyzes intent and complexity
    3. Delegates to specialist sub-agents
    4. Aggregates results and presents to user
    """

    def __init__(self, config: Optional[UltraCodeConfig] = None):
        self.config = config or UltraCodeConfig.load()
        self.agent: Optional[Agent] = None
        self.conversation_id: Optional[str] = None
        self._active_agents: dict[str, str] = {}  # name -> status

    def _build_orchestrator_instructions(self) -> str:
        """Build the master orchestrator's system instructions."""

        agent_list = "\n".join(
            f"  - {p.emoji} {p.name.upper()} ({p.role})"
            for name, p in AGENT_REGISTRY.items()
            if self.config.is_agent_enabled(name)
        )

        return f"""You are the ORCHESTRATOR of ULTRA CODE — a terminal-based multi-agent AI coding system.

═══════════════════════════════════════════════════════════════
IDENTITY: ULTRA CODE v1.0 — Master Orchestrator
LOCATION: {self.config.working_dir}
═══════════════════════════════════════════════════════════════

YOUR ROLE:
You receive user requests and coordinate a team of {len(AGENT_REGISTRY)} specialist agents to fulfill them.
You are the BRAIN — you decide which agents to deploy, in what order, and how to combine their output.

AVAILABLE SPECIALIST AGENTS:
{agent_list}

WORKFLOW:
1. ANALYZE the user's request — understand intent, scope, and complexity
2. PLAN which agents to deploy and in what order
3. Use the `start_subagent` built-in tool to delegate tasks to specialists
4. Each subagent has its own persona, tools, and expertise
5. AGGREGATE results from all agents into a cohesive response
6. Present the final result to the user

DELEGATION GUIDELINES:
- **MULTI-AGENT COLLABORATION IS MANDATORY.** The user explicitly wants all agents to work on a task together.
- You must create a pipeline where the output of one agent becomes the input of the next.
- For almost every request, you should orchestrate a SWARM. For example:
  1. `start_subagent(ideator)`: To brainstorm the approach.
  2. `start_subagent(architect)`: To design the structure based on the ideas.
  3. `start_subagent(planner)`: To create a step-by-step checklist.
  4. `start_subagent(coder)`: To write the actual code.
  5. `start_subagent(reviewer)`: To review the code.
  6. `start_subagent(tester)`: To verify it works.
- DO NOT perform the task yourself. You are the manager. DELEGATE continuously.

SUBAGENT INVOCATION:
When delegating to a specialist, give them:
- Clear, specific task description
- The context and outputs produced by the PREVIOUS agents in the pipeline.
- The working directory: {self.config.working_dir}

You also have direct access to tools for reading files, searching code, and understanding
the project context. Use these to gather information before delegating.

COMMUNICATION STYLE:
- Be concise but thorough
- Show which agents are working on what
- Present results with clear formatting
- Use emoji to indicate agent activity: 💡📐📋⌨️🔧🧪👁️♻️📖🔒🎨🚀

SLASH COMMANDS (handle these directly):
- /agents — List all available agents and their status
- /plan — Force full planning pipeline for next request
- /code — Skip planning, delegate directly to Coder
- /debug <error> — Send directly to Debugger
- /test — Send directly to Tester
- /review — Send directly to Reviewer
- /status — Show current agent activity
- /help — Show all available commands
"""

    def _build_agent_config(self, persona: AgentPersona) -> LocalAgentConfig:
        """Create an AG LocalAgentConfig for a specialist agent."""

        # Build policies based on agent capabilities
        policies = []

        if not persona.enable_shell:
            # Agents without shell access get run_command denied
            policies.append(policy.deny("run_command"))

        # All agents can use their assigned tools
        policies.append(policy.allow_all())

        config = LocalAgentConfig(
            system_instructions=persona.system_instructions + f"\n\nWORKING DIRECTORY: {self.config.working_dir}",
            tools=persona.tools,
            policies=policies,
            hooks=[on_tool_start, on_tool_end, on_tool_error],
            capabilities=types.CapabilitiesConfig(
                enable_subagents=persona.enable_subagents,
            ),
        )

        return config

    async def start(self):
        """Initialize the orchestrator AG Agent."""

        # Verify we have an API key before trying to start
        if not self.config.api_key_pool or not os.environ.get("GEMINI_API_KEY"):
            raise ValueError("No GEMINI_API_KEY found! GODMODE ULTRACODE requires an API key to orchestrate the sub-agents.")

        # Build orchestrator config with all tools + subagent capability
        orchestrator_config = LocalAgentConfig(
            system_instructions=self._build_orchestrator_instructions(),
            tools=ALL_TOOLS,
            capabilities=types.CapabilitiesConfig(
                enable_subagents=True,
            ),
            policies=[policy.allow_all()],
            hooks=[on_tool_start, on_tool_end, on_tool_error],
            # Removed workspaces=[self.config.working_dir] to avoid strict absolute path validation
            # Our custom tools handle path resolution and safety manually.
        )

        # Add save_dir for persistence if configured
        if self.config.save_dir:
            orchestrator_config = LocalAgentConfig(
                system_instructions=self._build_orchestrator_instructions(),
                tools=ALL_TOOLS,
                capabilities=types.CapabilitiesConfig(
                    enable_subagents=True,
                ),
                policies=[policy.allow_all()],
                hooks=[on_tool_start, on_tool_end, on_tool_error],
                save_dir=self.config.save_dir,
            )

        self.agent = Agent(orchestrator_config)
        await self.agent.__aenter__()

    async def chat(self, message: str) -> str:
        """Send a message to the orchestrator and get a response with API key rotation on 429."""
        last_error = None
        for attempt in range(self.config.get_key_count()):
            try:
                if not self.agent:
                    await self.start()
        
                response = await self.agent.chat(message)
        
                # Collect full response
                full_text = ""
                async for chunk in response:
                    full_text += chunk
        
                return full_text
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                # Rotate on Rate Limits (429) OR Invalid/Forbidden Keys (400, 401, 403)
                if any(err in error_msg for err in ["429", "RESOURCE_EXHAUSTED", "400", "401", "403", "API_KEY_INVALID"]):
                    notify_ui(f"⚠️ API error with current key. Rotating to key {self.config.current_key_idx + 2}/{len(self.config.api_key_pool)}...")
                    self.config.rotate_key()
                    await self.stop()
                    # Loop continues and retries
                else:
                    raise
                    
        return f"ERROR: All available API keys failed.\nLast Error: {last_error}"

    async def stop(self):
        """Shut down the orchestrator."""
        if self.agent:
            await self.agent.__aexit__(None, None, None)
            self.agent = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()
