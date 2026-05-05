"""
6_limit_buy_order.py — GTC BUY 2 ticks below best bid (deposit wallet collateral) → cancel.

Run:
    python 6_limit_buy_order.py

Requires: PRIVATE_KEY, DEPOSIT_WALLET, CLOB_V2_BASE_URL, POLYGON_RPC_URL in .env
pUSD collateral is held by the deposit wallet. maker = signer = deposit wallet.
signatureType=3 (POLY_1271).
"""

import os
import sys
import types
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

# ── Init client ──────────────────────────────────────────────────────────────────
temp_client = ClobClient(CLOB_HOST, chain_id=137, key=PRIVATE_KEY,
                         signature_type=SignatureTypeV2.POLY_1271, funder=DEPOSIT_WALLET)
creds  = temp_client.create_or_derive_api_key()
client = ClobClient(CLOB_HOST, chain_id=137, key=PRIVATE_KEY, creds=creds,
                    signature_type=SignatureTypeV2.POLY_1271, funder=DEPOSIT_WALLET)
print(f"Deposit wallet : {DW}")
print(f"API key        : {creds.api_key} ✓\n")

# ── Sync on-chain balances/allowances to CLOB ────────────────────────────────────
client.update_balance_allowance(
    BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=SignatureTypeV2.POLY_1271)
)
print("Balance/allowance synced ✓\n")

# ── Market info ──────────────────────────────────────────────────────────────────
info      = client.get_clob_market_info(COND_ID)
token_id  = YES_TOKEN_ID
tick_size = str(info.get("mts", "0.01"))
neg_risk  = info.get("nr", False)
print(f"Market: JD Vance 2028  tick={tick_size}  negRisk={neg_risk}  token={token_id[:16]}…")

# ── Order book — 2 ticks below best bid ──────────────────────────────────────────
book = client.get_order_book(token_id)
bids = sorted(book["bids"], key=lambda b: float(b["price"]), reverse=True)
if len(bids) < 3:
    print("Not enough bid levels"); exit(1)
price = float(bids[2]["price"])

# ── pUSD balance comes from deposit wallet ────────────────────────────────────────
raw_bal = w3.eth.contract(address=PUSD, abi=ERC20_ABI).functions.balanceOf(DW).call()
balance = raw_bal / 1e6
if balance < 1:
    print("⚠ Not enough pUSD in deposit wallet"); exit(1)

size = round((balance - 1) / price, 2)
print(f"Balance : ${balance:.4f} pUSD (deposit wallet)")
print(f"Placing GTC BUY: {size} shares @ ${price}")

# ── Place GTC limit BUY ───────────────────────────────────────────────────────────
resp = client.create_and_post_order(
    OrderArgs(token_id=token_id, price=price, size=size, side=Side.BUY),
    PartialCreateOrderOptions(tick_size=tick_size, neg_risk=neg_risk),
    OrderType.GTC,
)
order_id = resp.get("orderID") if isinstance(resp, dict) else resp.orderID
status   = resp.get("status")  if isinstance(resp, dict) else resp.status
print(f"\n✓ Order placed : {order_id}  status: {status}")

# ── Cancel (cleanup) ──────────────────────────────────────────────────────────────
cancel   = client.cancel_order(types.SimpleNamespace(orderID=order_id))
canceled = cancel.get("canceled", []) if isinstance(cancel, dict) else []
if order_id in canceled:
    print(f"✓ Cancelled    : {order_id}")
else:
    print(f"Cancel response: {cancel}")
