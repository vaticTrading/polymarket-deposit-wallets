/**
 * 4_allowances.ts — Set all trading approvals from the deposit wallet via WALLET batch.
 *
 * Run: npx tsx 4_allowances.ts
 * Approvals granted:
 *   pUSD ERC-20 → CTF, CTF_EX, NR_EX, NR_ADPT, OFFRAMP
 *   CTF ERC-1155 setApprovalForAll → CTF_EX, NR_EX, NR_ADPT
 * Excluded (relayer blocks): CTF_ADPT, NR_CTF_ADPT
 */

import "dotenv/config";
import { encodeFunctionData, getAddress, maxUint256 } from "viem";
import type { DepositWalletCall } from "./_relayer.js";
import { makeRelayer, walletBatch } from "./_relayer.js";

const DEPOSIT_WALLET = getAddress(process.env.DEPOSIT_WALLET!);

const PUSD    = getAddress("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB");
const CTF     = getAddress("0x4D97DCd97eC945f40cF65F87097ACe5EA0476045");
const CTF_EX  = getAddress("0xE111180000d2663C0091e4f400237545B87B996B");
const NR_EX   = getAddress("0xe2222d279d744050d28e00520010520000310F59");
const NR_ADPT = getAddress("0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296");
const OFFRAMP = getAddress("0x2957922Eb93258b93368531d39fAcCA3B4dC5854");

const ERC20_APPROVE_ABI = [{
    name: "approve", type: "function", stateMutability: "nonpayable",
    inputs: [{ name: "spender", type: "address" }, { name: "amount", type: "uint256" }],
    outputs: [{ name: "", type: "bool" }],
}] as const;

const ERC1155_APPROVE_ABI = [{
    name: "setApprovalForAll", type: "function", stateMutability: "nonpayable",
    inputs: [{ name: "operator", type: "address" }, { name: "approved", type: "bool" }],
    outputs: [],
}] as const;

function erc20Approve(token: `0x${string}`, spender: `0x${string}`): DepositWalletCall {
    return {
        target: token,
        value: "0",
        data: encodeFunctionData({ abi: ERC20_APPROVE_ABI, functionName: "approve", args: [spender, maxUint256] }),
    };
}

function erc1155Approve(token: `0x${string}`, operator: `0x${string}`): DepositWalletCall {
    return {
        target: token,
        value: "0",
        data: encodeFunctionData({ abi: ERC1155_APPROVE_ABI, functionName: "setApprovalForAll", args: [operator, true] }),
    };
}

const calls: DepositWalletCall[] = [
    // pUSD approvals
    erc20Approve(PUSD, CTF),
    erc20Approve(PUSD, CTF_EX),
    erc20Approve(PUSD, NR_EX),
    erc20Approve(PUSD, NR_ADPT),
    erc20Approve(PUSD, OFFRAMP),
    // CTF ERC-1155 approvals
    erc1155Approve(CTF, CTF_EX),
    erc1155Approve(CTF, NR_EX),
    erc1155Approve(CTF, NR_ADPT),
];

console.log(`Deposit wallet : ${DEPOSIT_WALLET}`);
console.log(`Submitting ${calls.length} approval(s) via WALLET batch…`);

const relayer = makeRelayer();
const res = await walletBatch(relayer, DEPOSIT_WALLET, calls);

console.log(`\n✓ ${calls.length} approval(s) confirmed`);
console.log(`Transaction hash : ${res?.transactionHash}`);
