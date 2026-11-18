import asyncio
import random
from typing import List

from google.antigravity import Agent, LocalAgentConfig


def _generate_perspectives(count: int) -> List[str]:
    base_perspectives = [
        "Security & Vulnerability Analyst",
        "Performance & Optimization Specialist",
        "Edge-case & Error-Handling Expert",
        "Scalability & Architecture Guru",
        "Simplicity & Clean Code Advocate",
        "UX & Accessibility Champion",
        "Data Integrity & Consistency Auditor",
        "Testability & QA Engineer",
        "Documentation & Clarity Reviewer",
        "DevOps & Deployment Strategist"
    ]
    
    # If count <= len, just sample. Otherwise repeat with random variations.
    results = []
    for i in range(count):
        base = base_perspectives[i % len(base_perspectives)]
        results.append(f"{base} (Instance {i+1})")
    return results

async def _run_single_agent(task: str, perspective: str, semaphore: asyncio.Semaphore) -> str:
    """Run a single sub-agent with a specific perspective."""
    async with semaphore:
        config = LocalAgentConfig(
            name=f"swarm_node_{id(perspective)}",
            system_instructions=f"You are a member of a massive AI swarm tackling a complex task. Your specific role is: {perspective}.\n"
                                f"Analyze the task deeply from your perspective, ignore other concerns, and propose the best possible solution or insight.\n"
                                f"Be concise but highly technical."
        )
        agent = Agent(config)
        
        try:
            async with agent:
                result = await agent.chat(task)
            return f"--- [{perspective}] ---\n{result}\n"
        except Exception as e:
            return f"--- [{perspective}] ---\nFAILED: {e}\n"

async def _execute_mega_swarm(task: str, num_agents: int) -> str:
    """Executes the massive swarm and judges the result."""
    num_agents = max(2, min(num_agents, 100)) # Cap at 100 to prevent system crash
    
    # Use a semaphore to limit concurrent API calls and prevent rate limiting
    # 20 concurrent requests is a safe upper bound for most local/cloud APIs
    semaphore = asyncio.Semaphore(20)
    
    perspectives = _generate_perspectives(num_agents)
    
    # 1. Spawn all agents concurrently
    tasks = [
        _run_single_agent(task, p, semaphore) 
        for p in perspectives
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Clean up results
    valid_results = [r for r in results if isinstance(r, str)]
    combined_output = "\n".join(valid_results)
    
    # 2. Spawn the Judge to synthesize
    judge_config = LocalAgentConfig(
        name="swarm_judge",
        system_instructions="You are the SWARM JUDGE. A massive swarm of AI agents has analyzed a task from hundreds of different perspectives.\n"
                            "Your job is to synthesize all their outputs, extract the best ideas, filter out noise, and produce ONE completely fool-proof, robust, and optimal final solution.\n"
                            "Format your response beautifully with Markdown."
    )
    judge = Agent(judge_config)
    
    judge_prompt = f"TASK:\n{task}\n\nSWARM RESULTS:\n{combined_output}\n\nSYNTHESIZE THE FINAL SOLUTION NOW."
    
    try:
        async with judge:
            final_solution = await judge.chat(judge_prompt)
        return f"🌟 MEGA-SWARM SYNTHESIS (Compiled from {len(valid_results)} agents) 🌟\n\n{final_solution}"
    except Exception as e:
        return f"ERROR during Judge synthesis: {e}"

def run_dynamic_swarm(task: str, num_agents: int = 100) -> str:
    """Deploys a massive, completely dynamic swarm of sub-agents to solve a complex task.
    
    This spins up `num_agents` (up to 100) distinct AI instances in parallel, each with a unique 
    perspective (e.g. Security, Performance, Edge-cases). After they all generate their solutions, 
    a final Judge agent synthesizes their outputs into a single, completely fool-proof master solution.
    
    Args:
        task: The complex problem, feature, or code to analyze.
        num_agents: The number of sub-agents to spawn (default 100).
    """
    
    # We must run the async loop from synchronous tool context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        # If we are already in an event loop (e.g., inside Antigravity's async context), 
        # we can't block synchronously. However, AG SDK tools currently run in executors 
        # or support async tools natively. We should check if the tool is invoked async.
        # But AG SDK tools are generally sync by default unless defined as async.
        # Let's use asyncio.run safely in a new thread if needed, or just return an instruction 
        # that the tool must be async.
        pass

    # Since the agent tool executor runs sync tools in a ThreadPoolExecutor, 
    # asyncio.run is perfectly safe here!
    return asyncio.run(_execute_mega_swarm(task, num_agents))
