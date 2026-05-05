"""
12_offramp.py — Unwrap deposit wallet's pUSD → USDC.e via WALLET batch (1:1).

Run:
    python 12_offramp.py

Requires: PRIVATE_KEY, DEPOSIT_WALLET, BUILDER_*, POLYGON_RPC_URL in .env
The unwrap call must come from the deposit wallet via a WALLET batch so USDC.e
is sent from the deposit wallet. The recipient can be the deposit wallet itself
or another address (e.g. your EOA). Edit RECIPIENT below as needed.
Prerequisite: pUSD → CollateralOfframp approval was set in 4_allowances.py.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from web3 import Web3
from py_builder_relayer_client.models import DepositWalletCall
from _relayer import make_relayer, wallet_batch

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

PRIVATE_KEY    = os.environ["PRIVATE_KEY"]
DEPOSIT_WALLET = os.environ["DEPOSIT_WALLET"]
RPC_URL        = os.environ.get("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")

USDC_E             = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
PUSD               = Web3.to_checksum_address("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB")
COLLATERAL_OFFRAMP = Web3.to_checksum_address("0x2957922Eb93258b93368531d39fAcCA3B4dC5854")

DW = Web3.to_checksum_address(DEPOSIT_WALLET)
# Change RECIPIENT to your EOA address if you want USDC.e sent to the EOA instead
RECIPIENT = DW

ERC20_ABI = [
    {"name": "balanceOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "account", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
]

# unwrap(address _asset, address _to, uint256 _amount)
# _asset = USDC_E (mirrors wrap call on CollateralOnramp)
OFFRAMP_ABI = [
    {"name": "unwrap", "type": "function", "stateMutability": "nonpayable",
     "inputs": [
         {"name": "_asset",  "type": "address"},
         {"name": "_to",     "type": "address"},
         {"name": "_amount", "type": "uint256"},
     ], "outputs": []},
]

w3       = Web3(Web3.HTTPProvider(RPC_URL))
pusd_c   = w3.eth.contract(address=PUSD,               abi=ERC20_ABI)
usdc_c   = w3.eth.contract(address=USDC_E,             abi=ERC20_ABI)
offramp_c = w3.eth.contract(address=COLLATERAL_OFFRAMP, abi=OFFRAMP_ABI)

pusd_bal    = pusd_c.functions.balanceOf(DW).call()
usdc_before = usdc_c.functions.balanceOf(RECIPIENT).call()

print(f"Deposit wallet : {DW}")
print(f"Recipient      : {RECIPIENT}\n")
print(f"pUSD   (wallet)   : {pusd_bal    / 1e6:.6f}")
print(f"USDC.e (recipient): {usdc_before / 1e6:.6f}")

if pusd_bal == 0:
    print("\n⚠ No pUSD in deposit wallet — nothing to unwrap"); exit(0)

print(f"\nUnwrapping {pusd_bal / 1e6:.6f} pUSD → USDC.e via WALLET batch…")

unwrap_data = offramp_c.encode_abi("unwrap", args=[USDC_E, RECIPIENT, pusd_bal])
calls       = [DepositWalletCall(target=COLLATERAL_OFFRAMP, value="0", data=unwrap_data)]
relayer     = make_relayer()
wallet_batch(relayer, DW, calls)

pusd_after  = pusd_c.functions.balanceOf(DW).call()
usdc_after  = usdc_c.functions.balanceOf(RECIPIENT).call()
print(f"\n✓ Offramp confirmed")
print(f"pUSD   (wallet) after   : {pusd_after  / 1e6:.6f}")
print(f"USDC.e (recipient) after: {usdc_after  / 1e6:.6f}  (+{(usdc_after - usdc_before) / 1e6:.6f}) ✓")
