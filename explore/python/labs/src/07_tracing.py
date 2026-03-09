# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task 07 — Tracing: Instrument agent execution with Azure Monitor OpenTelemetry.

This script enables distributed tracing for a Foundry AI agent using
OpenTelemetry and Azure Monitor.  It creates custom spans around agent
creation and inference, then exports those traces to Application Insights
so you can visualise the full call tree in the Azure Portal.

Narrative context — Seeing inside the black box
────────────────────────────────────────────────
Traditional apps have three observability pillars: metrics, logs, traces.
AI applications need four *additional* layers:

  • Prompt observability  — which prompt produced which output?
  • Data observability    — was the retrieved context correct and fresh?
  • Model observability   — which model version, what parameters?
  • Semantic observability — HTTP 200, but was the *answer* right?

OpenTelemetry spans are the connective tissue that ties all four layers
together.  Each span records timing, attributes, and parent-child
relationships — so you can trace a single user question from the API
gateway, through the orchestrator, into the vector search, and back
out to the response.

Learning objectives
───────────────────
  1. Enable generative-AI tracing via the AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING
     environment flag.
  2. Retrieve the Application Insights connection string from the Foundry
     project's telemetry endpoint.
  3. Configure Azure Monitor tracing *before* running any SDK calls so
     that the OpenTelemetry hooks capture every outgoing request.
  4. Create root and nested spans with semantic attributes that follow
     the OpenTelemetry GenAI conventions.
  5. View the resulting traces in the Azure Portal.

Prerequisites
─────────────
    pip install --pre azure-ai-projects azure-identity python-dotenv \\
                     azure-monitor-opentelemetry opentelemetry-api

Usage
─────
    cp sample.env .env   # fill in your values
    python src/07_tracing.py

Required environment variables
──────────────────────────────
    AZURE_AI_PROJECT_ENDPOINT   – Foundry project endpoint URL
    MODEL_DEPLOYMENT_NAME       – name of the deployed model (e.g. gpt-4.1)
