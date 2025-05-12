import asyncio
import json
from app.ml.ai_integration import AIIntegration

async def test_tool_learning():
    # Load tools metadata
    with open("tools/tools_metadata.json", "r") as f:
        tools_metadata = json.load(f)

    ai_integration = AIIntegration()

    for tool_key, tool_metadata in tools_metadata.items():
        print(f"Learning usage for tool: {tool_metadata['name']}")
        guide = await ai_integration.learn_tool_usage(tool_metadata)
        print(f"Guide for {tool_metadata['name']}:")
        print(guide)
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_tool_learning())
