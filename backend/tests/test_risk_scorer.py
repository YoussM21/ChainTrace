import pytest
from app.services.risk_scorer import RiskScorerService
from app.models.transaction import Transaction, Address, TransactionInput, TransactionOutput
from datetime import datetime


@pytest.fixture
def risk_scorer():
    return RiskScorerService()


@pytest.fixture
def sample_address():
    return Address(
        address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        balance=0.0,
        total_received=50.0,
        total_sent=50.0,
        tx_count=10,
    )


@pytest.fixture
def sample_transactions():
    return [
        Transaction(
            hash="tx1",
            time=datetime.now(),
            inputs=[
                TransactionInput(
                    address="addr1", value=1.0, prev_hash="prev1", output_index=0
                )
            ],
            outputs=[
                TransactionOutput(address="addr2", value=0.5, spent=False),
                TransactionOutput(address="addr3", value=0.5, spent=False),
            ],
            fee=0.0001,
            confirmations=6,
            total_input=1.0,
            total_output=1.0,
        )
    ]


@pytest.mark.asyncio
async def test_calculate_risk_score(risk_scorer, sample_address, sample_transactions):
    """Test basic risk score calculation."""
    risk_score = await risk_scorer.calculate_risk_score(
        "test_address", sample_address, sample_transactions
    )

    assert risk_score.address == "test_address"
    assert 0 <= risk_score.overall_score <= 100
    assert risk_score.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert isinstance(risk_score.factors, dict)
    assert isinstance(risk_score.flags, list)


def test_score_transaction_frequency(risk_scorer):
    """Test transaction frequency scoring."""
    assert risk_scorer._score_transaction_frequency(5) == 10.0
    assert risk_scorer._score_transaction_frequency(50) == 20.0
    assert risk_scorer._score_transaction_frequency(500) == 60.0
    assert risk_scorer._score_transaction_frequency(1500) == 80.0


def test_score_mixing_patterns(risk_scorer, sample_transactions):
    """Test mixing pattern detection."""
    score = risk_scorer._score_mixing_patterns(sample_transactions)
    assert 0 <= score <= 100


def test_score_address_age(risk_scorer, sample_address):
    """Test address age scoring."""
    sample_address.tx_count = 3
    score = risk_scorer._score_address_age(sample_address)
    assert score == 30.0

    sample_address.tx_count = 15
    score = risk_scorer._score_address_age(sample_address)
    assert score == 15.0

    sample_address.tx_count = 50
    score = risk_scorer._score_address_age(sample_address)
    assert score == 5.0
