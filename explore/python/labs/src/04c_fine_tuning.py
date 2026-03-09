"""
Task 04c — Fine-Tuning: Distill gpt-4.1 knowledge into gpt-4.1-mini.

This script uploads training and validation data, creates a supervised
fine-tuning job to customize gpt-4.1-mini with Zava DIY product
knowledge (distilled from gpt-4.1 responses), polls the job until it
completes, optionally deploys the fine-tuned model, and cleans up
uploaded files.

Narrative context  (Walkthrough §1.5 — "The Cost Tradeoff — Fine-Tuning")
──────────────────
gpt-4.1 is great but not cheap. If Cora handles 100K conversations a
month, we need a cheaper model that's just as good *for this specific
task*. The technique is **distillation**: take high-quality outputs from
gpt-4.1, format them as training data (the JSONL files referenced below),
and fine-tune gpt-4.1-mini to mimic them. Same quality, fraction of the
cost.

This is the capstone of Act 1 ("Build") — we went from a bare prompt
(Task 02) through retrieval-augmented generation (Task 03), tool-calling
(Task 04a-b), and now we're cutting the bill without cutting corners.

Learning objectives
───────────────────
• Upload JSONL datasets to the OpenAI Files API.
• Create and monitor a supervised fine-tuning job.
• Deploy a fine-tuned model via CognitiveServicesManagementClient.
• Clean up remote resources after training.

Prerequisites
─────────────
    pip install --pre azure-ai-projects azure-identity python-dotenv openai \\
        azure-mgmt-cognitiveservices

Usage
─────
    cp sample.env .env   # fill in your values
    python src/04c_fine_tuning.py

Required environment variables
──────────────────────────────
    AZURE_AI_PROJECT_ENDPOINT                – Foundry project endpoint URL
    AZURE_AI_PROJECTS_AZURE_SUBSCRIPTION_ID  – Azure subscription ID
    AZURE_AI_PROJECTS_AZURE_RESOURCE_GROUP   – Azure resource group name
    AZURE_AI_PROJECTS_AZURE_AOAI_ACCOUNT     – Azure OpenAI account name
"""

import os
import sys
import time

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


# ── Constants ────────────────────────────────────────────────────────────
# The tradeoff triangle: **quality, cost, latency — pick two**.
# gpt-4.1 gives quality but costs more and is slower. Fine-tuning
# gpt-4.1-mini shifts the balance toward cost and latency *without*
# sacrificing task-specific quality, because the training data carries
# the larger model's knowledge into the smaller one.
BASE_MODEL = "gpt-4.1-mini"  # the model we're fine-tuning
DEPLOYMENT_NAME = "gpt-4-1-mini-fine-tuned"
POLL_INTERVAL_SECONDS = 30

# Paths to training / validation JSONL files (relative to this script)
TRAINING_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "docs", "data", "sft_training_set.jsonl"
)
VALIDATION_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "docs", "data", "sft_validation_set.jsonl"
)


