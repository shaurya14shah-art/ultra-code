import os
import glob
import yaml

# Emojis for colors
COLOR_TO_EMOJI = {
    "red": "🔴",
    "blue": "🔵",
    "green": "🟢",
    "yellow": "🟡",
    "orange": "🟠",
    "purple": "🟣"
}

def generate():
    agents_dir = "/Users/USER/.gemini/antigravity-ide/brain/40298de1-2b41-4efb-b0a0-16c392e01494/scratch/claude-god-mode/agents"
    md_files = glob.glob(os.path.join(agents_dir, "*.md"))
    
    python_code = [
        "\"\"\"Generated God Mode Personas from claude-god-mode\"\"\"",
        "from dataclasses import dataclass, field",
        "from typing import Callable",
        "from .personas import AgentPersona, READ_TOOLS, WRITE_TOOLS, SHELL_TOOLS, STATE_TOOLS, MEMORY_TOOLS",
        "",
        "GOD_MODE_AGENTS = {}",
        ""
    ]
    
    for md_file in md_files:
        with open(md_file, "r") as f:
            content = f.read()
        
        # Parse frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_raw = parts[1].strip()
                body = parts[2].strip()
                
                frontmatter = {}
                for line in frontmatter_raw.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        frontmatter[k.strip()] = v.strip()
                
                name = frontmatter.get("name", os.path.basename(md_file).replace(".md", ""))
                desc = frontmatter.get("description", "")
                color = frontmatter.get("color", "blue").lower()
                emoji = COLOR_TO_EMOJI.get(color, "🤖")
                tools_raw = frontmatter.get("tools", "")
                
                # Determine tools based on raw string
                tools_list = "[*READ_TOOLS, *STATE_TOOLS, *MEMORY_TOOLS]"
                if "Write" in tools_raw or "Edit" in tools_raw:
                    tools_list = "[*READ_TOOLS, *WRITE_TOOLS, *STATE_TOOLS, *MEMORY_TOOLS]"
                if "Bash" in tools_raw or "Shell" in tools_raw:
                    tools_list = "[*READ_TOOLS, *WRITE_TOOLS, *SHELL_TOOLS, *STATE_TOOLS, *MEMORY_TOOLS]"
                
                var_name = name.upper().replace("-", "_")
                
                # Format system instructions properly
                escaped_body = body.replace('\"\"\"', '\\"\\"\\"')
                
                agent_code = f"""
{var_name} = AgentPersona(
    name="{name}",
    emoji="{emoji}",
    role="{desc.split('.')[0]}",
    tools={tools_list},
    system_instructions=\"\"\"{escaped_body}\"\"\",
)

GOD_MODE_AGENTS["{name}"] = {var_name}
"""
                python_code.append(agent_code)
                
    with open("/Users/USER/AG/ultra-code/ultracode_app/agents/god_mode_personas.py", "w") as f:
        f.write("\n".join(python_code))
        
    print(f"Generated {len(md_files)} God Mode agents.")

if __name__ == "__main__":
    generate()
