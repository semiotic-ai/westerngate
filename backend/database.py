import json
from os import environ as env

from redis import Redis

ARB_OUTPUT = "output"
WORKER_PATHS = "paths"
LEGIT = "legit"
SCAM = "scam"

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
