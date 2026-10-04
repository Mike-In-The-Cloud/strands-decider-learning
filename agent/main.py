from bedrock_agentcore.runtime import BedrockAgentCoreApp

from graph.stream import iter_graph_events

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload, context):
    prompt = payload.get("prompt", "") if isinstance(payload, dict) else ""
    if not isinstance(prompt, str) or not prompt.strip():
        yield {"type": "error", "error": "prompt must be a non-empty string"}
        return
    async for event in iter_graph_events(prompt):
        yield event


if __name__ == "__main__":
    app.run()
