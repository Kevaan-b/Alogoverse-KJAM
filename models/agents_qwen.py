from __future__ import annotations
import json, re, pathlib
from typing import List, Dict, Any, Optional
from models.orchestrator_base import AgentBase, ModelWrapper
import json


def _read_jsonl(path: str) -> List[dict]:
    p = pathlib.Path(path)
    if not p.exists():
        return []
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # tolerate junk lines
                continue
    return rows

def _first_json_obj(text: str) -> Optional[dict]:
    """Return the first top-level JSON object found in text, or None."""
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_str = False
    esc = False

    for i, ch in enumerate(text[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        return None
    return None

def _pick_top_k(items: List[dict], k: int = 6) -> List[dict]:
    return items[:k] if len(items) > k else items

class QwenFlightAgent(AgentBase):
    """
    Uses Qwen (via ModelWrapper) to choose a flight from a local JSONL db.
    Task payload expected from orchestrator:
        {"origin":"<city>","dest":"<city>"}
    Output dict (consumed by your pipeline):
        {"origin": ..., "dest": ..., "airline": ..., "date": ..., "price": ...}
    """
    def __init__(self, model: ModelWrapper, flights_path: str):
        super().__init__(model, "FlightAgent")
        self.flights_path = flights_path

    def _filter_candidates(self, origin: str, dest: str) -> List[dict]:
        rows = _read_jsonl(self.flights_path)
        out = [r for r in rows if r.get("origin") == origin and r.get("dest") == dest]
        # optional: sort by price (ascending) then earliest date
        def _key(r):
            return (r.get("price", 10**9), r.get("date", "9999-12-31"))
        out.sort(key=_key)
        return out

    def build_prompt(self, task: dict) -> str:
        origin = task.get("origin", "").strip()
        dest   = task.get("dest", "").strip()
        candidates = _pick_top_k(self._filter_candidates(origin, dest), k=8)

        # If nothing found, tell the model and ask it to return a null-ish object
        catalog = json.dumps(candidates, ensure_ascii=False)

        schema = """Return ONE JSON object only (no prose) with keys:
{
  "origin": "<origin city>",
  "dest": "<dest city>",
  "airline": "<airline>",
  "date": "<YYYY-MM-DD>",
  "price": <integer USD>
}"""

        prompt = f"""You are FlightAgent. Choose ONE best flight for the requested leg.

LEG:
- origin: {origin}
- dest: {dest}

CANDIDATE_DB (JSON array, top filtered rows):
{catalog}

Selection criteria (in order): 1) lowest price; 2) earlier date; 3) otherwise any.
If CANDIDATE_DB is empty, return:
{{"origin":"{origin}","dest":"{dest}","airline":"","date":"","price":0}}

Output format (STRICT):
- {schema}
- Output a single JSON object, no markdown, no commentary, no extra text."""

        return prompt

    def parse_response(self, response: str, task: dict) -> dict:
        obj = _first_json_obj(response) or {}
        # Basic sanitation / fill-ins
        obj.setdefault("origin", task.get("origin", ""))
        obj.setdefault("dest", task.get("dest", ""))
        obj.setdefault("airline", "")
        obj.setdefault("date", "")
        obj.setdefault("price", 0)
        return obj


class QwenHotelAgent(AgentBase):
    """
    Uses Qwen (via ModelWrapper) to choose a hotel from a local JSONL db.
    Task payload expected:
        {"city":"<city>","nights":<int>}
    Output dict:
        {"city": ..., "hotel": ..., "check_in": ..., "nights": ..., "price_per_night": ...}
    """
    def __init__(self, model: ModelWrapper, hotels_path: str):
        super().__init__(model, "HotelAgent")
        self.hotels_path = hotels_path

    def _filter_candidates(self, city: str) -> List[dict]:
        rows = _read_jsonl(self.hotels_path)
        out = [r for r in rows if r.get("city") == city]
        # sort by price_per_night ascending then earliest check_in
        def _key(r):
            return (r.get("price_per_night", 10**9), r.get("check_in", "9999-12-31"))
        out.sort(key=_key)
        return out

    def build_prompt(self, task: dict) -> str:
        city   = task.get("city", "").strip()
        nights = int(task.get("nights", 1) or 1)
        candidates = _pick_top_k(self._filter_candidates(city), k=8)

        catalog = json.dumps(candidates, ensure_ascii=False)

        schema = """Return ONE JSON object only (no prose) with keys:
{
  "city": "<city>",
  "hotel": "<hotel name>",
  "check_in": "<YYYY-MM-DD>",
  "nights": <integer>,
  "price_per_night": <integer USD>
}"""

        prompt = f"""You are HotelAgent. Choose ONE best hotel in the arrival city.

ARRIVAL:
- city: {city}
- requested_nights: {nights}

CANDIDATE_DB (JSON array, top filtered rows):
{catalog}

Selection criteria: prefer lowest price_per_night; if tie, earliest check_in.
If CANDIDATE_DB is empty, return:
{{"city":"{city}","hotel":"","check_in":"","nights":{nights},"price_per_night":0}}

Output format (STRICT):
- {schema}
- Output a single JSON object, no markdown, no commentary, no extra text.
- Always set "nights" to {nights} in the response."""

        return prompt

    def parse_response(self, response: str, task: dict) -> dict:
        obj = _first_json_obj(response) or {}
        obj.setdefault("city", task.get("city", ""))
        obj.setdefault("hotel", "")
        obj.setdefault("check_in", "")
        # enforce nights from task
        obj["nights"] = int(task.get("nights", obj.get("nights", 1) or 1))
        obj.setdefault("price_per_night", 0)
        return obj
