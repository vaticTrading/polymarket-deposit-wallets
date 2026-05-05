"""Quick diagnostic: find what CTF token balances the deposit wallet holds."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from web3 import Web3

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DW  = Web3.to_checksum_address(os.environ["DEPOSIT_WALLET"])
CTF = Web3.to_checksum_address("0x4D97DCd97eC945f40cF65F87097ACe5EA0476045")
RPC = os.environ.get("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")
w3  = Web3(Web3.HTTPProvider(RPC))

ERC1155_ABI = [
    {"name": "balanceOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "account", "type": "address"}, {"name": "id", "type": "uint256"}],
     "outputs": [{"name": "", "type": "uint256"}]},
]
ctf_c = w3.eth.contract(address=CTF, abi=ERC1155_ABI)

# Check the token IDs we expect
YES = 105267568073659068217311993901927962476298440625043565106676088842803600775810
NO  = 91863162118308663069733924043159186005106558783397508844234610341221325526200

print(f"Deposit wallet : {DW}")
print(f"CTF contract   : {CTF}")
print()
yes_bal = ctf_c.functions.balanceOf(DW, YES).call()
no_bal  = ctf_c.functions.balanceOf(DW, NO).call()
print(f"YES ({str(YES)[:20]}…) : {yes_bal} raw  ({yes_bal/1e6:.6f})")
print(f"NO  ({str(NO)[:20]}…) : {no_bal}  raw  ({no_bal/1e6:.6f})")

# Also scan the split transaction logs to find actual minted IDs
# Look at recent TransferBatch logs from CTF to the deposit wallet
print("\nChecking recent blocks for TransferBatch to deposit wallet...")
TRANSFER_BATCH_TOPIC = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"
from eth_abi import decode as abi_decode

latest = w3.eth.block_number
logs = w3.eth.get_logs({
    "address": CTF,
    "topics": [TRANSFER_BATCH_TOPIC],
    "fromBlock": latest - 500,
    "toBlock": "latest",
})
print(f"Found {len(logs)} TransferBatch log(s) in last 500 blocks")
for log in logs:
    topics = log["topics"]
    # topics[3] = to address (padded)
    to_addr = "0x" + topics[3].hex()[-40:]
    if to_addr.lower() == DW.lower():
        ids, amounts = abi_decode(["uint256[]", "uint256[]"], bytes(log["data"]))
        print(f"\nTransferBatch TO deposit wallet in tx {log['transactionHash'].hex()}")
        for tid, amt in zip(ids, amounts):
            print(f"  tokenId={tid}  amount={amt}  ({amt/1e6:.6f})")
