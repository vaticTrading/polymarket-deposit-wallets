/**
 * _rescue_usdc.ts — Transfer USDC.e from deposit wallet → EOA via WALLET batch.
 * One-off script to recover USDC.e that was sent to the deposit wallet by mistake.
 */

import "dotenv/config";
import { encodeFunctionData, getAddress, formatUnits } from "viem";
import { createPublicClient, http } from "viem";
import { polygon } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";
import type { DepositWalletCall } from "./_relayer.js";
import { makeRelayer, walletBatch } from "./_relayer.js";

const DEPOSIT_WALLET = getAddress(process.env.DEPOSIT_WALLET!);
const RPC_URL        = process.env.POLYGON_RPC_URL ?? "https://polygon-bor-rpc.publicnode.com";

const pk      = process.env.PRIVATE_KEY as `0x${string}`;
const account = privateKeyToAccount(pk.startsWith("0x") ? pk : `0x${pk}`);
const EOA     = account.address;

const USDC_E = getAddress("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174");

const ERC20_ABI = [
    {
        name: "balanceOf", type: "function", stateMutability: "view",
        inputs: [{ name: "account", type: "address" }],
        outputs: [{ name: "", type: "uint256" }],
    },
    {
        name: "transfer", type: "function", stateMutability: "nonpayable",
        inputs: [{ name: "to", type: "address" }, { name: "amount", type: "uint256" }],
        outputs: [{ name: "", type: "bool" }],
    },
] as const;

const publicClient = createPublicClient({ chain: polygon, transport: http(RPC_URL) });
const usdcBal = await publicClient.readContract({ address: USDC_E, abi: ERC20_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET] });

console.log(`Deposit wallet : ${DEPOSIT_WALLET}`);
console.log(`EOA            : ${EOA}`);
console.log(`USDC.e in wallet : ${formatUnits(usdcBal, 6)}`);

if (usdcBal === 0n) { console.error("⚠ No USDC.e in deposit wallet"); process.exit(1); }

console.log(`\nTransferring ${formatUnits(usdcBal, 6)} USDC.e → EOA via WALLET batch…`);

const transferData = encodeFunctionData({
    abi: ERC20_ABI,
    functionName: "transfer",
    args: [EOA, usdcBal],
});

const calls: DepositWalletCall[] = [{ target: USDC_E, value: "0", data: transferData }];
const relayer = makeRelayer();
const res = await walletBatch(relayer, DEPOSIT_WALLET, calls);

const usdcAfter = await publicClient.readContract({ address: USDC_E, abi: ERC20_ABI, functionName: "balanceOf", args: [EOA] });

console.log(`\n✓ Transfer confirmed`);
console.log(`Transaction hash     : ${res?.transactionHash}`);
console.log(`EOA USDC.e balance   : ${formatUnits(usdcAfter, 6)} ✓`);
