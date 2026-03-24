from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx

app = FastAPI()

# CORS - allow all origins for API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Blockstream API base
BLOCKSTREAM_API = "https://blockstream.info/api"

# ============ Models ============

class Address(BaseModel):
    address: str
    balance: float
    total_received: float
    total_sent: float
    tx_count: int

class TransactionInput(BaseModel):
    address: str
    value: float
    prev_hash: str
    output_index: int

class TransactionOutput(BaseModel):
    address: str
    value: float
    spent: bool

class Transaction(BaseModel):
    hash: str
    time: datetime
    inputs: List[TransactionInput]
    outputs: List[TransactionOutput]
    fee: float
    block_height: Optional[int]
    confirmations: int
    total_input: float
    total_output: float

class RiskScore(BaseModel):
    address: str
    overall_score: float
    factors: Dict[str, float]
    risk_level: str
    flags: List[str]

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    risk_score: float
    value: float
    metadata: Dict[str, Any]

class GraphEdge(BaseModel):
    source: str
    target: str
    value: float
    timestamp: Optional[datetime]
    tx_hash: Optional[str]

class TransactionGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    root_address: str
    depth: int
    total_value: float

# ============ Blockchain Service ============

async def get_address_info(address: str) -> Address:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BLOCKSTREAM_API}/address/{address}")
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

async def get_address_transactions(address: str, limit: int = 25) -> List[Transaction]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BLOCKSTREAM_API}/address/{address}/txs")
        response.raise_for_status()
        tx_list = response.json()

        transactions = []
        for tx_data in tx_list[:limit]:
            transactions.append(parse_transaction(tx_data))

        return transactions

def parse_transaction(tx_data: dict) -> Transaction:
    inputs = []
    for inp in tx_data.get("vin", []):
        prevout = inp.get("prevout")
        if prevout and prevout.get("scriptpubkey_address"):
            inputs.append(TransactionInput(
                address=prevout["scriptpubkey_address"],
                value=prevout.get("value", 0) / 1e8,
                prev_hash=inp.get("txid", ""),
                output_index=inp.get("vout", 0),
            ))

    outputs = []
    for out in tx_data.get("vout", []):
        if out.get("scriptpubkey_address"):
            outputs.append(TransactionOutput(
                address=out["scriptpubkey_address"],
                value=out.get("value", 0) / 1e8,
                spent=False,
            ))

    status = tx_data.get("status", {})
    block_time = status.get("block_time")
    tx_time = datetime.fromtimestamp(block_time) if block_time else datetime.now()

    return Transaction(
        hash=tx_data["txid"],
        time=tx_time,
        inputs=inputs,
        outputs=outputs,
        fee=tx_data.get("fee", 0) / 1e8,
        block_height=status.get("block_height"),
        confirmations=0,
        total_input=sum(inp.value for inp in inputs),
        total_output=sum(out.value for out in outputs),
    )

# ============ Risk Scoring ============

def calculate_risk_score(address: str, addr_info: Address, transactions: List[Transaction]) -> RiskScore:
    factors = {}
    flags = []

    # Transaction frequency
    tx_count = addr_info.tx_count
    if tx_count >= 1000:
        factors["transaction_frequency"] = 80.0
        flags.append("HIGH_TRANSACTION_VOLUME")
    elif tx_count >= 500:
        factors["transaction_frequency"] = 60.0
        flags.append("HIGH_TRANSACTION_VOLUME")
    elif tx_count >= 100:
        factors["transaction_frequency"] = 40.0
    elif tx_count >= 10:
        factors["transaction_frequency"] = 20.0
    else:
        factors["transaction_frequency"] = 10.0

    # Fund movement velocity
    if addr_info.total_received > 0:
        movement_ratio = addr_info.total_sent / addr_info.total_received
        if movement_ratio > 0.95 and tx_count > 10:
            factors["high_velocity"] = 40.0
            flags.append("RAPID_FUND_MOVEMENT")
        else:
            factors["high_velocity"] = movement_ratio * 20
    else:
        factors["high_velocity"] = 0

    # Mixing patterns (multiple similar outputs)
    mixing_score = 0
    for tx in transactions[:10]:
        if len(tx.outputs) > 3:
            values = [o.value for o in tx.outputs]
            unique_values = set(round(v, 4) for v in values)
            if len(unique_values) < len(values) * 0.5:
                mixing_score += 10
    factors["mixing_pattern"] = min(mixing_score, 50)
    if mixing_score > 20:
        flags.append("POTENTIAL_MIXING_SERVICE")

    # Complex patterns
    if len(transactions) > 5:
        avg_outputs = sum(len(tx.outputs) for tx in transactions[:10]) / min(len(transactions), 10)
        if avg_outputs > 5:
            factors["complex_patterns"] = 30.0
            flags.append("COMPLEX_TRANSACTION_PATTERNS")
        else:
            factors["complex_patterns"] = avg_outputs * 3
    else:
        factors["complex_patterns"] = 0

    overall = sum(factors.values()) / len(factors) if factors else 0

    if overall >= 60:
        level = "HIGH"
    elif overall >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return RiskScore(
        address=address,
        overall_score=round(overall, 1),
        factors=factors,
        risk_level=level,
        flags=flags,
    )

