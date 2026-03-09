"""
Task 04b — Context Engineering: Ground Cora's responses in real product data.

This script loads the Zava DIY product catalog (products.csv), builds
context from relevant products, and injects it into the prompt so Cora
can recommend specific products with accurate SKUs and prices.

Narrative context (walkthrough §1.3 — second half)
──────────────────────────────────────────────────
Context engineering is where most AI quality improvements come from.  In
04a Cora had a great persona but hallucinated brand names because she had
no product data.  Here we show the before/after: without grounding the
model invents products; with grounding it recommends real Zava items —
names, SKUs, and prices.  The model is usually fine — the context you
give it determines the output quality.

Learning objectives
───────────────────
• Load and parse external CSV data as grounding context.
• Implement keyword search with term-frequency scoring.
• Inject dynamic product context into a system prompt.
• Observe how grounded responses include real SKUs and prices.

Prerequisites
─────────────
    pip install --pre azure-ai-projects azure-identity python-dotenv

Usage
─────
    cp sample.env .env   # fill in your values
    python src/04b_context_engineering.py

Required environment variables
──────────────────────────────
    AZURE_AI_PROJECT_ENDPOINT   – Foundry project endpoint URL
    MODEL_DEPLOYMENT_NAME       – name of the deployed model (e.g. gpt-4.1)
"""

import csv
import os
import sys

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


# Cora's baseline system prompt (same personality as 04a)
CORA_SYSTEM_PROMPT = (
    "You are Cora, the friendly AI assistant for Zava DIY home improvement store.\n"
    "Help customers find the right products. Always reference specific products "
    "by name, SKU, and price.\n"
    "Be polite, concise, and helpful. Keep responses under 150 words."
)

# Customer questions that exercise product search and grounding
TEST_QUESTIONS = [
    "What paint should I use for my bathroom?",
    "Do you have anything eco-friendly?",
    "How much would it cost to paint a 12x12 room?",
]


def load_products(csv_path: str) -> list[dict[str, str | int | float]]:
    """Read the product catalog CSV and return a list of product dicts."""
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        products: list[dict[str, str | int | float]] = []
        for row in reader:
            products.append({
                "name": row["name"],
                "sku": row["sku"],
                "price": float(row["price"]),
                "description": row["description"],
                "stock_level": int(row["stock_level"]),
                "main_category": row["main_category"],
                "subcategory": row["subcategory"],
            })
    return products


# Intentionally simple: keyword search with term-frequency scoring, not a
# vector database.  "You don't always need the most sophisticated approach.
# Start simple, measure, then upgrade."  A vector DB would be overkill for
# ~50 products — plain keyword search is a perfectly valid v1.
def search_products(
    query: str,
    products: list[dict[str, str | int | float]],
) -> list[dict[str, str | int | float]]:
    """Keyword search with term-frequency scoring; return top 5 matches."""
    terms = query.lower().split()
    scored: list[tuple[int, dict[str, str | int | float]]] = []

    for product in products:
        # Build a single searchable text blob from key fields
        text = (
            f"{product['name']} {product['description']} "
            f"{product['main_category']} {product['subcategory']}"
        ).lower()
        # Score = number of query terms found in the product text
        score = sum(1 for t in terms if t in text)
        if score > 0:
            scored.append((score, product))

    # Sort descending by score, return the top 5
    scored.sort(key=lambda x: x[0], reverse=True)
    return [product for _, product in scored[:5]]


# Format matched products for injection into the prompt — the "grounding"
# pattern.  Each line includes name, SKU, price, description, and stock
# level so the model has everything it needs to make a recommendation
# without hallucinating details.
def format_product_context(
    products: list[dict[str, str | int | float]],
) -> str:
    """Format matched products as bullet-point context for the prompt."""
    if not products:
        return "No matching products found in catalog."
    lines = []
    for p in products:
        # Each line: • Name (SKU: XXX, $YY.YY) — Description [Stock: N]
        lines.append(
            f"• {p['name']} (SKU: {p['sku']}, ${p['price']:.2f}) "
            f"— {p['description']} [Stock: {p['stock_level']}]"
        )
    return "\n".join(lines)


def main() -> None:
    # ── Step 1: Load environment and create clients ──────────────────────
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

    # ── Step 2: Load product catalog from CSV ────────────────────────────
    catalog_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "docs", "data", "products.csv"
    )
    print(f"📦 Loading product catalog from {catalog_path}…")
    try:
        products = load_products(catalog_path)
    except FileNotFoundError:
        print(f"❌ Product catalog not found at {catalog_path}")
        sys.exit(1)
    print(f"   Loaded {len(products)} products.\n")

    # ── Step 3: Connect to Foundry and get OpenAI client ─────────────────
    print("🔐 Connecting to Microsoft Foundry…")
    print(f"   Endpoint: {project_endpoint}\n")

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=project_endpoint,
            credential=credential,
        ) as project_client,
    ):
        with project_client.get_openai_client() as openai_client:
            # ── Step 4–7: For each question, search → build context → ask Cora
            for question in TEST_QUESTIONS:
                print(f'👤 Customer: "{question}"')

                # Step 4: Search the catalog for relevant products
                relevant = search_products(question, products)
                context = format_product_context(relevant)
                print(f"   📋 Found {len(relevant)} relevant product(s)")

                # Step 5-6: Build the enhanced prompt with product context.
                # This is the core of context engineering — we dynamically
                # build the prompt by concatenating Cora's base personality
                # with real product data.  The model sees *different*
                # products for different queries, so answers stay grounded.
                enhanced_prompt = (
                    CORA_SYSTEM_PROMPT
                    + "\n\n## Available Products (from Zava DIY catalog)\n"
                    + context
                    + "\n\nUse ONLY the products listed above to make recommendations. "
                    "Include SKU and price."
                )

                # Step 7: Call the model with grounded context
                response = openai_client.responses.create(
                    model=deployment_name,
                    instructions=enhanced_prompt,
                    input=question,
                )

                print(f"🤖 Cora: {response.output_text}")
                print("─" * 60)

    # ── Summary ───────────────────────────────────────────────────────────
    # The walkthrough insight: "The model is usually fine — the context you
    # give it determines the output quality."  Compare these grounded
    # responses to the hallucinated ones from 04a to see the difference
    # a few lines of product context can make.
    print("\n✅ Context engineering complete!")
    print(
        "💡 Notice: Cora now references specific Zava DIY products with SKUs and prices."
    )
    print(
        "   Next, we'll fine-tune gpt-4.1-mini to bake this knowledge in (04c)."
    )


if __name__ == "__main__":
    main()
