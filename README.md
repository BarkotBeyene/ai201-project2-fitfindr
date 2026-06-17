# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

### `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`

**Purpose:** Searches the mock listings dataset for items matching a free-text description, with optional size and price filters.

**Inputs:**
- `description` (str): keywords describing what the user wants (e.g. `"vintage graphic tee"`), matched against each listing's `title`, `description`, and `style_tags`
- `size` (str or None): exact size to filter on, case-insensitive substring match (e.g. `"M"` matches a listing sized `"S/M"`); `None` skips size filtering
- `max_price` (float or None): inclusive price ceiling; `None` skips price filtering

**Returns:** A list of listing dicts (fields: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`), sorted by relevance score, highest first. Returns `[]` — never raises — when nothing matches.

Matches are scored by word overlap, with title/style_tags matches weighted double and description matches weighted once. The word `"vintage"` is excluded from counting as a sole qualifying match, since it appears on roughly 85% of this dataset's listings and provides almost no discrimination on its own. Description-only matches must be 4+ letters, preventing short incidental words (e.g. "tee" appearing inside an unrelated item's description) from qualifying a match by themselves.

---

### `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

**Purpose:** Given a found listing and the user's wardrobe, asks the LLM to suggest a complete outfit combining the new item with existing wardrobe pieces.

**Inputs:**
- `new_item` (dict): a listing dict, in the shape returned by `search_listings`
- `wardrobe` (dict): a dict with an `items` key containing a list of wardrobe item dicts (each with at least a `name` field)

**Returns:** A non-empty string. If `wardrobe["items"]` is empty, the tool calls the LLM with a different prompt asking for general styling advice based on the new item alone, rather than referencing nonexistent wardrobe items. Never returns `None` or an empty string.

---

### `create_fit_card(outfit: str, new_item: dict) -> str`

**Purpose:** Generates a short, casual, shareable caption describing the complete outfit, in the style of a real social media post.

**Inputs:**
- `outfit` (str): the styling suggestion string returned by `suggest_outfit`
- `new_item` (dict): the same listing dict passed to `suggest_outfit`

**Returns:** A 2–4 sentence caption string mentioning the item's title, price, and platform exactly once each. If `outfit` is empty or whitespace-only, the tool returns a fixed error string without calling the LLM. LLM temperature is set to 0.9 so repeated calls on identical input produce varied wording.

---

## Interaction Walkthrough

**User query:** "vintage graphic tee under $30"

**Step 1 — Tool called:**
- Tool: `search_listings`
- Input: `description="vintage graphic tee"`, `size=None`, `max_price=30.0` (parsed from the raw query by stripping the price phrase and filler words)
- Why this tool: the user is asking to find an item, which is the only tool that searches the listings dataset
- Output: a list of matching listings, top result `"Graphic Tee — 2003 Tour Bootleg Style"` ($24.0, Depop, good condition)

**Step 2 — Tool called:**
- Tool: `suggest_outfit`
- Input: `new_item=<the Graphic Tee listing dict from Step 1>`, `wardrobe=<example wardrobe>`
- Why this tool: once a specific item is found, the agent needs to figure out how to style it using the user's existing wardrobe before it can generate a caption
- Output: a styling suggestion combining the tee with baggy straight-leg jeans, a vintage black denim jacket, a brown leather belt, and black combat boots from the wardrobe, plus specific styling details (leave tee untucked, roll jacket sleeves, etc.)

**Step 3 — Tool called:**
- Tool: `create_fit_card`
- Input: `outfit=<the styling suggestion string from Step 2>`, `new_item=<the same Graphic Tee listing dict>`
- Why this tool: the outfit suggestion alone isn't shareable — this tool turns it into a casual caption a real person would post
- Output: *"I just scored this awesome Graphic Tee — 2003 Tour Bootleg Style on Depop for $24.0 and I'm obsessed. I paired it with my fave baggy jeans, vintage denim jacket, and black combat boots for a grunge-inspired look that's perfect for everyday wear 🤘..."*

**Final output to user:** the listing details (Graphic Tee, $24.0, Depop), the outfit suggestion naming specific wardrobe pieces, and the shareable fit card caption — all three populated in the Gradio UI panels.

---

## Error Handling and Fail Points

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | Query `"designer ballgown size XXS under $5"` matches nothing in the dataset | Returns `[]` with no exception. The agent's planning loop sets `session["error"]` to: *"No listings matched your search. Try raising your price limit or removing the size filter."* `session["fit_card"]` stays `None`; `suggest_outfit` and `create_fit_card` are never called. |
| `suggest_outfit` | Called with an empty wardrobe (`get_empty_wardrobe()`) | Falls back to general styling advice instead of crashing or referencing nonexistent items. Actual output: *"This graphic tee is perfect for creating a grunge-inspired look, and would pair well with high-waisted ripped jeans, a flannel shirt tied around the waist, and a pair of black Dr. Martens..."* |
| `create_fit_card` | Called with `outfit=""` | Returns a fixed error string without calling the LLM: *"Can't generate a fit card without a styling suggestion — try running suggest_outfit first."* Verified this short-circuits before the LLM client is ever touched. |

---

## State Management

A single `session` dict is the source of truth for one interaction, initialized fresh per query.

| Key | Set during | What it holds |
|---|---|---|
| `query` | initialization | the raw user query string |
| `parsed` | query parsing | dict with `description`, `size`, `max_price` extracted from the query via regex |
| `search_results` | after `search_listings` | the full list of matching listings |
| `selected_item` | after a non-empty search | the top result, passed by reference into both `suggest_outfit` and `create_fit_card` — confirmed to be the literal same object (checked with `id()` during testing) rather than a re-derived copy |
| `outfit_suggestion` | after `suggest_outfit` | the styling suggestion string, passed directly into `create_fit_card` |
| `fit_card` | after `create_fit_card` | the final caption string |
| `error` | only if search returns no results | set to an actionable message; remains `None` on a successful run |

`handle_query()` in `app.py` reads this same session dict and maps `selected_item` (formatted into readable text), `outfit_suggestion`, and `fit_card` directly onto the three Gradio output panels.

---

## Spec Reflection

**One way planning.md helped during implementation:**

Writing the planning loop as explicit branching logic before touching code — "if results is empty, set error and return early; otherwise set selected_item and proceed" — meant the AI-generated implementation matched the spec on the first pass. There was no back-and-forth needed once the logic was concrete enough to hand over directly as a prompt, rather than a vague description like "it decides what to do next."

**One divergence from your spec, and why:**

The original `search_listings` scoring (pure keyword overlap, no minimum threshold) was looser than planning.md implied. Testing on the real dataset showed a pair of cargo pants matching a `"vintage graphic tee"` query purely because the word "tee" appeared incidentally in its description ("great for layering with a long tee"). The deeper cause turned out to be that 18 of 21 listings carry the `"vintage"` tag, making that single word an almost useless discriminator on its own. I revised the implementation to exclude `"vintage"` as a sole qualifying match and require description-only matches to be 4+ letters, which cut a 20-result query down to 5 genuinely relevant results without breaking either required test case.

---

## AI Usage

**Instance 1 — `search_listings` implementation:** I gave Claude the Tool 1 spec block from planning.md (exact parameter names/types, return shape, failure behavior) and asked it to implement the function using `load_listings()`. After running it against the real dataset, the scoring was too loose (see Spec Reflection above), so I directed a follow-up revision specifically targeting the dominant `"vintage"` tag and short-word false matches, verifying the fix by comparing before/after result counts (20 results down to 5) on the real data before accepting it.

**Instance 2 — `run_agent` planning loop:** I gave Claude the full architecture diagram plus the Planning Loop and State Management sections from planning.md and asked it to implement `run_agent()`. Before accepting the generated code, I checked line by line that it branched on `len(results) == 0`, wrote into the `session` dict rather than passing loose variables, and didn't call all three tools unconditionally. I then verified state was actually flowing — not just architecturally correct — by confirming `selected_item` passed into `suggest_outfit` was the literal same object (via `id()` comparison) rather than a re-derived copy, and confirmed the no-results path never invoked `suggest_outfit` or `create_fit_card` by instrumenting a call log during testing.

---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.