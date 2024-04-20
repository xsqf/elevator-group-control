import argparse
import csv
import logging
from collections import defaultdict, deque, namedtuple
from itertools import filterfalse
from random import choice

LOG_FILE = "log.info"

logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s",
    level=logging.INFO,
    filename=LOG_FILE,
)


Passenger = namedtuple("Passenger", ["pid", "dest"])


class Elevator:
    def __init__(self, elevator_id, max_passengers):
        self.id = elevator_id
        self.max_passengers = max_passengers
        self.current_floor = 1  # All elevators start at floor 1
        self.passengers = {}  # Maps passenger ID to destination floor
        self.board_time = {}  # Tracks when passengers boarded
        self.target_floors = []  # Scheduled floors
        self.direction = 0  # 0 for idle, 1 for up, -1 for down

    def move(self):
        """Move towards closest floor in targets or idles w/o targets.

        Currently goes to relative closest target floor. This helps
        construct the shortest paths possible for direct travel time,
        but this does not guarantee the shortest waits possible.
        It currently does not account for reverse journey control.
        """
        if self.target_floors:
            floors_elsewhere = list(
                filterfalse(lambda x: x == self.current_floor, self.target_floors)
            )
            next_floor = min(
                floors_elsewhere, key=lambda x: abs(x - self.current_floor)
            )
            if self.current_floor < next_floor:
                self.direction = 1
            elif self.current_floor > next_floor:
                self.direction = -1
            self.current_floor += self.direction
        else:
            self.direction = 0

    def load_passenger(self, passenger_id, dest_floor, current_time):
        """Load waiting passenger if current occupied capacity allows.

        This is a relaxation of assumptions in favor of in-built capacity
        maximization. However, this is quirky and could lead to system
        saturation. Optimization opportunities exist and further
        benchmarking is needed to assess eliminating this relaxation.
        """
        if len(self.passengers) < self.max_passengers:
            if dest_floor in self.target_floors:
                self.passengers[passenger_id] = dest_floor  # Passenger boards elevator
                self.board_time[passenger_id] = current_time  # Log boarding time
                (
                    self.target_floors.remove(self.current_floor)
                    if self.current_floor in self.target_floors
                    else None
                )
                return True
        return False

    def unload_passengers(self, current_time):
        """Unload passengers at destination floor if current floor."""
        to_remove = [
            pid for pid, floor in self.passengers.items() if floor == self.current_floor
        ]
        if to_remove:
            (
                self.target_floors.remove(self.current_floor)
                if self.current_floor in self.target_floors
                else None
            )
            passengers_unloaded = {pid: self.board_time[pid] for pid in to_remove}
            for pid in to_remove:
                del self.passengers[pid]
                del self.board_time[pid]
            return passengers_unloaded
        return False


