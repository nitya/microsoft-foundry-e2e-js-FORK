# Task 03: Model Selection

## Learning Objectives

- Evaluate model options by listing deployments in your Foundry project programmatically
- Inspect deployment metadata: name, model name, model version, and SKU
- Test single-turn inference with the Responses API
- Chain prompts with `previous_response_id` for multi-turn conversational context

## Prerequisites

- [Task 02: Setup](02-setup.md) completed — `.env` configured, dependencies installed, connectivity verified

## Concepts

Choosing the right model is a tradeoff between **quality**, **speed**, and **cost**. Larger models like `gpt-4.1` produce richer, more nuanced answers but cost more per token and respond slower. Smaller models like `gpt-4.1-mini` are faster and cheaper but may miss subtle context. Foundry lets you deploy multiple models side-by-side so you can test each with real prompts before committing. The `AIProjectClient.deployments.list()` method gives you a programmatic view of every deployment in your project — no portal clicking required.

The **Responses API** (`openai_client.responses.create()`) is the primary inference endpoint. For single-turn calls you pass `model` and `input`. For multi-turn conversations, you pass `previous_response_id` — a server-side reference to the prior exchange — so the model can answer in context without you manually managing conversation history. This is simpler than the Chat Completions API's message array approach and is the recommended pattern for the Foundry SDK.

In this task you'll list your deployments to confirm what's available, then fire two related questions at the model. The second question ("And do I need a primer first?") only makes sense if the model remembers the first ("What kind of paint should I use for a bathroom renovation?"). If the follow-up response references bathrooms or paint, context is working correctly.

## Hands-On Steps

### Step 1 — Run the selection script

```bash
cd explore/python/labs
python src/03_selection.py
```

### Step 2 — Review the deployment list

The first section of output lists every model deployment in your project:

```
🔐 Connecting to Microsoft Foundry…
   Endpoint: https://<account>.services.ai.azure.com/api/projects/<project>

📋 Listing model deployments…
  • gpt-4.1        |  gpt-4.1 v2025-04-14  |  SKU: GlobalStandard
  • gpt-4.1-mini   |  gpt-4.1-mini v2025-04-14  |  SKU: GlobalStandard
  Total: 2 deployment(s)
```

Each line shows:
| Field | Description |
|-------|-------------|
| **Name** | The deployment name you use in API calls (`model=` parameter) |
| **Model** | The underlying model family and version |
| **SKU** | The pricing/throughput tier (e.g., `GlobalStandard`, `ProvisionedManaged`) |

### Step 3 — Examine the deployment listing code

The key pattern for enumerating deployments:

```python
from azure.ai.projects.models import ModelDeployment

for deployment in project_client.deployments.list():
    if isinstance(deployment, ModelDeployment):
        sku = getattr(deployment, "sku", None)
        sku_label = sku if sku else "n/a"
        print(
            f"  • {deployment.name}  |  "
            f"{deployment.model_name} v{deployment.model_version}  |  "
            f"SKU: {sku_label}"
        )
```

> **Note:** `deployments.list()` may return non-model deployments (e.g., embedding endpoints). The `isinstance(deployment, ModelDeployment)` filter ensures you only inspect model deployments.

### Step 4 — Study the multi-turn conversation code

First turn — a standalone product question:

```python
response = openai_client.responses.create(
    model=deployment_name,
    input="What kind of paint should I use for a bathroom renovation?",
)
```

Second turn — a follow-up that relies on context:

```python
follow_up = openai_client.responses.create(
    model=deployment_name,
    input="And do I need a primer first?",
    previous_response_id=response.id,
)
```

The `previous_response_id=response.id` parameter links the two calls. The server retrieves the prior exchange and includes it as context, so the model knows "primer" refers to the bathroom paint discussion.

### Step 5 — Review the expected output

```
🧪 Testing deployment "gpt-4.1" with a product question…

🤖 Model response:
For a bathroom renovation, you'll want a paint that can handle moisture
and humidity. Look for a semi-gloss or satin finish interior latex paint
with mildew-resistant properties...

💬 Follow-up question (using previous_response_id for context)…
🤖 Follow-up response:
Yes, using a primer is recommended for bathroom walls, especially if
you're painting over a darker color or dealing with new drywall...

✅ Model selection verified — inference with context is working!
```

The follow-up mentions bathrooms and paint without you restating the topic — that confirms `previous_response_id` is carrying context correctly.

### Step 6 — (Optional) Try modifying the test questions

Edit `src/03_selection.py` and change the questions to test different scenarios:

```python
# Try a different domain
response = openai_client.responses.create(
    model=deployment_name,
    input="What tools do I need for basic plumbing repairs?",
)

follow_up = openai_client.responses.create(
    model=deployment_name,
    input="Which of those should I buy first?",
    previous_response_id=response.id,
)
```

Re-run the script to verify the model maintains context across your custom questions.

## Checkpoint

✅ Deployment list displays at least one model with name, version, and SKU  
✅ First response answers the product question coherently  
✅ Follow-up response references the original topic (proving `previous_response_id` context works)

## What's Next

➡️ [Task 04: Customization](04-customization.md) — shape the model's behavior with prompt engineering, context engineering, and fine-tuning.
