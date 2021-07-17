import json
import multiprocessing
import time
import traceback
from multiprocessing import Pool
from pathlib import Path

from database import Database
from dex_scraper import get_largest_pairs
from logzero import logger
from path_builder import path_builder
from path_arb import *

LP_PER_DEX_ETH = 200
LP_PER_DEX_POLY = 200
MAX_PATH_LENGTH = 4

DB = Database()


def build_lps(subgraph, lp_per_dex, block_number=-1):
    lps = []
    for dex_name in subgraph:
        try:
            amms, block_number = get_largest_pairs(dex_name, lp_per_dex, block_number)
            lps += amms
        except:
            try:
                amms, block_number = get_largest_pairs(
                    dex_name, lp_per_dex, block_number
                )
                lps += amms
            except:
                logger.error(f"Failed to load {dex_name} subgraph")
                logger.error(traceback.format_exc())
    return lps


def path_string(input_path):
    paths = []
    for entry in input_path:
        chain = entry["chain"]
        _in = entry["token_in_symbol"]
        _out = entry["token_out_symbol"]
        paths.append(f"{chain}[${_in}->${_out}]")
    return " -> ".join(paths)


def path_analysis(path):
    reserve_token_info = DB.get_token_info()
    if len(path) == 2:
        amt_in, profit, between_lp_amts = fast_path_two_arb(
                                            float(path[0]["reserve_in"]),
                                            float(path[0]["reserve_out"]),
                                            float(path[1]["reserve_in"]),
                                            float(path[1]["reserve_out"]))
    elif len(path) == 3:
        amt_in, profit, between_lp_amts = fast_path_three_arb(
                                            float(path[0]["reserve_in"]),
                                            float(path[0]["reserve_out"]),
                                            float(path[1]["reserve_in"]),
                                            float(path[1]["reserve_out"]),
                                            float(path[2]["reserve_in"]),
                                            float(path[2]["reserve_out"]))
    elif len(path) == 4:
        amt_in, profit, between_lp_amts = fast_path_four_arb(
                                            float(path[0]["reserve_in"]),
                                            float(path[0]["reserve_out"]),
                                            float(path[1]["reserve_in"]),
                                            float(path[1]["reserve_out"]),
                                            float(path[2]["reserve_in"]),
                                            float(path[2]["reserve_out"]),
                                            float(path[3]["reserve_in"]),
                                            float(path[3]["reserve_out"]))
    elif len(path) == 5:
        amt_in, profit, between_lp_amts = fast_path_five_arb(
                                            float(path[0]["reserve_in"]),
                                            float(path[0]["reserve_out"]),
                                            float(path[1]["reserve_in"]),
                                            float(path[1]["reserve_out"]),
                                            float(path[2]["reserve_in"]),
                                            float(path[2]["reserve_out"]),
                                            float(path[3]["reserve_in"]),
                                            float(path[3]["reserve_out"]),
                                            float(path[4]["reserve_in"]),
                                            float(path[4]["reserve_out"]))
    else:
        logger.warn(f"Path length {len(path)} not supported.")
        return
    token_price = reserve_token_info[path[0]["token_in_symbol"]]
    profit_USD = profit * token_price
    amount_in_USD = amt_in * token_price
    if profit_USD > 0:
        logger.debug(
            f"${round(profit_USD, 2)} on ${round(amount_in_USD, 2)} using {path_string(path)}"
        )
        path[0]["token_in_count"] = between_lp_amts[0]
        for i in range(len(path) - 1):
            path[i]["token_out_count"] = between_lp_amts[i + 1]
            path[i + 1]["token_in_count"] = between_lp_amts[i + 1]
        path[-1]["token_out_count"] = between_lp_amts[-1]

        result = {
            "profit": profit,
            "profitUSD": profit_USD,
            "amt_in": amt_in,
            "path": path,
        }
        if profit > amt_in * 0.5:
            DB.add_scam(result)
        else:
            DB.add_legit(result)


def calculate(subgraphs, eth_block_num=-1, poly_block_num=-1):
    builder = path_builder()

    ethereum_dex_subgraphs = subgraphs["ethereum"]
    polygon_dex_subgraphs = subgraphs["polygon"]
    logger.debug("Building lps")
    ethereum_lps = build_lps(ethereum_dex_subgraphs, LP_PER_DEX_ETH, eth_block_num)
    polygon_lps = build_lps(polygon_dex_subgraphs, LP_PER_DEX_POLY, poly_block_num)
    
    logger.debug("Calculating Paths")
    paths = builder.cross_chain_paths(ethereum_lps, polygon_lps, MAX_PATH_LENGTH)
    logger.debug(f"Number of paths: {len(paths)}")

    # DB.add_paths(paths)
    # while not DB.arbs_ready():
    #     time.sleep(0.1)

    with Pool(multiprocessing.cpu_count()) as p:
        p.map(path_analysis, paths)

    probably_legit = DB.get_legit_arbs(delete=True)
    too_good_to_be_true = DB.get_scam_arbs(delete=True)
    arb_results = {
        "probably_legit": probably_legit,
        "too_good_to_be_true": too_good_to_be_true,
    }
    return arb_results


def main():
    reserve_tokens_file = Path(__file__).parent / "reserve_tokens.json"
    reserve_tokens = json.load(reserve_tokens_file.open("r"))
    logger.debug(f"Reserve Tokens: {json.dumps(reserve_tokens)}")
    DB.set_token_info(reserve_tokens)

    subgraphs_file = Path(__file__).parent / "subgraphs.json"
    subgraphs = json.load(subgraphs_file.open("r"))
    logger.debug(f"Subgraphs: {json.dumps(subgraphs)}")
    initial_arb_results = {"probably_legit": None, "too_good_to_be_true": None}
    DB.set_values(initial_arb_results)
    while True:
        logger.info("Calculating arb events")
        results = calculate(subgraphs)
        DB.set_values(results)


if __name__ == "__main__":
    main()
