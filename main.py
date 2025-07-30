import random
from generators.flight_gen import generate as generate_flights, sample as sample_flight
from generators.hotel_gen import generate as generate_hotels, sample as sample_hotel
from scenario import sample_scenario, build_orchestrator_prompt


def main():
    flight_path = "data/flights.jsonl"
    hotel_path = "data/hotels.jsonl"

    generate_flights(flight_path, num=200)
    generate_hotels(hotel_path, num=200)

    origin, dest = random.sample(["Paris", "Tokyo", "New York", "Berlin", "Dubai"], 2)
    flight = sample_flight(flight_path, origin, dest)
    hotel = sample_hotel(hotel_path, dest)

    print("Random flight:", flight or "<none found>")
    print("Random hotel:", hotel or "<none found>")

    scen = sample_scenario()
    print("\nScenario prompt:\n")
    print(build_orchestrator_prompt(scen))


if __name__ == "__main__":
    main()