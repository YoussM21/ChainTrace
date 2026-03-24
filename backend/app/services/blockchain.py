import httpx
from typing import Optional, List
from datetime import datetime
from ..models.transaction import Transaction, Address, TransactionInput, TransactionOutput


class BlockchainService:
    """Service to interact with Bitcoin blockchain via Blockstream API."""

    def __init__(self):
        self.base_url = "https://blockstream.info/api"
        self.client = httpx.AsyncClient(timeout=60.0)

    async def get_address_info(self, address: str) -> Address:
        """Fetch detailed information about a Bitcoin address."""
        url = f"{self.base_url}/address/{address}"

        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()

        chain = data.get("chain_stats", {})
        mempool = data.get("mempool_stats", {})

        total_received = chain.get("funded_txo_sum", 0) + mempool.get("funded_txo_sum", 0)
        total_sent = chain.get("spent_txo_sum", 0) + mempool.get("spent_txo_sum", 0)
        balance = total_received - total_sent
        tx_count = chain.get("tx_count", 0) + mempool.get("tx_count", 0)

        return Address(
            address=data["address"],
            balance=balance / 1e8,
            total_received=total_received / 1e8,
            total_sent=total_sent / 1e8,
            tx_count=tx_count,
        )

    async def get_address_transactions(
        self, address: str, limit: int = 50, last_seen_txid: Optional[str] = None
    ) -> List[Transaction]:
        """Fetch transactions for a given address."""
        url = f"{self.base_url}/address/{address}/txs"
        if last_seen_txid:
            url = f"{self.base_url}/address/{address}/txs/chain/{last_seen_txid}"

        response = await self.client.get(url)
        response.raise_for_status()
        tx_list = response.json()

        transactions = []
        for tx_data in tx_list[:limit]:
            transactions.append(self._parse_transaction(tx_data))

        return transactions

    async def get_transaction(self, tx_hash: str) -> Transaction:
        """Fetch a specific transaction by hash."""
        url = f"{self.base_url}/tx/{tx_hash}"

        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return self._parse_transaction(data)

    def _parse_transaction(self, tx_data: dict) -> Transaction:
        """Parse Blockstream transaction data into Transaction model."""
        inputs = []
        for inp in tx_data.get("vin", []):
            prevout = inp.get("prevout")
            if prevout and prevout.get("scriptpubkey_address"):
                inputs.append(
                    TransactionInput(
                        address=prevout["scriptpubkey_address"],
                        value=prevout.get("value", 0) / 1e8,
                        prev_hash=inp.get("txid", ""),
                        output_index=inp.get("vout", 0),
                    )
                )

        outputs = []
        for out in tx_data.get("vout", []):
            if out.get("scriptpubkey_address"):
                outputs.append(
                    TransactionOutput(
                        address=out["scriptpubkey_address"],
                        value=out.get("value", 0) / 1e8,
                        spent=False,  # Blockstream doesn't include spent status in tx response
                    )
                )

        status = tx_data.get("status", {})
        block_height = status.get("block_height")
        block_time = status.get("block_time")

        if block_time:
            tx_time = datetime.fromtimestamp(block_time)
        else:
            tx_time = datetime.now()

        return Transaction(
            hash=tx_data["txid"],
            time=tx_time,
            inputs=inputs,
            outputs=outputs,
            fee=tx_data.get("fee", 0) / 1e8,
            block_height=block_height,
            confirmations=0,  # Would need current block height to calculate
            total_input=sum(inp.value for inp in inputs),
            total_output=sum(out.value for out in outputs),
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
