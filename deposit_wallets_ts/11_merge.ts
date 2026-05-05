/**
 * 11_merge.ts — Merge YES + NO tokens back to pUSD via WALLET batch.
 *
 * Run: npx tsx 11_merge.ts
 * Same non-NegRisk binary market as 10_split.ts. Calls CTF.mergePositions directly.
 * Run 10_split.ts first to obtain matching YES + NO balances.
 */

import "dotenv/config";
import { encodeFunctionData, getAddress } from "viem";
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

const ERC20_ABI = [{
    name: "balanceOf", type: "function", stateMutability: "view",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
}] as const;

const ERC1155_ABI = [{
    name: "balanceOf", type: "function", stateMutability: "view",
    inputs: [{ name: "account", type: "address" }, { name: "id", type: "uint256" }],
    outputs: [{ name: "", type: "uint256" }],
}] as const;

const MERGE_ABI = [{
    name: "mergePositions", type: "function", stateMutability: "nonpayable",
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

const yesBal     = await publicClient.readContract({ address: CTF, abi: ERC1155_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET, YES_TOKEN_ID] });
const noBal      = await publicClient.readContract({ address: CTF, abi: ERC1155_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET, NO_TOKEN_ID] });
const pusdBefore = await publicClient.readContract({ address: PUSD, abi: ERC20_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET] });

console.log(`Deposit wallet : ${DEPOSIT_WALLET}`);
console.log(`Market         : Will bitcoin hit $1M before GTA VI? (non-NegRisk)`);
console.log(`Condition ID   : ${COND_ID}`);
console.log(`YES balance    : ${(Number(yesBal) / 1e6).toFixed(6)}`);
console.log(`NO  balance    : ${(Number(noBal)  / 1e6).toFixed(6)}`);
console.log(`pUSD (before)  : ${(Number(pusdBefore) / 1e6).toFixed(6)}`);

const mergeUnits = yesBal < noBal ? yesBal : noBal;
if (mergeUnits === 0n) { console.error("\n⚠ No matching YES/NO pair — run 10_split.ts first"); process.exit(1); }

const condBytes = `0x${COND_ID.slice(2)}` as `0x${string}`;
console.log(`\nMerging ${(Number(mergeUnits) / 1e6).toFixed(6)} YES+NO → pUSD…`);

const mergeData = encodeFunctionData({
    abi: MERGE_ABI,
    functionName: "mergePositions",
    args: [PUSD, BYTES32_ZERO, condBytes, [1n, 2n], mergeUnits],
});

const calls: DepositWalletCall[] = [{ target: CTF, value: "0", data: mergeData }];
const relayer = makeRelayer();
const res = await walletBatch(relayer, DEPOSIT_WALLET, calls);

const pusdAfter = await publicClient.readContract({ address: PUSD, abi: ERC20_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET] });

console.log(`\n✓ Merge confirmed`);
console.log(`Transaction hash : ${res?.transactionHash}`);
console.log(`pUSD (after)     : ${(Number(pusdAfter) / 1e6).toFixed(6)}  (+${((Number(pusdAfter) - Number(pusdBefore)) / 1e6).toFixed(6)}) ✓`);
