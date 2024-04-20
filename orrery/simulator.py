import argparse
import csv
import logging
from collections import defaultdict, deque, namedtuple
from random import choice

LOG_FILE = 'log.info'

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s',
    level=logging.INFO,
    filename=LOG_FILE,
)


Passenger = namedtuple('Passenger', ['pid', 'dest'])


class Elevator:
    def __init__(self, elevator_id, max_passengers):
        self.id = elevator_id
        self.max_passengers = max_passengers
        self.current_floor = 1  # All elevators start at floor 1
        self.passengers = {}  # Maps passenger ID to destination floor
        self.board_time = {}  # Tracks when passengers boarded
        self.target_floors = []  # Scheduled floors

    def move(self):
        """Move towards closest floor in targets or idles w/o targets.

        Currently goes to relative closest target floor. This helps
        construct the shortest paths possible for direct travel time,
        but this does not guarantee the shortest waits possible.
        It currently does not account for reverse journey control.
        """
        if self.target_floors:
            next_floor = min(self.target_floors, key=lambda x: abs(x - self.current_floor))
            self.current_floor += 1 if self.current_floor < next_floor else -1

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
                return True
        return False

    def unload_passengers(self, current_time):
        """Unload passengers at destination floor if current floor."""
        to_remove = [pid for pid, floor in self.passengers.items() if floor == self.current_floor]
        if to_remove:
            self.target_floors.remove(self.current_floor)
            for pid in to_remove:
                board_time = self.board_time[pid]
                yield pid, board_time  # Return passenger ID and their boarding time
                del self.passengers[pid]
                del self.board_time[pid]


class Building:
    def __init__(self, num_floors, num_elevators, max_passengers_per_elevator, strategy_function):
        self.num_floors = num_floors
        self.strategy = strategy_function
        # [ ] TODO: evaluate changing ID to string
        # Just use index of number of elevators range to ID each elevator
        self.elevators = [Elevator(eid, max_passengers_per_elevator) for eid in range(num_elevators)]
        self.state_log = defaultdict()  # Tracks elevator states over time
        self.wait_times = {}  # Maps passenger ID to their wait time
        self.travel_times = {}  # Maps passenger ID to their travel time
        self.occupancy = defaultdict(list)  # Tracks passengers waiting on each floor

    def process_request(self, time, passenger_id, source_floor, dest_floor, strategy):
        """Assign requests chronologically according to chosen strategy.

        "Skate": Random choice, random available, nearest available only
        """
        # [ ] TODO: VERIFY THOROUGHLY
        self.wait_times[passenger_id] = time  # Store time request entered system
        elevator = self.strategy(self.elevators, passenger_id, source_floor, dest_floor)
        if elevator:
            if dest_floor not in elevator.target_floors:
                elevator.target_floors.append(dest_floor)
            return True
        if not elevator:
            return False

    def simulate_time_step(self, current_time):
        """Move every elevator, first unload passengers, then load passengers."""
        for elevator in self.elevators:
            elevator.move()
            # [ ] TODO: Assess whether must replace unload yield with list
            for pid, board_time in elevator.unload_passengers(current_time):
                self.travel_times[pid] = current_time - board_time  # Store travel time
                self.wait_times[pid] = board_time - self.wait_times[pid]  # Store wait time
            for passenger in self.occupancy[elevator.current_floor]:
                if elevator.load_passenger(passenger.pid, passenger.dest, current_time):
                    self.occupancy[elevator.current_floor].remove(passenger)
        self.log_elevator_states(current_time)

    def log_elevator_states(self, current_time):
        elevator_states = {e.eid: e.current_floor for e in self.elevators}
        self.state_log[current_time] = elevator_states

    def run_simulation(self, requests):
        """Process sorted requests by time (i.e., chronologically)."""
        requests = deque(requests)  # Requests are pre-sorted at load
        current_time = 0
        self.log_elevator_states(current_time)
        # dev note: prefer explicit requests length > 0 over truthiness
        while len(requests) > 0 or any(e.passengers for e in self.elevators):
            while requests and requests[0][0] == current_time:
                time, pid, source, dest = requests.popleft()
                self.occupancy[source].append(Passenger(pid, dest))  # Track waiting passengers per floor
                self.process_request(time, pid, source, dest)
            self.simulate_time_step(current_time)
            current_time += 1
        self.output_statistics()
        self.output_elevator_states_to_csv()  # Output state log to CSV at end of sim

    def output_statistics(self):
        # Calculate and print min, max, and mean wait and travel times
        min_wait = min(self.wait_times.values())
        max_wait = max(self.wait_times.values())
        mean_wait = sum(self.wait_times.values()) / len(self.wait_times)

        min_travel = min(self.travel_times.values())
        max_travel = max(self.travel_times.values())
        mean_travel = sum(self.travel_times.values()) / len(self.travel_times)

        print(f"Wait Times - Min: {min_wait}, Max: {max_wait}, Mean: {mean_wait:.2f}")
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


def load_requests_from_csv(self, filepath='requests.csv'):
    filepath
    with open(filepath, newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip single-row header
        return sorted([(int(row[0]), row[1], int(row[2]), int(row[3])) for row in reader], key=lambda x: x[0])


