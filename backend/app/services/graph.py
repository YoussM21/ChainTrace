import asyncio
import networkx as nx
from typing import List, Set, Dict
from ..models.transaction import (
    Transaction,
    TransactionGraph,
    GraphNode,
    GraphEdge,
)
from .blockchain import BlockchainService
from .risk_scorer import RiskScorerService


class GraphService:
    """Service to build and analyze transaction graphs."""

    def __init__(
        self,
        blockchain_service: BlockchainService,
        risk_scorer: RiskScorerService,
    ):
        self.blockchain = blockchain_service
        self.risk_scorer = risk_scorer
        self._address_cache: Dict[str, dict] = {}

    async def build_transaction_graph(
        self,
        root_address: str,
        depth: int = 2,
        max_nodes: int = 100,
        min_value: float = 0.0001,
    ) -> TransactionGraph:
        """
        Build a transaction graph starting from a root address.

        Args:
            root_address: Starting Bitcoin address
            depth: How many hops to follow (1-5 recommended)
            max_nodes: Maximum number of nodes to prevent explosion
            min_value: Minimum transaction value to include (BTC)
        """
        visited_addresses: Set[str] = set()
        visited_txs: Set[str] = set()
        node_ids: Set[str] = set()

        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        total_value = 0.0

        # BFS traversal
        queue = [(root_address, 0)]  # (address, current_depth)

        while queue and len(nodes) < max_nodes:
            current_address, current_depth = queue.pop(0)

            if current_address in visited_addresses or current_depth > depth:
                continue

            visited_addresses.add(current_address)

            # Get address info and transactions
            try:
                # Fetch address info and transactions concurrently
                address_info, transactions = await asyncio.gather(
                    self.blockchain.get_address_info(current_address),
                    self.blockchain.get_address_transactions(current_address, limit=10),
                )

                # Calculate risk score (uses cached data, fast)
                risk_score = await self.risk_scorer.calculate_risk_score(
                    current_address, address_info, transactions
                )

                # Add address node
                nodes.append(
                    GraphNode(
                        id=current_address,
                        label=self._truncate_address(current_address),
                        type="address",
                        risk_score=risk_score.overall_score,
                        value=address_info.balance,
                        metadata={
                            "total_received": address_info.total_received,
                            "total_sent": address_info.total_sent,
                            "tx_count": address_info.tx_count,
                            "risk_level": risk_score.risk_level,
                            "flags": risk_score.flags,
                        },
                    )
                )
                node_ids.add(current_address)

                # Process transactions
                for tx in transactions:
                    if tx.hash in visited_txs:
                        continue

                    visited_txs.add(tx.hash)

                    # Determine if this is an incoming or outgoing tx
                    is_incoming = any(
                        out.address == current_address for out in tx.outputs
                    )
                    is_outgoing = any(
                        inp.address == current_address for inp in tx.inputs
                    )

                    if is_incoming:
                        # Add edges from input addresses to current address
                        for inp in tx.inputs:
                            if inp.value >= min_value and inp.address != current_address:
                                edges.append(
                                    GraphEdge(
                                        source=inp.address,
                                        target=current_address,
                                        value=inp.value,
                                        timestamp=tx.time,
                                        tx_hash=tx.hash,
                                    )
                                )
                                total_value += inp.value

                                # Add to queue for next depth
                                if current_depth < depth:
                                    queue.append((inp.address, current_depth + 1))

                    if is_outgoing:
                        # Add edges from current address to output addresses
                        for out in tx.outputs:
                            if out.value >= min_value and out.address != current_address:
                                edges.append(
                                    GraphEdge(
                                        source=current_address,
                                        target=out.address,
                                        value=out.value,
                                        timestamp=tx.time,
                                        tx_hash=tx.hash,
                                    )
                                )
                                total_value += out.value

                                # Add to queue for next depth
                                if current_depth < depth:
                                    queue.append((out.address, current_depth + 1))

                # Rate limit: small delay between addresses to avoid API throttling
                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"Error processing address {current_address}: {e}")
                continue

        # Add placeholder nodes for addresses referenced in edges but not visited
        # This ensures the graph library can render all edges
        for edge in edges:
            for addr in [edge.source, edge.target]:
                if addr not in node_ids:
                    nodes.append(
                        GraphNode(
                            id=addr,
                            label=self._truncate_address(addr),
                            type="address",
                            risk_score=0,
                            value=0,
                            metadata={"partial": True},
                        )
                    )
                    node_ids.add(addr)

        return TransactionGraph(
            nodes=nodes,
            edges=edges,
            root_address=root_address,
            depth=depth,
            total_value=total_value,
        )

    def analyze_graph_metrics(self, graph: TransactionGraph) -> dict:
        """Analyze graph and return metrics."""
        G = nx.DiGraph()

        # Build NetworkX graph
        for edge in graph.edges:
            G.add_edge(edge.source, edge.target, weight=edge.value)

        metrics = {
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "total_value": graph.total_value,
            "density": nx.density(G) if len(G.nodes()) > 1 else 0,
        }

        # Calculate centrality measures
        if len(G.nodes()) > 0:
            try:
                in_degree_centrality = nx.in_degree_centrality(G)
                out_degree_centrality = nx.out_degree_centrality(G)

                # Find most central nodes
                most_incoming = max(in_degree_centrality.items(), key=lambda x: x[1], default=(None, 0))
                most_outgoing = max(out_degree_centrality.items(), key=lambda x: x[1], default=(None, 0))

                metrics["most_incoming_node"] = most_incoming[0]
                metrics["most_outgoing_node"] = most_outgoing[0]
            except:
                pass

        return metrics

    def _truncate_address(self, address: str, length: int = 8) -> str:
        """Truncate Bitcoin address for display."""
        if len(address) <= length * 2:
            return address
        return f"{address[:length]}...{address[-length:]}"
