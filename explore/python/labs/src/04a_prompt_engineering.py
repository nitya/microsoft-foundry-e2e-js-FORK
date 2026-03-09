"""
Task 04a — Prompt Engineering: Craft and test Cora's system prompt.

This script defines Cora's personality, rules, and response format
via a system prompt, then tests it with Zava DIY customer questions.

Narrative context (walkthrough §1.3 — first half)
─────────────────────────────────────────────────
There are two levers you pull to make a model useful: the system prompt
and the context you inject.  The system prompt defines *who* Cora is —
her persona, her guardrails, and the shape of her answers.  This script
focuses on that first lever.  We'll pull the second lever in 04b when we
ground Cora in real product data.

Learning objectives
───────────────────
• Understand how a system prompt shapes an AI assistant's behaviour.
• Define persona, rules, and response format in a single prompt.
• Observe how the model responds in-character to varied questions.

Prerequisites
─────────────
    pip install --pre azure-ai-projects azure-identity python-dotenv

Usage
─────
    cp sample.env .env   # fill in your values
    python src/04a_prompt_engineering.py

Required environment variables
──────────────────────────────
    AZURE_AI_PROJECT_ENDPOINT   – Foundry project endpoint URL
    MODEL_DEPLOYMENT_NAME       – name of the deployed model (e.g. gpt-4.1)
"""

import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


# ── Cora's system prompt — this is where the magic happens ──────────────
# A good system prompt has three ingredients (reusable for any agent):
#   1. **Persona** — who the agent is and what it cares about.
#   2. **Rules**   — behavioral constraints (e.g., stay on-topic, be honest).
#   3. **Format**  — how the output should be structured.
# The prompt below weaves all three together for Cora.
CORA_SYSTEM_PROMPT = """\
You are Cora, the friendly and knowledgeable AI customer service assistant \
for Zava DIY, a home improvement retail store.

## Your Role
- Help customers find the right products for their projects.
- Answer questions about paint, primers, and home improvement supplies.
- Always be polite, encouraging, and concise.

## Rules
1. Always reference specific products by name, SKU, and price when available.
2. If you don't know the answer, say so honestly and suggest visiting the store.
3. Never provide advice on topics outside home improvement.
4. If a customer seems frustrated, acknowledge their concern and offer to help.
5. Keep responses under 150 words unless the customer asks for detailed information.

## Response Format
- Start with a direct answer to the question.
- Include specific product recommendations with SKU and price.
- End with a helpful tip or next step when appropriate."""


# Sample customer questions — these recur throughout the quest.
# "What paint should I use for my bathroom?" is the walkthrough's connective
# thread: we keep asking it as the system gets smarter, more instrumented,
# and more trustworthy.
TEST_QUESTIONS: list[str] = [
    "What paint should I use for my bathroom?",
    "Do you have anything eco-friendly?",
    "How much would it cost to paint a 12x12 room?",
    "Can you help me pick a color for my living room?",
]


def main() -> None:
    # ── Step 1: Load .env and create clients ────────────────────────────
    # The .env file lives next to the src/ folder (explore/python/labs/.env).
    env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
    load_dotenv(dotenv_path=env_path)

    project_endpoint = os.environ.get(
        "AZURE_AI_PROJECT_ENDPOINT", "<project endpoint>"
    )
    deployment_name = os.environ.get(
        "MODEL_DEPLOYMENT_NAME", "<model deployment name>"
    )

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

            # ── Step 2: Display the system prompt ───────────────────────
            print("🎨 Testing Cora's system prompt with customer questions…\n")
            print("System prompt:")
            print("─" * 60)
            print(CORA_SYSTEM_PROMPT)
            print("─" * 60)

            # ── Step 3: Send each question and print the response ───────
            for question in TEST_QUESTIONS:
                print(f'\n👤 Customer: "{question}"')

                try:
                    # Use the Responses API with instructions for the system prompt
                    response = openai_client.responses.create(
                        model=deployment_name,
                        instructions=CORA_SYSTEM_PROMPT,
                        input=question,
                    )

                    print(f"🤖 Cora: {response.output_text}")
                except Exception as exc:
                    print(f"⚠️  Error for this question: {exc}")

                print("─" * 60)

            # ── Summary ─────────────────────────────────────────────────
            # Key insight: Cora responds in character but doesn't know
            # specific Zava products yet.  She'll hallucinate brand names
            # because there is no product data in the prompt.  The model
            # is fine — the *context* you give it determines output
            # quality.  That's the setup for 04b.
            print("\n✅ Prompt engineering complete!")
            print(
                "💡 Notice: Cora responds in character but doesn't know "
                "specific Zava products yet."
            )
            print(
                "   Next, we'll add product context (04b) and fine-tune "
                "the model (04c)."
            )


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"The sample encountered an error: {err}")
