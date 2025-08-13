import random, json
from config import MIN_CITIES, MAX_CITIES, COMMON_CITIES, PROB_OPTIONAL_TASK

__all__ = ["sample_scenario", "build_orchestrator_prompt"]


def _unique_cities(n: int):
    cities = []
    while len(cities) < n:
        c = random.choice(COMMON_CITIES)
        if not cities or c != cities[-1]:
            cities.append(c)
    return cities


# -----------------------------------------------------------------------------
# Public helpers
# -----------------------------------------------------------------------------

def sample_scenario():
    depth = random.randint(MIN_CITIES, MAX_CITIES)
    width = 1 + int(random.random() < PROB_OPTIONAL_TASK)  # 1 or 2

    cities = _unique_cities(depth)
    book_hotels = [random.random() < 0.8 for _ in cities]
    plan_days = [random.randint(1, 3) for _ in cities]

    return {
        "depth": depth,
        "width": width,
        "cities": cities,
        "book_hotels": book_hotels,
        "plan_days": plan_days,
    }


def build_orchestrator_prompt(scenario: dict) -> str:
    cities       = scenario["cities"]
    book_hotels  = scenario["book_hotels"]
    plan_days    = scenario["plan_days"]

    # Build a leg table so the model has zero ambiguity
    legs = []
    for i in range(len(cities) - 1):
        origin = cities[i]
        dest   = cities[i + 1]
        legs.append({
            "leg": i + 1,
            "origin": origin,
            "dest": dest,
            "book_hotel": bool(book_hotels[i + 1]),  # hotel/plan apply to the arrival city
            "days_to_plan": int(plan_days[i + 1]),
        })

    route_str = " → ".join(cities)

    lines = [
        # === ROLE & GOAL ====================================================
        "You are the Orchestrator LLM for TripBenchmark.",
        f"ROUTE: {route_str}",
        "",
        # === WHAT AGENTS EXIST ==============================================
        "Available agents (use these role names exactly):",
        "- FlightAgent  – choose a flight for an origin→dest leg.",
        "- HotelAgent   – book accommodation at the arrival city.",
        "- PlannerAgent – create day-by-day activities at the arrival city.",
        "",
        # === HARD RULES THE PARSER RELIES ON ================================
        "OUTPUT FORMAT (strict):",
        "• Emit ONLY lines in this exact form, one task per line:",
        '[TASK] <AgentRole> | {"key":"value","key2":"value2"}',
        "• No Markdown, no prose, no blank lines, no extra spaces around [TASK].",
        "• JSON must be single-line, double-quoted keys/strings, no trailing commas.",
        "• AgentRole ∈ {FlightAgent, HotelAgent, PlannerAgent}.",
        "",
        # === WHAT TO EMIT FOR EACH LEG ======================================
        "For each consecutive pair of cities (i.e., each leg origin→dest):",
        "1) Emit a FlightAgent task with payload:",
        '   {"origin":"<origin>","dest":"<dest>"}',
        "2) If book_hotel is true for the arrival city, emit a HotelAgent task:",
        '   {"city":"<dest>","nights":<integer_nights>}',
        "   - Set nights to the days_to_plan for that arrival city (minimum 1).",
        "3) Always emit a PlannerAgent task for the arrival city:",
        '   {"city":"<dest>","days":<days_to_plan>}',
        "",
        # === DON’TS =========================================================
        "Do NOT invent cities or legs. Do NOT output keys other than shown.",
        "Do NOT include dates here; sub-agents will handle specifics later.",
        "",
        # === LEG TABLE THE MODEL SHOULD FOLLOW ==============================
        "LEG TABLE (follow exactly):"
    ]

    for leg in legs:
        lines.append(
            f'- Leg {leg["leg"]}: {leg["origin"]} → {leg["dest"]} | '
            f'book_hotel={str(leg["book_hotel"]).lower()} | days_to_plan={leg["days_to_plan"]}'
        )

    # === MINI EXAMPLE (conforms to your regex) ==============================
    lines += [
        "",
        "Example (format only; values are illustrative):",
        '[TASK] FlightAgent | {"origin":"Paris","dest":"Tokyo"}',
        '[TASK] HotelAgent | {"city":"Tokyo","nights":2}',
        '[TASK] PlannerAgent | {"city":"Tokyo","days":2}',
        "",
        # === FINAL INSTRUCTION ==============================================
        "Now output the tasks for the LEG TABLE above, and nothing else."
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    import models.qwen
    scen = sample_scenario()
    print(json.dumps(scen, indent=2))
    print("\n" + "="*80 + "\n")
    print(build_orchestrator_prompt(scen))
    model = models.qwen.QwenLocal()
    print(model.generate(build_orchestrator_prompt(scen)))
