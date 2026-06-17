# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Filters the mock listings dataset by description relevance, optional size match, and a maximum price ceiling, returning matches sorted by relevance.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): free-text description of what the user is looking for (e.g. "vintage graphic tee"), matched against each listing's title, description, and style_tags fields
- `size` (str): exact size to filter on (e.g. "M"); if None, no size filtering is applied
- `max_price` (float): upper price bound; listings with price above this are excluded

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of listing dicts, each containing the full fields from load_listings(): id, title, description, category, style_tags, size, condition, price, colors, brand, platform. Sorted with the most relevant match first. Returns [] (not None, not an exception) when nothing matches.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
Returns an empty list. The agent does not call suggest_outfit with an empty result — it sets session["error"] to a message telling the user nothing matched and suggesting they raise max_price or drop the size filter, then returns early.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given a newly found item and the user's current wardrobe, calls the LLM to suggest one or more complete outfit pairings using items already in the wardrobe.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): a single listing dict (the shape returned by search_listings, e.g. {"title": "Faded Band Tee", "price": 22.0, ...})
- `wardrobe` (dict): a wardrobe dict with an items key containing a list of wardrobe item dicts, as returned by get_example_wardrobe() or get_empty_wardrobe()

**What it returns:**
<!-- Describe the return value -->
A string containing a styling suggestion — which wardrobe items to pair with new_item and how (e.g. rolling sleeves, tucking, footwear choice). Never returns None or an empty string.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If wardrobe["items"] is empty, the tool does not call the LLM with an empty wardrobe context — instead it falls back to general styling advice based on new_item alone (e.g. generic pairing suggestions for that category) and returns that string. It never raises an exception or returns "".

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generates a short, shareable, caption-style description of the complete outfit, suitable for captioning a social post.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): the styling suggestion string returned by suggest_outfit
- `new_item` (dict): the same listing dict passed to suggest_outfit

**What it returns:**
<!-- Describe the return value -->
A string: a short, casual caption referencing the item, its source/price, and the styling pairing. Different inputs should produce different captions (verified by running on identical input multiple times and confirming variation, raising LLM temperature if not).

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If outfit is empty or missing, the tool does not call the LLM — it returns a descriptive error string (e.g. "Can't generate a fit card without a styling suggestion.") rather than raising an exception or returning an empty string.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The planning loop runs as a fixed sequence of conditional checks, not a fixed sequence of calls — each step's execution depends on the outcome of the step before it.

1. Parse the user query into description, size (or None if unspecified), and max_price.
2. Call search_listings(description, size, max_price).
3. If results is empty: set session["error"] = "No listings matched. Try raising your price limit or removing the size filter.", leave session["selected_item"], session["outfit_suggestion"], and session["fit_card"] as None, and return the session immediately. Do not proceed to step 4.
4. If results is non-empty: set session["selected_item"] = results[0].
5. Call suggest_outfit(new_item=session["selected_item"], wardrobe=wardrobe).
6. Set session["outfit_suggestion"] to the returned string. (This call cannot itself short-circuit the loop — suggest_outfit always returns a usable string, even on an empty wardrobe — so the loop always proceeds to step 7 once step 4 is reached.)
7. Call create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"]).
8. Set session["fit_card"] to the returned string.
9. Return the completed session.

The loop terminates early only at step 3. Every other branch point is absorbed inside the tool itself (each tool guarantees a usable return value), which is why the loop's only externally visible branch is the search-results check.
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | session["error"] is set to: "No listings matched your search. Try raising your price limit or removing the size filter." Loop returns immediately; suggest_outfit and create_fit_card are never called. |
| suggest_outfit | Wardrobe is empty | Tool returns general styling advice for new_item's category instead of a wardrobe-specific pairing, e.g.: "Your wardrobe is empty, but a faded graphic tee like this pairs well with relaxed denim and a low-profile sneaker — a classic, easy combo to build around." Loop proceeds normally to create_fit_card. |
| create_fit_card | Outfit input is missing or incomplete | Tool returns the literal string: "Can't generate a fit card without a styling suggestion — try running suggest_outfit first." No exception raised; session["fit_card"] is set to this string rather than left as None. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