"""

from __future__ import annotations

import os
import sys

# ── Step 1: Load environment and enable GenAI tracing ────────────────────
#
# The .env file is loaded FIRST, and the experimental tracing flag is set
# BEFORE any Azure SDK imports.  This ensures the SDK's internal
# OpenTelemetry instrumentation hooks are activated at import time.

from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
load_dotenv(dotenv_path=env_path)

# This env var MUST be set before importing Azure SDK packages.  The SDK
# checks it at import time to decide whether to activate internal
# OpenTelemetry instrumentation hooks.  If you set it *after* the imports,
# the hooks won't fire and you'll get no Gen AI spans — just silence.
os.environ["AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING"] = "true"


def main() -> None:
    # ── Step 2: Validate configuration and create the project client ─────
    project_endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
    deployment_name = os.environ.get("MODEL_DEPLOYMENT_NAME", "")

    if not project_endpoint or project_endpoint.startswith("<"):
        print("❌ AZURE_AI_PROJECT_ENDPOINT is not set in .env.")
        sys.exit(1)
    if not deployment_name or deployment_name.startswith("<"):
        print("❌ MODEL_DEPLOYMENT_NAME is not set in .env.")
        sys.exit(1)

    print("🔍 Connecting to Foundry project…")
    print(f"   Endpoint:   {project_endpoint}")
    print(f"   Model:      {deployment_name}\n")

    from azure.identity import DefaultAzureCredential
    from azure.ai.projects import AIProjectClient

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=project_endpoint,
            credential=credential,
        ) as project_client,
    ):
        # ── Step 3: Retrieve connection string and configure Azure Monitor ─
        #
        # The project client exposes the Application Insights connection
        # string associated with this Foundry project.  We feed it into
        # configure_azure_monitor so every span created below is exported
        # to the correct AI resource.
        print("📡 Retrieving Application Insights connection string…")

        try:
            connection_string = (
                project_client.telemetry
                .get_application_insights_connection_string()
            )
        except Exception as exc:
            print(f"⚠️  Could not retrieve connection string: {exc}")
            print("   Ensure Application Insights is linked to your Foundry project.")
            sys.exit(1)

        if not connection_string:
            print("⚠️  Connection string is empty — Application Insights may "
                  "not be configured for this project.")
            sys.exit(1)

        print("   ✅ Connection string obtained.\n")

        # Azure Monitor must be configured BEFORE we create any spans or
        # SDK client calls.  configure_azure_monitor registers the
        # exporter with the global TracerProvider — spans created before
        # this point have no exporter and are silently dropped.  Order
        # matters: env var → imports → configure → use.
        from opentelemetry import trace
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(connection_string=connection_string)

        tracer = trace.get_tracer("cora-zava-diy", "1.0.0")
        print("📡 Tracing enabled — sending telemetry to Application Insights…\n")

        # ── Step 4: Root span — wraps the entire traced scenario ─────────
        #
        # Everything inside this `with` block is recorded under a single
        # root span called "cora.agent.traced-run".  Child spans created
        # inside it are linked automatically.
        from azure.ai.projects.models import PromptAgentDefinition

        agent = None  # will hold the agent reference for cleanup

        with tracer.start_as_current_span("cora.agent.traced-run") as root_span:
            # gen_ai.system and gen_ai.provider.name follow OpenTelemetry's
            # emerging semantic conventions for generative AI.  These
            # standardised attribute names let you query traces by AI
            # system in Application Insights (e.g. filter all spans where
            # gen_ai.system == "az.ai.agents") regardless of which SDK or
            # language generated them.
            root_span.set_attribute("gen_ai.system", "az.ai.agents")
            root_span.set_attribute("gen_ai.provider.name", "microsoft.agents")
            root_span.set_attribute("model", deployment_name)
            root_span.set_attribute("projectEndpoint", project_endpoint)

            try:
                # ── Step 5: Create the agent inside a nested span ────────
                #
                # A child span tracks the agent-creation API call separately
                # from inference, making it easy to see latency breakdowns.
                with tracer.start_as_current_span("agents.createVersion") as agent_span:
                    agent_span.set_attribute("deploymentName", deployment_name)
                    agent_span.set_attribute("model", deployment_name)
                    agent_span.set_attribute(
                        "instructions",
                        "You are Cora, Zava DIY assistant",
                    )

                    print("🤖 Creating traced agent…")
                    agent = project_client.agents.create_version(
                        agent_name="cora-traced-agent",
                        definition=PromptAgentDefinition(
                            model=deployment_name,
                            instructions=(
                                "You are Cora, the friendly AI assistant for "
                                "Zava DIY home improvement store."
                            ),
                        ),
                    )

                    # Record agent metadata on the span for later querying
                    agent_span.set_attribute("agent.name", agent.name)
                    agent_span.set_attribute("agent.version", agent.version)
                    agent_span.set_attribute("agent.id", agent.id)

                    print(
                        f"   ✅ Agent created (name: {agent.name}, "
                        f"version: {agent.version})\n"
                    )

                # ── Step 6: Run inference inside another nested span ─────
                #
                # We create a conversation, send a test prompt via the
                # Responses API using the agent_reference pattern, and
                # record the result length on the span.
                #
                # This is where the walkthrough's debugging "wow" happens.
                # By examining spans you can discover, for example, that
                # search_products was called but check_stock was NOT —
                # meaning the bug isn't the model, it's the orchestration
                # design.  Observability moves you from guessing to knowing.
                with tracer.start_as_current_span("cora.inference") as inference_span:
                    inference_span.set_attribute(
                        "query", "What paint for my bathroom?"
                    )

                    print("💬 Running test inference…")
                    with project_client.get_openai_client() as openai_client:
                        conversation = openai_client.conversations.create()
                        response = openai_client.responses.create(
                            conversation=conversation.id,
                            extra_body={
                                "agent_reference": {
                                    "name": agent.name,
                                    "type": "agent_reference",
                                },
                            },
                            input="What paint should I use for my bathroom?",
                        )

                        output = response.output_text or ""
                        # ── Step 7: Set span attributes ──────────────────
                        inference_span.set_attribute(
                            "response.length", len(output)
                        )

                        # Show a truncated preview of the response
                        preview = output[:200]
                        print(f"   🤖 Response: {preview}…\n")

                        # Clean up the conversation
                        openai_client.conversations.delete(
                            conversation_id=conversation.id
                        )

            except Exception as exc:
                # Record the error on the root span so it shows up in
                # Application Insights as a failed operation.
                root_span.set_attribute("error", True)
                root_span.set_attribute("error.message", str(exc))
                print(f"\n❌ Error during traced run: {exc}")
                raise
            finally:
                # ── Step 8: Cleanup — delete the agent version ───────────
                # Deleting stale agent versions is important: they consume
                # quota, can be accidentally referenced by future evals,
                # and make the Foundry Portal harder to navigate.
                if agent is not None:
                    try:
                        project_client.agents.delete_version(
                            agent_name=agent.name,
                            agent_version=agent.version,
                        )
                        print("🧹 Agent version deleted.\n")
                    except Exception as cleanup_err:
                        print(
                            f"⚠️  Could not delete agent: {cleanup_err}\n"
                        )

    # ── Final: Tell the user where to find traces ────────────────────────
    print("📡 Telemetry sent successfully!")
    print("   View traces in Azure Portal → Application Insights → Transaction search")
    print('   Filter by: customDimensions["gen_ai.system"] = "az.ai.agents"')
    print()
    print("💡 Tip: Traces may take 2–5 minutes to appear in Application Insights.")
    print("🎉 Tracing complete — you're ready for Task 08!")


if __name__ == "__main__":
    main()
