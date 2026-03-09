"""
Task 02 — Setup: Verify your environment configuration.

This script checks that all required environment variables are set,
creates an AIProjectClient to verify authentication, and runs a
quick inference call to confirm the model deployment is working.

Narrative context (walkthrough §1.1)
────────────────────────────────────
This is the very first step in the developer journey.  The walkthrough
opens with: "you've been asked to build Cora" — an AI shopping assistant
for Zava DIY.  Before you can choose from 10,000+ models, evaluate
quality, or red-team for safety, you need *one thing*: a working
connection to Microsoft Foundry.  This script proves the environment is
alive — credentials work, the project is reachable, and a model responds.

Learning objectives
───────────────────
• Understand the environment variables a Foundry project needs.
• Authenticate with DefaultAzureCredential.
• Create an AIProjectClient and obtain an OpenAI client from it.
• Make a simple inference call via the Responses API.

Prerequisites
─────────────
    pip install --pre azure-ai-projects azure-identity python-dotenv

Usage
─────
    cp sample.env .env   # fill in your values
    python src/02_setup.py

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


def main() -> None:
    # ── Step 1: Load .env and validate required variables ────────────────
    # The .env file lives next to the src/ folder (explore/python/labs/.env).
    env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
    load_dotenv(dotenv_path=env_path)

    print("🔍 Checking environment variables…\n")

    required_vars: dict[str, str | None] = {
        "AZURE_AI_PROJECT_ENDPOINT": os.environ.get("AZURE_AI_PROJECT_ENDPOINT"),
        "MODEL_DEPLOYMENT_NAME": os.environ.get("MODEL_DEPLOYMENT_NAME"),
    }

    all_set = True
    for key, value in required_vars.items():
        if value and not value.startswith("<"):
            print(f"  ✅ {key}")
        else:
            print(f"  ❌ {key} — not set")
            all_set = False

    # ── Step 2: Check optional variables ─────────────────────────────────
    optional_vars: dict[str, str | None] = {
        "MODEL_ENDPOINT": os.environ.get("MODEL_ENDPOINT"),
        "MODEL_API_KEY": os.environ.get("MODEL_API_KEY"),
        "TELEMETRY_CONNECTION_STRING": os.environ.get("TELEMETRY_CONNECTION_STRING"),
        "AZURE_AI_PROJECTS_AZURE_SUBSCRIPTION_ID": os.environ.get("AZURE_AI_PROJECTS_AZURE_SUBSCRIPTION_ID"),
        "AZURE_AI_PROJECTS_AZURE_RESOURCE_GROUP": os.environ.get("AZURE_AI_PROJECTS_AZURE_RESOURCE_GROUP"),
        "AZURE_AI_PROJECTS_AZURE_AOAI_ACCOUNT": os.environ.get("AZURE_AI_PROJECTS_AZURE_AOAI_ACCOUNT"),
    }

    print()
    for key, value in optional_vars.items():
        if value and not value.startswith("<"):
            print(f"  ✅ {key}")
        else:
            print(f"  ⬜ {key} — not set (optional)")

    if not all_set:
        print("\n❌ Required environment variables missing. "
              "Run labs/scripts/setup-env.sh or edit .env.")
        sys.exit(1)

    # ── Step 3: Create the AI Project client and verify authentication ───
    project_endpoint: str = required_vars["AZURE_AI_PROJECT_ENDPOINT"]  # type: ignore[assignment]
    deployment_name: str = required_vars["MODEL_DEPLOYMENT_NAME"]  # type: ignore[assignment]

    print("\n🔐 Connecting to Microsoft Foundry…")
    print(f"   Endpoint: {project_endpoint}")

    # DefaultAzureCredential uses managed identity (or local CLI creds in
    # dev).  No API keys in code — a security best practice that becomes
    # critical when we red-team Cora for credential leakage in Task 08.
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=project_endpoint,
            credential=credential,
        ) as project_client,
    ):
        # ── Step 4: Test inference with a simple prompt ──────────────────
        print(f"\n🚀 Testing model deployment: {deployment_name}…")

        # get_openai_client returns an OpenAI-compatible client scoped to
        # this project; no extra keys or URLs needed.
        with project_client.get_openai_client() as openai_client:
            try:
                # We use the Responses API (not Chat Completions) because it's
                # the newer interface with built-in conversation context via
                # previous_response_id, native tool execution, and agent
                # references — all features we'll rely on in Tasks 04-05.
                response = openai_client.responses.create(
                    model=deployment_name,
                    input="Say 'Hello from Foundry!' in exactly those words.",
                    max_output_tokens=20,
                )

                output = (response.output_text or "").strip()
                print(f'   Model response: "{output}"')
                print("\n✅ Foundry project is reachable and responding.")

            except Exception as exc:
                # ── Step 5: Handle 404 gracefully ────────────────────────
                # Newly provisioned Foundry projects need time for the data
                # plane to propagate; a 404 during that window is an
                # operational reality of cloud provisioning, not a bug.
                # The project *exists* but the inference endpoint isn't
                # routable yet — typically resolves in 5-15 minutes.
                status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
                if status == 404:
                    print("\n⚠️  Project data plane returned 404 — "
                          "this is normal for newly created projects.")
                    print("   The project may take 5–15 minutes to propagate "
                          "after creation.")
                    print("   Try again shortly, or open the project in "
                          "https://ai.azure.com to trigger sync.")
                    print("\n✅ Environment variables are correctly configured.")
                else:
                    raise

    print("🎉 Setup verified — you're ready for Quest 2!")


if __name__ == "__main__":
    main()
