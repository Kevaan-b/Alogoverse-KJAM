import json, random, datetime, pathlib
from config import (
    COMMON_HOTELS as HOTELS,
    COMMON_CITIES as CITIES,
    HOTEL_PRICE_MEAN_RANGE,
    NIGHTS_MEAN_RANGE,
)


def _trunc_gauss(mu: float, sigma: float, lower: float, upper: float):
    while True:
        x = random.gauss(mu, sigma)
        if lower <= x <= upper:
            return x

def _rand_checkin() -> str:
    mean, std = random.randint(10, 60), random.randint(3, 15)
    offset = max(1, int(_trunc_gauss(mean, std, 1, 365)))
    return (datetime.date.today() + datetime.timedelta(days=offset)).isoformat()

def _rand_nights() -> int:
    mu = random.randint(*NIGHTS_MEAN_RANGE)
    sigma = mu * 0.4
    return max(1, int(_trunc_gauss(mu, sigma, 1, 30)))

def _rand_price_per_night() -> int:
    mu = random.randint(*HOTEL_PRICE_MEAN_RANGE)
    sigma = mu * 0.25
    return int(_trunc_gauss(mu, sigma, 30, 1200))


def generate(path: str, num: int = 100):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for _ in range(num):
            city = random.choice(CITIES)
            rec = {
                "hotel": random.choice(HOTELS),
                "city": city,
                "check_in": _rand_checkin(),
                "nights": _rand_nights(),
                "price_per_night": _rand_price_per_night(),
            }
            f.write(json.dumps(rec) + "\n")


def sample(path: str, city: str):
    with open(path, encoding="utf-8") as f:
        matches = [json.loads(line) for line in f if f'"city": "{city}"' in line]
    return random.choice(matches) if matches else {}

