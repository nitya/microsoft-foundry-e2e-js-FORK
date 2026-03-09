# Task 02: Setup

## Learning Objectives

- Understand the Foundry project structure and the environment variables it needs
- Authenticate with the Python SDK using `DefaultAzureCredential`
- Create an `AIProjectClient` and obtain an OpenAI-compatible client from it
- Verify connectivity by making a simple inference call via the Responses API

## Prerequisites

- An **Azure subscription** with access to [Microsoft Foundry](https://ai.azure.com)
- A **Foundry project** with a `gpt-4.1` model deployed
- **Azure CLI** installed and signed in (`az login` completed)
- Python 3.10+ installed
- Core SDK packages installed:
  ```bash
  pip install --pre azure-ai-projects azure-identity python-dotenv
  ```

## Concepts

A **Foundry project** is a container in Microsoft Foundry that groups together your model deployments, agents, evaluations, and traces. Every resource you create — a chat deployment, an agent like Cora, an evaluation run — lives inside a project. The project endpoint URL is the single connection string your code needs to reach all of these resources.

**Authentication** uses `DefaultAzureCredential` from the `azure-identity` package. Under the hood, it chains through several credential sources (environment variables, managed identity, Azure CLI, etc.) and picks the first one that works. For local development, it typically uses your `az login` session. This means you never hard-code secrets — the SDK finds credentials automatically.

The **`AIProjectClient`** is the Python SDK's entry point for everything in your project. From it you can list deployments, create agents, run evaluations, and — most importantly for this task — obtain an **OpenAI-compatible client** via `project_client.get_openai_client()`. That client speaks the same OpenAI Responses API you may already know, but it's scoped to your Foundry project so no extra keys or endpoint URLs are required.

## Hands-On Steps

### Step 1 — Configure environment variables

Copy the sample environment file and fill in your values. You can do this manually or use the helper script:

```bash
cd explore/python/labs

# Option A: Auto-populate from your Azure resources
../../labs/scripts/setup-env.sh

# Option B: Manual setup
cp sample.env .env
```

If you go with Option B, open `.env` and set at minimum:

```dotenv
# Your Foundry project endpoint (found on the project Overview page in ai.azure.com)
AZURE_AI_PROJECT_ENDPOINT=https://<account>.services.ai.azure.com/api/projects/<project>

# The deployment name of the model you want to use
MODEL_DEPLOYMENT_NAME=gpt-4.1
```

### Step 2 — Install dependencies

```bash
pip install --pre -r requirements.txt
```

> **Note:** The `--pre` flag is required to pull the latest preview release of `azure-ai-projects`.

### Step 3 — Run the setup verification script

```bash
python src/02_setup.py
```

### Step 4 — Understand the key code

Open `src/02_setup.py` and study these sections:

**Loading and validating environment variables:**

```python
env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
load_dotenv(dotenv_path=env_path)

required_vars = {
    "AZURE_AI_PROJECT_ENDPOINT": os.environ.get("AZURE_AI_PROJECT_ENDPOINT"),
    "MODEL_DEPLOYMENT_NAME": os.environ.get("MODEL_DEPLOYMENT_NAME"),
}
```

**Creating the client chain** (credential → project client → OpenAI client):

```python
with (
    DefaultAzureCredential() as credential,
    AIProjectClient(
        endpoint=project_endpoint,
        credential=credential,
    ) as project_client,
):
    with project_client.get_openai_client() as openai_client:
        response = openai_client.responses.create(
            model=deployment_name,
            input="Say 'Hello from Foundry!' in exactly those words.",
            max_output_tokens=20,
        )
```

All three objects are used as context managers (`with` blocks) so connections and tokens are properly cleaned up when the script exits.

### Step 5 — Review the expected output

A successful run looks like this:

```
🔍 Checking environment variables…

  ✅ AZURE_AI_PROJECT_ENDPOINT
  ✅ MODEL_DEPLOYMENT_NAME

  ⬜ MODEL_ENDPOINT — not set (optional)
  ⬜ MODEL_API_KEY — not set (optional)
  ⬜ TELEMETRY_CONNECTION_STRING — not set (optional)
  ⬜ AZURE_AI_PROJECTS_AZURE_SUBSCRIPTION_ID — not set (optional)
  ⬜ AZURE_AI_PROJECTS_AZURE_RESOURCE_GROUP — not set (optional)
  ⬜ AZURE_AI_PROJECTS_AZURE_AOAI_ACCOUNT — not set (optional)

🔐 Connecting to Microsoft Foundry…
   Endpoint: https://<your-account>.services.ai.azure.com/api/projects/<your-project>

🚀 Testing model deployment: gpt-4.1…
   Model response: "Hello from Foundry!"

✅ Foundry project is reachable and responding.
🎉 Setup verified — you're ready for Quest 2!
```

> **Tip:** If you get a 404 error, your project may still be propagating (this takes 5–15 minutes after creation). The script handles this gracefully and tells you to try again shortly.

## Checkpoint

✅ All required environment variables (`AZURE_AI_PROJECT_ENDPOINT`, `MODEL_DEPLOYMENT_NAME`) are set and validated  
✅ `DefaultAzureCredential` authenticates successfully  
✅ The model responds to a test prompt — you see `"Hello from Foundry!"` in the output

## What's Next

➡️ [Task 03: Model Selection](03-selection.md) — list your deployments and test multi-turn conversation context.
