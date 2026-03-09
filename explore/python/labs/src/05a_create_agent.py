"""
Task 05a — Create Agent: Define and register the Cora AI agent.

This script creates Cora as a Foundry agent with:
- A system prompt defining her persona and rules
- Function tools for product search and stock checking

Narrative context  (Walkthrough §1.4 — "From Script to Agent")
──────────────────
"An agent is a model plus tools plus a loop. The model decides what to
do, calls your tools, reads the results, and responds." This script
handles the first part — registering the agent definition with its tools
in Foundry. The actual conversation loop lives in 05b_run_agent.py.

Splitting creation from execution means you register once and run many
times, which mirrors how production deployments work: the agent
definition is infrastructure; the conversation is runtime.

Learning objectives
───────────────────
• Define agent instructions (system prompt) for a customer-service persona.
• Import reusable tool definitions from a shared module.
• Register a versioned agent via AIProjectClient.agents.create_version.

Prerequisites
─────────────
    pip install --pre azure-ai-projects azure-identity python-dotenv

Usage
─────
    cp sample.env .env   # fill in your values
    python src/05a_create_agent.py

Required environment variables
──────────────────────────────
    AZURE_AI_PROJECT_ENDPOINT   – Foundry project endpoint URL
    MODEL_DEPLOYMENT_NAME       – name of the deployed model (e.g. gpt-4.1)
"""

import os
import sys

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

# Tool definitions are maintained in 05c_tools so both the agent
# registration (here) and the runtime (05b) share a single source.
# Module names starting with a digit require importlib to load — Python's
# import system forbids identifiers that begin with a number. This is a
# language constraint, not a design choice; the JS version of these labs
# imports "05c_tools" with a plain require() and has no such issue.
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    "tools_05c", os.path.join(os.path.dirname(__file__), "05c_tools.py")
)
_tools_module = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_tools_module)
tool_definitions = _tools_module.tool_definitions

# ── Cora's system prompt ────────────────────────────────────────────────
# Why "ALWAYS use search_products before recommending"? (Rule 1 below)
# This directly prevents the bug surfaced in the walkthrough's debugging
# moment (§2.3): without this rule the model may skip tool calls and
# hallucinate products that don't exist in Zava's catalog. Explicit
# instruction-level constraints are the cheapest guardrail you have.
CORA_INSTRUCTIONS = """\
You are Cora, the friendly and knowledgeable AI customer service assistant \
for Zava DIY, a home improvement retail store.

## Your Role
- Help customers find the right products for their home improvement projects.
- Answer questions about paint, primers, tools, and supplies.
- Provide specific product recommendations with SKU and price.

## Tools Available
- **search_products**: Search the Zava DIY catalog by keyword. \
Use this when customers ask about products.
- **check_stock**: Check stock availability for a specific SKU. \
Use this when customers ask about availability.

## Rules
1. ALWAYS use the search_products tool before recommending products.
2. Reference products by name, SKU, and price.
3. If stock is low (< 5 units), warn the customer.
4. Never discuss topics outside home improvement.
5. If you can't help, suggest visiting a Zava DIY store.
6. Keep responses friendly, concise, and under 150 words.

## Response Format
- Start with a direct answer.
- Include specific product recommendations.
- Mention stock availability when relevant.
- End with a helpful tip when appropriate."""


def main() -> None:
    # ── Step 1: Load .env and create AIProjectClient ─────────────────────
    env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
    load_dotenv(dotenv_path=env_path)

    project_endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
    deployment_name = os.environ.get("MODEL_DEPLOYMENT_NAME", "")

    if not project_endpoint or project_endpoint.startswith("<"):
        print("❌ AZURE_AI_PROJECT_ENDPOINT is not set. Check your .env file.")
        sys.exit(1)
    if not deployment_name or deployment_name.startswith("<"):
        print("❌ MODEL_DEPLOYMENT_NAME is not set. Check your .env file.")
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
        # ── Step 2: Import tool definitions ──────────────────────────────
        # tool_definitions is imported at module level from 05c_tools.
        tool_names = [t["name"] for t in tool_definitions]
        print("🤖 Creating Cora agent…")
        print(f"   Model: {deployment_name}")
        print(f"   Tools: {', '.join(tool_names)}\n")

        # ── Step 3: Create the agent with instructions and tools ─────────
        # create_version registers a *versioned* agent in Foundry. Versioning
        # matters because in production you'll want to compare agent versions
        # via evaluation (Task 06), trace different versions in the dashboard
        # (Task 07), and red-team specific versions (Task 08).
        try:
            agent = project_client.agents.create_version(
                agent_name="cora-zava-diy",
                definition=PromptAgentDefinition(
                    model=deployment_name,
                    instructions=CORA_INSTRUCTIONS,
                    tools=tool_definitions,
                ),
            )
        except Exception as exc:
            print(f"❌ Failed to create agent: {exc}")
            sys.exit(1)

        # ── Step 4: Print success with agent details ─────────────────────
        print("✅ Agent created!")
        print(f"   ID:      {agent.id}")
        print(f"   Name:    {agent.name}")
        print(f"   Version: {agent.version}")

        # The agent name is needed to run conversations in 05b.
        # It's the key that links the entire pipeline:
        # creation (05a) → execution (05b) → tracing (07) → red-teaming (08).
        print(f'\n💡 Save the agent name "{agent.name}" '
              "— you'll need it in 05b_run_agent.py")


if __name__ == "__main__":
    main()
