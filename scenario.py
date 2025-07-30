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
    trips = " → ".join(scenario["cities"])

    lines: list[str] = [
        "You are the orchestrator LLM for TripBenchmark.",
        f"Route: {trips}.",
        "",
        "Sub-agents:",
        "• FlightAgent - pick a flight for each leg (origin → dest).",
        "• HotelAgent - reserve accommodation when requested.",
        "• PlannerAgent - craft daily activity plans.",
        "",
        "Rules:",
        "1. Adjacent cities are always different (already enforced).",
        "2. When revisiting a city, do **not** repeat activities from earlier visits.",
        "",
        "Tasks (one per leg):",
    ]

    for idx, city in enumerate(scenario["cities"]):
        lines.append(f"- Leg {idx+1}: arrive in {city}")
        if scenario["book_hotels"][idx]:
            lines.append("  • Book an appropriate hotel")
        lines.append(f"  • Plan {scenario['plan_days'][idx]} day(s) of activities")

    example = {
        "flights": [
            {"origin": "Dubai", "dest": "Tokyo", "airline": "AirDemo", "date": "2025-10-01"}
        ],
        "hotels": [
            {"city": "Tokyo", "hotel": "HotelDemo", "check_in": "2025-10-01", "nights": 3}
        ],
        "day_plans": [
            {"city": "Tokyo", "day": "2025-10-02", "morning": "Visit Senso‑ji", "afternoon": "Sushi class", "evening": "Skytree at sunset"}
        ],
    }

    lines.extend([
        "",
        "Return **ONLY** a JSON object with keys *flights*, *hotels*, *day_plans*.",
        json.dumps(example, indent=2),
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    scen = sample_scenario()
    print(json.dumps(scen, indent=2))
    print("\n" + "="*80 + "\n")
    print(build_orchestrator_prompt(scen))