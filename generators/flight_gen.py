import json, random, datetime, pathlib
from typing import List
from config import (
    COMMON_FLIGHT_AIRLINES as AIRLINES,
    COMMON_CITIES          as CITIES,
    FLIGHT_PRICE_MEAN_RANGE,
)


# --- helpers -----------------------------------------------------------------------

def _trunc_gauss(mu: float, sigma: float, lower: float, upper: float) -> float:
    """Sample from Normal distribution truncated to [lower, upper]."""
    while True:
        x = random.gauss(mu, sigma)
        if lower <= x <= upper:
            return x

def _rand_date(mean_offset: int | None = None, std: int | None = None) -> str:
    if mean_offset is None:
        mean_offset = random.randint(30, 120)
    if std is None:
        std = random.randint(5, 20)
    offset = max(1, int(_trunc_gauss(mean_offset, std, 1, 365)))
    return (datetime.date.today() + datetime.timedelta(days=offset)).isoformat()

def _rand_price() -> int:
    mu = random.randint(*FLIGHT_PRICE_MEAN_RANGE)
    sigma = mu * 0.2
    return int(_trunc_gauss(mu, sigma, 50, 2000))


# --- public API --------------------------------------------------------------------

def generate(path: str, num: int = 100):
    """Create *num* flight records at *path* (JSON‑lines)."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for _ in range(num):
            origin, dest = random.sample(CITIES, 2)  # guarantees origin != dest
            rec = {
                "airline": random.choice(AIRLINES),
                "origin": origin,
                "dest": dest,
                "date": _rand_date(),
                "price": _rand_price(),
            }
            f.write(json.dumps(rec) + "\n")


def sample(path: str, origin: str, dest: str):
    """Return one record for *origin* → *dest* (or an empty dict)."""
    with open(path, encoding="utf-8") as f:
        matches = [
            json.loads(line)
            for line in f
            if f'"origin": "{origin}"' in line and f'"dest": "{dest}"' in line
        ]
    return random.choice(matches) if matches else {}

