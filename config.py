MIN_CITIES = 2
MAX_CITIES = 5
PROB_OPTIONAL_TASK = 0.5  

COMMON_FLIGHT_AIRLINES = [
    "AirDemo",
    "SkyTest",
    "FlyMock",
]

COMMON_HOTELS = [
    "HotelDemo",
    "StayTest",
    "InnMock",
]

COMMON_CITIES = [
    "Paris",
    "Tokyo",
    "New York",
    "Berlin",
    "Dubai",
]

# --- distribution ranges -----------------------------------------------------------
FLIGHT_PRICE_MEAN_RANGE = (200, 700)   # USD – used as μ when sampling prices
HOTEL_PRICE_MEAN_RANGE  = (80, 350)   # USD/night – used as μ when sampling prices
NIGHTS_MEAN_RANGE       = (3, 7)   # nights – used as μ when sampling nights

ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
ANTHROPIC_KEY = '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'

LOGGING_ENABLED = True