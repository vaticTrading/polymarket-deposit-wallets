/**
 * 7_market_buy_order.ts — FOK market BUY at best ask + 1 tick (deposit wallet).
 *
 * Run: npx tsx 7_market_buy_order.ts
 * FOK: executes immediately at the best available price or cancels.
 */

import "dotenv/config";
import { AssetType, Side, OrderType } from "@polymarket/clob-client-v2";
import { createPublicClient, http, getAddress, formatUnits } from "viem";
import { polygon } from "viem/chains";
import { makeClient, DEPOSIT_WALLET, RPC_URL, fokBuySize } from "./_clob.js";

const COND_ID      = "0x7ad403c3508f8e3912940fd1a913f227591145ca0614074208e0b962d5fcc422";
const YES_TOKEN_ID = "16040015440196279900485035793550429453516625694844857319147506590755961451627";

const PUSD = getAddress("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB");
const ERC20_ABI = [{
    name: "balanceOf", type: "function", stateMutability: "view",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
}] as const;

const client = await makeClient();

await client.updateBalanceAllowance({ asset_type: AssetType.COLLATERAL });

const publicClient = createPublicClient({ chain: polygon, transport: http(RPC_URL) });
const rawBal  = await publicClient.readContract({ address: PUSD, abi: ERC20_ABI, functionName: "balanceOf", args: [getAddress(DEPOSIT_WALLET)] });
const balance = Number(formatUnits(rawBal, 6));
if (balance < 1) { console.error("⚠ Not enough pUSD in deposit wallet"); process.exit(1); }

const info     = await client.getClobMarketInfo(COND_ID);
const tickSize = String(info.mts ?? "0.01") as "0.1" | "0.01" | "0.001" | "0.0001";
const tick     = parseFloat(tickSize);
const negRisk  = info.nr ?? false;

const book = await client.getOrderBook(YES_TOKEN_ID);
const asks = ((book as any).asks ?? []).sort((a: any, b: any) => parseFloat(a.price) - parseFloat(b.price));
if (!asks.length) { console.error("No asks — cannot market buy"); process.exit(1); }

// 1 tick above best ask to guarantee fill
const price = Math.round((parseFloat(asks[0].price) + tick) * 10000) / 10000;
const size  = fokBuySize(balance, price);  // shares
if (size <= 0) { console.error(`⚠ No valid size for price=${price}`); process.exit(1); }

// For market BUY: amount = pUSD to spend
const amount = Math.round(size * price * 100) / 100;

console.log(`Balance  : $${balance.toFixed(4)} pUSD`);
console.log(`Placing FOK market BUY: ${size} shares @ $${price}  (best ask: $${asks[0].price})`);

const resp = await client.createAndPostMarketOrder(
    { tokenID: YES_TOKEN_ID, price, amount, side: Side.BUY },
    { tickSize, negRisk },
    OrderType.FOK,
);
const orderId = (resp as any).orderID;
const status  = (resp as any).status;
console.log(`\n✓ Order result : ${orderId}  status: ${status}`);
