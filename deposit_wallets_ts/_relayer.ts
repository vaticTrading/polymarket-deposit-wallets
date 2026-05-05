import "dotenv/config";
import { RelayClient } from "@polymarket/builder-relayer-client";
import type { DepositWalletCall } from "@polymarket/builder-relayer-client";
import { BuilderConfig } from "@polymarket/builder-signing-sdk";
import { createWalletClient, Hex, http } from "viem";
import { polygon } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";

export const RELAYER_URL = process.env.RELAYER_URL ?? "https://relayer-v2.polymarket.com/";
export const RPC_URL     = process.env.POLYGON_RPC_URL ?? "https://polygon-bor-rpc.publicnode.com";
export const CHAIN_ID    = 137;

export function makeRelayer(): RelayClient {
    const pk = process.env.PRIVATE_KEY as Hex;
    const account = privateKeyToAccount(pk.startsWith("0x") ? pk : `0x${pk}`);
    const wallet = createWalletClient({
        account,
        chain: polygon,
        transport: http(RPC_URL),
    });
    const builderConfig = new BuilderConfig({
        localBuilderCreds: {
            key:        process.env.BUILDER_API_KEY!,
            secret:     process.env.BUILDER_SECRET!,
            passphrase: process.env.BUILDER_PASSPHRASE!,
        },
    });
    return new RelayClient(RELAYER_URL, CHAIN_ID, wallet, 
        // builderConfig
    );
}

export async function walletBatch(
    relayer: RelayClient,
    depositWallet: string,
    calls: DepositWalletCall[],
) {
    const deadline = Math.floor(Date.now() / 1000 + 600).toString();
    const resp = await relayer.executeDepositWalletBatch(calls, depositWallet, deadline);
    return resp.wait();
}

export type { DepositWalletCall };
