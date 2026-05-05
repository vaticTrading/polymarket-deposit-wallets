"""
2_deploy_wallet.py — Deploy a deposit wallet via relayer WALLET-CREATE.

Run:
    python 2_deploy_wallet.py

Requires: PRIVATE_KEY, BUILDER_API_KEY, BUILDER_SECRET, BUILDER_PASSPHRASE in .env

The deposit wallet address is deterministic (derived from owner EOA + factory).
Store the printed address as DEPOSIT_WALLET in your .env — required by every
subsequent script.

No user signature is included in the WALLET-CREATE payload (the relayer handles
deployment). The deployed wallet is uniquely tied to your EOA — the factory
ensures no one else can claim it for a different owner.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from _relayer import make_relayer, CHAIN_ID

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

relayer = make_relayer()

# Deterministically derive the deposit wallet address before deploying
deposit_wallet = relayer.get_expected_deposit_wallet()
print(f"Chain          : {CHAIN_ID}")
print(f"Owner (EOA)    : {relayer.signer.address()}")
print(f"Deposit wallet : {deposit_wallet}  (deterministic — store as DEPOSIT_WALLET in .env)\n")

print("Submitting WALLET-CREATE to relayer…")
response  = relayer.deploy_deposit_wallet()
confirmed = response.wait()

print(f"\n✓ Deposit wallet deployed: {deposit_wallet}")
print(f"  Add to .env:  DEPOSIT_WALLET={deposit_wallet}")
print("\nNext: fund the wallet — send USDC.e to your EOA then run 3_wrap.py")
