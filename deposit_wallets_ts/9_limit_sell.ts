/**
 * 9_limit_sell.ts — GTC SELL YES tokens 2 ticks above best ask → cancel.
 *
 * Run: npx tsx 9_limit_sell.ts
 * Places a limit sell above market so it won't fill, then immediately cancels.
 */

import "dotenv/config";
import { AssetType, Side, OrderType } from "@polymarket/clob-client-v2";
import { createPublicClient, http, getAddress } from "viem";
import { polygon } from "viem/chains";
import { makeClient, DEPOSIT_WALLET, RPC_URL, validSize } from "./_clob.js";

const COND_ID      = "0x7ad403c3508f8e3912940fd1a913f227591145ca0614074208e0b962d5fcc422";
const YES_TOKEN_ID = "16040015440196279900485035793550429453516625694844857319147506590755961451627";

const CTF = getAddress("0x4D97DCd97eC945f40cF65F87097ACe5EA0476045");
const ERC1155_ABI = [{
    name: "balanceOf", type: "function", stateMutability: "view",
    inputs: [{ name: "account", type: "address" }, { name: "id", type: "uint256" }],
    outputs: [{ name: "", type: "uint256" }],
}] as const;

const client = await makeClient();

await client.updateBalanceAllowance({ asset_type: AssetType.CONDITIONAL, token_id: YES_TOKEN_ID });

const publicClient = createPublicClient({ chain: polygon, transport: http(RPC_URL) });
const rawBal   = await publicClient.readContract({ address: CTF, abi: ERC1155_ABI, functionName: "balanceOf", args: [getAddress(DEPOSIT_WALLET), BigInt(YES_TOKEN_ID)] });
const holdings = Number(rawBal) / 1e6;
if (holdings < 0.01) { console.error("⚠ No YES tokens — run 7_market_buy_order.ts first"); process.exit(1); }

const info     = await client.getClobMarketInfo(COND_ID);
const tickSize = String(info.mts ?? "0.01") as "0.1" | "0.01" | "0.001" | "0.0001";
const tick     = parseFloat(tickSize);
const negRisk  = info.nr ?? false;

const book = await client.getOrderBook(YES_TOKEN_ID);
const asks = ((book as any).asks ?? []).sort((a: any, b: any) => parseFloat(a.price) - parseFloat(b.price));
if (!asks.length) { console.error("No asks in book"); process.exit(1); }

// 2 ticks above best ask — won't fill
const price = Math.round((parseFloat(asks[0].price) + 2 * tick) * 10000) / 10000;
const size  = validSize(holdings, price);
if (size <= 0) { console.error(`⚠ No valid size for price=${price}`); process.exit(1); }

console.log(`YES holdings : ${holdings.toFixed(5)} tokens`);
console.log(`Placing GTC SELL: ${size} shares @ $${price}  (best ask: $${asks[0].price})`);

const resp = await client.createAndPostOrder(
    { tokenID: YES_TOKEN_ID, price, size, side: Side.SELL },
    { tickSize, negRisk },
    OrderType.GTC,
);
const orderId = (resp as any).orderID;
const status  = (resp as any).status;
console.log(`\n✓ Order placed : ${orderId}  status: ${status}`);

// Cancel (cleanup)
const cancel   = await client.cancelOrder({ orderID: orderId });
const canceled = (cancel as any).canceled ?? [];
if (canceled.includes(orderId)) {
    console.log(`✓ Cancelled    : ${orderId}`);
} else {
    console.log(`Cancel response: ${JSON.stringify(cancel)}`);
}