class Building:
    def __init__(self, num_floors, num_elevators, max_passengers_per_elevator, strategy_function):
        self.num_floors = num_floors
        self.strategy = strategy_function
        # Just use index of number of elevators range to ID each elevator
        self.elevators = [Elevator(i, max_passengers_per_elevator) for i in range(1, num_elevators + 1)]
        self.state_log = defaultdict()  # Tracks elevator states over time
        self.wait_times = {}  # Maps passenger ID to their wait time
        self.travel_times = {}  # Maps passenger ID to their travel time
        self.occupancy = defaultdict(list)  # Tracks passengers waiting on each floor

    def process_request(self, time, passenger_id, source_floor, dest_floor):
        """Assign requests chronologically according to chosen strategy.

        "Skate": Random choice, random available, nearest available only
        """
        self.wait_times[passenger_id] = time  # Store time request entered system
        elevator = self.strategy(self.elevators, passenger_id, source_floor, dest_floor)
        if elevator:
            elevator.target_floors.extend([source_floor, dest_floor])
            return True
        if not elevator:
            return False

    def simulate_time_step(self, current_time):
        """First unload any passengers, then load passengers, then move."""
        self.log_elevator_states(current_time)
        for elevator in self.elevators:
            unloaded_passengers = elevator.unload_passengers(current_time)
            if unloaded_passengers:
                for pid, board_time in unloaded_passengers.items():
                    self.travel_times[pid] = current_time - board_time  # Store travel time
                    self.wait_times[pid] = board_time - self.wait_times[pid]  # Store wait time
            for passenger in self.occupancy[elevator.current_floor]:
                if elevator.load_passenger(passenger.pid, passenger.dest, current_time):
                    self.occupancy[elevator.current_floor].remove(passenger)
            elevator.move()

    def log_elevator_states(self, current_time):
        elevator_states = {e.id: e.current_floor for e in self.elevators}
        self.state_log[current_time] = elevator_states

    def run_simulation(self, requests):
        """Process sorted requests by time (i.e., chronologically)."""
        requests = deque(requests)  # Requests are pre-sorted at load
        current_time = 0
        self.log_elevator_states(current_time)
        # dev note: prefer explicit requests length > 0 over truthiness
        # So long as there are requests or passengers in elevators or on floors:
        while len(requests) > 0 or any(e.passengers for e in self.elevators) or any(self.occupancy.values()):
            while requests and requests[0][0] == current_time:
                time, pid, source, dest = requests.popleft()
                pending_request = requests.popleft()
                time, pid, source, dest = pending_request
                self.occupancy[source].append(Passenger(pid, dest))  # Track waiting passengers per floor
                self.process_request(time, pid, source, dest)
            self.simulate_time_step(current_time)
            current_time += 1
        self.output_statistics()

    def output_statistics(self):
        """Calculate and print min, max, and mean wait and travel times."""
        print(f"Total passengers served: {len(self.wait_times)}")

        min_wait = min(self.wait_times.values())
        max_wait = max(self.wait_times.values())
        mean_wait = sum(self.wait_times.values()) / len(self.wait_times)

        print(f"Wait Times - Min: {min_wait}, Max: {max_wait}, Mean: {mean_wait:.2f}")

        min_travel = min(self.travel_times.values())
        max_travel = max(self.travel_times.values())
        mean_travel = sum(self.travel_times.values()) / len(self.travel_times)

        print(f"Travel Times - Min: {min_travel}, Max: {max_travel}, Mean: {mean_travel:.2f}")

    def output_elevator_states_to_csv(self, filename='elevator_states.csv'):
        """Output the recorded states of all elevators to a CSV file."""
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['time', 'elevator_id', 'current_floor'])
            for time, states in sorted(self.state_log.items()):
                for elevator_id, floor in states.items():
                    writer.writerow([time, elevator_id, floor])


def random_choice(elevators, passenger_id, source_floor, dest_floor):
    return choice(elevators)


def nearest_available(elevators, passenger_id, source_floor, dest_floor):
    available = sorted(elevators, key=lambda e: len(e.passengers))
    nearest_available_elevator = min(available, key=lambda e: abs(e.current_floor - source_floor))
    return nearest_available_elevator


def random_available(elevators, passenger_id, source_floor, dest_floor):
    available = sorted(elevators, key=lambda e: len(e.passengers))
    return choice(available)


def load_requests_from_csv(filepath):
    with open(filepath, newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip single row header
        return sorted([(int(row[0]), row[1], int(row[2]), int(row[3])) for row in reader], key=lambda x: x[0])


def main():
    parser = argparse.ArgumentParser(
        prog='orrery',
        description="Run Orrery elevator simulation.",
    )
    parser.add_argument("-f", "--floors", type=int, help="Number of floors in the building")
    parser.add_argument("-e", "--elevators", type=int, help="Number of elevators in the building")
    parser.add_argument("-c", "--capacity", type=int, help="Maximum passenger capacity of each elevator")
    parser.add_argument(
        "-s",
        "--strategy",
        type=str,
        choices=[
            'random',
            'available',
            'nearest',
        ],
        default='nearest',
        help="Elevator assignment strategy"
    )
    parser.add_argument("-r", "--requests", type=str, help="Path to requests CSV")
    args = parser.parse_args()
    logging.debug(f"Arguments parsed: {args}")

    strategy_mapping = {
        'random': random_choice,
        'available': random_available,
        'nearest': nearest_available,
    }

    strategy_func = strategy_mapping[args.strategy]

    building = Building(args.floors, args.elevators, args.capacity, strategy_func)

    requests = load_requests_from_csv(args.requests)
    building.run_simulation(requests)
    building.output_elevator_states_to_csv(f'elevator_states__{args.strategy}__{args.requests}')


if __name__ == "__main__":
    main()