# ============ Graph Building ============

async def build_graph(root_address: str, depth: int = 2, max_nodes: int = 50, min_value: float = 0.0001) -> TransactionGraph:
    visited = set()
    nodes = []
    edges = []
    node_ids = set()
    total_value = 0.0

    queue = [(root_address, 0)]

    while queue and len(nodes) < max_nodes:
        current_address, current_depth = queue.pop(0)

        if current_address in visited or current_depth > depth:
            continue

        visited.add(current_address)

        try:
            addr_info = await get_address_info(current_address)
            transactions = await get_address_transactions(current_address, limit=10)
            risk = calculate_risk_score(current_address, addr_info, transactions)

            nodes.append(GraphNode(
                id=current_address,
                label=f"{current_address[:8]}...{current_address[-8:]}",
                type="address",
                risk_score=risk.overall_score,
                value=addr_info.balance,
                metadata={
                    "total_received": addr_info.total_received,
                    "total_sent": addr_info.total_sent,
                    "tx_count": addr_info.tx_count,
                    "risk_level": risk.risk_level,
                    "flags": risk.flags,
                },
            ))
            node_ids.add(current_address)

            for tx in transactions:
                is_incoming = any(out.address == current_address for out in tx.outputs)
                is_outgoing = any(inp.address == current_address for inp in tx.inputs)

                if is_incoming:
                    for inp in tx.inputs:
                        if inp.value >= min_value and inp.address != current_address:
                            edges.append(GraphEdge(
                                source=inp.address,
                                target=current_address,
                                value=inp.value,
                                timestamp=tx.time,
                                tx_hash=tx.hash,
                            ))
                            total_value += inp.value
                            if current_depth < depth:
                                queue.append((inp.address, current_depth + 1))

                if is_outgoing:
                    for out in tx.outputs:
                        if out.value >= min_value and out.address != current_address:
                            edges.append(GraphEdge(
                                source=current_address,
                                target=out.address,
                                value=out.value,
                                timestamp=tx.time,
                                tx_hash=tx.hash,
                            ))
                            total_value += out.value
                            if current_depth < depth:
                                queue.append((out.address, current_depth + 1))
        except Exception as e:
            print(f"Error processing {current_address}: {e}")
            continue

    # Add placeholder nodes for edges
    for edge in edges:
        for addr in [edge.source, edge.target]:
            if addr not in node_ids:
                nodes.append(GraphNode(
                    id=addr,
                    label=f"{addr[:8]}...{addr[-8:]}",
                    type="address",
                    risk_score=0,
                    value=0,
                    metadata={"partial": True},
                ))
                node_ids.add(addr)

    return TransactionGraph(
        nodes=nodes,
        edges=edges,
        root_address=root_address,
        depth=depth,
        total_value=total_value,
    )

# ============ API Endpoints ============

@app.get("/")
async def root():
    return {"message": "ChainTrace API", "version": "1.0.0"}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/address/{address}", response_model=Address)
async def api_get_address(address: str):
    try:
        return await get_address_info(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/address/{address}/transactions", response_model=List[Transaction])
async def api_get_transactions(address: str, limit: int = Query(default=25, le=50)):
    try:
        return await get_address_transactions(address, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/address/{address}/risk", response_model=RiskScore)
async def api_get_risk(address: str):
    try:
        addr_info = await get_address_info(address)
        transactions = await get_address_transactions(address)
        return calculate_risk_score(address, addr_info, transactions)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/graph/{address}", response_model=TransactionGraph)
async def api_get_graph(
    address: str,
    depth: int = Query(default=2, ge=1, le=3),
    max_nodes: int = Query(default=50, ge=10, le=100),
    min_value: float = Query(default=0.0001, ge=0),
):
    try:
        return await build_graph(address, depth, max_nodes, min_value)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
