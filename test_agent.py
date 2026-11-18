import asyncio
from google.antigravity import Agent, LocalAgentConfig
import os

os.environ["GEMINI_API_KEY"] = "AQ.Ab8RN6L9JHsLrgzrds5aMqQI4E4gDptCXFjWvLkyaIHuiDcLQg"

async def main():
    config = LocalAgentConfig(system_instructions="You are a test agent.")
    async with Agent(config) as agent:
        try:
            response = await agent.chat("Hello")
            print("Response:", response)
        except Exception as e:
            print("ERROR:", repr(e))

asyncio.run(main())
