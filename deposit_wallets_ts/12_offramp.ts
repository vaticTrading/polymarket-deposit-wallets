/**
 * 12_offramp.ts — Unwrap pUSD → USDC.e back to EOA via WALLET batch.
 *
 * Run: npx tsx 12_offramp.ts
 * CollateralOfframp.unwrap() is called from the deposit wallet via WALLET batch.
 * Approval for OFFRAMP was set in 4_allowances.ts.
 */

import "dotenv/config";
import { encodeFunctionData, getAddress } from "viem";
import { createPublicClient, http, formatUnits } from "viem";
import { polygon } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";
import type { DepositWalletCall } from "./_relayer.js";
import { makeRelayer, walletBatch } from "./_relayer.js";

const DEPOSIT_WALLET = getAddress(process.env.DEPOSIT_WALLET!);
const RPC_URL        = process.env.POLYGON_RPC_URL ?? "https://polygon-bor-rpc.publicnode.com";

const pk      = process.env.PRIVATE_KEY as `0x${string}`;
const account = privateKeyToAccount(pk.startsWith("0x") ? pk : `0x${pk}`);
const EOA     = account.address;

const PUSD    = getAddress("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB");
const USDC_E  = getAddress("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174");
const OFFRAMP = getAddress("0x2957922Eb93258b93368531d39fAcCA3B4dC5854");

const ERC20_ABI = [{
    name: "balanceOf", type: "function", stateMutability: "view",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
}] as const;

const OFFRAMP_ABI = [{
    name: "unwrap", type: "function", stateMutability: "nonpayable",
    inputs: [
        { name: "token",     type: "address" },
        { name: "recipient", type: "address" },
        { name: "amount",    type: "uint256" },
    ],
    outputs: [],
}] as const;

const publicClient = createPublicClient({ chain: polygon, transport: http(RPC_URL) });
const pusdBal   = await publicClient.readContract({ address: PUSD, abi: ERC20_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET] });
const unwrapAmt = pusdBal;

console.log(`Deposit wallet : ${DEPOSIT_WALLET}`);
console.log(`EOA            : ${EOA}`);
console.log(`pUSD balance   : ${formatUnits(pusdBal, 6)}`);

if (unwrapAmt === 0n) { console.error("⚠ No pUSD in deposit wallet"); process.exit(1); }

console.log(`Unwrapping     : ${formatUnits(unwrapAmt, 6)} pUSD → USDC.e to EOA…`);

const unwrapData = encodeFunctionData({
    abi: OFFRAMP_ABI,
    functionName: "unwrap",
    args: [USDC_E, EOA, unwrapAmt],
});

const calls: DepositWalletCall[] = [{ target: OFFRAMP, value: "0", data: unwrapData }];
const relayer = makeRelayer();
const res = await walletBatch(relayer, DEPOSIT_WALLET, calls);

const usdcAfter = await publicClient.readContract({ address: USDC_E, abi: ERC20_ABI, functionName: "balanceOf", args: [EOA] });

console.log(`\n✓ Offramp confirmed`);
console.log(`Transaction hash   : ${res?.transactionHash}`);
console.log(`EOA USDC.e balance : ${formatUnits(usdcAfter, 6)} ✓`);
