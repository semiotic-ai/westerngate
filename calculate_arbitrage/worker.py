import json
import multiprocessing
import socket
import time
from multiprocessing import Pool
from multiprocessing.connection import arbitrary_address
from pathlib import Path
from random import randrange

import calculate
import graphql as gql
from database import Database
from dex_scraper import get_largest_pairs
from logzero import logger
from path_arb import arb_calculator
from path_builder import path_builder


def main():
    while True:
        time.sleep(randrange(30, 60))
        logger.info(f"Hello from {socket.gethostname()}")


if __name__ == "__main__":
    main()
