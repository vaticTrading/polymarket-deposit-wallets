/**
 * _wrap_from_wallet.ts — Convert USDC.e sitting in the deposit wallet → pUSD
 *                        in a single WALLET batch (approve + wrap).
 *
 * Run: npx tsx _wrap_from_wallet.ts
 * No EOA involvement — the deposit wallet approves its own USDC.e to the
 * CollateralOnramp and calls wrap(), minting pUSD back to itself.
 */

import "dotenv/config";
import { encodeFunctionData, getAddress, formatUnits, maxUint256 } from "viem";
import { createPublicClient, http } from "viem";
import { polygon } from "viem/chains";
import type { DepositWalletCall } from "./_relayer.js";
import { makeRelayer, walletBatch } from "./_relayer.js";

const DEPOSIT_WALLET = getAddress(process.env.DEPOSIT_WALLET!);
const RPC_URL        = process.env.POLYGON_RPC_URL ?? "https://polygon-bor-rpc.publicnode.com";

const USDC_E = getAddress("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174");
const PUSD   = getAddress("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB");
const ONRAMP = getAddress("0x93070a847efEf7F70739046A929D47a521F5B8ee");

const ERC20_ABI = [
    {
        name: "balanceOf", type: "function", stateMutability: "view",
        inputs: [{ name: "account", type: "address" }],
        outputs: [{ name: "", type: "uint256" }],
    },
    {
        name: "approve", type: "function", stateMutability: "nonpayable",
        inputs: [{ name: "spender", type: "address" }, { name: "amount", type: "uint256" }],
        outputs: [{ name: "", type: "bool" }],
    },
] as const;

const ONRAMP_ABI = [{
    name: "wrap", type: "function", stateMutability: "nonpayable",
    inputs: [
        { name: "_asset",  type: "address" },
        { name: "_to",     type: "address" },
        { name: "_amount", type: "uint256" },
    ],
    outputs: [],
}] as const;

const publicClient = createPublicClient({ chain: polygon, transport: http(RPC_URL) });

const usdcBal    = await publicClient.readContract({ address: USDC_E, abi: ERC20_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET] });
const pusdBefore = await publicClient.readContract({ address: PUSD,   abi: ERC20_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET] });

console.log(`Deposit wallet : ${DEPOSIT_WALLET}`);
console.log(`USDC.e balance : ${formatUnits(usdcBal, 6)}`);
console.log(`pUSD   before  : ${formatUnits(pusdBefore, 6)}`);

if (usdcBal === 0n) { console.error("\n⚠ No USDC.e in deposit wallet"); process.exit(1); }

console.log(`\nSubmitting approve + wrap in single WALLET batch…`);

const calls: DepositWalletCall[] = [
    {
        target: USDC_E,
        value: "0",
        data: encodeFunctionData({ abi: ERC20_ABI, functionName: "approve", args: [ONRAMP, maxUint256] }),
    },
    {
        target: ONRAMP,
        value: "0",
        data: encodeFunctionData({ abi: ONRAMP_ABI, functionName: "wrap", args: [USDC_E, DEPOSIT_WALLET, usdcBal] }),
    },
];

const relayer = makeRelayer();
const res = await walletBatch(relayer, DEPOSIT_WALLET, calls);

const pusdAfter = await publicClient.readContract({ address: PUSD, abi: ERC20_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET] });

console.log(`\n✓ Confirmed`);
console.log(`Transaction hash : ${res?.transactionHash}`);
console.log(`pUSD before      : ${formatUnits(pusdBefore, 6)}`);
console.log(`pUSD after       : ${formatUnits(pusdAfter, 6)}  (+${formatUnits(pusdAfter - pusdBefore, 6)}) ✓`);
