# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Task 05c — Tools: Product search and stock-check implementations.

This module provides the tool functions that the Cora AI agent uses to
answer customer questions about Zava DIY products.  It reads the product
catalog from a CSV file and exposes two capabilities:

  • search_products — keyword search across names, descriptions, and categories
  • check_stock    — stock-level lookup by SKU

Narrative context
─────────────────
The walkthrough's key insight about tools:

    "The magic isn't in the framework — it's in how well you define
     the tools and how clearly you instruct the model when to use them."

This module defines the tools that make Cora *useful*.  Without them she
can only give generic advice; with them she can look up real products,
check real inventory, and give actionable answers.

Learning objectives
───────────────────
  1. Understand how to define OpenAI-compatible *function tool* schemas so
     an agent can decide when to call your code.
  2. See how a simple keyword-scoring algorithm can power product search
     without a vector database.
  3. Learn the dispatcher pattern (execute_tool) that maps tool names
     coming from the model back to real Python functions.

Prerequisites
─────────────
  • Python 3.10+
  • The product catalog at  docs/data/products.csv  (relative to repo root)

Usage
─────
    from labs.src.tools_05c import search_products, check_stock, execute_tool

    # Direct call
    print(search_products("exterior primer"))

    # Via dispatcher (as the agent runtime would call it)
    print(execute_tool("check_stock", {"sku": "PFIP000001"}))
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass

# ── Step 1: Define the Product data model ────────────────────────────────
#
# A dataclass gives us a clean, typed representation of each catalog row.
# Using a dataclass (vs. a raw dict) gives us type safety and IDE
# auto-complete.  frozen=True makes instances immutable, preventing
# accidental mutation of cached catalog data.
# Fields mirror the CSV columns (image_path is omitted — not needed for
# search or stock checks).


@dataclass(frozen=True)
class Product:
    """A single product in the Zava DIY catalog."""

    name: str
    sku: str
    price: float
    description: str
    stock_level: int
    main_category: str
    subcategory: str


# ── Step 2: Load and cache the product catalog ──────────────────────────
#
# The CSV path is resolved relative to *this* file so the code works
# regardless of where the caller's working directory is.  Python's built-in
# csv.DictReader handles quoted fields automatically — no manual parsing
# needed (unlike the JS version).

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "docs", "data", "products.csv"
)

_products: list[Product] | None = None


def _get_products() -> list[Product]:
    """Load the catalog from CSV on first call; return cached list after."""
    global _products
    if _products is not None:
        return _products

    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)  # automatically uses the header row as keys
        _products = [
            Product(
                name=row["name"],
                sku=row["sku"],
                price=float(row["price"]),
                description=row["description"],
                stock_level=int(row["stock_level"]),
                main_category=row["main_category"],
                subcategory=row["subcategory"],
            )
            for row in reader
        ]
    return _products


# ── Step 3: Implement search_products ────────────────────────────────────
#
# Scoring strategy: split the query into whitespace-delimited terms, then
# count how many terms appear anywhere in the product's searchable text
# (name + description + categories).  Higher overlap → higher rank.
# Return the top 5 matches formatted as readable strings.
#
# Walkthrough connection (Act 2, Section 2.3 — Debugging):
# The fact that search_products and check_stock are *separate* tools is
# what causes the "out of stock" bug.  The model can call search_products
# without calling check_stock, so it may recommend out-of-stock items.
# The walkthrough's fix: "make stock checking part of the search_products
# tool itself, so the model can't skip it."


def search_products(query: str) -> str:
    """Search the Zava DIY product catalog by keyword.

    Returns up to 5 matching products with name, SKU, price, description,
    and current stock level.
    """
    products = _get_products()
    terms = query.lower().split()

    # Score each product by the number of query terms that appear in its text
    scored = []
    for p in products:
        text = f"{p.name} {p.description} {p.main_category} {p.subcategory}".lower()
        score = sum(1 for t in terms if t in text)
        if score > 0:
            scored.append((p, score))

    # Sort by score descending, keep top 5
    scored.sort(key=lambda pair: pair[1], reverse=True)
    top = scored[:5]

    if not top:
        return "No products found matching your query."

    return "\n".join(
        f"{p.name} (SKU: {p.sku}, ${p.price:.2f}) — {p.description} "
        f"[Stock: {p.stock_level}]"
        for p, _score in top
    )


# ── Step 4: Implement check_stock ────────────────────────────────────────
#
# Look up a product by SKU (case-insensitive) and return a human-readable
# status string.  Thresholds: 0 → OUT OF STOCK, <5 → LOW STOCK, else IN STOCK.
# These thresholds map directly to Cora's system instructions in 05a, which
# say "if stock is low (< 5 units), warn the customer."  Keeping the
# threshold logic here (not in the prompt) ensures consistency.


def check_stock(sku: str) -> str:
    """Check the current stock level for a specific product by SKU.

    Returns the product name, SKU, stock status, unit count, and price.
    """
    products = _get_products()

    # Case-insensitive SKU lookup
    product = next((p for p in products if p.sku.lower() == sku.lower()), None)

    if product is None:
        return f'Product with SKU "{sku}" not found in catalog.'

    # Determine human-readable stock status
    if product.stock_level == 0:
        status = "OUT OF STOCK"
    elif product.stock_level < 5:
        status = "LOW STOCK"
    else:
        status = "IN STOCK"

    return (
        f"{product.name} (SKU: {product.sku}) — {status} "
        f"({product.stock_level} units available), ${product.price:.2f}"
    )


# ── Step 5: Define OpenAI-compatible tool schemas ────────────────────────
#
# These definitions tell the model what tools are available, what arguments
# they accept, and how to describe them to end-users.  "strict": True
# enables structured-output mode — the model *must* produce valid JSON
# matching the schema exactly, eliminating parse errors.  This is a
# production reliability pattern: without it, the model might return
# malformed JSON that crashes the tool-call loop.

tool_definitions: list[dict] = [
    {
        "type": "function",
        "name": "search_products",
        "description": (
            "Search the Zava DIY product catalog by keyword. "
            "Returns matching products with name, SKU, price, and description."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search keywords (e.g., 'bathroom paint', "
                        "'exterior primer', 'eco-friendly')"
                    ),
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "check_stock",
        "description": (
            "Check the current stock level for a specific product by SKU number."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "The product SKU (e.g., 'PFIP000001')",
                },
            },
            "required": ["sku"],
            "additionalProperties": False,
        },
    },
]


# ── Step 6: Tool dispatcher ──────────────────────────────────────────────
#
# The dispatcher pattern decouples tool *definition* (what the model knows
# about — the schemas in Step 5) from tool *execution* (what actually runs).
# This separation matters because the same tool_definitions are used in
# agent registration (05a_create_agent.py), while the dispatcher is used
# at runtime (05b_run_agent.py).  Adding a new tool means updating both
# the schema list and the dispatch table — but nothing else changes.

_TOOL_DISPATCH: dict[str, callable] = {
    "search_products": lambda args: search_products(args["query"]),
    "check_stock": lambda args: check_stock(args["sku"]),
}


def execute_tool(name: str, args: dict) -> str:
    """Dispatch a tool call by name and return the result string."""
    handler = _TOOL_DISPATCH.get(name)
    if handler is None:
        return f"Unknown tool: {name}"
    return handler(args)
