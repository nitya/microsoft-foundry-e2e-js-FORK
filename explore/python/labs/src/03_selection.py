"""
Task 03 — Selection: List deployments and test a model with conversational context.

This script lists all available model deployments in your Foundry project,
then sends a test product question to the configured model and follows up
with a second question that uses the Responses API's built-in conversation
context (previous_response_id).

Narrative context (walkthrough §1.2 — "10K Models, One Decision")
─────────────────────────────────────────────────────────────────
Foundry gives you access to 10,000+ models.  As the walkthrough puts it,
"That's not a feature — that's a paradox of choice."  The key insight:
model selection is a tradeoff — capability vs. cost vs. latency.  Start
with the most capable model that fits your latency budget, then distill
down later (we revisit this tradeoff in Task 06 when we evaluate cheaper
alternatives).  This script is how you kick the tires on whatever model
you chose.

Learning objectives
───────────────────
• List model deployments programmatically with AIProjectClient.
• Inspect deployment metadata (name, model, version, SKU).
• Use the Responses API for single-turn inference.
• Chain prompts with previous_response_id for multi-turn context.

Prerequisites
─────────────
    pip install --pre azure-ai-projects azure-identity python-dotenv

Usage
─────
    cp sample.env .env   # fill in your values
    python src/03_selection.py

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
from azure.ai.projects.models import ModelDeployment


def main() -> None:
    # ── Step 1: Load environment and create clients ──────────────────────
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
        # ── Step 2: List all model deployments ───────────────────────────
        # "What's deployed in my project?" is the first question any
        # developer faces.  deployments.list() answers it — giving you
        # model names, versions, and SKUs so you can reason about
        # capability, cost, and rate limits before writing any prompts.
        print("📋 Listing model deployments…")
        try:
            count = 0
            # deployments.list() returns all deployments in the project;
            # filter to ModelDeployment instances for model-specific metadata.
            for deployment in project_client.deployments.list():
                if isinstance(deployment, ModelDeployment):
                    count += 1
                    sku = getattr(deployment, "sku", None)
                    sku_label = sku if sku else "n/a"
                    print(
                        f"  • {deployment.name}  |  "
                        f"{deployment.model_name} "
                        f"v{deployment.model_version}  |  "
                        f"SKU: {sku_label}"
                    )
            print(f"  Total: {count} deployment(s)\n")

        except Exception as exc:
            # Newly created projects may return 404 while propagating.
            status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
            if status == 404:
                print("  ⚠️  Could not list deployments (project may still be propagating).")
                print(f"  Continuing with configured deployment: {deployment_name}\n")
            else:
                raise

        # ── Step 3: Send a test prompt via the Responses API ─────────────
        print(f'🧪 Testing deployment "{deployment_name}" with a product question…\n')

        # get_openai_client returns an OpenAI-compatible client scoped to
        # this project; no extra keys or URLs needed.
        with project_client.get_openai_client() as openai_client:
            # First turn — the walkthrough's running example question.
            # "What paint should I use for my bathroom?" is the thread
            # that ties the entire talk together: we'll ask it again in
            # Task 04 (with tools), Task 06 (evaluation), and Task 07
            # (tracing) to see how the answer evolves as the system
            # gets smarter, more instrumented, and more trustworthy.
            response = openai_client.responses.create(
                model=deployment_name,
                input="What kind of paint should I use for a bathroom renovation?",
            )
            print("🤖 Model response:")
            print(response.output_text)

            # ── Step 4: Follow-up with conversation context ──────────────
            # previous_response_id is the Responses API's built-in
            # conversation memory.  The server retains the prior exchange,
            # so we don't resend the full message history.  This is
            # fundamentally different from Chat Completions, where you'd
            # need to manually accumulate and re-post every message.
            print("\n💬 Follow-up question (using previous_response_id for context)…")
            follow_up = openai_client.responses.create(
                model=deployment_name,
                input="And do I need a primer first?",
                previous_response_id=response.id,
            )
            print("🤖 Follow-up response:")
            print(follow_up.output_text)

    print("\n✅ Model selection verified — inference with context is working!")


if __name__ == "__main__":
    main()
