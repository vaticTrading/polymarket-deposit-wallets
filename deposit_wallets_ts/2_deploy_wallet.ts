/**
 * 2_deploy_wallet.ts — Derive + deploy the deposit wallet for your EOA.
 *
 * Run: npx tsx 2_deploy_wallet.ts
 * After success: copy the printed address into .env as DEPOSIT_WALLET=0x...
 */

import "dotenv/config";
import { makeRelayer } from "./_relayer.js";

const relayer = makeRelayer();

const expected = await relayer.deriveDepositWalletAddress();
console.log(`Expected deposit wallet : ${expected}`);
console.log(`Deploying…`);

const resp = await relayer.deployDepositWallet();
const res  = await resp.wait();

console.log(`\n✓ Deploy confirmed`);
console.log(`Transaction hash : ${res?.transactionHash}`);
console.log(`\nAdd to .env:\nDEPOSIT_WALLET=${expected}`);
