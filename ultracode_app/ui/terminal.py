"""
ULTRA CODE — Terminal UI (Textual)
A premium, full-screen Terminal User Interface for the 12-agent fleet.
"""

import asyncio
from typing import Optional
import re
import time
import os
import json
import glob
import subprocess

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual.widgets import Header, Footer, Static, Input, Markdown, Label, ListView, ListItem, ProgressBar
from textual.worker import Worker, get_current_worker
from textual import work

from ..core.orchestrator import Orchestrator, set_ui_callback
from ..core.config import UltraCodeConfig
from ..agents.personas import AGENT_REGISTRY

ASCII_ART = r"""
██╗   ██╗███╗   ██╗██╗██╗   ██╗███████╗██████╗ ███████╗███████╗
██║   ██║████╗  ██║██║██║   ██║██╔════╝██╔══██╗██╔════╝██╔════╝
██║   ██║██╔██╗ ██║██║██║   ██║█████╗  ██████╔╝███████╗█████╗  
██║   ██║██║╚██╗██║██║╚██╗ ██╔╝██╔══╝  ██╔══██╗╚════██║██╔══╝  
╚██████╔╝██║ ╚████║██║ ╚████╔╝ ███████╗██║  ██║███████║███████╗
 ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝
              [ G O D M O D E   O N L I N E ]
"""

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

class AgentSidebar(Vertical):
    """Sidebar showing all available agents and their status."""
    
    def on_mount(self):
        self.active_agent = None
        self.spinner_frame = 0
        self.set_interval(0.1, self.animate_spinner)

    def compose(self) -> ComposeResult:
        yield Label("/// AGENT FLEET ///", id="sidebar-title")
        for name, persona in AGENT_REGISTRY.items():
            lbl = Label(f"  {persona.emoji} {name.upper()}", id=f"agent-{name}", classes="agent-list-item agent-idle")
            yield lbl

    def animate_spinner(self):
        if not self.active_agent:
            return
            
        self.spinner_frame = (self.spinner_frame + 1) % len(SPINNER_FRAMES)
        char = SPINNER_FRAMES[self.spinner_frame]
        
        try:
            lbl = self.query_one(f"#agent-{self.active_agent}", Label)
            persona = AGENT_REGISTRY.get(self.active_agent)
            if persona:
                lbl.update(f"{char} {persona.emoji} {self.active_agent.upper()} {char}")
        except Exception:
            pass
            
    def set_agent_active(self, agent_name: str):
        """Highlight an agent."""
        self.active_agent = agent_name if agent_name in AGENT_REGISTRY else None
        
        # Reset all
        for name, persona in AGENT_REGISTRY.items():
            try:
                lbl = self.query_one(f"#agent-{name}", Label)
                if name == self.active_agent:
                    lbl.remove_class("agent-idle")
                    lbl.add_class("agent-active")
                else:
                    lbl.remove_class("agent-active")
                    lbl.add_class("agent-idle")
                    lbl.update(f"  {persona.emoji} {name.upper()}")
            except:
                pass

