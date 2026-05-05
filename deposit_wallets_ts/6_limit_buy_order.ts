/**
 * 6_limit_buy_order.ts — GTC BUY 2 ticks below best bid → cancel.
 *
 * Run: npx tsx 6_limit_buy_order.ts
 * Requires: PRIVATE_KEY, DEPOSIT_WALLET, CLOB_V2_BASE_URL, POLYGON_RPC_URL in .env
 */

import "dotenv/config";
import { AssetType, Side, OrderType } from "@polymarket/clob-client-v2";
import { createPublicClient, http, getAddress, formatUnits } from "viem";
import { polygon } from "viem/chains";
import { makeClient, DEPOSIT_WALLET, RPC_URL } from "./_clob.js";

const COND_ID      = "0x7ad403c3508f8e3912940fd1a913f227591145ca0614074208e0b962d5fcc422";
const YES_TOKEN_ID = "16040015440196279900485035793550429453516625694844857319147506590755961451627";

const PUSD = getAddress("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB");
const ERC20_ABI = [{
    name: "balanceOf", type: "function", stateMutability: "view",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
}] as const;

const client = await makeClient();

// Sync pUSD balance to CLOB (BalanceAllowanceParams uses snake_case)
await client.updateBalanceAllowance({ asset_type: AssetType.COLLATERAL });

const publicClient = createPublicClient({ chain: polygon, transport: http(RPC_URL) });
const rawBal  = await publicClient.readContract({ address: PUSD, abi: ERC20_ABI, functionName: "balanceOf", args: [getAddress(DEPOSIT_WALLET)] });
const balance = Number(formatUnits(rawBal, 6));
if (balance < 1) { console.error("⚠ Not enough pUSD in deposit wallet"); process.exit(1); }

const info     = await client.getClobMarketInfo(COND_ID);
const tickSize = String(info.mts ?? "0.01") as "0.1" | "0.01" | "0.001" | "0.0001";
const negRisk  = info.nr ?? false;

const book = await client.getOrderBook(YES_TOKEN_ID);
const bids = ((book as any).bids ?? []).sort((a: any, b: any) => parseFloat(b.price) - parseFloat(a.price));
if (bids.length < 3) { console.error("Not enough bid levels"); process.exit(1); }

const price = parseFloat(bids[2].price);
const size  = Math.round(((balance - 1) / price) * 100) / 100;

console.log(`Balance  : $${balance.toFixed(4)} pUSD`);
console.log(`Placing GTC BUY: ${size} shares @ $${price}`);

const resp = await client.createAndPostOrder(
    { tokenID: YES_TOKEN_ID, price, size, side: Side.BUY },
    { tickSize, negRisk },
    OrderType.GTC,
);
const orderId = (resp as any).orderID;
const status  = (resp as any).status;
console.log(`\n✓ Order placed : ${orderId}  status: ${status}`);

// Cancel (cleanup) — cancelOrder takes { orderID }
const cancel   = await client.cancelOrder({ orderID: orderId });
const canceled = (cancel as any).canceled ?? [];
if (canceled.includes(orderId)) {
    console.log(`✓ Cancelled    : ${orderId}`);
} else {
    console.log(`Cancel response: ${JSON.stringify(cancel)}`);
}
