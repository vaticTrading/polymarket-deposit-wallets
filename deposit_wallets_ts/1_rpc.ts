/**
 * 1_rpc.ts — Check EOA + deposit wallet balances on Polygon.
 *
 * Run: npx tsx 1_rpc.ts
 * Shows: EOA MATIC + USDC.e balance, deposit wallet pUSD balance.
 */

import "dotenv/config";
import { createPublicClient, http, formatUnits, getAddress, Hex } from "viem";
import { polygon } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";

const RPC_URL        = process.env.POLYGON_RPC_URL ?? "https://polygon-bor-rpc.publicnode.com";
const DEPOSIT_WALLET = process.env.DEPOSIT_WALLET;

const pk      = process.env.PRIVATE_KEY as Hex;
const account = privateKeyToAccount(pk.startsWith("0x") ? pk : `0x${pk}`);
const EOA     = account.address;

const USDC_E = getAddress("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174");
const PUSD   = getAddress("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB");

const ERC20_ABI = [{
    name: "balanceOf", type: "function", stateMutability: "view",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
}] as const;

const client = createPublicClient({ chain: polygon, transport: http(RPC_URL) });

const maticBal = await client.getBalance({ address: EOA });
const usdcBal  = await client.readContract({ address: USDC_E, abi: ERC20_ABI, functionName: "balanceOf", args: [EOA] });

console.log(`EOA              : ${EOA}`);
console.log(`MATIC balance    : ${formatUnits(maticBal, 18)}`);
console.log(`USDC.e balance   : ${formatUnits(usdcBal, 6)}`);

if (DEPOSIT_WALLET) {
    const dw       = getAddress(DEPOSIT_WALLET);
    const pusdBal  = await client.readContract({ address: PUSD,   abi: ERC20_ABI, functionName: "balanceOf", args: [dw] });
    const usdcDwBal = await client.readContract({ address: USDC_E, abi: ERC20_ABI, functionName: "balanceOf", args: [dw] });
    console.log(`\nDeposit wallet   : ${dw}`);
    console.log(`pUSD balance     : ${formatUnits(pusdBal, 6)}`);
    console.log(`USDC.e balance   : ${formatUnits(usdcDwBal, 6)}`);
} else {
    console.log("\n⚠ DEPOSIT_WALLET not set — run 2_deploy_wallet.ts first");
}