class UltraCodeApp(App):
    """The main Textual application for ULTRA CODE."""

    CSS_PATH = "terminal.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, config: Optional[UltraCodeConfig] = None):
        super().__init__()
        self.config = config or UltraCodeConfig.load()
        self.orchestrator = Orchestrator(self.config)
        self.turn_count = 0
        
        # Register global callback for AG SDK hooks (tool execution)
        set_ui_callback(self.on_agent_event)

    def on_agent_event(self, message: str):
        """Called by the orchestrator hooks from a background thread."""
        self.call_from_thread(self.update_status, message)
        
        # Check if spawning an agent
        if "Spawning" in message:
            # Extract agent name, e.g., "Spawning architect..."
            match = re.search(r"Spawning (\w[\w-]*)\.\.\.", message)
            if match:
                agent_name = match.group(1)
                self.call_from_thread(self.highlight_agent, agent_name)

    def highlight_agent(self, agent_name: str):
        try:
            sidebar = self.query_one(AgentSidebar)
            sidebar.set_agent_active(agent_name)
        except Exception:
            pass

    def update_status(self, message: str):
        """Update the status bar."""
        try:
            status_bar = self.query_one("#status-bar", Label)
            status_bar.update(message)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Horizontal():
            yield AgentSidebar(id="sidebar")
            
            with Vertical(id="main-area"):
                yield Static(ASCII_ART, id="header-panel")
                yield VerticalScroll(id="chat-container")
                yield Label("SYSTEM: ONLINE. AWAITING DIRECTIVES.", id="status-bar")
                yield Input(placeholder="> INITIATE NEURAL LINK...", id="input-box")

    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = f"GODMODE ULTRACODE v3.7 — {self.config.model}"
        
        chat = self.query_one("#chat-container", VerticalScroll)
        greeting = Markdown("### SYSTEM INITIALIZED\n\nNeural link established. The fleet is standing by.\nType `/help` for commands or give a directive.")
        greeting.add_class("system-message")
        chat.mount(greeting)
        
        self.query_one(Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle prompt submission."""
        user_input = event.value.strip()
        if not user_input:
            return

        event.input.value = ""
        
        if user_input.lower() in ("/exit", "/quit"):
            self.exit()
            return
            
        if user_input.lower() in ("s1", "/reload"):
            chat = self.query_one("#chat-container", VerticalScroll)
            chat.remove_children()
            greeting = Markdown("### SYSTEM PURGED\n\nMemory cleared. Awaiting new sequence.")
            greeting.add_class("system-message")
            chat.mount(greeting)
            return

        if user_input.lower() in ("s2", "/memory"):
            script_path = os.path.expanduser("~/.gemini/config/skills/obsidian-terminal-memory/scripts/visualize_graph.py")
            try:
                result = subprocess.run(["python3", script_path], capture_output=True, text=True)
                output = result.stdout if result.stdout else result.stderr
            except Exception as e:
                output = str(e)
                
            chat = self.query_one("#chat-container", VerticalScroll)
            user_md = Markdown(f"**Directive:**\n{user_input}")
            user_md.add_class("user-message")
            chat.mount(user_md)
            
            md = Markdown(f"**Neural Graph Extraction:**\n```\n{output}\n```")
            md.add_class("agent-message")
            chat.mount(md)
            chat.scroll_end(animate=False)
            return
            
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd == "/help":
                help_text = """### COMMAND DIRECTIVES
- `/help` - Show this datapad
- `/clear` - Purge the terminal
- `/swarm <task>` - Deploy core fleet sequentially
- `/hyper <task>` - Deploy massive hyper-swarm (DANGER: High Token Burn)
"""
                chat = self.query_one("#chat-container", VerticalScroll)
                md = Markdown(help_text)
                md.add_class("system-message")
                chat.mount(md)
                chat.scroll_end(animate=False)
                return
                
            if cmd == "/clear":
                chat = self.query_one("#chat-container", VerticalScroll)
                chat.remove_children()
                return
                
            if cmd == "/plan":
                user_input = f"[PLANNING MODE] Create a detailed implementation plan for: {args}"
            elif cmd == "/code":
                user_input = f"[DIRECT CODING] Implement the following without a planning phase: {args}"
            elif cmd == "/swarm":
                user_input = f"[SWARM MODE] Deploy the 5-pet swarm to execute: {args}"
            elif cmd == "/hyper":
                user_input = f"[HYPER MODE] Deploy the 12-agent hyper-swarm to execute: {args}"
            else:
                self.update_status(f"Unknown command: {cmd}")
                return

        self.turn_count += 1
        
        chat = self.query_one("#chat-container", VerticalScroll)
        user_md = Markdown(f"**USER >>**\n{user_input}")
        user_md.add_class("user-message")
        chat.mount(user_md)
        chat.scroll_end(animate=False)
        
        agent_md = Markdown("...")
        agent_md.add_class("agent-message")
        chat.mount(agent_md)
        chat.scroll_end(animate=False)
        
        self.update_status("[...] PROCESSING NEURAL LINK...")
        event.input.disabled = True
        
        self.run_orchestrator(user_input, agent_md, event.input)

    @work(thread=True)
    def run_orchestrator(self, prompt: str, markdown_widget: Markdown, input_widget: Input) -> None:
        """Run the orchestrator chat in a background thread."""
        worker = get_current_worker()
        
        async def _run():
            full_response = ""
            try:
                req_path = "/Users/USER/AG/ultra-code/.ipc_request.txt"
                res_path = "/Users/USER/AG/ultra-code/.ipc_response.txt"
                stream_path = "/Users/USER/AG/ultra-code/.ipc_stream.txt"
                
                brain_dir = "/Users/USER/.gemini/antigravity-ide/brain/"
                try:
                    latest_dir = max(glob.glob(os.path.join(brain_dir, '*-*-*-*-*')), key=os.path.getmtime)
                    transcript_path = os.path.join(latest_dir, ".system_generated/logs/transcript.jsonl")
                except ValueError:
                    transcript_path = ""

                last_line_count = 0
                if os.path.exists(transcript_path):
                    with open(transcript_path, "r") as tf:
                        last_line_count = sum(1 for _ in tf)
                        
                with open(req_path, "w") as f:
                    f.write(prompt)
                
                self.call_from_thread(self.update_status, ">>> ORCHESTRATOR ACTIVE")
                while not os.path.exists(res_path):
                    if os.path.exists(stream_path):
                        try:
                            with open(stream_path, "r") as f:
                                chunk = f.read()
                            if chunk:
                                full_response += chunk + "\n"
                                self.call_from_thread(markdown_widget.update, full_response)
                                self.call_from_thread(self.query_one("#chat-container", VerticalScroll).scroll_end, animate=False)
                                open(stream_path, "w").close()
                        except Exception:
                            pass
                            
                    if os.path.exists(transcript_path):
                        try:
                            with open(transcript_path, "r") as tf:
                                lines = tf.readlines()
                                if len(lines) > last_line_count:
                                    for line in lines[last_line_count:]:
                                        if not line.strip(): continue
                                        data = json.loads(line)
                                        if data.get("type") == "PLANNER_RESPONSE" and data.get("tool_calls"):
                                            for tool in data["tool_calls"]:
                                                name = tool.get("name", "")
                                                args = tool.get("arguments", {})
                                                
                                                formatted = ""
                                                if name in ["multi_replace_file_content", "replace_file_content"]:
                                                    target = args.get("TargetFile", "")
                                                    formatted = f"\n> ⚠️ **FILE BREACH:** Editing `{os.path.basename(target)}`\n"
                                                elif name == "run_command":
                                                    cmd = args.get("CommandLine", "")
                                                    formatted = f"\n> ⚡ **SYSTEM OVERRIDE:** `{cmd}`\n"
                                                elif name == "view_file":
                                                    target = args.get("AbsolutePath", "")
                                                    formatted = f"\n> 👁️ **SCANNING:** `{os.path.basename(target)}`\n"
                                                elif name == "write_to_file":
                                                    target = args.get("TargetFile", "")
                                                    formatted = f"\n> 💾 **SYNTHESIZING:** `{os.path.basename(target)}`\n"
                                                    
                                                if formatted:
                                                    full_response += formatted
                                                    self.call_from_thread(markdown_widget.update, full_response)
                                                    self.call_from_thread(self.query_one("#chat-container", VerticalScroll).scroll_end, animate=False)
                                    last_line_count = len(lines)
                        except Exception:
                            pass
                            
                    time.sleep(0.3)
                    if worker.is_cancelled:
                        break
                        
                if not worker.is_cancelled:
                    with open(res_path, "r") as f:
                        final_chunk = f.read()
                    os.remove(res_path)
                    
                    for char in final_chunk:
                        full_response += char
                        self.call_from_thread(markdown_widget.update, full_response)
                        self.call_from_thread(self.query_one("#chat-container", VerticalScroll).scroll_end, animate=False)
                        time.sleep(0.005) # Super fast matrix-like typing
                        if worker.is_cancelled:
                            break
                            
                self.call_from_thread(self.update_status, f"CYCLE {self.turn_count} COMPLETE.")
                self.call_from_thread(self.highlight_agent, "") # Reset highlighting
            except Exception as e:
                self.call_from_thread(markdown_widget.update, full_response + f"\n\n**[FATAL SYSTEM ERROR]:** {e}")
                self.call_from_thread(self.update_status, "SYSTEM HALTED.")
            finally:
                def _reenable():
                    input_widget.disabled = False
                    input_widget.focus()
                self.call_from_thread(_reenable)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run())
        finally:
            loop.close()

    async def run_app(self):
        await super().run_async()
