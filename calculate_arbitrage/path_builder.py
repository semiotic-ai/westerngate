class path_builder:
    def __init__(self):
        self.reserve_tokens = {
            "ethereum": {
                "WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2".lower(),
                "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48".lower(),
                "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7".lower(),
                "UNI": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984".lower(),
                "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599".lower(),
                "DAI": "0x6b175474e89094c44da98b954eedeac495271d0f".lower(),
                "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9".lower(),
                "COMP": "0xc00e94cb662c3520282e6f5717214004a7f26888".lower(),
                "SUSHI": "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2".lower(),
                "YFI": "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e".lower(),
                "SNX": "0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f".lower(),
                "CRV": "0xD533a949740bb3306d119CC777fa900bA034cd52".lower(),
                "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA".lower()
            },
            "polygon": {
                "WETH": "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619".lower(),
                "USDC": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174".lower(),
                "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F".lower(),
                "UNI": "0xb33eaad8d922b1083446dc23f610c2567fb5180f".lower(),
                "WBTC": "0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6".lower(),
                "DAI": "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063".lower(),
                "AAVE": "0xd6df932a45c0f255f85145f286ea0b292b21c90b".lower(),
                "COMP": "0x8505b9d2254a7ae468c0e9dd10ccea3a837aef5c".lower(),
                "SUSHI": "0x0b3f868e0be5597d5db7feb59e1cadbb0fdda50a".lower(),
                "YFI": "0xda537104d6a5edd53c6fbba9a898708e465260b6".lower(),
                "SNX": "0x50b728d8d964fd00c2d0aad81718b71311fef68a".lower(),
                "CRV": "0x172370d5cd63279efa6d502dab29171933a610af".lower(),
                "LINK": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39".lower()
            }
        }

        self.eth_to_poly = {self.reserve_tokens["ethereum"][ticker]: self.reserve_tokens["polygon"][ticker] for ticker in self.reserve_tokens["ethereum"]}
        self.poly_to_eth = {self.reserve_tokens["polygon"][ticker]: self.reserve_tokens["ethereum"][ticker] for ticker in self.reserve_tokens["ethereum"]}

    def cross_chain_paths(self, ethereum_amm_list, polygon_amm_list, max_path_len = 4):
        # Start by getting all possible paths between our reserve tokens for each chain
        ethereum_reserve_paths = self._reserve_paths(ethereum_amm_list, max_path_len - 1, "ethereum")
        polygon_reserve_paths = self._reserve_paths(polygon_amm_list, max_path_len - 1, "polygon")

        candidate_paths = []

        for ethereum_start in self.reserve_tokens["ethereum"].values():
            for ethereum_path in ethereum_reserve_paths[ethereum_start.lower()]:

                # Loop through polygon paths that start where the ethereum ends
                for polygon_path in polygon_reserve_paths[self.eth_to_poly[ethereum_path[-1]["token_out_id"].lower()]]:

                    # Check that the polygon path end is equal to the ethereum beginning
                    if ethereum_start.lower() == self.poly_to_eth[polygon_path[-1]["token_out_id"].lower()]:

                        # Make sure the path is not longer than the set max
                        if len(polygon_path) + len(ethereum_path) <= max_path_len:
                            candidate_paths.append(polygon_path + ethereum_path)

        for polygon_start in self.reserve_tokens["polygon"].values():
            for polygon_path in polygon_reserve_paths[polygon_start.lower()]:

                # Loop through ethereum paths that start where the polygon ends
                for ethereum_path in ethereum_reserve_paths[self.poly_to_eth[polygon_path[-1]["token_out_id"].lower()]]:

                    # Check that the ethereum path end is equal to the polygon beginning
                    if polygon_start.lower() == self.eth_to_poly[ethereum_path[-1]["token_out_id"].lower()]:

                        # Make sure the path is not longer than the set max
                        if len(ethereum_path) + len(polygon_path) <= max_path_len:
                            candidate_paths.append(ethereum_path + polygon_path)

        return candidate_paths

    def _reserve_paths(self, amm_list, max_path_len, chain):

        reserve_tokens = self.reserve_tokens[chain]

        # We will store edges of each possible length - first we consider edges of length 1
        adjacency_list = [{}]

        # Construct adjacency list of AMM edges (we add references to each AMM
        # edge object in both directions to consider all possible paths)
        for amm in amm_list:
            edge = {"end": amm["token1"]["id"].lower(), "amm_list": [amm]}
            if amm["token0"]["id"].lower() in adjacency_list[0]:
                adjacency_list[0][amm["token0"]["id"].lower()].append(edge)
            else:
                adjacency_list[0][amm["token0"]["id"].lower()] = [edge]

            reverse_edge = {"end": amm["token0"]["id"].lower(), "amm_list": [amm]}
            if amm["token1"]["id"].lower() in adjacency_list[0]:
                adjacency_list[0][amm["token1"]["id"].lower()].append(reverse_edge)
            else:
                adjacency_list[0][amm["token1"]["id"].lower()] = [reverse_edge]

        # Remove all tokens that only appear once from adjacency list and aren't reserve tokens
        while True:
            del_keys = []

            for key in adjacency_list[0]:
                if len(adjacency_list[0][key]) == 1 and key not in reserve_tokens.values():
                    del_keys.append(key)

                    # Now we must delete the corresponding reference elsewhere in the adjacency_list
                    other_token = adjacency_list[0][key][0]["end"]

                    for entry in adjacency_list[0][other_token]:
                        if entry["end"] == key:
                            adjacency_list[0][other_token].remove(entry)

                if len(adjacency_list[0][key]) == 0:
                    del_keys.append(key)

            # Break loop once we find no more keys to delete
            if not del_keys:
                break

            for key in del_keys:
                del(adjacency_list[0][key])

        # Adjacency list containing the paths that go between the reserve tokens
        reserve_paths = {key: [] for key in reserve_tokens.values()}

        # Initially we must fill it with all simple edges that move between two reserve currencies
        for reserve_token in reserve_tokens.values():
            if reserve_token in adjacency_list[0]:
                for edge in adjacency_list[0][reserve_token]:
                    if edge["end"] in reserve_tokens.values():
                        reserve_paths[reserve_token].append(edge)

        # It will take two edges to move from one reserve token to another
        # reserve token. Path lengths longer than two can move through tokens
        # not included in our list of reserve tokens. Path lengths of three must
        # include edges where at least one token is a reserve token. Path lengths
        # of 4 or more meanwhile can contain edges where neither token is a reserve token

        for path_len in range(max_path_len - 1):
            adjacency_list.append({key: [] for key in adjacency_list[0]})

            for join_token in adjacency_list[path_len]:
                # Check if we can join each of our current longest edges
                for edge in adjacency_list[path_len][join_token]:

                    # A path must start and end with a reserve token, if this path
                    # is one less than the max path length then we will enforce
                    # that at least one token is a reserve token
                    if path_len + 2 >= max_path_len - 1 and edge["end"] not in reserve_tokens.values():
                        continue

                    # Check for joining with each of our smallest edges
                    for simple_edge in adjacency_list[0][join_token]:

                        # Similarly to above we are enforcing that the second token
                        # must also be a reserve token if the current path length is the max path length
                        if path_len + 2 >= max_path_len and simple_edge["end"] not in reserve_tokens.values():
                            continue

                        # Make sure that there is no overlap in included AMMS
                        # and that the new edge would not have the same endpoint
                        if simple_edge["amm_list"][0] not in edge["amm_list"] and \
                           simple_edge["end"] != edge["end"]:

                           new_edge = {
                               "end": edge["end"],
                               "amm_list": simple_edge["amm_list"] + edge["amm_list"]
                           }

                           adjacency_list[path_len + 1][simple_edge["end"]].append(new_edge)

                           if edge["end"] in reserve_tokens.values() and simple_edge["end"] in reserve_tokens.values():
                                reserve_paths[simple_edge["end"]].append(new_edge)

        # Format it for interfacing with front end
        reserve_path_formatted = {key: [] for key in reserve_paths}

        for key in reserve_paths:
            for edge in reserve_paths[key]:
                curr_token = key

                reserve_path_formatted[key].append([])
                for amm in edge["amm_list"]:

                    reserve_path_formatted[key][-1].append({})
                    reserve_path_formatted[key][-1][-1]["chain"] = chain
                    reserve_path_formatted[key][-1][-1]["id"] = amm["id"]

                    if amm["token0"]["id"] == curr_token:
                        reserve_path_formatted[key][-1][-1]["token_in_symbol"] = amm["token0"]["symbol"]
                        reserve_path_formatted[key][-1][-1]["token_out_symbol"] = amm["token1"]["symbol"]
                        reserve_path_formatted[key][-1][-1]["token_in_id"] = amm["token0"]["id"]
                        reserve_path_formatted[key][-1][-1]["token_out_id"] = amm["token1"]["id"]
                        reserve_path_formatted[key][-1][-1]["reserve_in"] = amm["reserve0"]
                        reserve_path_formatted[key][-1][-1]["reserve_out"] = amm["reserve1"]

                        curr_token = amm["token1"]["id"]
                    elif amm["token1"]["id"] == curr_token:
                        reserve_path_formatted[key][-1][-1]["token_in_symbol"] = amm["token1"]["symbol"]
                        reserve_path_formatted[key][-1][-1]["token_out_symbol"] = amm["token0"]["symbol"]
                        reserve_path_formatted[key][-1][-1]["token_in_id"] = amm["token1"]["id"]
                        reserve_path_formatted[key][-1][-1]["token_out_id"] = amm["token0"]["id"]
                        reserve_path_formatted[key][-1][-1]["reserve_in"] = amm["reserve1"]
                        reserve_path_formatted[key][-1][-1]["reserve_out"] = amm["reserve0"]

                        curr_token = amm["token0"]["id"]

                    else:
                        raise Exception("Can not format invalid path!")

        return reserve_path_formatted
