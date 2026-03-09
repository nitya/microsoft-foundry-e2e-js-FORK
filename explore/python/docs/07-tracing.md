# Task 07: Tracing

## Learning Objectives

- Instrument agent execution with OpenTelemetry distributed tracing
- Configure Azure Monitor to receive traces from the Python SDK
- Create root and nested spans with Gen AI semantic attributes
- Send traces to Application Insights and view them in Azure Portal

## Prerequisites

- Task 05 completed (Cora agent working)
- Application Insights resource connected to your Foundry project
- `AZURE_AI_PROJECT_ENDPOINT` and `MODEL_DEPLOYMENT_NAME` set in `labs/.env`
- Optional: `TELEMETRY_CONNECTION_STRING` in `.env` (auto-detected if not set)

## Concepts

**OpenTelemetry** is the industry standard for distributed tracing. It captures the
timing and relationships between operations as *spans* organized into *traces*. Azure
Monitor integrates natively through `azure-monitor-opentelemetry`, which exports spans
to Application Insights where you can search, filter, and visualize them.

**Critical ordering requirement:** `configure_azure_monitor()` must be called *before*
creating any SDK clients. The Azure Monitor SDK hooks into the OpenTelemetry pipeline at
configuration time. If you create an `AIProjectClient` first and configure monitoring
later, those early calls won't be traced. The script in this task sets the environment
variable and calls `configure_azure_monitor()` before any agent operations begin.

The Python SDK auto-instruments agent API calls — you get spans for
`agents.create_version()`, `conversations.create()`, and `responses.create()` without
writing tracing code. For your own application logic, you create custom spans using
`tracer.start_as_current_span()`. The Gen AI semantic conventions
(`gen_ai.system`, `gen_ai.provider.name`, `model`) let you filter traces in the Portal
to find agent-specific activity across all your telemetry.

## Hands-On Steps

### Step 1 — Verify telemetry configuration

Check that your `.env` file has the project endpoint set. The connection string for
Application Insights can either be set explicitly or retrieved at runtime:

```bash
# Option A: Auto-detect (recommended) — the script fetches it from Foundry
# No extra config needed, just ensure AZURE_AI_PROJECT_ENDPOINT is set.

# Option B: Explicit — add to labs/.env
TELEMETRY_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...
```

### Step 2 — Enable Gen AI tracing

Set the experimental flag that enables generative AI span capture. The script does this
automatically, but you can also set it in your shell:

```bash
export AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING=true
```

> **Why is this needed?** Gen AI tracing is behind a feature flag because it can capture
> prompt content in span attributes. Setting this explicitly opts you in.

### Step 3 — Run the tracing script

```bash
cd explore/python/labs
python -m src.07_tracing
```

### Step 4 — Understand the key code

**1. Enable tracing before imports:**

```python
import os
os.environ["AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING"] = "true"

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
load_dotenv(dotenv_path=env_path)
```

**2. Retrieve connection string and configure Azure Monitor:**

```python
connection_string = (
    project_client.telemetry
    .get_application_insights_connection_string()
)

from opentelemetry import trace
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(connection_string=connection_string)
tracer = trace.get_tracer("cora-zava-diy", "1.0.0")
```

**3. Create a root span with Gen AI attributes:**

```python
with tracer.start_as_current_span("cora.agent.traced-run") as root_span:
    root_span.set_attribute("gen_ai.system", "az.ai.agents")
    root_span.set_attribute("gen_ai.provider.name", "microsoft.agents")
    root_span.set_attribute("model", deployment_name)
    root_span.set_attribute("projectEndpoint", project_endpoint)
```

**4. Nested span for agent creation:**

```python
    with tracer.start_as_current_span("agents.createVersion") as agent_span:
        agent_span.set_attribute("deploymentName", deployment_name)

        agent = project_client.agents.create_version(
            agent_name="cora-traced-agent",
            definition=PromptAgentDefinition(
                model=deployment_name,
                instructions="You are Cora, the friendly AI assistant for Zava DIY...",
            ),
        )

        agent_span.set_attribute("agent.name", agent.name)
        agent_span.set_attribute("agent.version", agent.version)
        agent_span.set_attribute("agent.id", agent.id)
```

**5. Nested span for inference:**

```python
    with tracer.start_as_current_span("cora.inference") as inference_span:
        inference_span.set_attribute("query", "What paint for my bathroom?")

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

            inference_span.set_attribute("response.length", len(response.output_text or ""))
            openai_client.conversations.delete(conversation_id=conversation.id)
```

**6. Error handling on the root span:**

```python
    except Exception as exc:
        root_span.set_attribute("error", True)
        root_span.set_attribute("error.message", str(exc))
        raise
```

**7. Cleanup — delete the temporary agent:**

```python
    finally:
        if agent is not None:
            project_client.agents.delete_version(
                agent_name=agent.name,
                agent_version=agent.version,
            )
```

### Step 5 — View traces in Azure Portal

1. Open the [Azure Portal](https://portal.azure.com)
2. Navigate to your **Application Insights** resource (linked to your Foundry project)
3. Go to **Transaction search** in the left menu
4. Set the time range to the **last 30 minutes**
5. Look for operations named `cora.agent.traced-run`

You should see a trace with nested spans:

```
cora.agent.traced-run          ← root span
├── agents.createVersion       ← agent registration
└── cora.inference             ← conversation with Cora
    ├── conversations.create   ← auto-instrumented SDK call
    └── responses.create       ← auto-instrumented SDK call
```

### Step 6 — Filter by Gen AI attributes

To find only agent-related traces across all your telemetry:

```kusto
// In Application Insights → Logs (KQL)
dependencies
| where customDimensions["gen_ai.system"] == "az.ai.agents"
| project timestamp, name, duration, customDimensions
| order by timestamp desc
```

Or use the **Transaction search** filter:

- Custom property: `gen_ai.system` = `az.ai.agents`

> **Note:** Traces may take 2–5 minutes to appear in Application Insights after the
> script completes.

**Expected console output:**

```
🔍 Tracing enabled — sending telemetry to Application Insights

✅ Agent created: cora-traced-agent (version: 1)
💬 Query: What paint should I use for my bathroom?
📝 Response: For your bathroom, I'd recommend...

📊 Traces sent! View them in Azure Portal:
   Application Insights → Transaction search
   Filter: gen_ai.system = az.ai.agents

🧹 Cleaned up agent: cora-traced-agent
```

## Checkpoint

✅ Script completes without errors  
✅ Traces appear in Application Insights within 2–5 minutes  
✅ Root span `cora.agent.traced-run` is visible with nested child spans  
✅ Custom attributes (`gen_ai.system`, `model`, `agent.name`) are populated  
✅ Auto-instrumented SDK spans appear under the inference span

## What's Next

➡️ [Task 08: Red-Teaming](08-red-teaming.md) — probe the agent for vulnerabilities
using automated adversarial testing.
