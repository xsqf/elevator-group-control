import logging
import math
from collections import namedtuple
from random import expovariate, sample, seed

### DEV ###
# [ ] TODO: parameterize
# hardcoded globals for dev and testing

LOG_FILE = 'log.info'

ELEVATORS = 3
CAPACITY = 4
FLOORS = 5


logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s',
    level=logging.INFO,
    filename=LOG_FILE,
)

# [ ] TODO: docstrings
# [ ] TODO: unit tests

###########

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
    requests = [list(hall_call) for hall_call in hall_calls]
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
