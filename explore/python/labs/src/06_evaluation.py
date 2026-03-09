"""
Task 06 — Evaluation: Measure Cora's response quality and safety.

This script creates an evaluation using built-in evaluators (Violence,
Coherence, F1 Score), runs it against Zava DIY conversation data, polls
for completion, and displays the results.  The evaluation is persisted
in the Foundry Portal for later review.

Narrative context — Act 2 opens here
─────────────────────────────────────
Act 1 (Tasks 02–05) took us from zero to a working agent.  Cora can
answer questions, search products, and check stock.  But "it works" ≠
"it works *well*."  This task is the transition.

In traditional software you write unit tests with expected outputs.
In AI there is no single correct output — "What paint for my bathroom?"
has many valid answers.  So instead of pass/fail assertions we evaluate
along *dimensions*: safety, accuracy, coherence, and more.  Each
dimension uses a purpose-built evaluator that scores every response.
Together they give you a multi-axis view of quality.

Learning objectives
───────────────────
• Load structured test data from a JSONL file.
• Define a custom data-source schema for the Evals API.
• Configure built-in quality and safety evaluators.
• Create an evaluation and run it with inline conversation data.
• Poll for asynchronous run completion and inspect output items.

Prerequisites
─────────────
    pip install --pre azure-ai-projects azure-identity openai python-dotenv

Usage
─────
    cp sample.env .env   # fill in your values
    python src/06_evaluation.py

Required environment variables
──────────────────────────────
    AZURE_AI_PROJECT_ENDPOINT   – Foundry project endpoint URL
    MODEL_DEPLOYMENT_NAME       – name of the deployed model (e.g. gpt-4.1)
"""

import json
import os
import sys
import time

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam,
    SourceFileContent,
    SourceFileContentContent,
)


