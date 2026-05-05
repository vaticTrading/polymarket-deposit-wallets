"""
9_limit_sell.py — GTC SELL YES tokens 2 ticks above best ask (deposit wallet) → cancel.

Run:
    python 9_limit_sell.py

Requires: PRIVATE_KEY, DEPOSIT_WALLET, CLOB_V2_BASE_URL, POLYGON_RPC_URL in .env
Places a limit sell above market so it won't fill, then immediately cancels.
signatureType=3 (POLY_1271).
"""

import os
import sys
import types
from math import gcd
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from web3 import Web3
from py_clob_client_v2 import (
    AssetType,
    BalanceAllowanceParams,
    ClobClient,
    OrderArgs,
    OrderType,
    PartialCreateOrderOptions,
    Side,
    SignatureTypeV2,
)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

COND_ID        = "0x7ad403c3508f8e3912940fd1a913f227591145ca0614074208e0b962d5fcc422"  # JD Vance 2028
YES_TOKEN_ID   = "16040015440196279900485035793550429453516625694844857319147506590755961451627"

PRIVATE_KEY    = os.environ["PRIVATE_KEY"]
DEPOSIT_WALLET = os.environ["DEPOSIT_WALLET"]
CLOB_HOST      = os.environ.get("CLOB_V2_BASE_URL", "https://clob.polymarket.com")
RPC_URL        = os.environ.get("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")

CTF = Web3.to_checksum_address("0x4D97DCd97eC945f40cF65F87097ACe5EA0476045")
ERC1155_ABI = [
    {"name": "balanceOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "account", "type": "address"}, {"name": "id", "type": "uint256"}],
     "outputs": [{"name": "", "type": "uint256"}]},
]


def valid_size(holdings: float, price: float) -> float:
    """Largest size ≤ holdings where size has ≤5 decimal places and size*price has ≤2."""
    s = f"{price:.10f}".rstrip("0")
    d = len(s.split(".")[1]) if "." in s else 0
    q = 10 ** d
    p = round(price * q)
    mod  = q * 1000
    step = (mod // gcd(p, mod)) / 1e5
    n    = int(holdings / step)
    return round(n * step, 5)


w3 = Web3(Web3.HTTPProvider(RPC_URL))
DW = Web3.to_checksum_address(DEPOSIT_WALLET)

temp_client = ClobClient(CLOB_HOST, chain_id=137, key=PRIVATE_KEY,
                         signature_type=SignatureTypeV2.POLY_1271, funder=DEPOSIT_WALLET)
creds  = temp_client.create_or_derive_api_key()
client = ClobClient(CLOB_HOST, chain_id=137, key=PRIVATE_KEY, creds=creds,
                    signature_type=SignatureTypeV2.POLY_1271, funder=DEPOSIT_WALLET)
print(f"Deposit wallet : {DW}  |  API key: {creds.api_key} ✓\n")

info      = client.get_clob_market_info(COND_ID)
token_id  = YES_TOKEN_ID
tick_size = str(info.get("mts", "0.01"))
tick      = float(tick_size)
neg_risk  = info.get("nr", False)

# Sync conditional token balance to CLOB
client.update_balance_allowance(
    BalanceAllowanceParams(asset_type=AssetType.CONDITIONAL,
                           token_id=token_id,
                           signature_type=SignatureTypeV2.POLY_1271)
)

ctf_c    = w3.eth.contract(address=CTF, abi=ERC1155_ABI)
yes_raw  = ctf_c.functions.balanceOf(DW, int(token_id)).call()
holdings = yes_raw / 1e6
if holdings < 0.01:
    print("⚠ No YES tokens in deposit wallet — run 7_market_buy_order.py first"); exit(1)

book = client.get_order_book(token_id)
asks = sorted(book["asks"], key=lambda a: float(a["price"]))
if not asks:
    print("No asks in book"); exit(1)

# 2 ticks above best ask — won't fill
price = round(float(asks[0]["price"]) + 2 * tick, 4)
size  = valid_size(holdings, price)

if size <= 0:
    print(f"⚠ No valid size for price={price} and holdings={holdings}"); exit(1)

print(f"YES holdings : {holdings:.5f} tokens")
print(f"Valid size   : {size}  (step constraint for price {price})")
print(f"Placing GTC SELL: {size} shares @ ${price}  (best ask: ${float(asks[0]['price'])})")

resp = client.create_and_post_order(
    OrderArgs(token_id=token_id, price=price, size=size, side=Side.SELL),
    PartialCreateOrderOptions(tick_size=tick_size, neg_risk=neg_risk),
    OrderType.GTC,
)
order_id = resp.get("orderID") if isinstance(resp, dict) else resp.orderID
status   = resp.get("status")  if isinstance(resp, dict) else resp.status
print(f"\n✓ Order placed : {order_id}  status: {status}")

# Cancel (cleanup)
cancel   = client.cancel_order(types.SimpleNamespace(orderID=order_id))
canceled = cancel.get("canceled", []) if isinstance(cancel, dict) else []
if order_id in canceled:
    print(f"✓ Cancelled    : {order_id}")
else:
    print(f"Cancel response: {cancel}")
