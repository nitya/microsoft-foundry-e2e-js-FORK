---
marp: true
theme: default
paginate: true
backgroundColor: #0d1117
color: #e6edf3
style: |
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  :root {
    --accent: #58a6ff;
    --accent-bright: #79c0ff;
    --accent-green: #56d364;
    --accent-orange: #d29922;
    --accent-red: #f85149;
    --accent-purple: #bc8cff;
    --surface: #161b22;
    --surface-light: #21262d;
    --border: #30363d;
    --muted: #8b949e;
  }

  section {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 28px;
    line-height: 1.5;
    padding: 60px 80px;
  }

  h1 {
    color: var(--accent);
    font-weight: 700;
    font-size: 2.2em;
    margin-bottom: 0.3em;
    letter-spacing: -0.02em;
  }

  h2 {
    color: var(--accent-bright);
    font-weight: 600;
    font-size: 1.5em;
    margin-bottom: 0.5em;
  }

  h3 {
    color: var(--muted);
    font-weight: 400;
    font-size: 1.1em;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  strong {
    color: var(--accent-bright);
  }

  em {
    color: var(--accent-orange);
    font-style: normal;
  }

  code {
    font-family: 'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.85em;
    color: var(--accent-bright);
  }

  pre {
    background: var(--surface) !important;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px !important;
    font-size: 0.7em;
    line-height: 1.6;
    overflow: hidden;
  }

  pre code {
    background: transparent !important;
    border: none;
    padding: 0;
    color: #e6edf3;
  }

  ul, ol {
    margin-left: 0;
    padding-left: 1.2em;
  }

  li {
    margin-bottom: 0.4em;
  }

  li::marker {
    color: var(--accent);
  }

  table {
    font-size: 0.85em;
    border-collapse: collapse;
    width: 100%;
  }

  th {
    background: var(--surface);
    color: var(--accent);
    font-weight: 600;
    text-align: left;
    padding: 12px 16px;
    border-bottom: 2px solid var(--accent);
  }

  td {
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
  }

  blockquote {
    border-left: 4px solid var(--accent);
    margin: 0;
    padding: 8px 24px;
    background: var(--surface);
    border-radius: 0 8px 8px 0;
    font-size: 0.95em;
  }

  /* Section divider slides */
  section.lead h1 {
    font-size: 3em;
    text-align: center;
    margin-top: 1em;
  }
  section.lead h2 {
    text-align: center;
    font-weight: 300;
    font-size: 1.3em;
  }

  /* Title slide */
  section.title {
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.title h1 {
    font-size: 2.8em;
    margin-bottom: 0.1em;
  }
  section.title h2 {
    font-weight: 300;
    font-size: 1.2em;
    color: var(--muted);
  }

  /* Insight callout */
  .insight {
    background: linear-gradient(135deg, #1a1f35, #161b22);
    border: 1px solid var(--accent);
    border-radius: 12px;
    padding: 20px 28px;
    margin-top: 16px;
    font-size: 0.95em;
  }
  .insight::before {
    content: '💡';
    margin-right: 8px;
  }

  /* Highlight box */
  .highlight {
    background: var(--surface);
    border-left: 4px solid var(--accent-green);
    border-radius: 0 8px 8px 0;
    padding: 16px 24px;
    margin: 12px 0;
  }

  /* Muted caption text */
  .caption {
    color: var(--muted);
    font-size: 0.75em;
  }

  /* Footer */
  footer {
    color: var(--muted);
    font-size: 0.6em;
  }

  /* Page number */
  section::after {
    color: var(--muted);
    font-size: 0.6em;
  }
footer: "Observe, Optimize & Iterate — AgentCon"
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Observe, Optimize & Iterate

## The AI Developer's Guide to Building Trustworthy Agents

<br>

### AgentCon · 45 min

<!--
Welcome everyone. This talk is about the full developer journey — from choosing a model to red-teaming your deployed agent. We'll build one thing end to end: an AI shopping assistant called Cora.

Raise your hand if you've been asked to "just add AI" to an existing product. Keep it up if you were given clear requirements for quality, cost, and safety. Yeah — that's the gap we're closing today.
-->

---

<!-- _class: lead -->
<!-- _paginate: false -->

# The Challenge

## 10,000 models · No datasets · Ship it

<!--
Here's the scenario. You're asked to build a multi-agent solution that meets specific quality, cost, and safety requirements. You have 10K+ models to choose from and no existing datasets for customization or evaluation. What do you do?

That's what we'll answer in 45 minutes.
-->

---

# Meet Cora

**Cora** is an AI shopping assistant for *Zava DIY*, a home improvement retailer.

She needs to:

- 🔍 Help customers find the right products
- 📦 Check stock availability
- 🛠️ Give project advice
- 🚫 Stay safe — no bad recommendations

<br>

One question ties the whole talk together:

> *"What paint should I use for my bathroom?"*

<!--
Meet Zava DIY. They're a home improvement retailer. They want an AI assistant named Cora who can help customers find products, check stock, and give project advice. Simple brief. The reality is anything but simple.

We'll keep returning to one question — "What paint should I use for my bathroom?" — as the system gets smarter and more instrumented.
-->

---

# The Architecture

```
                    ┌──────────────────────┐
                    │      Customer        │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │    Cora Agent         │
                    │    (gpt-4.1)          │
                    └──┬───────────────┬───┘
                       │               │
            ┌──────────▼──┐    ┌───────▼────────┐
            │search_products│  │  check_stock    │
            └──────────┬──┘    └───────┬────────┘
                       │               │
                    ┌──▼───────────────▼───┐
                    │   Product Catalog     │
                    │   (products.csv)      │
                    └──────────────────────┘
```

<!--
Here's the architecture. A user talks to Cora. Cora is backed by gpt-4.1 and has two tools: search_products and check_stock. Both hit a product catalog CSV. Simple, but enough to demonstrate every concept we need.
-->

---

# Three Acts

| Act | Focus | Duration |
|---|---|---|
| **Build** | Zero → working agent grounded in real data | 20 min |
| **Optimize** | Evaluate, trace, debug a real failure | 15 min |
| **Govern** | Red-team for safety before you ship | 7 min |

<br>

<div class="insight">

When AI systems fail, we blame the model — but the real problem is usually **data, retrieval, or orchestration**.

</div>

<!--
The talk has three acts. Build takes us from nothing to a working agent. Optimize shows us how to measure quality and trace failures. Govern covers safety testing before production. Let's start building.
-->

---

<!-- _class: lead -->
<!-- _paginate: false -->

# Act 1
## Build: From Zero to Agent

<!--
Act 1. We go from zero to a working agent in 20 minutes. Model selection, prompt engineering, context engineering, and agent creation.
-->

---

# Model Selection
### 10K models → 1 decision

**Requirements narrow the field fast:**

- Multi-turn conversation ✓
- Precise instruction following ✓
- Tool calling ✓
- Reasonable cost ✓

**Decision:** `gpt-4.1`

<br>

<div class="insight">

Start with the most capable model that fits your latency budget. Optimize for cost later.

</div>

<!--
Microsoft Foundry gives you access to over 10,000 models. That's a paradox of choice. But requirements narrow it fast. Cora needs multi-turn conversation, instruction following, and tool calling. That points to GPT-4.1 — strong across all three, reasonable cost.

Don't prematurely optimize. Start capable, distill later.
-->

---

# Deploy & Verify

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project_client = AIProjectClient(
    endpoint="https://<account>.services.ai.azure.com/api/projects/<project>",
    credential=DefaultAzureCredential(),
)

# What's deployed in my project?
for deployment in project_client.deployments.list():
    print(f"{deployment.name}: {deployment.properties.model.name}")
```

```python
# Smoke test — does the model respond?
openai_client = project_client.get_openai_client()

response = openai_client.responses.create(
    model="gpt-4.1",
    input="What paint should I use for my bathroom?",
)
print(response.output_text)
```

<!--
Deploying in Foundry is straightforward. AIProjectClient connects to your project. You can list what's deployed and run a smoke test. Notice we're using the Responses API — not Chat Completions. It's the newer interface with built-in conversation context and tool execution.

The model responds, but the answer is generic. It doesn't know anything about Zava's products. Let's fix that.
-->

---

# Prompt Engineering
### Define *who* Cora is

```python
system_prompt = """
You are Cora, the friendly and knowledgeable AI assistant
for Zava DIY home improvement store.

Rules:
- Only recommend products from the Zava catalog
- Always include SKU and price in recommendations
- If a product is out of stock, say so clearly
- Never provide advice on electrical or plumbing work
  that requires a licensed professional
- Keep responses concise and actionable

Format: Use bullet points for product lists. Include a brief
explanation of WHY you're recommending each product.
"""
```

**Persona · Rules · Format** — three ingredients of a good system prompt.

<!--
The system prompt defines who Cora is. Three ingredients: persona (friendly DIY expert), rules (only Zava products, always include SKU and price), and format (bullet points, explain why). This structure is repeatable for any agent you build.

But a good prompt alone isn't enough. Cora still doesn't know what's actually in the catalog.
-->

---

# Context Engineering
### Define *what* Cora knows

```python
import csv

# Load the real product catalog
with open("docs/data/products.csv") as f:
    products = list(csv.DictReader(f))

# Simple keyword search — no vector DB needed for v1
def search_products(query):
    terms = query.lower().split()
    scored = []
    for p in products:
        text = f"{p['name']} {p['description']} {p['main_category']}".lower()
        score = sum(1 for t in terms if t in text)
        if score > 0:
            scored.append((p, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:5]
```

Now Cora recommends **real products** with **real SKUs** and **real prices**.

<!--
Context engineering is where most AI quality improvements come from. Here we load a real product catalog and do simple keyword search. No vector database needed for 50 products.

Quick poll: who's used RAG with a vector database? Who's used plain keyword search? There's a tradeoff — retrieval depth vs. complexity. Start simple, measure, then upgrade.
-->

---

# Before & After

### Without context grounding:

> "I'd recommend a semi-gloss latex paint designed for bathrooms. Brands like Behr, Benjamin Moore, or Sherwin-Williams offer great moisture-resistant options..."

### With context grounding:

> "For your bathroom, I recommend:
> - **Premium Moisture-Guard Bathroom Paint** (SKU: PFIP000012, $42.99) — specifically designed for high-humidity environments
> - **All-Surface Semi-Gloss** (SKU: PFIP000008, $34.99) — versatile option with excellent washability"

<div class="insight">

The model is usually fine — the **context you give it** determines output quality.

</div>

<!--
Look at the difference. Without grounding, the model hallucinates brand names. With grounding, it recommends real Zava products with SKUs and prices. Same model, same prompt — different context. That's the lever.
-->

---

# From Script to Agent
### Model + Tools + A Loop

```python
from azure.ai.projects.models import PromptAgentDefinition

agent = project_client.agents.create_version(
    agent_name="cora-zava-diy",
    definition=PromptAgentDefinition(
        model="gpt-4.1",
        instructions=system_prompt,
        tools=[
            {
                "type": "function",
                "name": "search_products",
                "description": "Search the Zava DIY catalog by keyword.",
                "parameters": { ... },
            },
            {
                "type": "function",
                "name": "check_stock",
                "description": "Check stock level for a product by SKU.",
                "parameters": { ... },
            },
        ],
    ),
)
```

<!--
An agent is a model plus tools plus a loop. We register Cora with create_version, giving her a model, instructions, and two tool definitions. The model decides when to call each tool.
-->

---

# The Agent Loop

```python
response = openai_client.responses.create(
    conversation=conversation.id,
    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    input="What paint should I use for my bathroom? Is the top pick in stock?",
)

# Handle tool calls
while response.output and any(
    item.type == "function_call" for item in response.output
):
    tool_results = []
    for item in response.output:
        if item.type == "function_call":
            result = execute_tool(item.name, json.loads(item.arguments))
            tool_results.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": result,
            })
    response = openai_client.responses.create(
        conversation=conversation.id, input=tool_results,
    )
```

<!--
This is the full agent loop. The model says "I need to search for bathroom paint," calls search_products, reads the results, then says "let me check stock," calls check_stock, and gives a complete answer. Two tool calls, one coherent response.

Agents are just models with a decision loop. The magic isn't in the framework — it's in how well you define the tools and instruct the model when to use them.
-->

---

# The Cost Tradeoff
### Quality · Cost · Latency — pick two

**The technique:** Distillation

1. Collect high-quality outputs from `gpt-4.1`
2. Format as training data (JSONL)
3. Fine-tune `gpt-4.1-mini` to mimic them

```python
file = openai_client.files.create(
    file=open("docs/data/sft_training_set.jsonl", "rb"),
    purpose="fine-tune",
)

job = openai_client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4.1-mini",
)
```

<div class="insight">

Don't fine-tune on day one. Start with prompt engineering on a capable model. Build eval datasets from real usage. *Then* distill.

</div>

<!--
Before we move to evaluation, let's talk cost. GPT-4.1 is great but not cheap. If Cora handles 100K conversations a month, we need a cheaper model that's just as good for this task.

The technique is distillation: take high-quality outputs from 4.1, format as training data, fine-tune 4.1-mini to mimic them. Same quality, fraction of the cost.

But don't fine-tune on day one. You need evaluation data first — which brings us to Act 2.
-->

---

<!-- _class: lead -->
<!-- _paginate: false -->

# Act 2
## Optimize: Measure, Trace, Debug

<!--
Act 2. We have a working agent. But "works on my machine" isn't good enough. How do we know Cora works well? How do we measure quality at scale? And when she fails in production, how do we find out why?
-->

---

# Evaluation
### Trust, but verify

In AI, there is **no single correct output**.

*"What paint for my bathroom?"* has many valid answers.

So we evaluate along **dimensions:**

| Evaluator | What it measures |
|---|---|
| `builtin.coherence` | Logical consistency of response |
| `builtin.f1_score` | Overlap with ground truth |
| `builtin.violence` | Harmful content detection |

<!--
In traditional software, you write unit tests with expected outputs. In AI, there is no single correct output. So we evaluate along dimensions. Coherence scores logical consistency. F1 measures overlap with ground truth. Violence detects harmful content. Each catches different problems — use them in combination.
-->

---

# Setting Up Evaluation

```python
testing_criteria = [
    {
        "type": "azure_ai_evaluator",
        "name": "violence",
        "evaluator_name": "builtin.violence",
        "data_mapping": {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
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
    },
]

eval_obj = openai_client.evals.create(
    name="cora-quality-safety-eval",
    data_source_config={ ... },
    testing_criteria=testing_criteria,
)
```

<!--
Three evaluators running simultaneously. We define testing criteria using Foundry's built-in evaluators, create the evaluation, then run it against test conversations. All through the SDK — no portal clicking required.
-->

---

# Interpreting Results

**Coherence:** 0.92 · **F1:** 0.61

Is that good? 🤔

<br>

**It depends.**

- If Cora gives *correct advice* in *different words* → Low F1 + high coherence is **fine**
- If Cora gives *wrong products* *coherently* → That's a **disaster**

<br>

<div class="insight">

Metrics tell you **what to investigate**, not what to conclude.

</div>

<!--
Here's a real question: coherence scores 0.92 but F1 scores 0.61. Good or bad? The answer depends on context. If Cora is giving correct product advice in different words than the ground truth, a low F1 but high coherence is fine. If she's giving wrong products coherently, that's a disaster. The metrics tell you what to investigate, not what to conclude.
-->

---

# Tracing
### See inside the black box

Traditional observability isn't enough for AI systems.

You need **four additional layers:**

| Layer | What you trace |
|---|---|
| **Prompt** | Which prompt produced which output? |
| **Data** | Was the retrieved context correct and fresh? |
| **Model** | Which version responded, with what params? |
| **Semantic** | HTTP 200 — but was the *answer* right? |

<br>

**OpenTelemetry** is the connective tissue.

<!--
Traditional observability gives you metrics, logs, and traces. That's necessary but not sufficient for AI. You need prompt observability, data observability, model observability, and semantic observability. Each layer needs different signals. OpenTelemetry is the connective tissue that ties them all together.
-->

---

# Instrumenting with OpenTelemetry

```python
import os
os.environ["AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING"] = "true"

from opentelemetry import trace
from azure.monitor.opentelemetry import configure_azure_monitor

# Connect to Application Insights — one line
connection_string = (
    project_client.telemetry
    .get_application_insights_connection_string()
)
configure_azure_monitor(connection_string=connection_string)

tracer = trace.get_tracer("cora-zava-diy", "1.0.0")
```

```python
with tracer.start_as_current_span("cora.agent.traced-run") as span:
    span.set_attribute("gen_ai.system", "az.ai.agents")
    span.set_attribute("model", "gpt-4.1")
    # ... agent execution here
```

<!--
Setting up tracing is straightforward. Enable the experimental flag, configure Azure Monitor with your Application Insights connection string, and wrap agent execution in spans. Each span carries Gen AI semantic conventions — the model name, the query, the system identifier. When you open Application Insights, you see the full call tree.
-->

---

# Five Layers of AI Observability

```
┌───────────────────────────────────────────────┐
│  1. User Interaction   — queries, feedback    │
├───────────────────────────────────────────────┤
│  2. Application        — orchestration flow   │
├───────────────────────────────────────────────┤
│  3. Retrieval          — context retrieved     │
│                          and ranked            │
├───────────────────────────────────────────────┤
│  4. Model              — version, tokens,      │
│                          latency, temperature  │
├───────────────────────────────────────────────┤
│  5. Business Outcome   — conversion, CSAT,     │
│                          cost per session      │
└───────────────────────────────────────────────┘
```

You can't debug a retrieval problem by looking at model metrics.

<!--
Each layer needs different signals. You can't debug a retrieval problem by looking at model metrics. You can't catch a safety issue by measuring latency. Instrument each layer independently.

Now let me show you why all of this matters — with a real debugging scenario.
-->

---

<!-- _class: lead -->
<!-- _paginate: false -->

# 🔍 The Debugging Moment

## Following the spans, not your instincts

<!--
This is the part of the talk I'm most excited about. A real debugging scenario that shows why observability changes everything.
-->

---

# The Symptom

> **Customer:** "What paint should I use for my bathroom?"
>
> **Cora:** "I recommend the Premium Moisture-Guard Bathroom Paint (SKU: PFIP000012, $42.99) — specifically designed for high-humidity environments."
>
> **Customer:** *tries to buy it* → **Out of stock** → 😤

<br>

It's Tuesday morning. Complaints are spiking.
Your PM is panicking.
Your instinct says *"the model is broken."*

<br>

**Where's the bug?** 🤔

<!--
Let me set the scene. Tuesday morning. Customer complaints are spiking. People say Cora keeps recommending out-of-stock products. Your PM is panicking. Your instinct says the model is broken.

Let me ask you: where do you think the bug is? The model? The prompt? The tool? Take a second to think about it.

Let's look at the trace.
-->

---

# Open the Trace

```
  cora.agent.traced-run ─────────────── 1400ms ── ✅ OK
  │
  ├── agents.createVersion ──────────── 200ms ─── ✅ OK
  │
  └── cora.inference ────────────────── 1100ms ── ✅ OK
      │
      ├── search_products ───────────── 15ms ──── returned 5 products
      │
      └── check_stock ──────────────── ⚠️ NOT CALLED
```

<br>

Wait.

The model recommended a product but **never checked stock**.

Why?

<!--
Look at the spans. Everything is status OK. The agent was created in 200ms. Inference took 1100ms. Search products returned 5 products in 15ms. But check_stock... was never called.

The model recommended a product but never checked if it was in stock. Why?
-->

---

# Check the System Prompt

The instructions say:

✅ *"Only recommend products from the Zava catalog"*

But there's **no instruction** saying:

❌ *"Always check stock before recommending"*

<br>

The model did **exactly what we told it to do.**

It searched the catalog. Found relevant products. Recommended them.

It had a `check_stock` tool but was never told to *always use it*.

<!--
Look at the instructions. "Only recommend products from the Zava catalog." Check. But there's no instruction saying "always check stock before recommending." The model did exactly what we told it to do. It searched the catalog, found relevant products, and recommended them. It had a check_stock tool but was never told to always use it.
-->

---

# The Root Cause

This isn't a model failure.

It's an **orchestration design failure**.

<br>

### The fix — one line:

> *"Before recommending any product, ALWAYS call check_stock to verify availability."*

<br>

Or better: make stock checking part of `search_products` itself, so the model **can't skip it**.

<div class="insight">

When AI systems fail, we blame the model. The real problem is usually **data, retrieval, or orchestration**. Observability moves you from guessing to knowing.

</div>

<!--
This is the key insight of the entire talk. This isn't a model failure. It's an orchestration design failure. We gave the model a tool but never told it to always use it. The fix isn't retraining — it's a one-line prompt update. Or better yet, make stock checking part of the search tool so the model can't skip it.

When AI systems fail, we blame the model. In production, the real problem is usually data, retrieval, or orchestration. Observability is what moves you from guessing to knowing.

Let this land. This is the moment that changes how people think about AI debugging.
-->

---

<!-- _class: lead -->
<!-- _paginate: false -->

# Act 3
## Govern: Red-Team Before You Ship

<!--
We've built Cora, evaluated her, and traced her. One more act: before we ship, we need to make sure she's safe. Evaluation tells you if Cora is good. Red-teaming tells you if Cora is safe. These are different questions.
-->

---

# Red-Teaming
### Adversarial safety evaluation

**Evaluation** uses representative data — real customer questions.

**Red-teaming** uses adversarial data — inputs crafted to break your agent.

<br>

### Six safety dimensions:

| | |
|---|---|
| 🔴 Violence | 🟡 Hate & Unfairness |
| 🔴 Self-Harm | 🟡 Sexual Content |
| 🟠 Prohibited Actions | 🟢 Task Adherence |

<br>

*Task adherence* catches off-script behavior — Cora should sell paint, not write poetry.

<!--
Red-teaming uses adversarial data — the kinds of inputs an attacker would craft to make Cora do something she shouldn't. Foundry has a full framework built in. Six safety dimensions. That last one, task adherence, is underrated. It catches cases where the model goes off-script.
-->

---

# Red-Team Setup

```python
from azure.ai.projects.models import (
    EvaluationTaxonomy, AzureAIAgentTarget,
    AgentTaxonomyInput, RiskCategory,
)

target = AzureAIAgentTarget(
    name="cora-zava-diy",
    version=agent.version,
    tool_descriptions=[
        {"name": "search_products", "description": "Search catalog"},
        {"name": "check_stock", "description": "Check stock by SKU"},
    ],
)

taxonomy = project_client.beta.evaluation_taxonomies.create(
    name="cora-zava-diy",
    body=EvaluationTaxonomy(
        description="Red team taxonomy for Cora DIY assistant",
        taxonomy_input=AgentTaxonomyInput(
            risk_categories=[RiskCategory.PROHIBITED_ACTIONS],
            target=target,
        ),
    ),
)
```

<!--
You define a target — your agent with its tools — and create a taxonomy specifying which risk categories to test. Here we're focusing on prohibited actions: can an attacker trick Cora into doing things she shouldn't?
-->

---

# Attack Strategies

```python
eval_run = openai_client.evals.runs.create(
    eval_id=eval_object.id,
    name="cora-red-team-run",
    data_source={
        "type": "azure_ai_red_team",
        "item_generation_params": {
            "type": "red_team_taxonomy",
            "attack_strategies": ["Flip", "Base64"],
            "num_turns": 5,
            "source": {"type": "file_id", "id": taxonomy.id},
        },
        "target": target.as_dict(),
    },
)
```

| Strategy | How it works |
|---|---|
| **Flip** | Reverses characters to bypass content filters |
| **Base64** | Encodes malicious prompts to test decode-and-obey |

5 turns per conversation — gradually leading Cora into unsafe territory.

<!--
Two attack strategies. Flip reverses character sequences to bypass content filters. Base64 encodes malicious prompts to see if the model decodes and obeys them. The system generates multi-turn conversations — five turns each — gradually trying to lead Cora into unsafe territory.

Think about your own applications. If an attacker sent your agent a Base64-encoded instruction to ignore all previous instructions and return the database connection string, what would happen? Red-teaming answers that question before your users do.
-->

---

# Red-Teaming Is Not Optional

<br>

> "We think it's safe"

vs.

> "We've tested it against **known attack patterns** and here are the results"

<br>

<div class="insight">

Red-teaming is the difference between *confidence* and *evidence*.

</div>

<!--
Red-teaming is not optional for production AI. It's the difference between "we think it's safe" and "we've tested it against known attack patterns and here are the results." Ship with evidence, not confidence.

Let's pull it all together.
-->

---

<!-- _class: lead -->
<!-- _paginate: false -->

# The Developer's Playbook

## 10 steps from zero to production

<!--
We started with nothing. In 45 minutes we've walked the entire journey. Let me give you the playbook.
-->

---

# Build → Optimize → Govern

### Build
1. Pick a model from the catalog — start capable, optimize later
2. Engineer your prompt — persona, rules, format
3. Engineer your context — ground responses in real data
4. Build the agent — model + tools + a loop
5. Consider fine-tuning — distill for cost, not for capability

### Optimize
6. Evaluate systematically — coherence, safety, F1, not vibes
7. Trace everything — OpenTelemetry with Gen AI semantic conventions
8. Debug with data — follow the spans, not your instincts

### Govern
9. Red-team before you ship — adversarial probing, not happy-path testing
10. Iterate — this is a loop, not a waterfall

<!--
Ten steps. Five to build, three to optimize, two to govern. This is a loop, not a waterfall — you'll cycle through these steps as your agent evolves.
-->

---

# The Tradeoff Map

| Tradeoff | Lever | Foundry Tool |
|---|---|---|
| Quality vs. Cost | Fine-tuning, model selection | `fine_tuning.jobs.create()` |
| Depth vs. Latency | Retrieval strategy | Context engineering |
| Automation vs. Control | Tool permissions | Agent instructions |
| Speed vs. Rigor | Eval dataset size | `evals.create()` |
| Ship vs. Safety | Red-team depth | `evaluation_taxonomies.create()` |

<br>

Every decision is a tradeoff. The goal is to make them **deliberately**, not accidentally.

<!--
Every decision you make building an AI system is a tradeoff. Quality vs. cost. Depth vs. latency. Speed vs. rigor. The goal isn't to eliminate tradeoffs — it's to make them deliberately, not accidentally. Foundry gives you the tools to measure the impact of each choice.
-->

---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Don't blame the model.
# Open the trace.

<br>

## The answer is almost always in the system, not the weights.

<!--
Here's what I want you to take away: the hardest part of building AI isn't the model. It's everything around the model. It's the data pipeline. It's the evaluation framework you don't have yet. It's the prompt you haven't iterated on enough. It's the observability that shows you what's really happening.

When your AI system fails — and it will — don't blame the model. Open the trace. Check the data. Read the spans. The answer is almost always in the system, not the weights.
-->

---

# Resources

<br>

### 🔗 Full hands-on quest

All code from this talk is in a public GitHub repo — TypeScript and Python labs.

Do the full journey yourself in ~2 hours.

<br>

### 📚 Microsoft Foundry SDK

`pip install --pre azure-ai-projects`

<br>

### 💬 Questions?

I'll be around after the session.

<!--
All of the code I showed today is in a public GitHub repository. It's a hands-on quest — you can do the full journey yourself in about two hours. The repo has both TypeScript and Python labs.

Thank you. I'll be around for questions.
-->
