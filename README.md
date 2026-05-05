# Deposit Wallet Trading Examples (Python + TypeScript)

This repository bundles both deposit wallet migration demos in one place:

- `deposit_wallets/` (Python)
- `deposit_wallets_ts/` (TypeScript)

It is intended as a practical showcase of how to trade from **deposit wallets** for new API users.

## What this demonstrates

- Deploying deterministic deposit wallets with relayer `WALLET-CREATE`
- Executing wallet batches with relayer `WALLET`
- Funding and approvals from the deposit wallet itself
- Trading on CLOB V2 with `signatureType = 3` (`POLY_1271`)
- Split/merge/offramp helper flows

## Project structure

- `deposit_wallets/`
  - Python scripts `1_...py` to `12_...py`
  - `requirements.txt`
  - local README with script-level details
- `deposit_wallets_ts/`
  - TypeScript scripts `1_...ts` to `12_...ts`
  - `package.json` script aliases
  - local README with script-level details

## Documentation entry points

- Docs index: <https://docs.polymarket.com/llms.txt>
- Trading quickstart: <https://docs.polymarket.com/trading/quickstart>
- Clients and SDKs: <https://docs.polymarket.com/api-reference/clients-sdks>

## Quick run

Python:

```bash
cd deposit_wallets
pip install -r requirements.txt
cp .env.example .env
python 1_rpc.py
```

TypeScript:

```bash
cd deposit_wallets_ts
npm install
cp .env.example .env
npm run 1
```
