"""
7_market_buy_order.py — FOK market BUY at best ask + 1 tick (deposit wallet).

Run:
    python 7_market_buy_order.py

Requires: PRIVATE_KEY, DEPOSIT_WALLET, CLOB_V2_BASE_URL, POLYGON_RPC_URL in .env
FOK (Fill-or-Kill): executes immediately at the best available price or cancels.
signatureType=3 (POLY_1271).
"""

import os
import sys
from math import gcd
sys.path.insert(0, os.path.dirname(__file__))


def fok_size(budget: float, price: float) -> float:
    """
    Largest valid FOK market buy size where:
      - size * price has ≤2 decimal places  (maker/pUSD constraint)
      - size itself has ≤5 decimal places   (taker/shares constraint)

    For price p/q (e.g. 0.212 = 212/1000):
      size must be a multiple of  (q*1000 / gcd(p, q*1000)) / 1e5
    For price=0.212 this gives step=2.5 shares.
    """
    s = f"{price:.10f}".rstrip("0")
    d = len(s.split(".")[1]) if "." in s else 0
    q = 10 ** d
    p = round(price * q)
    mod  = q * 1000
    step = (mod // gcd(p, mod)) / 1e5
    n    = int(budget / (price * step))
    return round(n * step, 5)

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

PRIVATE_KEY    = os.environ["PRIVATE_KEY"]
DEPOSIT_WALLET = os.environ["DEPOSIT_WALLET"]
CLOB_HOST      = os.environ.get("CLOB_V2_BASE_URL", "https://clob.polymarket.com")
RPC_URL        = os.environ.get("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")
COND_ID        = "0x7ad403c3508f8e3912940fd1a913f227591145ca0614074208e0b962d5fcc422"  # JD Vance 2028
YES_TOKEN_ID   = "16040015440196279900485035793550429453516625694844857319147506590755961451627"

PUSD = Web3.to_checksum_address("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB")
ERC20_ABI = [{"name": "balanceOf", "type": "function", "stateMutability": "view",
              "inputs": [{"name": "account", "type": "address"}],
              "outputs": [{"name": "", "type": "uint256"}]}]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
DW = Web3.to_checksum_address(DEPOSIT_WALLET)

temp_client = ClobClient(CLOB_HOST, chain_id=137, key=PRIVATE_KEY,
                         signature_type=SignatureTypeV2.POLY_1271, funder=DEPOSIT_WALLET)
creds  = temp_client.create_or_derive_api_key()
client = ClobClient(CLOB_HOST, chain_id=137, key=PRIVATE_KEY, creds=creds,
                    signature_type=SignatureTypeV2.POLY_1271, funder=DEPOSIT_WALLET)
print(f"Deposit wallet : {DW}  |  API key: {creds.api_key} ✓\n")

client.update_balance_allowance(
    BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=SignatureTypeV2.POLY_1271)
)

info      = client.get_clob_market_info(COND_ID)
token_id  = YES_TOKEN_ID
tick_size = str(info.get("mts", "0.01"))
tick      = float(tick_size)
neg_risk  = info.get("nr", False)

book = client.get_order_book(token_id)
asks = sorted(book["asks"], key=lambda a: float(a["price"]))
if not asks:
    print("No asks — cannot market buy"); exit(1)

# Price 1 tick above best ask to guarantee fill
price = round(float(asks[0]["price"]) + tick, 4)

raw_bal = w3.eth.contract(address=PUSD, abi=ERC20_ABI).functions.balanceOf(DW).call()
balance = raw_bal / 1e6
if balance < 1:
    print("⚠ Not enough pUSD in deposit wallet"); exit(1)

size = fok_size(balance, price)        # largest valid size satisfying CLOB precision rules
print(f"Balance : ${balance:.4f} pUSD (deposit wallet)")
print(f"Placing FOK market BUY: {size} shares @ ${price}  (best ask: ${float(asks[0]['price'])})")

resp = client.create_and_post_order(
    OrderArgs(token_id=token_id, price=price, size=size, side=Side.BUY),
    PartialCreateOrderOptions(tick_size=tick_size, neg_risk=neg_risk),
    OrderType.FOK,
)
order_id = resp.get("orderID") if isinstance(resp, dict) else resp.orderID
status   = resp.get("status")  if isinstance(resp, dict) else resp.status
print(f"\n✓ Order result : {order_id}  status: {status}")
