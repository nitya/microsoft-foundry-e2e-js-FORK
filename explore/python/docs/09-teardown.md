# Task 09: Teardown

You've completed the full developer journey! Before you go, let's clean up the Azure resources created during this quest to avoid unnecessary charges. Azure resources cost money even when idle — model deployments, agents, and evaluations all consume quota.

## Learning Objectives

By the end of this task you will be able to:

- Clean up all SDK-managed cloud resources (agents, evaluations) programmatically.
- Identify resources that require **manual cleanup** via the Azure Portal or CLI.
- Understand the cost implications of leaving resources running.

## Prerequisites

| Requirement | Details |
|---|---|
| Previous tasks | All previous tasks completed (or partially completed — teardown works regardless) |
| Environment configured | `AZURE_AI_PROJECT_ENDPOINT` set in `.env` |
| Python packages | `pip install --pre azure-ai-projects azure-identity python-dotenv openai` |

## Concepts

### Why Teardown Matters

Azure resources cost money even when idle. Model deployments consume compute quota, agents remain registered in your project, and evaluations persist in storage. After a workshop or learning session, cleaning up prevents unexpected charges on your Azure subscription.

### What Gets Cleaned Up

The teardown process has two layers:

1. **Automated cleanup** (handled by the script) — The Python script deletes SDK-managed resources: agent versions created during Tasks 05–08 and evaluations created during Tasks 06–08. These are resources the SDK can enumerate and remove programmatically.

2. **Manual cleanup** (handled by you) — Some resources live outside the SDK's scope: model deployments in the Foundry Portal, the Foundry project itself, and the Azure resource group. These require manual deletion through the portal or CLI.

### Resource Scope

The teardown script targets three specific agents created across the quest labs:

| Agent Name | Created In | Purpose |
|---|---|---|
| `cora-zava-diy` | Task 05 | Main Cora agent with tools |
| `cora-traced-agent` | Task 07 | Agent instrumented with tracing |
| `cora-redteam-agent` | Task 08 | Agent used for red-team evaluation |

## Hands-On Steps

### Step 1 — Run the Teardown Script

```bash
python src/09_teardown.py
```

The script connects to your Foundry project and automatically cleans up agents and evaluations.

### Step 2 — Understand What the Script Does

The teardown script performs four operations in sequence:

**Delete agents** — Enumerates all agents in the project and deletes any matching the quest's agent names:

```python
AGENT_NAMES = ["cora-zava-diy", "cora-traced-agent", "cora-redteam-agent"]

for agent in project_client.agents.list():
    if agent.name in AGENT_NAMES:
        project_client.agents.delete_version(
            agent_name=agent.name,
            agent_version=agent.version,
        )
```

**Delete evaluations** — Removes all evaluations in the project via the OpenAI Evals API:

```python
with project_client.get_openai_client() as openai_client:
    for eval_obj in openai_client.evals.list():
        openai_client.evals.delete(eval_id=eval_obj.id)
```

**List remaining deployments** — Prints any model deployments still active so you know what to clean up manually:

```python
for deployment in project_client.deployments.list():
    print(f"  📦 {deployment.name}")
```

**Print manual cleanup instructions** — Guides you through the remaining steps.

### Step 3 — Delete Model Deployments (Manual)

The script lists remaining deployments but cannot delete them programmatically. Remove them via the Foundry Portal:

1. Go to [https://ai.azure.com](https://ai.azure.com) and sign in.
2. Navigate to your project.
3. Click **Models + endpoints** in the left sidebar.
4. For each deployment listed, click the **⋮** menu → **Delete**.

> ⚠️ **Warning:** Model deployments are the most expensive idle resource. Delete these first to stop charges immediately.

### Step 4 — Delete the Resource Group (Manual)

To remove **all** Azure resources at once, delete the entire resource group.

**Option A — Azure CLI:**

```bash
az group delete --name <your-resource-group> --yes --no-wait
```

**Option B — Azure Portal:**

1. Go to [https://portal.azure.com](https://portal.azure.com) and sign in.
2. Click **Resource groups** on the landing page.
3. Find and click the resource group you created for this quest.
4. Click **Delete resource group** at the top.
5. Type the resource group name to confirm and click **Delete**.

> 💡 **Tip:** Deleting the resource group removes everything inside it — the Foundry project, deployments, storage, and all associated resources. This is the cleanest way to ensure nothing is left behind.

### Step 5 — Clean Up Codespaces (If Applicable)

If you used GitHub Codespaces for this quest:

1. Click the green **Codespaces** button (bottom-left) → **Stop Current Codespace**.
2. Go to [github.com/codespaces](https://github.com/codespaces).
3. Find your codespace, click **⋮** → **Delete**.

### Expected Output

```
🧹 Tearing down Quest 2 resources…

🔐 Connecting to Microsoft Foundry…
   Endpoint: https://<your-project>.services.ai.azure.com/api/projects/<id>

🤖 Cleaning up agents: cora-zava-diy, cora-traced-agent, cora-redteam-agent…
  🗑️  Deleted agent: cora-zava-diy (version 1)
  🗑️  Deleted agent: cora-traced-agent (version 1)
  🗑️  Deleted agent: cora-redteam-agent (version 1)
   Deleted 3 agent(s).

📊 Cleaning up evaluations…
  🗑️  Deleted evaluation: eval_abc123
  🗑️  Deleted evaluation: eval_def456
   Deleted 2 evaluation(s).

🚀 Remaining deployments (delete manually if needed):
  📦 gpt-4.1
  📦 gpt-4.1-mini

📌 Manual cleanup (if needed):
   1. Delete model deployments in Foundry Portal → Deployments
   2. Delete the Foundry project in Azure Portal → Resource groups
   3. Delete the resource group if no longer needed:
        az group delete --name <your-resource-group>

────────────────────────────────────────────────────────
✅ Automated cleanup complete — 3 agent(s), 2 evaluation(s) deleted.

🎉 Congratulations on completing Quest 2!
   You've built an end-to-end AI agent with Microsoft Foundry.
```

## Checkpoint

✅ Verify cleanup is complete:

- [ ] All agents deleted (no matching agents in Foundry Portal)
- [ ] All evaluations deleted
- [ ] Model deployments deleted manually via the Foundry Portal
- [ ] Resource group deleted (or scheduled for deletion)
- [ ] Codespaces session stopped and deleted (if applicable)

## 🎉 Congratulations!

You've completed **Quest 2 — the end-to-end developer journey with the Python SDK and Microsoft Foundry!**

### What You Accomplished

1. **Setup** (Tasks 02–03) — Configured your environment and verified connectivity.
2. **Customization** (Tasks 04a–04c) — Engineered prompts, grounded in product data, fine-tuned a model.
3. **Agent Design** (Tasks 05a–05c) — Built Cora with function tools and conversation management.
4. **Evaluation** (Task 06) — Measured quality and safety with built-in evaluators.
5. **Tracing** (Task 07) — Instrumented execution with OpenTelemetry and Azure Monitor.
6. **Red-Teaming** (Task 08) — Tested against adversarial attacks and identified vulnerabilities.
7. **Teardown** (Task 09) — Cleaned up all cloud resources.

### Next Steps

Now think about how to apply these skills to your own projects:

1. **Write a custom evaluator** — What metrics matter for your specific use case?
2. **Extend Cora's tools** — Add inventory management, order tracking, or return policies.
3. **Fine-tune with your data** — Use real customer conversations for better distillation.
4. **Deploy to production** — Add content filtering, rate limiting, and monitoring.

---

**[← Task 08: Red-Teaming](./08-red-teaming.md)** | **← Back to [README](../../../README.md)**
