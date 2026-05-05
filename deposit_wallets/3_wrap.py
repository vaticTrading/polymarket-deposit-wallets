"""
3_wrap.py — Wrap EOA's USDC.e → pUSD, minted directly to the deposit wallet (1:1).

Run:
    python 3_wrap.py

Requires: PRIVATE_KEY, DEPOSIT_WALLET, POLYGON_RPC_URL in .env
Send USDC.e to your EOA address before running. The EOA calls CollateralOnramp
directly (no relayer needed here) and mints pUSD straight into the deposit wallet.

Why the EOA calls wrap directly: the wrap recipient can be any address, so we
skip a WALLET batch and save a round-trip. The EOA pays no gas — it holds no
MATIC because the relayer covers gas. Wait, the EOA DOES need MATIC for this
direct on-chain call. If you prefer fully gasless, send USDC.e to the deposit
wallet and use 4_allowances.py logic to call wrap from the wallet batch instead.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from web3 import Web3

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

PRIVATE_KEY    = os.environ["PRIVATE_KEY"]
DEPOSIT_WALLET = os.environ.get("DEPOSIT_WALLET", "").strip()
RPC_URL        = os.environ.get("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")

if not DEPOSIT_WALLET:
    raise SystemExit("DEPOSIT_WALLET is not set in .env. Run 2_deploy_wallet.py and set DEPOSIT_WALLET first.")

if not Web3.is_address(DEPOSIT_WALLET):
    raise SystemExit(
        f"Invalid DEPOSIT_WALLET in .env: {DEPOSIT_WALLET!r}. Expected a 0x-prefixed 42-char hex address."
    )

USDC_E            = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
PUSD              = Web3.to_checksum_address("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB")
COLLATERAL_ONRAMP = Web3.to_checksum_address("0x93070a847efEf7F70739046A929D47a521F5B8ee")
DW                = Web3.to_checksum_address(DEPOSIT_WALLET)

ERC20_ABI = [
    {"name": "balanceOf",  "type": "function", "stateMutability": "view",
     "inputs": [{"name": "account", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "allowance", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "approve",   "type": "function", "stateMutability": "nonpayable",
     "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "outputs": [{"name": "", "type": "bool"}]},
]

# wrap(address _asset, address _to, uint256 _amount)
ONRAMP_ABI = [
    {"name": "wrap", "type": "function", "stateMutability": "nonpayable",
     "inputs": [
         {"name": "_asset",  "type": "address"},
         {"name": "_to",     "type": "address"},
         {"name": "_amount", "type": "uint256"},
     ], "outputs": []},
]

pk      = PRIVATE_KEY if PRIVATE_KEY.startswith("0x") else "0x" + PRIVATE_KEY
w3      = Web3(Web3.HTTPProvider(RPC_URL))
# Polygon is a PoA chain — blocks have oversized extraData that web3.py rejects without this
from web3.middleware import ExtraDataToPOAMiddleware
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
account = w3.eth.account.from_key(pk)
EOA     = account.address

usdc_c   = w3.eth.contract(address=USDC_E,            abi=ERC20_ABI)
pusd_c   = w3.eth.contract(address=PUSD,              abi=ERC20_ABI)
onramp_c = w3.eth.contract(address=COLLATERAL_ONRAMP, abi=ONRAMP_ABI)

usdc_bal    = usdc_c.functions.balanceOf(EOA).call()
pusd_before = pusd_c.functions.balanceOf(DW).call()

print(f"EOA            : {EOA}")
print(f"Deposit wallet : {DW}\n")
print(f"USDC.e (EOA)   : {usdc_bal    / 1e6:.6f}")
print(f"pUSD   (wallet): {pusd_before / 1e6:.6f}")

if usdc_bal == 0:
    print("\n⚠ No USDC.e on EOA — send USDC.e to your EOA first")
    exit(0)

MAX_UINT256 = 2**256 - 1

# Step 1: Approve USDC.e → CollateralOnramp (EOA calls directly)
current_approval = usdc_c.functions.allowance(EOA, COLLATERAL_ONRAMP).call()
if current_approval < usdc_bal:
    nonce   = w3.eth.get_transaction_count(EOA)
    tx      = usdc_c.functions.approve(COLLATERAL_ONRAMP, MAX_UINT256).build_transaction({
        "from": EOA, "nonce": nonce,
    })
    signed  = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"  ✓ USDC.e approved → CollateralOnramp  {tx_hash.hex()}")

# Step 2: Wrap USDC.e → pUSD, recipient = deposit wallet
print(f"\nWrapping {usdc_bal / 1e6:.6f} USDC.e → pUSD into deposit wallet…")
nonce    = w3.eth.get_transaction_count(EOA)
tx       = onramp_c.functions.wrap(USDC_E, DW, usdc_bal).build_transaction({
    "from": EOA, "nonce": nonce,
})
signed   = account.sign_transaction(tx)
wrap_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
w3.eth.wait_for_transaction_receipt(wrap_hash)

pusd_after = pusd_c.functions.balanceOf(DW).call()
print(f"\n✓ Wrap tx: {wrap_hash.hex()}")
print(f"pUSD (wallet) before : {pusd_before / 1e6:.6f}")
print(f"pUSD (wallet) after  : {pusd_after  / 1e6:.6f}  (+{(pusd_after - pusd_before) / 1e6:.6f}) ✓")
print("\nNext: run 4_allowances.py to approve trading contracts from the deposit wallet")
