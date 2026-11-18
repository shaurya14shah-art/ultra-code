import re

replacements = {
    "tree-of-thought": "🌲",
    "adversarial-coach": "⚔️",
    "spec-interviewer": "📋",
    "integration-enforcer": "🔗",
    "hypothesis-tester": "🧪",
    "architect": "🏛️",
    "ensemble-judge": "⚖️",
    "ui-architect": "🎨",
    "design-critic": "👁️",
}

with open("ultracode_app/agents/god_mode_personas.py", "r") as f:
    content = f.read()

for agent, emoji in replacements.items():
    # Find the AgentPersona definition and replace emoji="[...]"
    pattern = rf'(name="{agent}",\s*emoji=")[^"]+(")'
    content = re.sub(pattern, rf'\g<1>{emoji}\g<2>', content)

with open("ultracode_app/agents/god_mode_personas.py", "w") as f:
    f.write(content)
