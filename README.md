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

## Manual upload to GitHub (no CLI auth needed)

### Option A: Upload files directly in GitHub web UI

1. Create a new empty GitHub repository in your browser.
2. Open the new repo page.
3. Click **Add file** -> **Upload files**.
4. Drag and drop everything inside this folder:
   - `deposit_wallets/`
   - `deposit_wallets_ts/`
   - `.gitignore`
   - `README.md`
5. Add commit message: `Initial deposit wallet examples (py + ts)`.
6. Click **Commit changes**.

### Option B: Upload a ZIP from browser

1. Zip this folder (`deposit_wallets_combined_repo`).
2. In GitHub, open your new empty repo.
3. Use **Add file** -> **Upload files** and drop the extracted files (or upload file sets in batches).
4. Commit from the web UI.

## Notes

- Do not upload real private keys or `.env` values.
- Existing proxy/Safe users are not modified by this demo; this is the deposit wallet path for new API users.