User query
    │
    ▼
Planning Loop
    │
    ├─► search_listings(description, size, max_price)
    │       │
    │       │ results=[]
    │       ├──► session["error"] = "No listings matched..." 
    │       │         │
    │       │         ▼
    │       │     [RETURN SESSION — error path, steps 5–8 skipped]
    │       │
    │       │ results=[item, ...]
    │       ▼
    │   session["selected_item"] = results[0]
    │       │
    ├─► suggest_outfit(session["selected_item"], wardrobe)
    │       │
    │   session["outfit_suggestion"] = "..."
    │       │
    ├─► create_fit_card(session["outfit_suggestion"], session["selected_item"])
    │       │
    │   session["fit_card"] = "..."
    │       │
    ▼
Return session (selected_item, outfit_suggestion, fit_card, error=None)
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I'll use Claude. For each tool, I'll paste only that tool's spec block from this planning.md (what it does, input parameters with types, return shape, failure behavior) and ask Claude to implement that single function in tools.py using load_listings() / get_example_wardrobe() / get_empty_wardrobe() from utils/data_loader.py — not reimplementing file loading. I'll do this one tool at a time rather than all three at once, so each generated function can be checked in isolation.
Before running each generated function, I'll verify: does it accept exactly the parameters named in the spec (same names, same types)? Does it return the exact shape described (e.g. for search_listings, a list of full listing dicts, not just titles)? Does it implement the documented failure behavior (empty list, fallback string, or error string — never an exception)? After that check, I'll run it against the specific test inputs from Milestone 3 (a matching query, an impossible query, an empty wardrobe, an empty outfit string) before writing the corresponding pytest test.

**Milestone 4 — Planning loop and state management:**
I'll give Claude the full architecture diagram from this planning.md plus the Planning Loop and State Management sections as one combined prompt, and ask it to implement run_agent() in agent.py following the existing TODO structure in the file.
Before running the generated code, I'll check it against the spec line by line: does it check len(results) == 0 and short-circuit before calling suggest_outfit/create_fit_card when true? Does it write into a session dict rather than passing loose local variables between calls? Does it avoid calling all three tools unconditionally regardless of the search outcome? If any of these don't match, I'll revise the generated code rather than the spec. After that, I'll run the example query from the Complete Interaction section and print session["selected_item"] and session["outfit_suggestion"] at each stage to confirm they're literally the same objects passed forward, not re-derived.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The planning loop parses the query and calls search_listings(description="vintage graphic tee", size=None, max_price=30.0). Size wasn't specified in this query, so it's passed as None rather than guessed. This returns a list of matching listing dicts from load_listings(), filtered by description match and price ceiling.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
The loop checks len(results) > 0. Since matches exist, it takes the top result (e.g. {"title": "Faded Band Tee", "price": 22.0, "platform": "depop", ...}) and stores it in session["selected_item"]. It then calls suggest_outfit(new_item=session["selected_item"], wardrobe=get_example_wardrobe()), passing the mention of "baggy jeans and chunky sneakers" along as context so the LLM can lean toward items matching that style if they exist in the wardrobe.

**Step 3:**
<!-- Continue until the full interaction is complete -->
suggest_outfit returns a styling suggestion string (e.g. pairing the tee with wide-leg jeans and chunky sneakers from the wardrobe). This is stored in session["outfit_suggestion"]. The loop then calls create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"]).

**Step 4:**
<!-- Continue until the full interaction is complete -->
create_fit_card returns a short, caption-style description combining the item and the suggested pairing. This is stored in session["fit_card"]. With all three tools complete and no errors set, the loop ends and returns the full session.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees the matched listing (title, price, platform, condition), the outfit suggestion describing how to wear it with their existing wardrobe, and the shareable fit card caption — all three populated in the Gradio panels.

**On failure:**
If search_listings returns an empty list, the loop sets session["error"] to a message telling the user no matches were found and suggesting they loosen the price or drop the size filter, then returns immediately — suggest_outfit and create_fit_card are never called, and session["fit_card"] stays None.