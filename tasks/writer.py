import json, os, sys
from datetime import date
from tools.web_search import AnthropicWebSearch

_ITINERARY_SCHEMA = """
Return **ONLY** valid JSON strictly matching this schema - no markdown, no extra keys!

{
  "city": "<city name>",
  "start_date": "<YYYY-MM-DD>",
  "end_date": "<YYYY-MM-DD>",
  "days": [
    {
      "date": "<YYYY-MM-DD>",
      "morning": "<14-word max description>",
      "afternoon": "<14-word max description>",
      "evening": "<14-word max description>"
    }
  ]
}
"""


def generate_itinerary(city: str, current_date: str, next_flight_date: str, output_path: str):
    searcher = AnthropicWebSearch()

    prompt = (
        f"You are an expert travel planner. Today is {current_date}; the traveller departs on {next_flight_date}.\n"
        f"Plan day-by-day activities **in {city}** for the dates in between.\n"
        f"Activities must not repeat. Use concise language.\n\n"
        f"{_ITINERARY_SCHEMA}"
    )

    try:
        raw = searcher.search(prompt, max_tokens=800)
    except Exception as e:
        raw = json.dumps({"error": str(e)})

    # Ensure we always log something JSON‑parseable
    try:
        obj = json.loads(raw.strip())
        line = json.dumps(obj, ensure_ascii=False)
    except Exception:
        line = json.dumps({"city": city, "start_date": current_date, "end_date": next_flight_date, "raw": raw})

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    generate_itinerary("Tokyo", date.today().isoformat(), "2025-07-04", "logs/itineraries.jsonl")
