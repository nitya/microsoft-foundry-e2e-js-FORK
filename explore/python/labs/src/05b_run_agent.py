"""
Task 05b — Run Agent: Send customer questions to Cora and handle tool calls.

This script creates a conversation, sends customer questions to the
Cora agent, handles function tool calls (product search, stock check),
and displays the final responses.

Narrative context (Act 1, Section 1.4 — "From Script to Agent")
───────────────────────────────────────────────────────────────
This is where Cora stops being a script and becomes a real agent.  The
walkthrough illustrates the full agent loop:

    "The model says 'I need to search for bathroom paint,' calls
     search_products, reads the results, then says 'let me check
     stock on the top pick,' calls check_stock, and finally gives
     the customer a complete answer.  Two tool calls, one coherent
     response."

The key shift: the *model* decides which tools to call and in what
order — the developer just provides the tools and executes them.

Learning objectives
───────────────────
• Create a multi-turn conversation via the Conversations API.
• Route messages through a named Foundry agent.
• Detect function-call outputs and execute tools locally.
• Submit tool results back to the agent for a final answer.

Prerequisites
─────────────
    pip install --pre azure-ai-projects azure-identity openai python-dotenv
    python src/05a_create_agent.py   # create the Cora agent first

Usage
─────
    python src/05b_run_agent.py
"""

import importlib.util
import json
import os
import sys

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# ── Step 2: Import the local tool executor ──────────────────────────────
# Module names starting with a digit require importlib to load.
_tools_path = os.path.join(os.path.dirname(__file__), "05c_tools.py")
_spec = importlib.util.spec_from_file_location("tools_05c", _tools_path)
_tools_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tools_module)
execute_tool = _tools_module.execute_tool


# Agent name must match the one created in 05a_create_agent.py
AGENT_NAME = "cora-zava-diy"

# Test questions chosen to exercise different capabilities:
#   • General recommendation → triggers search_products
#   • Stock inquiry          → triggers check_stock directly
#   • Nuanced request        → tests both tools together (search, then stock)
CUSTOMER_QUESTIONS = [
    "What paint should I use for my bathroom?",
    "Is the Interior Semi-Gloss Paint in stock?",
    "I need something eco-friendly for my baby's nursery.",
]

# Safety guardrail: cap the number of tool-call round-trips.  Without this,
# a model that keeps requesting tools could loop forever.  In production
# you'd also enforce token budgets and wall-clock timeout limits.
MAX_TOOL_ITERATIONS = 5


def main() -> None:
    # ── Step 1: Load .env and create clients ────────────────────────────
    env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
    load_dotenv(dotenv_path=env_path)

    project_endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
    if not project_endpoint or project_endpoint.startswith("<"):
        print("❌ AZURE_AI_PROJECT_ENDPOINT is not set. "
              "Run labs/scripts/setup-env.sh or edit .env.")
        sys.exit(1)

    print("🔐 Connecting to Microsoft Foundry…")
    print(f"   Endpoint: {project_endpoint}\n")

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=project_endpoint,
            credential=credential,
        ) as project_client,
    ):
        # Obtain an OpenAI-compatible client scoped to this project
        with project_client.get_openai_client() as openai_client:
            print("💬 Running Cora agent conversations…\n")

            for question in CUSTOMER_QUESTIONS:
                _run_conversation(openai_client, question)

    print("\n✅ Agent conversations complete!")
    print("💡 Notice how Cora uses tools to search products and "
          "check stock before responding.")


def _run_conversation(openai_client, question: str) -> None:
    """Send a single customer question through the agent and handle tool calls."""
    print(f'👤 Customer: "{question}"')

    try:
        # ── Step 4a: Create a conversation with the customer message ────
        # The Conversations API creates server-side state.  Unlike the
        # Responses API (which chains via previous_response_id), a
        # conversation persists across multiple interactions and can be
        # resumed — handy for multi-turn customer support sessions.
        conversation = openai_client.conversations.create(
            items=[{"type": "message", "role": "user", "content": question}],
        )

        # ── Step 4b: Get the agent's initial response ───────────────────
        response = openai_client.responses.create(
            conversation=conversation.id,
            extra_body={
                "agent_reference": {"name": AGENT_NAME, "type": "agent_reference"},
            },
        )

        # ── Step 4c: Tool-call loop ─────────────────────────────────────
        # This is the heart of the agent pattern.  The *model* is the
        # decision-maker, not the developer.  We don't hardcode which
        # tools to call or in what order — the model decides based on
        # the user's question and its instructions.  Our job is simply
        # to execute whatever the model asks for and feed results back.
        iterations = 0
        while iterations < MAX_TOOL_ITERATIONS:
            # Check whether the response contains any function calls
            function_calls = [
                item for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:
                break  # No more tool calls — the agent has a final answer

            # Execute each requested tool and collect results
            tool_results = []
            for call in function_calls:
                args = json.loads(call.arguments)
                print(f"   🔧 Tool call: {call.name}({json.dumps(args)})")

                result = execute_tool(call.name, args)
                print(f"   📋 Result: {result[:100]}…")

                tool_results.append({
                    "type": "function_call_output",
                    "call_id": call.id,
                    "output": result,
                })

            # Submit tool results back to the agent for the next turn
            response = openai_client.responses.create(
                input=tool_results,
                previous_response_id=response.id,
                extra_body={
                    "agent_reference": {"name": AGENT_NAME},
                },
            )

            iterations += 1

        # ── Step 4d: Print the agent's final text response ──────────────
        print(f"🤖 Cora: {response.output_text}")
        print("─" * 60)

        # Clean up the conversation to free server-side resources.
        # Important for cost management when running at scale — each
        # open conversation consumes memory on the service side.
        openai_client.conversations.delete(conversation.id)

    except Exception as exc:
        print(f"⚠️  Error processing question: {exc}")
        print("─" * 60)


if __name__ == "__main__":
    main()
