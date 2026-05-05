# Deposit Wallet Trading Flow (TypeScript)

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

1. `1_rpc.ts` - RPC connectivity and signer sanity checks
2. `2_deploy_wallet.ts` - Deploy/derive deposit wallet through relayer
3. `3_wrap.ts` - Fund/wrap collateral into wallet flow
4. `4_allowances.ts` - Set approvals from the deposit wallet
5. `5_init_clob.ts` - Initialize CLOB client with deposit wallet settings
6. `6_limit_buy_order.ts` - Place a limit buy order
7. `7_market_buy_order.ts` - Place a market buy order
8. `8_market_sell_order.ts` - Place a market sell order
9. `9_limit_sell.ts` - Place a limit sell order
10. `10_split.ts` - Split conditional tokens
11. `11_merge.ts` - Merge conditional tokens
12. `12_offramp.ts` - Offramp/withdraw workflow

Utility scripts:

- `_clob.ts`
- `_relayer.ts`
- `_rescue_usdc.ts`
- `_wrap_from_wallet.ts`

## Requirements

- Node.js 20+
- Builder relayer + CLOB credentials
- Polygon RPC URL

Install dependencies:

```bash
npm install
```

## Environment

Copy and fill the local env file:

```bash
cp .env.example .env
```

Expected values include API credentials, private key, relayer URL, CLOB URL, chain ID, token IDs, and contract addresses.

## Running

You can run directly with npm script aliases:

```bash
npm run 1
npm run 2
```

Or with tsx:

```bash
npx tsx 1_rpc.ts
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
