from typing import List, Dict
from ..models.transaction import RiskScore, Transaction, Address
import math


class RiskScorerService:
    """Advanced risk scoring engine for Bitcoin addresses."""

    # Known high-risk patterns and services
    KNOWN_MIXERS = {
        # Add known mixing service addresses here
        "mixer_patterns": ["mix", "tumbl", "wasabi", "coinjoin"]
    }

    KNOWN_EXCHANGES = {
        # Major exchanges tend to have lower risk
        "binance", "coinbase", "kraken", "bitstamp"
    }

    def __init__(self):
        self.risk_weights = {
            "transaction_frequency": 0.15,
            "mixing_pattern": 0.25,
            "new_address": 0.10,
            "high_velocity": 0.20,
            "round_numbers": 0.10,
            "multiple_outputs": 0.10,
            "privacy_tools": 0.10,
        }

    async def calculate_risk_score(
        self, address: str, address_info: Address, transactions: List[Transaction]
    ) -> RiskScore:
        """Calculate comprehensive risk score for an address."""
        factors = {}

        # 1. Transaction frequency analysis
        factors["transaction_frequency"] = self._score_transaction_frequency(
            address_info.tx_count
        )

        # 2. Mixing pattern detection
        factors["mixing_pattern"] = self._score_mixing_patterns(transactions)

        # 3. New address risk (less history = slightly higher risk)
        factors["new_address"] = self._score_address_age(address_info)

        # 4. High velocity (rapid movement of funds)
        factors["high_velocity"] = self._score_velocity(transactions)

        # 5. Round number transactions (potential structuring)
        factors["round_numbers"] = self._score_round_numbers(transactions)

        # 6. Multiple outputs pattern (potential mixing)
        factors["multiple_outputs"] = self._score_multiple_outputs(transactions)

        # 7. Privacy tool usage
        factors["privacy_tools"] = self._score_privacy_tools(transactions)

        # Calculate weighted overall score
        overall_score = sum(
            factors[key] * self.risk_weights.get(key, 0) for key in factors
        )
        overall_score = min(100, max(0, overall_score))

        # Determine risk level
        if overall_score >= 75:
            risk_level = "CRITICAL"
        elif overall_score >= 50:
            risk_level = "HIGH"
        elif overall_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Generate flags
        flags = self._generate_flags(factors, transactions)

        return RiskScore(
            address=address,
            overall_score=round(overall_score, 2),
            factors=factors,
            risk_level=risk_level,
            flags=flags,
        )

    def _score_transaction_frequency(self, tx_count: int) -> float:
        """Score based on transaction frequency."""
        if tx_count >= 1000:
            return 80.0  # Very high activity
        elif tx_count >= 500:
            return 60.0
        elif tx_count >= 100:
            return 40.0
        elif tx_count >= 10:
            return 20.0
        else:
            return 10.0

    def _score_mixing_patterns(self, transactions: List[Transaction]) -> float:
        """Detect mixing service patterns."""
        if not transactions:
            return 0.0

        mixing_indicators = 0
        total_checks = 0

        for tx in transactions:
            total_checks += 1

            # Check for common mixing patterns
            # 1. Many outputs to different addresses
            if len(tx.outputs) > 10:
                mixing_indicators += 1

            # 2. Equal-value outputs (common in mixing)
            if len(tx.outputs) > 1:
                output_values = [out.value for out in tx.outputs]
                if len(set(output_values)) == 1:
                    mixing_indicators += 1

            # 3. CoinJoin patterns (many inputs, many outputs)
            if len(tx.inputs) > 5 and len(tx.outputs) > 5:
                mixing_indicators += 1

        if total_checks == 0:
            return 0.0

        score = (mixing_indicators / total_checks) * 100
        return min(100.0, score * 2)  # Amplify the score

    def _score_address_age(self, address_info: Address) -> float:
        """Score based on address age (newer = slightly higher risk)."""
        if address_info.tx_count < 5:
            return 30.0
        elif address_info.tx_count < 20:
            return 15.0
        else:
            return 5.0

    def _score_velocity(self, transactions: List[Transaction]) -> float:
        """Score based on how quickly funds move through the address."""
        if len(transactions) < 2:
            return 0.0

        # Sort by time
        sorted_txs = sorted(transactions, key=lambda x: x.time)

        # Calculate time between transactions
        rapid_movements = 0
        for i in range(len(sorted_txs) - 1):
            time_diff = (sorted_txs[i + 1].time - sorted_txs[i].time).total_seconds()
            # If transactions within 1 hour
            if time_diff < 3600:
                rapid_movements += 1

        if len(sorted_txs) == 0:
            return 0.0

        velocity_score = (rapid_movements / len(sorted_txs)) * 100
        return min(100.0, velocity_score * 1.5)

    def _score_round_numbers(self, transactions: List[Transaction]) -> float:
        """Detect round number transactions (potential structuring)."""
        if not transactions:
            return 0.0

        round_number_txs = 0
        for tx in transactions:
            for output in tx.outputs:
                # Check if value is a round number (e.g., 1.0, 0.5, 10.0)
                if output.value > 0 and output.value == round(output.value, 1):
                    round_number_txs += 1
                    break

        score = (round_number_txs / len(transactions)) * 100
        return min(100.0, score)

    def _score_multiple_outputs(self, transactions: List[Transaction]) -> float:
        """Score based on transactions with many outputs."""
        if not transactions:
            return 0.0

        high_output_txs = sum(1 for tx in transactions if len(tx.outputs) > 5)
        score = (high_output_txs / len(transactions)) * 100
        return min(100.0, score * 1.2)

    def _score_privacy_tools(self, transactions: List[Transaction]) -> float:
        """Detect usage of privacy-enhancing tools."""
        # This would check for SegWit, Taproot, etc.
        # For now, return a baseline
        return 0.0

    def _generate_flags(
        self, factors: Dict[str, float], transactions: List[Transaction]
    ) -> List[str]:
        """Generate warning flags based on risk factors."""
        flags = []

        if factors.get("mixing_pattern", 0) > 50:
            flags.append("POTENTIAL_MIXING_SERVICE")

        if factors.get("high_velocity", 0) > 60:
            flags.append("RAPID_FUND_MOVEMENT")

        if factors.get("transaction_frequency", 0) > 70:
            flags.append("HIGH_TRANSACTION_VOLUME")

        if factors.get("round_numbers", 0) > 40:
            flags.append("STRUCTURED_TRANSACTIONS")

        if factors.get("multiple_outputs", 0) > 50:
            flags.append("COMPLEX_TRANSACTION_PATTERNS")

        return flags
