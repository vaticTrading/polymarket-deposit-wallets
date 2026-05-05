/**
 * 5_init_clob.ts — Init ClobClient with POLY_1271 (deposit wallet), derive API key,
 *                  fetch market info + order book.
 *
 * Run: npx tsx 5_init_clob.ts
 * Requires: PRIVATE_KEY, DEPOSIT_WALLET, CLOB_V2_BASE_URL in .env
 */

import "dotenv/config";
import { makeClient } from "./_clob.js";

// JD Vance 2028
const COND_ID      = "0x7ad403c3508f8e3912940fd1a913f227591145ca0614074208e0b962d5fcc422";
const YES_TOKEN_ID = "16040015440196279900485035793550429453516625694844857319147506590755961451627";

const client = await makeClient();

const info = await client.getClobMarketInfo(COND_ID);
console.log(`Market info : tick=${info.mts}  negRisk=${info.nr}  tokens=${JSON.stringify(info.t?.map((t: any) => t.o))}`);

const book = await client.getOrderBook(YES_TOKEN_ID);
const bids = ((book as any).bids ?? []).sort((a: any, b: any) => parseFloat(b.price) - parseFloat(a.price));
const asks = ((book as any).asks ?? []).sort((a: any, b: any) => parseFloat(a.price) - parseFloat(b.price));

console.log(`\nOrder book (YES):`);
console.log(`  Best bid : ${bids[0]?.price ?? "n/a"}  size=${bids[0]?.size ?? "n/a"}`);
console.log(`  Best ask : ${asks[0]?.price ?? "n/a"}  size=${asks[0]?.size ?? "n/a"}`);
console.log(`\n✓ CLOB client initialised successfully`);
