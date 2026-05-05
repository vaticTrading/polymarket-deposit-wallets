/**
 * 10_split.ts — Split deposit wallet's pUSD → YES + NO tokens via WALLET batch.
 *
 * Run: npx tsx 10_split.ts
 * Uses a non-NegRisk binary market and calls CTF.splitPosition directly.
 * Market: Will bitcoin hit $1M before GTA VI?
 */

import "dotenv/config";
import { encodeFunctionData, getAddress, decodeAbiParameters } from "viem";
import { createPublicClient, http } from "viem";
import { polygon } from "viem/chains";
import type { DepositWalletCall } from "./_relayer.js";
import { makeRelayer, walletBatch } from "./_relayer.js";

const DEPOSIT_WALLET = getAddress(process.env.DEPOSIT_WALLET!);
const RPC_URL        = process.env.POLYGON_RPC_URL ?? "https://polygon-bor-rpc.publicnode.com";

const COND_ID      = "0xbb57ccf5853a85487bc3d83d04d669310d28c6c810758953b9d9b91d1aee89d2";
const YES_TOKEN_ID = 59096053829818928821715698848500684407651115475127977519494489878858719753099n;
const NO_TOKEN_ID  = 108204443821004451954683085420839421584079841084134544675147755750632966106254n;

const PUSD         = getAddress("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB");
const CTF          = getAddress("0x4D97DCd97eC945f40cF65F87097ACe5EA0476045");
const BYTES32_ZERO = "0x0000000000000000000000000000000000000000000000000000000000000000" as const;
const TRANSFER_BATCH_TOPIC = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb";

const ERC20_ABI = [{
    name: "balanceOf", type: "function", stateMutability: "view",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
}] as const;

const SPLIT_ABI = [{
    name: "splitPosition", type: "function", stateMutability: "nonpayable",
    inputs: [
        { name: "collateralToken",    type: "address" },
        { name: "parentCollectionId", type: "bytes32" },
        { name: "conditionId",        type: "bytes32" },
        { name: "partition",          type: "uint256[]" },
        { name: "amount",             type: "uint256" },
    ],
    outputs: [],
}] as const;

const publicClient = createPublicClient({ chain: polygon, transport: http(RPC_URL) });
const rawBal     = await publicClient.readContract({ address: PUSD, abi: ERC20_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET] });
const splitUnits = rawBal > 1_000_000n ? rawBal - 1_000_000n : 0n;

console.log(`Deposit wallet : ${DEPOSIT_WALLET}`);
console.log(`Market         : Will bitcoin hit $1M before GTA VI? (non-NegRisk)`);
console.log(`Condition ID   : ${COND_ID}`);
console.log(`pUSD balance   : ${(Number(rawBal) / 1e6).toFixed(6)}`);

if (splitUnits === 0n) { console.error("⚠ Not enough pUSD (need > $1)"); process.exit(1); }

const condBytes = `0x${COND_ID.slice(2)}` as `0x${string}`;
console.log(`\nSplitting ${(Number(splitUnits) / 1e6).toFixed(6)} pUSD → YES + NO…`);

const splitData = encodeFunctionData({
    abi: SPLIT_ABI,
    functionName: "splitPosition",
    args: [PUSD, BYTES32_ZERO, condBytes, [1n, 2n], splitUnits],
});

const calls: DepositWalletCall[] = [{ target: CTF, value: "0", data: splitData }];
const relayer = makeRelayer();
const res = await walletBatch(relayer, DEPOSIT_WALLET, calls);

console.log(`\n✓ Split confirmed`);
console.log(`Transaction hash : ${res?.transactionHash}`);

// Parse minted token IDs from TransferBatch log (best effort)
try {
    const txHash = res?.transactionHash as `0x${string}` | undefined;
    if (txHash) {
        const receipt = await publicClient.getTransactionReceipt({ hash: txHash });
        for (const log of receipt.logs) {
            if (log.address.toLowerCase() === CTF.toLowerCase() && log.topics[0] === TRANSFER_BATCH_TOPIC) {
                const [ids, amounts] = decodeAbiParameters(
                    [{ type: "uint256[]" }, { type: "uint256[]" }],
                    log.data,
                );
                for (let i = 0; i < ids.length; i++) {
                    const label = ids[i] === YES_TOKEN_ID ? "YES" : ids[i] === NO_TOKEN_ID ? "NO " : `[${i}]`;
                    console.log(`  ${label} tokenId=${ids[i]}  amount=${(Number(amounts[i]) / 1e6).toFixed(6)}`);
                }
            }
        }
    }
} catch (e) {
    console.log(`(Could not parse token IDs from receipt: ${e})`);
}

console.log(`\nYES token: ${YES_TOKEN_ID}`);
console.log(`NO  token: ${NO_TOKEN_ID}`);
console.log("\nRun 11_merge.ts to convert YES+NO back to pUSD");
