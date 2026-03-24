from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BLOCKSTREAM_API = "https://blockstream.info/api"

# ============ Blockchain Helpers ============

async def fetch_address(address: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BLOCKSTREAM_API}/address/{address}")
        response.raise_for_status()
        data = response.json()

        chain = data.get("chain_stats", {})
        mempool = data.get("mempool_stats", {})

        total_received = chain.get("funded_txo_sum", 0) + mempool.get("funded_txo_sum", 0)
        total_sent = chain.get("spent_txo_sum", 0) + mempool.get("spent_txo_sum", 0)

        return {
            "address": data["address"],
            "balance": (total_received - total_sent) / 1e8,
            "total_received": total_received / 1e8,
            "total_sent": total_sent / 1e8,
            "tx_count": chain.get("tx_count", 0) + mempool.get("tx_count", 0),
        }

async def fetch_transactions(address: str, limit: int = 25) -> list:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BLOCKSTREAM_API}/address/{address}/txs")
        response.raise_for_status()
        tx_list = response.json()
        return [parse_tx(tx) for tx in tx_list[:limit]]

def parse_tx(tx_data: dict) -> dict:
    inputs = []
    for inp in tx_data.get("vin", []):
        prevout = inp.get("prevout")
        if prevout and prevout.get("scriptpubkey_address"):
            inputs.append({
                "address": prevout["scriptpubkey_address"],
                "value": prevout.get("value", 0) / 1e8,
                "prev_hash": inp.get("txid", ""),
                "output_index": inp.get("vout", 0),
            })

    outputs = []
    for out in tx_data.get("vout", []):
        if out.get("scriptpubkey_address"):
            outputs.append({
                "address": out["scriptpubkey_address"],
                "value": out.get("value", 0) / 1e8,
                "spent": False,
            })

    status = tx_data.get("status", {})
    block_time = status.get("block_time")

    return {
        "hash": tx_data["txid"],
        "time": datetime.fromtimestamp(block_time).isoformat() if block_time else datetime.now().isoformat(),
        "inputs": inputs,
        "outputs": outputs,
        "fee": tx_data.get("fee", 0) / 1e8,
        "block_height": status.get("block_height"),
        "confirmations": 0,
        "total_input": sum(i["value"] for i in inputs),
        "total_output": sum(o["value"] for o in outputs),
    }

def calc_risk(address: str, addr_info: dict, txs: list) -> dict:
    factors = {}
    flags = []
    tx_count = addr_info["tx_count"]

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

    if addr_info["total_received"] > 0:
        ratio = addr_info["total_sent"] / addr_info["total_received"]
        if ratio > 0.95 and tx_count > 10:
            factors["high_velocity"] = 40.0
            flags.append("RAPID_FUND_MOVEMENT")
        else:
            factors["high_velocity"] = ratio * 20
    else:
        factors["high_velocity"] = 0

    mixing = 0
    for tx in txs[:10]:
        if len(tx["outputs"]) > 3:
            values = [o["value"] for o in tx["outputs"]]
            unique = set(round(v, 4) for v in values)
            if len(unique) < len(values) * 0.5:
                mixing += 10
    factors["mixing_pattern"] = min(mixing, 50)
    if mixing > 20:
        flags.append("POTENTIAL_MIXING_SERVICE")

    overall = sum(factors.values()) / len(factors) if factors else 0
    level = "HIGH" if overall >= 60 else "MEDIUM" if overall >= 40 else "LOW"

    return {
        "address": address,
        "overall_score": round(overall, 1),
        "factors": factors,
        "risk_level": level,
        "flags": flags,
    }

async def build_graph(root: str, depth: int = 2, max_nodes: int = 50, min_val: float = 0.0001) -> dict:
    visited = set()
    nodes = []
    edges = []
    node_ids = set()
    total = 0.0
    queue = [(root, 0)]

    while queue and len(nodes) < max_nodes:
        addr, d = queue.pop(0)
        if addr in visited or d > depth:
            continue
        visited.add(addr)

        try:
            info = await fetch_address(addr)
            txs = await fetch_transactions(addr, 10)
            risk = calc_risk(addr, info, txs)

            nodes.append({
                "id": addr,
                "label": f"{addr[:8]}...{addr[-8:]}",
                "type": "address",
                "risk_score": risk["overall_score"],
                "value": info["balance"],
                "metadata": {
                    "total_received": info["total_received"],
                    "total_sent": info["total_sent"],
                    "tx_count": info["tx_count"],
                    "risk_level": risk["risk_level"],
                    "flags": risk["flags"],
                },
            })
            node_ids.add(addr)

            for tx in txs:
                incoming = any(o["address"] == addr for o in tx["outputs"])
                outgoing = any(i["address"] == addr for i in tx["inputs"])

                if incoming:
                    for inp in tx["inputs"]:
                        if inp["value"] >= min_val and inp["address"] != addr:
                            edges.append({
                                "source": inp["address"],
                                "target": addr,
                                "value": inp["value"],
                                "timestamp": tx["time"],
                                "tx_hash": tx["hash"],
                            })
                            total += inp["value"]
                            if d < depth:
                                queue.append((inp["address"], d + 1))

                if outgoing:
                    for out in tx["outputs"]:
                        if out["value"] >= min_val and out["address"] != addr:
                            edges.append({
                                "source": addr,
                                "target": out["address"],
                                "value": out["value"],
                                "timestamp": tx["time"],
                                "tx_hash": tx["hash"],
                            })
                            total += out["value"]
                            if d < depth:
                                queue.append((out["address"], d + 1))
        except:
            continue

    for e in edges:
        for a in [e["source"], e["target"]]:
            if a not in node_ids:
                nodes.append({
                    "id": a,
                    "label": f"{a[:8]}...{a[-8:]}",
                    "type": "address",
                    "risk_score": 0,
                    "value": 0,
                    "metadata": {"partial": True},
                })
                node_ids.add(a)

    return {"nodes": nodes, "edges": edges, "root_address": root, "depth": depth, "total_value": total}

# ============ Endpoints ============

@app.get("/")
async def root():
    return {"message": "ChainTrace API", "version": "1.0.0"}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/address/{address}")
async def get_address(address: str):
    try:
        return await fetch_address(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/address/{address}/transactions")
async def get_transactions(address: str, limit: int = Query(default=25, le=50)):
    try:
        return await fetch_transactions(address, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/address/{address}/risk")
async def get_risk(address: str):
    try:
        info = await fetch_address(address)
        txs = await fetch_transactions(address)
        return calc_risk(address, info, txs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/graph/{address}")
async def get_graph(
    address: str,
    depth: int = Query(default=2, ge=1, le=3),
    max_nodes: int = Query(default=50, ge=10, le=100),
    min_value: float = Query(default=0.0001, ge=0),
):
    try:
        return await build_graph(address, depth, max_nodes, min_value)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
