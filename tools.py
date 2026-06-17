"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """

    listings = load_listings()
    query_words = set(re.findall(r"[a-z0-9]+", description.lower()))

    results = []
    for item in listings:
        if max_price is not None and item["price"] > max_price:
            continue

        if size is not None:
            item_size = item.get("size", "")
            if size.strip().lower() not in item_size.strip().lower():
                continue

        searchable = " ".join([
            item.get("title", ""),
            item.get("description", ""),
            " ".join(item.get("style_tags", [])),
        ]).lower()
        searchable_words = set(re.findall(r"[a-z0-9]+", searchable))

        score = len(query_words & searchable_words)
        if score == 0:
            continue

        results.append((score, item))

    results.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in results]

# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    client = _get_groq_client()
    items = wardrobe.get("items", [])

    if not items:
        prompt = (
            f"A user just found this secondhand item: {new_item['title']} "
            f"({', '.join(new_item.get('style_tags', []))}, "
            f"{', '.join(new_item.get('colors', []))}). "
            "They don't have any wardrobe items on file yet. "
            "Give 2-3 sentences of general styling advice: what kinds of "
            "items would pair well with this piece, and what overall vibe "
            "it suits. Be specific and concrete, not generic."
        )
    else:
        wardrobe_desc = "\n".join(f"- {it['name']}" for it in items)
        prompt = (
            f"A user just found this secondhand item: {new_item['title']} "
            f"({', '.join(new_item.get('style_tags', []))}, "
            f"{', '.join(new_item.get('colors', []))}). "
            f"Here is their existing wardrobe:\n{wardrobe_desc}\n\n"
            "Suggest one complete outfit combining the new item with "
            "specific named pieces from their wardrobe. Be specific about "
            "styling details (how to wear it, what to tuck/roll/pair)."
        )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    result = response.choices[0].message.content.strip()

    if not result:
        return (
            f"Pair the {new_item['title']} with neutral basics you already "
            "own — it's versatile enough to build a few looks around."
        )
    return result

# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    if not outfit or not outfit.strip():
        return (
            "Can't generate a fit card without a styling suggestion — "
            "try running suggest_outfit first."
        )

    client = _get_groq_client()
    prompt = (
        f"Write a short, casual Instagram/TikTok caption (2-4 sentences) for "
        f"an outfit post. The item is: {new_item['title']}, bought for "
        f"${new_item['price']} on {new_item['platform']}. "
        f"The styling: {outfit}. "
        "Mention the item name, price, and platform naturally — each once. "
        "Make it sound like a real person posting, not a product listing. "
        "Use casual language, maybe an emoji, no hashtags needed."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )
    result = response.choices[0].message.content.strip()

    if not result:
        return (
            f"thrifted this {new_item['title'].lower()} for "
            f"${new_item['price']} on {new_item['platform']} and I'm obsessed"
        )
    return result