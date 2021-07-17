from typing import Any, Dict, List, Optional, Tuple

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport


def query_subgraph(
    subgraph_name: str,
    query_str: str,
    variables: Optional[Dict[str, str]] = None,
    provider_url: str = "https://api.thegraph.com/subgraphs/name/",
    custom_headers: Dict[str, str] = {},
) -> Dict:
    transport = AIOHTTPTransport(
        url=provider_url + subgraph_name, headers=custom_headers,
        timeout=900
    )
    client = Client(transport=transport, fetch_schema_from_transport=False, execute_timeout=1200)
    query = gql(query_str)
    result = client.execute(query, variables)
    return result


def get_largest_pairs(
    dex_subgraph: str,
    first: int = 100,
    block: int = -1,
    provider_url: str = "https://api.thegraph.com/subgraphs/name/",
    custom_headers: Dict[str, str] = {},
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Supported dex_subgraphs:
        - uniswap/uniswap-v2
        - sushiswap/exchange
        - sushiswap/matic-exchange
        - sameepsi/quickswap

    Returns a tuple of :
        - the list of largest pairs by liquidity on the platform
        - latest block indexed (unrelated to the block argument)
    """

    block_argument = f"{{number: {block}}}" if block >= 0 else "null"

    r = query_subgraph(
        dex_subgraph,
        f"""
        {{
            pairs(
                orderBy: reserveUSD,
                first: {first},
                orderDirection: desc,
                block: {block_argument}
            ) {{
                id
                token1 {{
                    id
                    symbol
                }}
                token0 {{
                    id
                    symbol
                }}
                reserve0
                reserve1
                reserveUSD
            }}
            _meta {{
                block {{
                    number
                }}
            }}
        }}
        """,
        provider_url=provider_url,
        custom_headers=custom_headers,
    )
    return r["pairs"], r["_meta"]["block"]["number"]


def _block_timestamp(blocks_subgraph: str, block_number: int) -> int:
    r = query_subgraph(
        blocks_subgraph,
        f"""
        {{
            blocks(where: {{number: {block_number}}}) {{
                timestamp
            }}
        }}
        """,
    )

    return int(r["blocks"][0]["timestamp"])


def eth_block_timestamp(block_number: int) -> int:
    return _block_timestamp("blocklytics/ethereum-blocks", block_number)


def matic_block_timestamp(block_number: int) -> int:
    return _block_timestamp("matthewlilley/polygon-blocks", block_number)
