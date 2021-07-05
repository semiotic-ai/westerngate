import json
import sys
from os import environ as env

from logzero import logger
from redis import Redis

ARB_OUTPUT = "output"
WORKER_PATHS = "paths"
LEGIT = "legit"
SCAM = "scam"
TOKEN_INFO = "tokens"
MAXLEN = 100000


class Database:
    def __init__(self):
        redis_port = env.get("REDIS_PORT")
        redis_host = env.get("REDIS_HOST")
        if not redis_port:
            raise ValueError("REDIS_PORT needs to be set")
        if not redis_host:
            raise ValueError("REDIS_HOST needs to be set")
        self.redis: Redis = Redis(
            host=redis_host, port=redis_port, db=0, decode_responses=True
        )

    def grab_json(self):
        """Grab the json"""
        the_json = self.redis.get(ARB_OUTPUT)
        return json.loads(the_json)

    def set_values(self, input_dict: dict):
        """Dump the dict to redis"""

        try:
            string_dict = json.dumps(input_dict, cls=json.JSONEncoder)
            self.redis.set(ARB_OUTPUT, string_dict)
            return True
        except:
            logger.error(f"Error setting {input_dict} due to {sys.exc_info()[0]}")
            error_results = {"probably_legit": "Error", "too_good_to_be_true": "Error"}
            self.redis.set(ARB_OUTPUT, str(error_results))
            return False

    def set_token_info(self, token_info):
        try:
            string_dict = json.dumps(token_info, cls=json.JSONEncoder)
            self.redis.set(TOKEN_INFO, string_dict)
        except:
            logger.error(f"Error setting {token_info} due to {sys.exc_info()[0]}")

    def get_token_info(self):
        if self.redis.exists(TOKEN_INFO):
            return json.loads(self.redis.get(TOKEN_INFO))
        return {}

    def add_scam(self, input_dict):
        try:
            string_dict = json.dumps(input_dict, cls=json.JSONEncoder)
            self.redis.rpush(SCAM, string_dict)
        except:
            logger.error(
                f"Error adding scam arb {input_dict} due to {sys.exc_info()[0]}"
            )

    def add_legit(self, input_dict):
        try:
            string_dict = json.dumps(input_dict, cls=json.JSONEncoder)
            self.redis.rpush(LEGIT, string_dict)
        except:
            logger.error(
                f"Error adding legit arb {input_dict} due to {sys.exc_info()[0]}"
            )

    def get_legit_arbs(self, delete=False):
        """Retrieve legit arb list and clear it"""
        legit_arbs = self._get_arbs(LEGIT)
        if delete:
            self.redis.delete(LEGIT)
        return legit_arbs

    def get_scam_arbs(self, delete=False):
        """Retrieve scam arb list and clear it"""
        scam_arbs = self._get_arbs(SCAM)
        if delete:
            self.redis.delete(SCAM)
        return scam_arbs.sort(key=lambda x: x["profitUSD"], reverse=True)


    def _get_arbs(self, token):
        if not self.redis.exists(token):
            return []
        arbs = self.redis.lrange(token, 0, -1)
        arbs = [json.loads(x) for x in arbs]
        arbs.sort(key=lambda x: x["profitUSD"], reverse=True)
        return arbs

    # def arbs_ready(self):
    #     """Check to see if the arbs are ready to harvest"""
    #     return True

    # def add_paths(self, paths):
    #     """Add paths to worker stream"""
    #     for path in paths:
    #         self.redis.xadd(WORKER_PATHS, path, maxlen=MAXLEN)

    # def claim_path(self, worker_id):
    #     """Grab a path and claim it"""
    #     self.redis.xclaim()
