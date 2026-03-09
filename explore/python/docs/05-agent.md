# Task 05: Agent

## Learning Objectives

- Understand how a Foundry agent combines a model, instructions, and tools into one unit
- Create an agent with function tools using `project_client.agents.create_version()`
- Run multi-turn conversations where the agent decides when to call tools
- Handle the tool-call loop: detect calls, execute locally, submit results back

## Prerequisites

- Task 04 completed (model deployment working, `.env` configured)
- `AZURE_AI_PROJECT_ENDPOINT` and `MODEL_DEPLOYMENT_NAME` set in `labs/.env`
- Python dependencies installed (`pip install -r labs/requirements.txt`)

## Concepts

An agent is **Model + Instructions + Tools**. The model decides *when* to call a tool
based on the user's message and the system instructions. Your code is responsible for
*executing* the tool and returning the result. The agent never runs tools itself — it
produces structured function-call requests that your application fulfils.

Function tools are described with JSON Schema so the model knows what parameters each
tool accepts. In the Zava DIY scenario, Cora has two tools: `search_products` (keyword
search across the product catalog) and `check_stock` (SKU-level inventory lookup). The
schemas use `"strict": true` to guarantee the model produces valid arguments every time.

The conversation loop works like this: you send a user message → the agent responds,
possibly with one or more `function_call` items in its output → your code parses the
arguments, calls the real function, and submits the results back as
`function_call_output` → the agent produces a final text response incorporating the
tool results. This loop can repeat up to `MAX_TOOL_ITERATIONS` times per turn.

## Hands-On Steps

### Step 1 — Review the tool implementations

Open `labs/src/05c_tools.py` and examine the two tool functions and their schemas:

```python
# Product catalog is loaded from CSV on first call and cached
@dataclass(frozen=True, slots=True)
class Product:
    name: str
    sku: str
    price: float
    description: str
    stock_level: int
    main_category: str
    subcategory: str

def search_products(query: str) -> str:
    """Keyword-scored search across the Zava DIY catalog. Returns top 5 matches."""

def check_stock(sku: str) -> str:
    """Case-insensitive SKU lookup with stock-status thresholds."""
```

Note the dispatcher pattern that maps tool names to handlers:

```python
_TOOL_DISPATCH: dict[str, callable] = {
    "search_products": lambda args: search_products(args["query"]),
    "check_stock":     lambda args: check_stock(args["sku"]),
}

def execute_tool(name: str, args: dict) -> str:
    handler = _TOOL_DISPATCH.get(name)
    if handler is None:
        return f"Unknown tool: {name}"
    return handler(args)
```

And the OpenAI-compatible tool definitions list:

```python
tool_definitions: list[dict] = [
    {
        "type": "function",
        "name": "search_products",
        "description": "Search the Zava DIY product catalog by keyword...",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keywords..."}
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "check_stock",
        "description": "Check the current stock level for a specific product by SKU number.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "description": "The product SKU (e.g., 'PFIP000001')"}
            },
            "required": ["sku"],
            "additionalProperties": False,
        },
    },
]
```

### Step 2 — Create the agent

Run the agent registration script:

```bash
cd explore/python/labs
python -m src.05a_create_agent
```

This script:

1. Loads `.env` and validates the required environment variables.
2. Creates an `AIProjectClient` with `DefaultAzureCredential()`.
3. Imports `tool_definitions` from `05c_tools.py`.
4. Registers the agent with Foundry:

```python
from azure.ai.projects.models import PromptAgentDefinition

agent = project_client.agents.create_version(
    agent_name="cora-zava-diy",
    definition=PromptAgentDefinition(
        model=deployment_name,
        instructions=CORA_INSTRUCTIONS,   # system prompt defining Cora's persona
        tools=tool_definitions,
    ),
)
```

**Expected output:**

```
✅ Agent created: cora-zava-diy (version: 1)
```

### Step 3 — Run conversations

Send test questions through the agent:

```bash
python -m src.05b_run_agent
```

The script sends three customer questions:

```python
CUSTOMER_QUESTIONS = [
    "What paint should I use for my bathroom?",
    "Is the Interior Semi-Gloss Paint in stock?",
    "I need something eco-friendly for my baby's nursery.",
]
```

### Step 4 — Understand the conversation loop

For each question, `05b_run_agent.py` executes this loop:

```python
AGENT_NAME = "cora-zava-diy"
MAX_TOOL_ITERATIONS = 5

# 1. Create a conversation with the customer message
conversation = openai_client.conversations.create()
response = openai_client.responses.create(
    conversation=conversation.id,
    extra_body={
        "agent_reference": {"name": AGENT_NAME, "type": "agent_reference"},
    },
    input=question,
)

# 2. Tool-call loop
for _ in range(MAX_TOOL_ITERATIONS):
    tool_calls = [item for item in response.output if item.type == "function_call"]
    if not tool_calls:
        break  # Agent is done — no more tool calls

    tool_results = []
    for call in tool_calls:
        args = json.loads(call.arguments)
        result = execute_tool(call.name, args)
        tool_results.append({
            "type": "function_call_output",
            "call_id": call.id,
            "output": result,
        })

    # 3. Submit results back to the agent
    response = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={
            "agent_reference": {"name": AGENT_NAME, "type": "agent_reference"},
        },
        input=tool_results,
        previous_response_id=response.id,
    )

# 4. Get the final text response
print(response.output_text)
openai_client.conversations.delete(conversation_id=conversation.id)
```

### Step 5 — Observe the output

You should see Cora respond with specific product recommendations pulled from the
catalog. For example:

```
━━━ Question: What paint should I use for my bathroom? ━━━

🔧 Tool call: search_products({"query": "bathroom paint"})
   → Interior Semi-Gloss Paint (SKU: PFIP000003, $47.00) — ...

💬 Cora: For your bathroom, I'd recommend our Interior Semi-Gloss Paint
   (SKU: PFIP000003, $47.00). Semi-gloss is ideal for bathrooms because
   it resists moisture and is easy to clean. ⚠️ Heads up — stock is low
   (2 units), so grab it soon!
```

## Checkpoint

✅ Agent `cora-zava-diy` is registered in your Foundry project  
✅ All three test questions produce tool calls followed by text responses  
✅ Cora references real product names, SKUs, and prices from the Zava DIY catalog  
✅ Low-stock warnings appear for products with fewer than 5 units (e.g., PFIP000003)

## What's Next

➡️ [Task 06: Evaluation](06-evaluation.md) — measure how well Cora responds using
built-in quality and safety evaluators.
