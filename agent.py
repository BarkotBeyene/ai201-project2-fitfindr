"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card
import re


# ── session state ─────────────────────────────────────────────────────────────
def parse_query(query: str) -> dict:
    text = query.lower()
 
    max_price = None
    price_match = re.search(r"(?:under|max|below)\s*\$?(\d+(?:\.\d+)?)", text)
    if not price_match:
        price_match = re.search(r"\$(\d+(?:\.\d+)?)", text)
    if price_match:
        max_price = float(price_match.group(1))
 
    size = None
    size_match = re.search(r"size\s*[:\-]?\s*([a-z0-9/]+)", text)
    if size_match:
        size = size_match.group(1).upper()
 
    first_sentence = re.split(r"[.!?]", query)[0]
    description = first_sentence
    description = re.sub(r"(?:under|max|below)\s*\$?\d+(?:\.\d+)?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\$\d+(?:\.\d+)?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"size\s*[:\-]?\s*[a-zA-Z0-9/]+", "", description, flags=re.IGNORECASE)
    description = re.sub(
        r"\b(i'?m\s+)?(looking for|searching for|want|need)\s+(a|an|some)?\b",
        "", description, flags=re.IGNORECASE,
    )
    description = re.sub(r"[,]+", " ", description)
    description = re.sub(r"\s+", " ", description).strip()
 
    return {"description": description, "size": size, "max_price": max_price}

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    """
    session = _new_session(query, wardrobe)
 
    # Step 2: parse
    session["parsed"] = parse_query(query)
 
    # Step 3: search
    results = search_listings(
        session["parsed"]["description"],
        session["parsed"]["size"],
        session["parsed"]["max_price"],
    )
    session["search_results"] = results
 
    if not results:
        session["error"] = (
            "No listings matched your search. Try raising your price limit "
            "or removing the size filter."
        )
        return session  # early return — steps 4-6 skipped
 
    # Step 4: select top result
    session["selected_item"] = results[0]
 
    # Step 5: suggest outfit
    session["outfit_suggestion"] = suggest_outfit(session["selected_item"], wardrobe)
 
    # Step 6: create fit card
    session["fit_card"] = create_fit_card(session["outfit_suggestion"], session["selected_item"])
 
    # Step 7: return
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
