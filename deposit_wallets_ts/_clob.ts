/**
 * _clob.ts — Shared helper: init an authenticated ClobClient for the deposit wallet.
 */

import "dotenv/config";
import { ClobClient, Chain, SignatureTypeV2 } from "@polymarket/clob-client-v2";
import { createWalletClient, http, Hex } from "viem";
import { polygon } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";

export const HOST           = process.env.CLOB_V2_BASE_URL ?? "https://clob.polymarket.com";
export const PRIVATE_KEY    = process.env.PRIVATE_KEY!;
export const DEPOSIT_WALLET = process.env.DEPOSIT_WALLET!;
export const RPC_URL        = process.env.POLYGON_RPC_URL ?? "https://polygon-bor-rpc.publicnode.com";

function makeSigner() {
    const pk      = PRIVATE_KEY as Hex;
    const account = privateKeyToAccount(pk.startsWith("0x") ? pk : `0x${pk}`);
    return createWalletClient({ account, chain: polygon, transport: http(RPC_URL) });
}

export async function makeClient(): Promise<ClobClient> {
    const signer     = makeSigner();
    const tempClient = new ClobClient({
        host:          HOST,
        chain:         Chain.POLYGON,
        signer,
        signatureType: SignatureTypeV2.POLY_1271,
        funderAddress: DEPOSIT_WALLET,
    });
    const creds  = await tempClient.createOrDeriveApiKey();
    const client = new ClobClient({
        host:          HOST,
        chain:         Chain.POLYGON,
        signer,
        creds,
        signatureType: SignatureTypeV2.POLY_1271,
        funderAddress: DEPOSIT_WALLET,
    });
    console.log(`Deposit wallet : ${DEPOSIT_WALLET}  |  API key: ${creds.key} ✓\n`);
    return client;
}

/** GCD for FOK precision constraint. */
function gcd(a: bigint, b: bigint): bigint {
    while (b) { [a, b] = [b, a % b]; }
    return a;
}

/**
 * Largest valid GTC/FOK sell size ≤ holdings where:
 *   size * price has ≤ 2 decimal places  (pUSD constraint)
 *   size itself  has ≤ 5 decimal places  (shares constraint)
 */
export function validSize(holdings: number, price: number): number {
    const priceStr = price.toFixed(10).replace(/0+$/, "");
    const decimals = priceStr.includes(".") ? priceStr.split(".")[1].length : 0;
    const q   = BigInt(10 ** decimals);
    const p   = BigInt(Math.round(price * Number(q)));
    const mod = q * 1000n;
    const step = Number(mod / gcd(p, mod)) / 1e5;
    const n    = Math.floor(holdings / step);
    return Math.round(n * step * 1e5) / 1e5;
}

/**
 * Largest valid FOK market BUY size ≤ budget (in pUSD) at given price.
 */
export function fokBuySize(budget: number, price: number): number {
    const priceStr = price.toFixed(10).replace(/0+$/, "");
    const decimals = priceStr.includes(".") ? priceStr.split(".")[1].length : 0;
    const q   = BigInt(10 ** decimals);
    const p   = BigInt(Math.round(price * Number(q)));
    const mod = q * 1000n;
    const step = Number(mod / gcd(p, mod)) / 1e5;
    const n    = Math.floor(budget / (price * step));
    return Math.round(n * step * 1e5) / 1e5;
}
