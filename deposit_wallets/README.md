# Deposit Wallet Trading Flow (Python)

This repository demonstrates the end-to-end migration flow for new API users who trade on Polymarket using **deposit wallets**.

## Why this exists

Deposit wallets replace proxy/Safe onboarding for new API users. Trading orders from deposit wallets use:

- `signatureType = 3` (`POLY_1271`) for CLOB orders
- ERC-1271 validation on the wallet
- relayer `WALLET-CREATE` and `WALLET` transaction paths

Documentation index: <https://docs.polymarket.com/llms.txt>
Trading quickstart: <https://docs.polymarket.com/trading/quickstart>
Clients and SDKs: <https://docs.polymarket.com/api-reference/clients-sdks>

## Flow scripts

Run the scripts in numeric order:

1. `1_rpc.py` - RPC connectivity and signer sanity checks
2. `2_deploy_wallet.py` - Deploy/derive deposit wallet through relayer
3. `3_wrap.py` - Fund/wrap collateral into wallet flow
4. `4_allowances.py` - Set approvals from the deposit wallet
5. `5_init_clob.py` - Initialize CLOB client with deposit wallet settings
6. `6_limit_buy_order.py` - Place a limit buy order
7. `7_market_buy_order.py` - Place a market buy order
8. `8_market_sell_order.py` - Place a market sell order
9. `9_limit_sell.py` - Place a limit sell order
10. `10_split.py` - Split conditional tokens
11. `11_merge.py` - Merge conditional tokens
12. `12_offramp.py` - Offramp/withdraw workflow

Utility scripts:

- `_check_tokens.py`
- `_relayer.py`

## Requirements

- Python 3.10+
- Builder relayer + CLOB credentials
- Polygon RPC URL

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment

Copy and fill the local env file:

```bash
cp .env.example .env
```

Expected values include API credentials, private key, relayer URL, CLOB URL, chain ID, token IDs, and contract addresses.

## Running

Example:

```bash
python 1_rpc.py
python 2_deploy_wallet.py
```

Follow the migration checklist during testing:

- Deploy with `WALLET-CREATE`
- Fund the deposit wallet (not just owner EOA)
- Approve spenders via `WALLET` batch
- Refresh CLOB balance allowance with `signature_type = 3`
- Post orders with `maker` and `signer` set to the deposit wallet

## Notes

- Existing proxy/Safe users are out of scope for this repo.
- The integration code stays the same between preprod and prod; only endpoint URLs change.
