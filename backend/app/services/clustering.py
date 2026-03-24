from typing import List, Set, Dict
from collections import defaultdict
from ..models.transaction import Transaction


class ClusteringService:
    """Service to identify related addresses using clustering heuristics."""

    def __init__(self):
        pass

    def cluster_addresses(self, transactions: List[Transaction]) -> Dict[str, Set[str]]:
        """
        Apply clustering heuristics to group related addresses.

        Uses common-input-ownership heuristic: addresses that appear
        as inputs in the same transaction likely belong to the same entity.
        """
        clusters: Dict[str, Set[str]] = {}
        address_to_cluster: Dict[str, str] = {}

        for tx in transactions:
            if len(tx.inputs) < 2:
                continue

            # Get all input addresses
            input_addresses = [inp.address for inp in tx.inputs]

            # Find if any address already belongs to a cluster
            existing_cluster_id = None
            for addr in input_addresses:
                if addr in address_to_cluster:
                    existing_cluster_id = address_to_cluster[addr]
                    break

            # If cluster exists, add all addresses to it
            if existing_cluster_id:
                for addr in input_addresses:
                    clusters[existing_cluster_id].add(addr)
                    address_to_cluster[addr] = existing_cluster_id
            else:
                # Create new cluster
                cluster_id = f"cluster_{len(clusters)}"
                clusters[cluster_id] = set(input_addresses)
                for addr in input_addresses:
                    address_to_cluster[addr] = cluster_id

        return clusters

    def detect_peeling_chain(self, transactions: List[Transaction]) -> List[str]:
        """
        Detect peeling chain pattern: repeated transactions where one output
        goes to a new address and the other (change) goes back.

        Common in darknet markets and exchange withdrawals.
        """
        peeling_chain = []

        # Sort transactions by time
        sorted_txs = sorted(transactions, key=lambda x: x.time)

        for tx in sorted_txs:
            if len(tx.outputs) == 2:
                # Check if one output is significantly smaller (likely the payment)
                # and the other is change
                values = [out.value for out in tx.outputs]
                if max(values) > min(values) * 5:  # 5x difference
                    peeling_chain.append(tx.hash)

        return peeling_chain

    def identify_change_addresses(self, tx: Transaction, known_address: str) -> List[str]:
        """
        Identify likely change addresses in a transaction.

        Heuristics:
        1. Change usually goes to a new address
        2. Change amount is usually different from payment
        3. Change is typically the larger output
        """
        if known_address not in [inp.address for inp in tx.inputs]:
            return []

        change_candidates = []

        for output in tx.outputs:
            # If output goes to a different address than any input
            if output.address not in [inp.address for inp in tx.inputs]:
                # And it's one of the larger outputs
                if output.value == max(out.value for out in tx.outputs):
                    change_candidates.append(output.address)

        return change_candidates

    def detect_mixing_behavior(self, transactions: List[Transaction]) -> Dict[str, any]:
        """
        Detect mixing/tumbling behavior patterns.

        Indicators:
        - Transactions with many inputs and outputs
        - Equal-value outputs
        - Time-delayed transactions
        """
        mixing_score = 0
        indicators = []

        for tx in transactions:
            # Many inputs + many outputs
            if len(tx.inputs) > 5 and len(tx.outputs) > 5:
                mixing_score += 20
                indicators.append(f"Complex transaction: {tx.hash}")

            # Equal-value outputs (CoinJoin signature)
            output_values = [out.value for out in tx.outputs]
            if len(output_values) > 2:
                unique_values = set(output_values)
                if len(unique_values) < len(output_values) * 0.5:
                    mixing_score += 30
                    indicators.append(f"Equal outputs detected: {tx.hash}")

        return {
            "mixing_score": min(100, mixing_score),
            "indicators": indicators,
            "is_likely_mixing": mixing_score > 50,
        }
