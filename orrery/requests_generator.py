import argparse
import csv
import logging
import math
from collections import namedtuple
from random import expovariate, sample, seed

HallCall = namedtuple('HallCall', ['passenger_id', 'time', 'origin', 'destination'])


def call_floors(floors):
    return sample(range(1, floors + 1), k=2)


def erv(lambd=1.0):
    """Exponential random variable with rate parameter lambda"""
    return expovariate(lambd)


def generate_hall_calls(duration, floors, arriving_every=1.0):
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

    scale_param = arriving_every
    rate_param = 1.0 / scale_param

    elapsed = 0.0
    arrivals = []
    while (next_arrival := elapsed + erv(rate_param)) < duration:
        elapsed = next_arrival
        arrivals.append(elapsed)

    arrival_times = [math.floor(arrival) for arrival in arrivals]

    calls_data = [(arrival_time, *call_floors(floors)) for arrival_time in arrival_times]

    call_tuples = [(f'passenger{index}', *call_data)
                   for index, call_data in enumerate(calls_data, start=1)]

    hall_calls = [HallCall(*call_tuple) for call_tuple in call_tuples]

    return hall_calls


def generate_requests(hall_calls):
    """Turn unordered hall calls into sorted list of request value tuples."""
    requests = [(call.time, call.passenger_id, call.origin, call.destination) for call in hall_calls]
    # Sort chronologically
    requests.sort(key=lambda x: x[0])
    return requests


def write_requests_to_csv(requests, filename, seed=None):
    """Output the recorded states of all elevators to a CSV file."""
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['time', 'id', 'source', 'dest'])
        for time, pid, source, dest in requests:
            writer.writerow([time, pid, source, dest])


def set_seed(seed_int=None):
    """Set seed using random integer from 0 to 100 and return int."""
    seed_int = math.randint(0, 100) if seed_int == None else seed_int
    seed(seed_int)
    return seed_int


if __name__ == "__main__":
    logging.info('Initiating random request generation...')
    parser = argparse.ArgumentParser(
        description="Generate random hall calls to CSV.",
    )
    parser.add_argument("-f", "--floors", type=int, help="Number of floors in the building")
    parser.add_argument("-d", "--duration", type=int, help="Duration to generate hall calls")
    parser.add_argument("-s", "--seed", type=int, help="Random seed for determinism")
    parser.add_argument("--arrivingevery", default=1.0, type=float, help="Rate parameter for exponential interarrival times")
    parser.add_argument("--filename", type=str, default='requests.csv', help="Path to output CSV")
    args = parser.parse_args()

    try:
        hall_calls = generate_hall_calls(args.duration, args.floors, args.arrivingevery)
        requests = generate_requests(hall_calls)
        if args.seed:
            set_seed(args.seed)
            seed_string = f'_seed{args.seed}'
        else:
            seed_string = ''
        filename = f'requests_{args.floors}{seed_string}.csv'
        write_requests_to_csv(requests, filename, args.seed)
        print(f"Wrote requests to {filename}.")
    # [ ] TODO: bare except
    except:
        logging.error('Error generating random requests.')

    logging.info('Exiting request generation.')
