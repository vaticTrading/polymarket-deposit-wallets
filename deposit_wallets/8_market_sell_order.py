"""
8_market_sell_order.py — FOK market SELL YES tokens at best bid - 1 tick (deposit wallet).

Run:
    python 8_market_sell_order.py

Requires: PRIVATE_KEY, DEPOSIT_WALLET, CLOB_V2_BASE_URL, POLYGON_RPC_URL in .env
Sells YES tokens from the deposit wallet at market. Must have bought them first (7_market_buy_order.py).
signatureType=3 (POLY_1271).
"""

import os
import sys
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


def fok_size(holdings: float, price: float) -> float:
    """
    Largest valid FOK sell size ≤ holdings where:
      - size has ≤5 decimal places        (maker/shares constraint)
      - size * price has ≤2 decimal places (taker/pUSD constraint)

    For price p/q the valid step = (q*1000 / gcd(p, q*1000)) / 1e5
    """
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

# Sync YES token balance to CLOB
client.update_balance_allowance(
    BalanceAllowanceParams(asset_type=AssetType.CONDITIONAL,
                           token_id=token_id,
                           signature_type=SignatureTypeV2.POLY_1271)
)

# Check on-chain YES token balance
ctf_c    = w3.eth.contract(address=CTF, abi=ERC1155_ABI)
yes_raw  = ctf_c.functions.balanceOf(DW, int(token_id)).call()
holdings = yes_raw / 1e6
if holdings < 0.01:
    print("⚠ No YES tokens in deposit wallet — run 7_market_buy_order.py first"); exit(1)

book = client.get_order_book(token_id)
bids = sorted(book["bids"], key=lambda b: float(b["price"]), reverse=True)
if not bids:
    print("No bids — cannot market sell"); exit(1)

# 1 tick below best bid to guarantee fill
price = round(float(bids[0]["price"]) - tick, 4)
size  = fok_size(holdings, price)

if size <= 0:
    print(f"⚠ No valid size for price={price} and holdings={holdings}"); exit(1)

print(f"YES holdings : {holdings:.5f} tokens")
print(f"Valid size   : {size}  (step constraint for price {price})")
print(f"Placing FOK market SELL: {size} shares @ ${price}  (best bid: ${float(bids[0]['price'])})")

resp = client.create_and_post_order(
    OrderArgs(token_id=token_id, price=price, size=size, side=Side.SELL),
    PartialCreateOrderOptions(tick_size=tick_size, neg_risk=neg_risk),
    OrderType.FOK,
)
order_id = resp.get("orderID") if isinstance(resp, dict) else resp.orderID
status   = resp.get("status")  if isinstance(resp, dict) else resp.status
print(f"\n✓ Order result : {order_id}  status: {status}")
