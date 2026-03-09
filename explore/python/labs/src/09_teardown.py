"""
Task 09 — Teardown: Clean up all resources created during the quest.

This script deletes agents, evaluations, and lists remaining deployments
so you can remove them manually.  It also prints guidance for cleaning up
Azure resources (project, resource group) via the portal or CLI.

Narrative context  (Closing — Operational Teardown)
───────────────────────────────────────────────────
The walkthrough concludes with the 10-step developer playbook:
  Build   (5 steps): provision → deploy → connect → ground → orchestrate
  Optimize (3 steps): evaluate → trace → debug
  Govern  (2 steps): red-team → monitor

This script is the operational end — cleaning up every resource the quest
created.  The walkthrough's final message: "The hardest part of building
AI isn't the model.  It's everything around the model."

Learning objectives
───────────────────
• Programmatically enumerate and delete AI agents.
• Remove evaluations created during the quest.
• Understand which resources require manual cleanup.

Prerequisites
─────────────
    pip install --pre azure-ai-projects azure-identity python-dotenv openai

Usage
─────
    cp sample.env .env   # fill in your values
    python src/09_teardown.py

Required environment variables
──────────────────────────────
    AZURE_AI_PROJECT_ENDPOINT   – Foundry project endpoint URL
"""

import os
import sys

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


# Agent names created across the quest labs.
# Each entry maps to a step in the Build → Optimize → Govern journey:
#   • cora-zava-diy      — created in 05a, the first working agent (Build)
#   • cora-traced-agent   — created in 07, the traced/debuggable agent (Optimize)
#   • cora-redteam-agent  — created in 08, the safety-tested agent (Govern)
# Every phase left a resource behind; this is where we clean them up.
AGENT_NAMES = ["cora-zava-diy", "cora-traced-agent", "cora-redteam-agent"]


def main() -> None:
    # ── Step 1: Load .env and create clients ─────────────────────────────
    env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
    load_dotenv(dotenv_path=env_path)

    project_endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
    if not project_endpoint or project_endpoint.startswith("<"):
        print("❌ AZURE_AI_PROJECT_ENDPOINT is not set. Check your .env file.")
        sys.exit(1)

    print("🧹 Tearing down Quest 2 resources…\n")
    print("🔐 Connecting to Microsoft Foundry…")
    print(f"   Endpoint: {project_endpoint}\n")

    # Track per-step success for the final summary.
    deleted_agents = 0
    deleted_evals = 0
    errors: list[str] = []

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=project_endpoint,
            credential=credential,
        ) as project_client,
    ):
        # ── Step 2: Identify agents to delete ────────────────────────────
        print(f"🤖 Cleaning up agents: {', '.join(AGENT_NAMES)}…")

        # ── Step 3: Delete matching agents ───────────────────────────────
        try:
            for agent in project_client.agents.list():
                if agent.name in AGENT_NAMES:
                    project_client.agents.delete_version(
                        agent_name=agent.name,
                        agent_version=agent.version,
                    )
                    print(f"  🗑️  Deleted agent: {agent.name} (version {agent.version})")
                    deleted_agents += 1

            if deleted_agents == 0:
                print("   No matching agents found — already clean.")
            else:
                print(f"   Deleted {deleted_agents} agent(s).")
        except Exception as exc:
            print(f"   ⚠️  Agent cleanup failed: {exc}")
            errors.append("agents")

        # ── Step 4: Delete evaluations ───────────────────────────────────
        # Evaluations persist in the Foundry Portal and are valuable for
        # historical comparison — tracking quality trends across releases.
        # In production you'd keep them longer and use them as a quality
        # ledger.  Here we delete them to leave a clean slate.
        print("\n📊 Cleaning up evaluations…")
        try:
            # The OpenAI client exposes the evals API for this project.
            with project_client.get_openai_client() as openai_client:
                for eval_obj in openai_client.evals.list():
                    openai_client.evals.delete(eval_id=eval_obj.id)
                    print(f"  🗑️  Deleted evaluation: {eval_obj.id}")
                    deleted_evals += 1

            if deleted_evals == 0:
                print("   No evaluations found — already clean.")
            else:
                print(f"   Deleted {deleted_evals} evaluation(s).")
        except Exception as exc:
            print(f"   ⚠️  Evaluation cleanup failed: {exc}")
            errors.append("evaluations")

        # ── Step 5: List remaining deployments (informational) ───────────
        print("\n🚀 Remaining deployments (delete manually if needed):")
        try:
            dep_count = 0
            for deployment in project_client.deployments.list():
                print(f"  📦 {deployment.name}")
                dep_count += 1
            if dep_count == 0:
                print("   No deployments found.")
        except Exception as exc:
            print(f"   ⚠️  Could not list deployments: {exc}")
            errors.append("deployments")

    # ── Step 6: Manual cleanup instructions ──────────────────────────────
    # There's a clear split between automated and manual cleanup:
    #   Automated (API-deletable): agents, evaluations — handled above.
    #   Manual (Portal / CLI only): model deployments, projects, resource
    #   groups.  These are infrastructure-level resources that require
    #   explicit human confirmation before deletion.
    print("\n📌 Manual cleanup (if needed):")
    print("   1. Delete model deployments in Foundry Portal → Deployments")
    print("   2. Delete the Foundry project in Azure Portal → Resource groups")
    print("   3. Delete the resource group if no longer needed:")
    print("        az group delete --name <your-resource-group>")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print(f"✅ Automated cleanup complete — "
          f"{deleted_agents} agent(s), {deleted_evals} evaluation(s) deleted.")
    if errors:
        print(f"⚠️  Errors encountered in: {', '.join(errors)}")
    # When your AI system fails — and it will — don't blame the model.
    # Open the trace.  Check the data.  Read the spans.  The answer is
    # almost always in the system, not the weights.
    print("\n🎉 Congratulations on completing Quest 2! "
          "You've built an end-to-end AI agent with Microsoft Foundry.")


if __name__ == "__main__":
    main()
