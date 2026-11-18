import os

with open("user_msg.txt", "r") as f:
    content = f.read()

# Define the boundaries based on exact indices
files = {
    "SKILL.md": (25914, 38571),
    "scripts/pets.py": (12720, 21980),
    "references/pets.md": (21980, 25914),
    "scripts/orchestrator.py": (38571, 45225),
    "references/agent-roles.md": (45225, len(content))
}

base_dir = "/Users/USER/.gemini/config/skills/ultracode"

for file_path, (start, end) in files.items():
    full_path = os.path.join(base_dir, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content[start:end].strip() + "\n")
    print(f"Wrote {full_path}")