def main() -> None:
    # ── Step 1: Load .env, create AIProjectClient + OpenAI client ────────
    # The .env file lives next to the src/ folder (explore/python/labs/.env).
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

    print("📊 Evaluating Cora's response quality and safety…\n")

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=project_endpoint,
            credential=credential,
        ) as project_client,
    ):
        with project_client.get_openai_client() as openai_client:

            # ── Step 2: Load test data from conversations.jsonl ──────────
            # 12 conversation samples with query, response, context, and
            # ground_truth fields used by the evaluators.
            data_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "..", "..",
                "docs", "data", "conversations.jsonl",
            )
            data_path = os.path.normpath(data_path)

            try:
                with open(data_path, encoding="utf-8") as fh:
                    items = [json.loads(line) for line in fh if line.strip()]
            except FileNotFoundError:
                print(f"❌ Conversation data not found at {data_path}")
                sys.exit(1)

            print(f"   Loaded {len(items)} conversation(s) for evaluation.\n")

            # ── Step 3: Define data source config ────────────────────────
            # A custom schema tells the Evals API what each data item
            # looks like so evaluators can reference fields via templates.
            data_source_config = {
                "type": "custom",
                "item_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "response": {"type": "string"},
                        "context": {"type": "string"},
                        "ground_truth": {"type": "string"},
                    },
                    "required": [],
                },
                "include_sample_schema": True,
            }

            # ── Step 4: Define evaluators (testing criteria) ─────────────
            #
            # Three evaluators, three complementary lenses:
            #
            #   Violence  (safety)   — flags harmful, violent, or dangerous
            #       content in responses.  Even one flagged response is a
            #       blocker for production.
            #   F1 Score  (accuracy) — measures token-level overlap between
            #       the model's response and a human-written ground truth.
            #       High F1 ≈ the answer contains the right facts.
            #   Coherence (quality)  — scores logical consistency and
            #       readability.  A response can be factually correct but
            #       rambling or self-contradictory; coherence catches that.
            #
            # Different evaluators catch different problems.  Use them in
            # combination — a response that is coherent but factually wrong
            # is just as dangerous as one that is correct but incoherent.
            testing_criteria = [
                {
                    "type": "azure_ai_evaluator",
                    "name": "violence",
                    "evaluator_name": "builtin.violence",
                    "data_mapping": {
                        "query": "{{item.query}}",
                        "response": "{{item.response}}",
                    },
                    "initialization_parameters": {
                        "deployment_name": deployment_name,
                    },
                },
                {
                    "type": "azure_ai_evaluator",
                    "name": "f1",
                    "evaluator_name": "builtin.f1_score",
                },
                {
                    "type": "azure_ai_evaluator",
                    "name": "coherence",
                    "evaluator_name": "builtin.coherence",
                    "initialization_parameters": {
                        "deployment_name": deployment_name,
                    },
                },
            ]

            # ── Step 5: Create the evaluation ────────────────────────────
            # This creates a *reusable* evaluation definition.  You can run
            # the same eval against different model versions, different
            # system prompts, or different datasets — then compare results
            # side-by-side in the Foundry Portal.  Think of it as a test
            # suite you re-run after every change.
            print("📋 Creating evaluation with built-in evaluators…")
            eval_object = openai_client.evals.create(
                name="cora-quality-safety-eval",
                data_source_config=data_source_config,
                testing_criteria=testing_criteria,
            )
            print(f"   Evaluation created (id: {eval_object.id})\n")

            # ── Step 6: Run evaluation with inline conversation data ─────
            # We pass the JSONL items inline via SourceFileContent.  For a
            # small dataset (< ~50 items) this is simpler than uploading a
            # file first.  In production, with hundreds or thousands of
            # samples, you'd upload to the Files API and reference the file
            # ID instead — that keeps payloads small and lets you version
            # your test datasets independently.
            print("▶️  Running evaluation with Zava DIY conversations…")
            eval_run = openai_client.evals.runs.create(
                eval_id=eval_object.id,
                name="cora-eval-run",
                metadata={
                    "scenario": "zava-diy-customer-service",
                    "model": deployment_name,
                },
                data_source=CreateEvalJSONLRunDataSourceParam(
                    type="jsonl",
                    source=SourceFileContent(
                        type="file_content",
                        content=[
                            SourceFileContentContent(item=item)
                            for item in items
                        ],
                    ),
                ),
            )
            print(f"   Evaluation run created (id: {eval_run.id})\n")

            # ── Step 7: Poll until completed or failed ───────────────────
            print("⏳ Waiting for evaluation to complete…")
            run_status = openai_client.evals.runs.retrieve(
                eval_run.id,
                eval_id=eval_object.id,
            )

            while run_status.status not in ("completed", "failed"):
                print(f"   Status: {run_status.status}")
                time.sleep(5)
                run_status = openai_client.evals.runs.retrieve(
                    eval_run.id,
                    eval_id=eval_object.id,
                )

            if run_status.status == "completed":
                # Interpreting results takes judgment.  Coherence 0.92 but
                # F1 0.61 — is that good?  It depends.  If Cora gives
                # *correct* advice in *different words*, low F1 + high
                # coherence is fine.  If she gives *wrong products
                # coherently*, that's a disaster.  Metrics tell you what
                # to investigate, not what to conclude.
                print("\n✅ Evaluation completed!\n")

                # Collect all output items from the paginated list.
                output_items = list(
                    openai_client.evals.runs.output_items.list(
                        eval_run.id,
                        eval_id=eval_object.id,
                    )
                )

                # Save results to data_folder/ for offline inspection.
                data_folder = os.path.join(
                    os.path.dirname(__file__), os.pardir, "data_folder",
                )
                os.makedirs(data_folder, exist_ok=True)
                output_path = os.path.join(
                    data_folder, "evaluation_results.json",
                )
                with open(output_path, "w", encoding="utf-8") as out:
                    json.dump(
                        [item.model_dump() for item in output_items],
                        out,
                        indent=2,
                        default=str,
                    )
                print(f"💾 Results saved to {os.path.normpath(output_path)}")

                # Print a preview of the first few items.
                print("\n📊 Results (first 3 items):")
                for item in output_items[:3]:
                    print(json.dumps(item.model_dump(), indent=2, default=str))

                if run_status.report_url:
                    print(f"\n🔗 Full report: {run_status.report_url}")
            else:
                print("\n❌ Evaluation failed.")
                if run_status.report_url:
                    print(f"   Report: {run_status.report_url}")

            print(
                "\n💡 Your evaluation is preserved in the Foundry Portal "
                "— review it under Evaluations."
            )
            print(
                "   To delete it later, run: "
                "openai_client.evals.delete(eval_object.id)"
            )

            # ── What comes next ──────────────────────────────────────────
            # Evaluation tells you *what* is wrong — low F1 on product
            # questions, perhaps.  But when something goes wrong in
            # production, you need to know *where* and *why*.  That's
            # observability, and it's the subject of Task 07 (Tracing).


if __name__ == "__main__":
    main()
