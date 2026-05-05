"""
_relayer.py — Shared helper: RelayClient factory + wallet_batch().
Import only — do not run directly.
"""

import os
import time

from py_builder_relayer_client.client import RelayClient
from py_builder_relayer_client.models import DepositWalletCall, TransactionType
from py_builder_signing_sdk.config import BuilderApiKeyCreds, BuilderConfig

RELAYER_URL = os.environ.get("RELAYER_URL", "https://relayer-v2.polymarket.com/")
CHAIN_ID    = int(os.environ.get("CHAIN_ID", "137"))


def make_relayer() -> RelayClient:
    """Build a RelayClient from env vars. Call after load_dotenv()."""
    config = BuilderConfig(
        local_builder_creds=BuilderApiKeyCreds(
            key=os.environ["BUILDER_API_KEY"],
            secret=os.environ["BUILDER_SECRET"],
            passphrase=os.environ["BUILDER_PASSPHRASE"],
        )
    )
    return RelayClient(
        RELAYER_URL,
        CHAIN_ID,
        os.environ["PRIVATE_KEY"],
        config,
    )


def wallet_batch(relayer: RelayClient, deposit_wallet: str, calls: list) -> object:
    """
    Fetch WALLET nonce, sign, and submit a batch of on-chain calls
    from the deposit wallet. Returns the confirmed receipt object.

    calls: list of DepositWalletCall(target, value, data)
    """
    nonce_payload = relayer.get_nonce(
        relayer.signer.address(),
        TransactionType.WALLET.value,
    )
    nonce    = str(nonce_payload["nonce"])
    deadline = str(int(time.time()) + 240)

    response = relayer.execute_deposit_wallet_batch(
        calls=calls,
        wallet_address=deposit_wallet,
        nonce=nonce,
        deadline=deadline,
    )
    return response.wait()
