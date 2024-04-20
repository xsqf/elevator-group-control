import argparse
import csv
import logging
from itertools import filterfalse
from logging.handlers import RotatingFileHandler
from collections import defaultdict, deque, namedtuple
from random import choice

LOG_FILE = 'log.info'

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s',
    level=logging.INFO,
    filename=LOG_FILE,
)

logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # Step 2: Set the logger to capture all levels of messages
file_handler = RotatingFileHandler('log.info', maxBytes=1024*1024*5, backupCount=5)  # 5 MB file size
console_handler = logging.StreamHandler()  # Default is sys.stdout
formatter = logging.Formatter('%(asctime)s : %(name)s : %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# logging.debug('This is a debug message')
# logging.info('This is an informational message')
# logging.warning('This is a warning message')
# logging.error('This is an error message')
# logging.critical('This is a critical message')


Passenger = namedtuple('Passenger', ['pid', 'dest'])


class Elevator:
    def __init__(self, elevator_id, max_passengers):
        self.id = elevator_id
        self.max_passengers = max_passengers
        self.current_floor = 1  # All elevators start at floor 1
        self.passengers = {}  # Maps passenger ID to destination floor
        self.board_time = {}  # Tracks when passengers boarded
        self.target_floors = []  # Scheduled floors
        self.direction = 0  # 0 for idle, 1 for up, -1 for down
        logging.debug(f"Elevator {self.id} initialized at floor {self.current_floor} with capacity {self.max_passengers}")

    def move(self):
        """Move towards closest floor in targets or idles w/o targets.

        Currently goes to relative closest target floor. This helps
        construct the shortest paths possible for direct travel time,
        but this does not guarantee the shortest waits possible.
        It currently does not account for reverse journey control.
        """
        logging.debug(f"Elevator {self.id} is at floor {self.current_floor}")
        if self.target_floors:
            floors_elsewhere = list(filterfalse(lambda x: x == self.current_floor, self.target_floors))
            next_floor = min(floors_elsewhere, key=lambda x: abs(x - self.current_floor))
            logging.debug(f"Next floor for Elevator {self.id} is {next_floor}")
            if self.current_floor < next_floor:
                self.direction = 1
            elif self.current_floor > next_floor:
                self.direction = -1
            self.current_floor += self.direction
            logging.debug(f"Elevator {self.id} moves to floor {self.current_floor}")
        else:
            self.direction = 0
            logging.debug(f"Elevator {self.id} idles at floor {self.current_floor}")

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
                logging.debug(f"Passenger {passenger_id} boards elevator {self.id} at floor {self.current_floor} going to floor {dest_floor}")
                self.target_floors.remove(self.current_floor) if self.current_floor in self.target_floors else None
                return True
        logging.debug(f"Elevator {self.id} at capacity, cannot load passenger {passenger_id}")
        return False

    def unload_passengers(self, current_time):
        """Unload passengers at destination floor if current floor."""
        to_remove = [pid for pid, floor in self.passengers.items() if floor == self.current_floor]
        if to_remove:
            logging.debug(f"Elevator {self.id} at floor {self.current_floor} unloading passengers {to_remove}")
            self.target_floors.remove(self.current_floor)
            if self.current_floor not in self.target_floors:
                logging.debug(f"Current floor {self.current_floor} successfully removed from Elevator {self.id} target floors.")
            passengers_unloaded = {pid: self.board_time[pid] for pid in to_remove}
            for pid in to_remove:
                del self.passengers[pid]
                del self.board_time[pid]
                logging.debug(f"Passenger {pid} unloads from elevator {self.id} at floor {self.current_floor}.")
            return passengers_unloaded
        return False


class Building:
    def __init__(self, num_floors, num_elevators, max_passengers_per_elevator, strategy_function):
        self.num_floors = num_floors
        self.strategy = strategy_function
        # [ ] TODO: evaluate changing ID to string
        # Just use index of number of elevators range to ID each elevator
        self.elevators = [Elevator(i, max_passengers_per_elevator) for i in range(1, num_elevators + 1)]
        self.state_log = defaultdict()  # Tracks elevator states over time
        self.wait_times = {}  # Maps passenger ID to their wait time
        self.travel_times = {}  # Maps passenger ID to their travel time
        self.occupancy = defaultdict(list)  # Tracks passengers waiting on each floor
        logging.debug(f"Building initialized with {num_floors} floors and {num_elevators} elevators.")

    def process_request(self, time, passenger_id, source_floor, dest_floor):
        """Assign requests chronologically according to chosen strategy.

        "Skate": Random choice, random available, nearest available only
        """
        logging.debug(f"Processing request at time {time} for passenger {passenger_id} from floor {source_floor} to {dest_floor}.")
        # [ ] TODO: VERIFY THOROUGHLY
        self.wait_times[passenger_id] = time  # Store time request entered system
        logging.debug(f"Stored Passenger {passenger_id} wait time as {self.wait_times[passenger_id]}.")
        elevator = self.strategy(self.elevators, passenger_id, source_floor, dest_floor)
        if elevator:
            logging.debug(f"Elevator {elevator.id} assigned to passenger {passenger_id}")
            elevator.target_floors.extend([source_floor, dest_floor])
            logging.debug(f"Source {source_floor} and dest {dest_floor} added to Elevator {elevator.id} target floors: {elevator.target_floors}")
            return True
        if not elevator:
            logging.debug(f"No elevator available for passenger {passenger_id} at time {time}")
            return False

    def simulate_time_step(self, current_time):
        """First unload any passengers, then load passengers, then move."""
        logging.debug(f"Simulating time step at time {current_time}")
        self.log_elevator_states(current_time)
        logging.debug(f"State log for time {current_time}: {self.state_log[current_time]}")
        for elevator in self.elevators:
            unloaded_passengers = elevator.unload_passengers(current_time)
            if unloaded_passengers:
                logging.debug(f"Unloading passengers from Elevator {elevator.id} at floor {elevator.current_floor}...")
                for pid, board_time in unloaded_passengers.items():
                    logging.debug(f"Unloading Passenger {pid} from Elevator {elevator.id} at floor {elevator.current_floor}.")
                    self.travel_times[pid] = current_time - board_time  # Store travel time
                    self.wait_times[pid] = board_time - self.wait_times[pid]  # Store wait time
                    logging.debug(f"Unloaded Passenger {pid}: travel time {self.travel_times[pid]} and wait time {self.wait_times[pid]} from board time {board_time}.")
                logging.debug(f"Completed unloading passengers from Elevator {elevator.id} at floor {elevator.current_floor}.")
            for passenger in self.occupancy[elevator.current_floor]:
                logging.debug(f"Attempting to load Passenger {passenger.pid} at floor {elevator.current_floor} into Elevator {elevator.id}.")
                if elevator.load_passenger(passenger.pid, passenger.dest, current_time):
                    logging.debug(f"Passenger {passenger.pid} loaded into Elevator {elevator.id} at floor {elevator.current_floor}.")
                    self.occupancy[elevator.current_floor].remove(passenger)
                    logging.debug(f"Removed Passenger {passenger.pid} from floor {elevator.current_floor} occupancy list.")
            logging.debug(f"Completed deboarding and boarding of Elevator {elevator.id} at floor {elevator.current_floor} at time {current_time}.")
            elevator.move()

    def log_elevator_states(self, current_time):
        elevator_states = {e.id: e.current_floor for e in self.elevators}
        self.state_log[current_time] = elevator_states
        logging.debug(f"Logged elevator states at time {current_time}.")

    def run_simulation(self, requests):
        """Process sorted requests by time (i.e., chronologically)."""
        requests = deque(requests)  # Requests are pre-sorted at load
        current_time = 0
        self.log_elevator_states(current_time)
        # dev note: prefer explicit requests length > 0 over truthiness
        # So long as there are requests or passengers in elevators or on floors:
        while len(requests) > 0 or any(e.passengers for e in self.elevators) or any(self.occupancy.values()):
            if requests:
                logging.debug(f"DEBUG ONLY: Requests preview: {requests}")
            elif any(e.passengers for e in self.elevators):
                logging.debug(f"Elevators still fulfilling passenger dropoffs: {[e.passengers.keys() for e in self.elevators]}")
            elif any(self.occupancy.values()):
                logging.debug(f"Passengers still waiting on floors: {self.occupancy}")
            while requests and requests[0][0] == current_time:
                logging.debug(f"Processing outstanding requests at time {current_time}.")
                pending_request = requests.popleft()
                logging.debug(f"Pending request: {pending_request}")
                time, pid, source, dest = pending_request
                self.occupancy[source].append(Passenger(pid, dest))  # Track waiting passengers per floor
                logging.debug(f"Passenger {pid} added to floor {source} occupancy list: {self.occupancy[source]}")
                self.process_request(time, pid, source, dest)
                logging.debug(f"Processed request for Passenger {pid} at time {time}.")
            self.simulate_time_step(current_time)
            logging.debug(f"Completed simulating time step {current_time}.")
            current_time += 1
            logging.debug(f"Time advanced to {current_time}.")
            if current_time > 100:
                logging.debug(f"DEBUG ONLY: Breaking simulation at time {current_time}.")
                break  # dev note: limit simulation to 100 time steps
        self.output_statistics()
        logging.debug("Simulation complete.")

    def output_statistics(self):
        """Calculate and logging.debug min, max, and mean wait and travel times."""
        logging.debug("Outputting simulation statistics.")
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
            logging.debug(f"Outputting elevator states to {filename}.")
            writer = csv.writer(file)
            writer.writerow(['time', 'elevator_id', 'current_floor'])
            for time, states in sorted(self.state_log.items()):
                for elevator_id, floor in states.items():
                    writer.writerow([time, elevator_id, floor])
        logging.debug(f"Wrote elevator states successfully.")


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
        logging.debug(f"Loading requests from {filepath}.")
        reader = csv.reader(file)
        header_row = next(reader)  # Skip (and show) single row header
        logging.debug(f"Header row: {header_row}")
        logging.debug(f"Skipped header row.")
        return sorted([(int(row[0]), row[1], int(row[2]), int(row[3])) for row in reader], key=lambda x: x[0])
        logging.debug(f"Loaded sorted requests successfully.")

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