def main() -> None:
    # ── Step 1: Load .env, create clients, read config ───────────────────
    env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
    load_dotenv(dotenv_path=env_path)

    project_endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
    subscription_id = os.environ.get("AZURE_AI_PROJECTS_AZURE_SUBSCRIPTION_ID", "")
    resource_group = os.environ.get("AZURE_AI_PROJECTS_AZURE_RESOURCE_GROUP", "")
    account_name = os.environ.get("AZURE_AI_PROJECTS_AZURE_AOAI_ACCOUNT", "")

    if not project_endpoint or project_endpoint.startswith("<"):
        print("❌ AZURE_AI_PROJECT_ENDPOINT is not set. Check your .env file.")
        sys.exit(1)

    credential = DefaultAzureCredential()
    project_client = AIProjectClient(endpoint=project_endpoint, credential=credential)
    openai_client = project_client.get_openai_client()

    print(f"📚 Fine-tuning {BASE_MODEL} with Zava DIY product knowledge\n")

    # Track uploaded file IDs so we can clean them up even on failure
    train_file_id: str | None = None
    val_file_id: str | None = None

    try:
        # ── Step 2: Upload training and validation files ─────────────────
        print("📤 Uploading training data…")
        with open(TRAINING_FILE_PATH, "rb") as f:
            train_file = openai_client.files.create(file=f, purpose="fine-tune")
        train_file_id = train_file.id
        print(f"   Training file uploaded (id: {train_file_id})")

        print("📤 Uploading validation data…")
        with open(VALIDATION_FILE_PATH, "rb") as f:
            val_file = openai_client.files.create(file=f, purpose="fine-tune")
        val_file_id = val_file.id
        print(f"   Validation file uploaded (id: {val_file_id})")

        # Wait for the platform to finish processing the uploads
        print("⏳ Waiting for file processing…")
        openai_client.files.wait_for_processing(train_file_id)
        openai_client.files.wait_for_processing(val_file_id)
        print("   Files processed.\n")

        # ── Step 3: Create a supervised fine-tuning job ──────────────────
        # Hyperparameters explained:
        #   • n_epochs (3)  — how many times the model sees every example.
        #     Too few ⇒ under-fit; too many ⇒ over-fit to the training set.
        #   • batch_size (1) — examples processed before each weight update.
        #     Smaller batches = noisier gradients but can improve stability
        #     on small datasets like ours.
        #   • learning_rate_multiplier (1.0) — controls how aggressively the
        #     model adapts. >1 learns faster but risks instability.
        #
        # Key insight from the walkthrough: "Don't fine-tune on day one.
        # Start with prompt engineering on a capable model. Build eval
        # datasets from real usage. *Then* distill."
        print(f"🔧 Creating fine-tuning job ({BASE_MODEL})…")
        job = openai_client.fine_tuning.jobs.create(
            training_file=train_file_id,
            validation_file=val_file_id,
            model=BASE_MODEL,
            method={
                "type": "supervised",
                "supervised": {
                    "hyperparameters": {
                        "n_epochs": 3,
                        "batch_size": 1,
                        "learning_rate_multiplier": 1.0,
                    },
                },
            },
            extra_body={"trainingType": "Standard"},
        )
        print(f"   Job created (id: {job.id}, status: {job.status})")

        # ── Step 4: Poll for completion ──────────────────────────────────
        print("\n⏳ Monitoring fine-tuning progress…")
        current_job = openai_client.fine_tuning.jobs.retrieve(job.id)
        while current_job.status not in ("succeeded", "failed", "cancelled"):
            print(f"   Status: {current_job.status}")
            time.sleep(POLL_INTERVAL_SECONDS)
            current_job = openai_client.fine_tuning.jobs.retrieve(job.id)

        if current_job.status != "succeeded":
            print(f"\n❌ Fine-tuning {current_job.status}.")
            return

        fine_tuned_model = current_job.fine_tuned_model
        print(f"\n✅ Fine-tuning succeeded!")
        print(f"   Fine-tuned model: {fine_tuned_model}")

        # ── Step 5: Deploy the fine-tuned model ──────────────────────────
        # This is the full cycle: upload data → train → deploy.
        # Three API calls is all it takes to go from an expensive model to
        # a cost-optimized one that's just as accurate for Cora's task.
        if fine_tuned_model and subscription_id and not subscription_id.startswith("<"):
            print("\n🚀 Deploying fine-tuned model…")

            # Import Azure management SDK only when needed for deployment
            from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
            from azure.mgmt.cognitiveservices.models import (
                Deployment,
                DeploymentProperties,
                DeploymentModel,
                Sku,
            )

            cogsvc_client = CognitiveServicesManagementClient(
                credential=credential,
                subscription_id=subscription_id,
            )
            deployment = cogsvc_client.deployments.begin_create_or_update(
                resource_group_name=resource_group,
                account_name=account_name,
                deployment_name=DEPLOYMENT_NAME,
                deployment=Deployment(
                    properties=DeploymentProperties(
                        model=DeploymentModel(
                            format="OpenAI",
                            name=fine_tuned_model,
                            version="1",
                        ),
                    ),
                    sku=Sku(name="GlobalStandard", capacity=50),
                ),
            )
            deployment.result()  # block until the deployment completes
            print(f'   Deployment "{DEPLOYMENT_NAME}" completed.')
        else:
            print("\n⚠️  Skipping deployment — subscription/resource vars not set.")

    except Exception as exc:
        print(f"\n❌ Error during fine-tuning: {exc}")
        raise

    finally:
        # ── Step 6: Clean up uploaded files ──────────────────────────────
        print("\n🧹 Cleaning up uploaded files…")
        for file_id in (train_file_id, val_file_id):
            if file_id:
                try:
                    openai_client.files.delete(file_id)
                    print(f"   Deleted file {file_id}")
                except Exception as del_err:
                    print(f"   ⚠️  Could not delete {file_id}: {del_err}")
        print("   Cleanup complete.")


# The walkthrough transitions from here to Act 2 — "we have an agent,
# maybe even a fine-tuned one. Time to measure if it's any good."
# Next stop: Task 06 (evaluation) and Task 07 (tracing).

if __name__ == "__main__":
    main()
