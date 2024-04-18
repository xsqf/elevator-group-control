# import argparse
# import logging
# import math
# import os
# import re
# import sys
# from collections import defaultdict, namedtuple
# from random import expovariate, sample
# from statistics import mean
# from timeit import default_timer as timer


# [ ] DEV: Controller
# class ElevatorGroupController:

# [ ] DEV: Simulator
# class OrrerySimulator:


# def load_hall_calls_csv(hall_calls_filename):
#     """Load all hall calls (i.e., requests) from CSV file.

#     The expected format is a four-column CSV with a single-row header.
#     The primary key is the passenger ID.
#     Rows following the header contain one hall call per row.
#     For example:
#         ------------------------------------
#         id,time,origin,destination
#         passenger1,0,1,51
#         passenger2,0,1,37
#         passenger3,10,20,1
#         ------------------------------------
#     * id (str)
#     * time (int)
#     * origin (int)
#     * destination (int)

#     Args:
#         hall_calls_filename (str): path to CSV file of hall calls data

#     Returns:
#         [ ] TODO: same data structure as auto-generated
#     """

#     return hall_calls_metadata


# if __name__ == '__main__':
#     p = argparse.ArgumentParser(description='Simulate elevator group behavior.')
#     p.add_argument(
#         'hall_calls_file',
#         default='hall_calls_sample.csv',
#         help='CSV file of all hall calls (i.e., elevator requests)',
#     )
#     p.add_argument(
#         '--log_file',
#         default=LOG_FILE,
#         help='logging filename specification',
#     )
#     args = p.parse_args()

#     # try:
#     #     logging.info('Initiating simulator and loading hall calls...')
#     #     hall_calls = load_hall_calls(args.hall_calls_file)
#     # except:
#     #     logging.error(f'Error loading {args.hall_calls_file}. Exiting...', exc_info=True)
#     #     sys.exit(1)
