import random

class Flight:

    def __init__ (self, flight_id: int, arrival: int, departure: int, passengers: int):
        self.flight_id = flight_id
        self.arrival = arrival
        self.departure = departure
        self.passengers = passengers

    def to_dict(self):
        return{
            "flight_id": self.flight_id,
            "arrival": self.arrival,
            "departure": self.departure,
            "passengers": self.passengers
        }
    


def generate_flight_data(num_flights: int = 20, num_gates: int = 5, seed: int = 67) -> list[dict]:

    random.seed(seed)
    flights = []

    for i in range(num_flights):
        arrival = random.randint(0, 1380)
        duration = random.randint(30, 180)
        departure = arrival + duration
        passengers = random.randint(20, 300)

        flights.append(Flight(i, arrival, departure, passengers).to_dict())

    return flights


if __name__ == "__main__":

    flights = generate_flight_data(num_flights=20, num_gates=5, seed=67)
    for flight in flights:
        hrs_arr = flight['arrival'] // 60
        mins_arr = flight['arrival'] % 60
        hrs_dep = flight['departure'] // 60
        mins_dep = flight['departure'] % 60
        print(f"Flight {flight['flight_id']}: Arrival = {hrs_arr:02d}:{mins_arr:02d}, Departure = {hrs_dep:02d}:{mins_dep:02d}, Passengers = {flight['passengers']}")

        