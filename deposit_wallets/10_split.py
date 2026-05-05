"""
10_split.py — Split deposit wallet's pUSD → YES + NO tokens via WALLET batch.

Run:
    python 10_split.py

Requires: PRIVATE_KEY, DEPOSIT_WALLET, BUILDER_*, POLYGON_RPC_URL in .env

Uses a standard (non-NegRisk) binary market and calls CTF.splitPosition directly.
This works because pUSD → CTF approval was set in 4_allowances.py.

Why not through an adapter: both CtfCollateralAdapter and NegRiskCtfCollateralAdapter
are blocked by the relayer's approve allowlist, so we can't grant them pUSD approval
from the deposit wallet. The raw CTF contract IS approved, so direct split works for
standard binary markets.

Market used: Will bitcoin hit $1M before GTA VI? (non-NegRisk, ~50/50)
Run 11_merge.py to recover pUSD from YES+NO tokens.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from web3 import Web3
from eth_abi import decode as abi_decode
from py_builder_relayer_client.models import DepositWalletCall
from _relayer import make_relayer, wallet_batch

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DEPOSIT_WALLET = os.environ["DEPOSIT_WALLET"]
RPC_URL        = os.environ.get("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")

# Standard binary market — Will bitcoin hit $1M before GTA VI?
COND_ID      = "0xbb57ccf5853a85487bc3d83d04d669310d28c6c810758953b9d9b91d1aee89d2"
YES_TOKEN_ID = "59096053829818928821715698848500684407651115475127977519494489878858719753099"
NO_TOKEN_ID  = "108204443821004451954683085420839421584079841084134544675147755750632966106254"

PUSD          = Web3.to_checksum_address("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB")
CTF           = Web3.to_checksum_address("0x4D97DCd97eC945f40cF65F87097ACe5EA0476045")
BYTES32_ZERO  = b"\x00" * 32
TRANSFER_BATCH = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"

ERC20_ABI = [
    {"name": "balanceOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "account", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
]

# CTF.splitPosition(collateralToken, parentCollectionId, conditionId, partition, amount)
CTF_ABI = [
    {"name": "splitPosition", "type": "function", "stateMutability": "nonpayable",
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
ctf_c  = w3.eth.contract(address=CTF,  abi=CTF_ABI)

raw_bal     = pusd_c.functions.balanceOf(DW).call()
split_units = raw_bal - 1_000_000 if raw_bal > 1_000_000 else 0

print(f"Deposit wallet : {DW}")
print(f"Market         : Will bitcoin hit $1M before GTA VI? (non-NegRisk)")
print(f"Condition ID   : {COND_ID}")
print(f"pUSD balance   : {raw_bal / 1e6:.6f}")

if split_units == 0:
    print("⚠ Not enough pUSD in deposit wallet (need > $1)"); exit(1)

cond_bytes = bytes.fromhex(COND_ID.lstrip("0x"))
print(f"\nSplitting {split_units / 1e6:.6f} pUSD → YES + NO via WALLET batch (direct CTF call)…")

split_data = ctf_c.encode_abi(
    "splitPosition",
    args=[PUSD, BYTES32_ZERO, cond_bytes, [1, 2], split_units],
)
calls    = [DepositWalletCall(target=CTF, value="0", data=split_data)]
relayer  = make_relayer()
confirmed = wallet_batch(relayer, DW, calls)

print(f"\n✓ Split confirmed")

# Parse minted token IDs from TransferBatch log (best effort)
try:
    tx_hash = confirmed.transaction_hash if hasattr(confirmed, "transaction_hash") else None
    if tx_hash:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        for log in receipt["logs"]:
            if (log["address"].lower() == CTF.lower()
                    and log["topics"][0].hex() == TRANSFER_BATCH):
                ids, amounts = abi_decode(
                    ["uint256[]", "uint256[]"], bytes.fromhex(log["data"].hex()[2:])
                )
                for i, (tid, amt) in enumerate(zip(ids, amounts)):
                    label = "YES" if str(tid) == YES_TOKEN_ID else "NO " if str(tid) == NO_TOKEN_ID else f"[{i}]"
                    print(f"  {label} tokenId={tid}  amount={amt/1e6:.6f}")
except Exception as e:
    print(f"(Could not parse token IDs from receipt: {e})")

print(f"\nYES token: {YES_TOKEN_ID}")
print(f"NO  token: {NO_TOKEN_ID}")
print("\nRun 11_merge.py to convert YES+NO back to pUSD")
