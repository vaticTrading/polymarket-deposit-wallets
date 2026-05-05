/**
 * 3_wrap.ts — Wrap EOA's USDC.e → pUSD, minted directly into the deposit wallet.
 *
 * Run: npx tsx 3_wrap.ts
 * EOA calls CollateralOnramp directly (no relayer). Wraps full USDC.e balance.
 * Skips approve if allowance is already sufficient.
 */

import "dotenv/config";
import {
    createPublicClient,
    createWalletClient,
    http,
    getAddress,
    formatUnits,
    maxUint256,
    Hex,
} from "viem";
import { polygon } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";

const RPC_URL        = process.env.POLYGON_RPC_URL ?? "https://polygon-bor-rpc.publicnode.com";
const DEPOSIT_WALLET = getAddress(process.env.DEPOSIT_WALLET!);

const pk      = process.env.PRIVATE_KEY as Hex;
const account = privateKeyToAccount(pk.startsWith("0x") ? pk : `0x${pk}`);
const EOA     = account.address;

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
        name: "allowance", type: "function", stateMutability: "view",
        inputs: [{ name: "owner", type: "address" }, { name: "spender", type: "address" }],
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
const walletClient = createWalletClient({ account, chain: polygon, transport: http(RPC_URL) });

const usdcBal    = await publicClient.readContract({ address: USDC_E, abi: ERC20_ABI, functionName: "balanceOf", args: [EOA] });
const pusdBefore = await publicClient.readContract({ address: PUSD,   abi: ERC20_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET] });

console.log(`EOA            : ${EOA}`);
console.log(`Deposit wallet : ${DEPOSIT_WALLET}\n`);
console.log(`USDC.e (EOA)   : ${formatUnits(usdcBal, 6)}`);
console.log(`pUSD   (wallet): ${formatUnits(pusdBefore, 6)}`);

if (usdcBal === 0n) { console.error("\n⚠ No USDC.e on EOA — send USDC.e to your EOA first"); process.exit(0); }

// Step 1: Approve if needed
const allowance = await publicClient.readContract({ address: USDC_E, abi: ERC20_ABI, functionName: "allowance", args: [EOA, ONRAMP] });
if (allowance < usdcBal) {
    console.log("\nApproving USDC.e → CollateralOnramp…");
    const approveTx = await walletClient.writeContract({ address: USDC_E, abi: ERC20_ABI, functionName: "approve", args: [ONRAMP, maxUint256] });
    await publicClient.waitForTransactionReceipt({ hash: approveTx });
    console.log(`  ✓ Approved  ${approveTx}`);
}

// Step 2: Wrap full USDC.e balance → pUSD into deposit wallet
console.log(`\nWrapping ${formatUnits(usdcBal, 6)} USDC.e → pUSD into deposit wallet…`);
const wrapTx = await walletClient.writeContract({ address: ONRAMP, abi: ONRAMP_ABI, functionName: "wrap", args: [USDC_E, DEPOSIT_WALLET, usdcBal] });
await publicClient.waitForTransactionReceipt({ hash: wrapTx });

const pusdAfter = await publicClient.readContract({ address: PUSD, abi: ERC20_ABI, functionName: "balanceOf", args: [DEPOSIT_WALLET] });
console.log(`\n✓ Wrap tx: ${wrapTx}`);
console.log(`pUSD (wallet) before : ${formatUnits(pusdBefore, 6)}`);
console.log(`pUSD (wallet) after  : ${formatUnits(pusdAfter, 6)}  (+${formatUnits(pusdAfter - pusdBefore, 6)}) ✓`);
