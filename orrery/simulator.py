import logging
import math
from collections import namedtuple
from random import expovariate, sample, seed

### DEV ###
# [ ] TODO: parameterize
# hardcoded globals for dev and testing

LOG_FILE = 'log.info'

ELEVATORS = 3
MAX_PASSENGERS = 4
FLOORS = 10


logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s',
    level=logging.INFO,
    filename=LOG_FILE,
)

# [ ] TODO: docstrings
# [ ] TODO: unit tests

###########


class Elevator:
    def __init__(self, elevator_id, max_passengers):
        self.id = elevator_id
        self.max_passengers = max_passengers
        self.current_floor = 1  # All elevators start at floor 1
        self.passengers = {}  # Tracks passengers to their destination floors
        self.target_floors = []  # Scheduled floors

    def move(self):
        """Move towards the next scheduled floor."""
        if self.target_floors:
            next_floor = min(self.target_floors, key=lambda x: abs(x - self.current_floor))
            self.current_floor += 1 if self.current_floor < next_floor else -1

    def load_passenger(self, passenger_id, target_floor):
        """Load passenger if current occupied capacity allows."""
        if len(self.passengers) < self.max_passengers:
            self.passengers[passenger_id] = target_floor
            if target_floor not in self.target_floors:
                self.target_floors.append(target_floor)
            return True
        return False

    def unload_passengers(self):
        """Unload passengers at destination floor if current floor."""
        to_remove = [pid for pid, floor in self.passengers.items() if floor == self.current_floor]
        for pid in to_remove:
            del self.passengers[pid]
            self.target_floors.remove(self.current_floor)


class Building:
    def __init__(self, num_floors, num_elevators, max_passengers_per_elevator):
        self.num_floors = num_floors
        # [ ] TODO: evaluate changing ID to string
        # Just use index of number of elevators range to ID each elevator
        self.elevators = [Elevator(i, max_passengers_per_elevator) for i in range(num_elevators)]

    def process_request(self, time, passenger_id, source_floor, target_floor):
        """Assign the first available elevator.

        Skate: simple round-robin or nearest available strategy
        """
        # [ ] TODO: VERIFY THIS DOES WHAT I WANT
        # Return available elevators in order of least occupied.
        available_elevators = sorted(self.elevators, key=lambda e: len(e.passengers))
        for elevator in available_elevators:
            # If elevator can accommodate passenger, assign to them.
            if elevator.load_passenger(passenger_id, target_floor):
                return True
        return False

    def simulate_time_step(self):
        """Move every elevator to next floor then unload passengers."""
        for elevator in self.elevators:
            elevator.move()
            elevator.unload_passengers()
        self.log_elevator_states()

    def log_elevator_states(self):
        state = {e.id: e.current_floor for e in self.elevators}
        self.logs.append(state)

    def run_simulation(self, requests):
        """Process sorted requests by time (i.e., chronologically)."""
        # NOTE CHANGE: Went back to original CSV header since demo.
        # [ ] MUST TODO: revert to original CSV header!!
        requests = deque(requests)  # Requests are pre-sorted at load
        current_time = 0
        # dev note: prefer explicit requests length > 0 over truthiness
        while len(requests) > 0 or any(e.passengers for e in self.elevators):
            while requests and requests[0][0] == current_time:
                time, pid, source, dest = requests.popleft()
                self.process_request(time, pid, source, dest)
            self.simulate_time_step()
            current_time += 1
        self.output_statistics()

    def output_statistics(self):
        # [ ] TODO: implement the calculation and output of summary statistics
        pass

# Example initialization and simulation run
building = Building(50, 3, 5)
requests = [
    (0, "passenger1", 1, 51),
    (0, "passenger2", 1, 37),
    (10, "passenger3", 20, 1)
]
building.run_simulation(requests)


HallCall = namedtuple('HallCall', ['id', 'time', 'origin', 'destination'])


def call_floors():
    return sample(range(1, FLOORS + 1), k=2)


def erv(lambd=1.0):
    """Exponential random variable with rate parameter lambda"""
    return expovariate(lambd)


def generate_hall_calls(duration=25, arriving_every=1.0):
    """Generate a random representative set of hall calls.

    Hall calls arrive every one unit time on average by default (β=λ=1).
    Arguments configure "for how long" and "how often."

    Hall calls are modeled as a homogeneous Poisson point process with
    exponentially distributed interarrival times reflecting some chosen
    desired mean time between calls, β (beta, the scale parameter). Beta
    is the inverse of the mean arrival rate per unit time, λ (lambda,
    the rate parameter). Lambda is the typical exponential distribution
    parameterization, but here beta is a more natural user specification
    (e.g., "calls arriving every 12 seconds" is β = 12 versus λ ≈ 0.08).

    Args:
        duration (int): length of time window to model (e.g., 100 units)
        arriving_every (float): desired mean time between hall calls, β

    Returns:
        List[HallCall]: list of hall calls as list of named tuples
    """

    # [ ] TODO: remove hardcoded seed and values for demo
    seed(42)
    arriving_every = 2.0

    scale_param = arriving_every
    rate_param = 1.0 / scale_param

    elapsed = 0.0
    arrivals = []
    while (next_arrival := elapsed + erv(rate_param)) < duration:
        elapsed = next_arrival
        arrivals.append(elapsed)

    arrival_times = [math.floor(arrival) for arrival in arrivals]

    calls_data = [(arrival_time, *call_floors()) for arrival_time in arrival_times]

    call_tuples = [(f'passenger{index}', *call_data)
                   for index, call_data in enumerate(calls_data, start=1)]

    hall_calls = [HallCall(*call_tuple) for call_tuple in call_tuples]

    return hall_calls


def generate_requests(hall_calls):
    """Turn unordered hall calls into sorted list of request value tuples."""
    requests = list(tuple(hall_calls))
    # Sort chronologically
    requests.sort(key=lambda x: x[0])
    return requests


def set_seed(seed_int=42):
    """Set seed using random integer from 0 to 100 and return int."""
    seed_int = math.randint(0, 100) if seed_int == None else seed_int
    seed(seed_int)
    return seed_int


if __name__ == "__main__":
    logging.info('Initializing simulation...')

    try:
        demo_hall_calls = generate_hall_calls()
        demo_requests = generate_requests(demo_hall_calls)
        print(demo_requests)
        logging.info('Printed demo requests.')
    # [ ] TODO: bare except
    except:
        logging.error('Error printing demo requests.')

    logging.info('Exiting simulation.')
