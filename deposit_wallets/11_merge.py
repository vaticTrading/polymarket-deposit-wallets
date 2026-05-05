"""
11_merge.py — Merge deposit wallet's YES + NO tokens back to pUSD via WALLET batch.

Run:
    python 11_merge.py

Requires: PRIVATE_KEY, DEPOSIT_WALLET, BUILDER_*, POLYGON_RPC_URL in .env

Uses the same non-NegRisk binary market as 10_split.py and calls CTF.mergePositions
directly — identical reasoning: both adapters are blocked by the relayer allowlist,
but CTF itself is approved for pUSD (set in 4_allowances.py).

Market used: Will bitcoin hit $1M before GTA VI? (non-NegRisk, ~50/50)
Run 10_split.py first to obtain matching YES + NO token balances.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from web3 import Web3
from py_builder_relayer_client.models import DepositWalletCall
from _relayer import make_relayer, wallet_batch

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DEPOSIT_WALLET = os.environ["DEPOSIT_WALLET"]
RPC_URL        = os.environ.get("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")

# Same non-NegRisk binary market as 10_split.py
COND_ID      = "0xbb57ccf5853a85487bc3d83d04d669310d28c6c810758953b9d9b91d1aee89d2"
YES_TOKEN_ID = 59096053829818928821715698848500684407651115475127977519494489878858719753099
NO_TOKEN_ID  = 108204443821004451954683085420839421584079841084134544675147755750632966106254

PUSD         = Web3.to_checksum_address("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB")
CTF          = Web3.to_checksum_address("0x4D97DCd97eC945f40cF65F87097ACe5EA0476045")
BYTES32_ZERO = b"\x00" * 32

ERC20_ABI = [
    {"name": "balanceOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "account", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
]

ERC1155_ABI = [
    {"name": "balanceOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "account", "type": "address"}, {"name": "id", "type": "uint256"}],
     "outputs": [{"name": "", "type": "uint256"}]},
]

# CTF.mergePositions(collateralToken, parentCollectionId, conditionId, partition, amount)
CTF_ABI = [
    {"name": "mergePositions", "type": "function", "stateMutability": "nonpayable",
     "inputs": [
         {"name": "collateralToken",    "type": "address"},
         {"name": "parentCollectionId", "type": "bytes32"},
         {"name": "conditionId",        "type": "bytes32"},
         {"name": "partition",          "type": "uint256[]"},
         {"name": "amount",             "type": "uint256"},
     ], "outputs": []},
]

w3     = Web3(Web3.HTTPProvider(RPC_URL))
DW     = Web3.to_checksum_address(DEPOSIT_WALLET)
pusd_c = w3.eth.contract(address=PUSD, abi=ERC20_ABI)
ctf_c  = w3.eth.contract(address=CTF,  abi=ERC1155_ABI)
ctf_rw = w3.eth.contract(address=CTF,  abi=CTF_ABI)

yes_bal     = ctf_c.functions.balanceOf(DW, YES_TOKEN_ID).call()
no_bal      = ctf_c.functions.balanceOf(DW, NO_TOKEN_ID).call()
pusd_before = pusd_c.functions.balanceOf(DW).call()

print(f"Deposit wallet : {DW}")
print(f"Market         : Will bitcoin hit $1M before GTA VI? (non-NegRisk)")
print(f"Condition ID   : {COND_ID}")
print(f"YES balance    : {yes_bal / 1e6:.6f}")
print(f"NO  balance    : {no_bal  / 1e6:.6f}")
print(f"pUSD (before)  : {pusd_before / 1e6:.6f}")

merge_units = min(yes_bal, no_bal)
if merge_units == 0:
    print("\n⚠ No matching YES/NO token pair — run 10_split.py first"); exit(1)

cond_bytes = bytes.fromhex(COND_ID.lstrip("0x"))
print(f"\nMerging {merge_units / 1e6:.6f} YES+NO → pUSD via WALLET batch (direct CTF call)…")

merge_data = ctf_rw.encode_abi(
    "mergePositions",
    args=[PUSD, BYTES32_ZERO, cond_bytes, [1, 2], merge_units],
)
calls   = [DepositWalletCall(target=CTF, value="0", data=merge_data)]
relayer = make_relayer()
wallet_batch(relayer, DW, calls)

pusd_after = pusd_c.functions.balanceOf(DW).call()
print(f"\n✓ Merge confirmed")
print(f"pUSD (after)   : {pusd_after / 1e6:.6f}  (+{(pusd_after - pusd_before) / 1e6:.6f}) ✓")
