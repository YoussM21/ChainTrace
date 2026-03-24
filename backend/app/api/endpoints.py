from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..models.transaction import (
    Address,
    Transaction,
    RiskScore,
    TransactionGraph,
)
from ..services.blockchain import BlockchainService
from ..services.risk_scorer import RiskScorerService
from ..services.graph import GraphService
from ..services.clustering import ClusteringService

router = APIRouter()

# Initialize services
blockchain_service = BlockchainService()
risk_scorer = RiskScorerService()
graph_service = GraphService(blockchain_service, risk_scorer)
clustering_service = ClusteringService()


@router.get("/address/{address}", response_model=Address)
async def get_address_info(address: str):
    """Get detailed information about a Bitcoin address."""
    try:
        return await blockchain_service.get_address_info(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/address/{address}/transactions", response_model=list[Transaction])
async def get_address_transactions(
    address: str,
    limit: int = Query(default=50, le=200),
    last_seen_txid: Optional[str] = None,
):
    """Get transactions for a Bitcoin address."""
    try:
        return await blockchain_service.get_address_transactions(
            address, limit=limit, last_seen_txid=last_seen_txid
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/address/{address}/risk", response_model=RiskScore)
async def get_address_risk_score(address: str):
    """Calculate risk score for a Bitcoin address."""
    try:
        address_info = await blockchain_service.get_address_info(address)
        transactions = await blockchain_service.get_address_transactions(address)
        risk_score = await risk_scorer.calculate_risk_score(
            address, address_info, transactions
        )
        return risk_score
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transaction/{tx_hash}", response_model=Transaction)
async def get_transaction(tx_hash: str):
    """Get details of a specific transaction."""
    try:
        return await blockchain_service.get_transaction(tx_hash)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph/{address}", response_model=TransactionGraph)
async def build_transaction_graph(
    address: str,
    depth: int = Query(default=2, ge=1, le=4),
    max_nodes: int = Query(default=100, ge=10, le=500),
    min_value: float = Query(default=0.0001, ge=0.0),
):
    """
    Build a transaction graph starting from an address.

    Args:
        address: Root Bitcoin address
        depth: How many transaction hops to follow (1-4)
        max_nodes: Maximum nodes to include (10-500)
        min_value: Minimum transaction value in BTC
    """
    try:
        graph = await graph_service.build_transaction_graph(
            root_address=address,
            depth=depth,
            max_nodes=max_nodes,
            min_value=min_value,
        )
        return graph
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph/{address}/metrics")
async def get_graph_metrics(
    address: str,
    depth: int = Query(default=2, ge=1, le=4),
    max_nodes: int = Query(default=100, ge=10, le=500),
):
    """Get graph metrics and analysis."""
    try:
        graph = await graph_service.build_transaction_graph(
            root_address=address, depth=depth, max_nodes=max_nodes
        )
        metrics = graph_service.analyze_graph_metrics(graph)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/address/{address}/clustering")
async def cluster_address_relationships(address: str):
    """Identify related addresses using clustering heuristics."""
    try:
        transactions = await blockchain_service.get_address_transactions(
            address, limit=100
        )
        clusters = clustering_service.cluster_addresses(transactions)
        peeling_chain = clustering_service.detect_peeling_chain(transactions)
        mixing_behavior = clustering_service.detect_mixing_behavior(transactions)

        return {
            "address": address,
            "clusters": {k: list(v) for k, v in clusters.items()},
            "peeling_chain": peeling_chain,
            "mixing_behavior": mixing_behavior,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ChainTrace API"}
