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

KNOWN_HIGH_RISK = {
    "1HQ3Go3ggs8pFnXuHVHRytPCq5fGG8Hbhx": "Binance Hot Wallet",
    "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h": "Binance",
    "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s": "Binance Cold Wallet",
    "385cR5DM96n1HvBDMzLHPYcw89fZAXULJP": "Binance-BTC-Cold",
}

SANCTIONED_ADDRESSES = {
    "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh": "OFAC Sanctioned",
    "12t9YDPgwueZ9NyMgw519p7AA8isjr6SMw": "OFAC Sanctioned",
}

def calc_risk(address: str, addr_info: dict, txs: list) -> dict:
    factors = {}
    flags = []
    tx_count = addr_info["tx_count"]
    total_received = addr_info["total_received"]
    total_sent = addr_info["total_sent"]
    balance = addr_info["balance"]

    # 1. Transaction Frequency
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

    # 2. High Velocity (rapid fund movement)
    if total_received > 0:
        ratio = total_sent / total_received
        if ratio > 0.95 and tx_count > 10:
            factors["high_velocity"] = 40.0
            flags.append("RAPID_FUND_MOVEMENT")
        else:
            factors["high_velocity"] = ratio * 20
    else:
        factors["high_velocity"] = 0

    # 3. Mixing Pattern Detection
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

    # 4. Round Number Transactions (structuring/layering)
    round_count = 0
    for tx in txs[:15]:
        for out in tx["outputs"]:
            val = out["value"]
            if val > 0.01 and (val == round(val, 1) or val == round(val, 0)):
                round_count += 1
    if round_count >= 5:
        factors["round_numbers"] = min(round_count * 5, 40)
        flags.append("STRUCTURING_PATTERN")
    else:
        factors["round_numbers"] = round_count * 3

    # 5. Large Value Transfers
    large_transfers = 0
    for tx in txs:
        if tx["total_output"] > 10:  # > 10 BTC
            large_transfers += 1
    if large_transfers > 0:
        factors["large_transfers"] = min(large_transfers * 15, 50)
        if large_transfers >= 3:
            flags.append("LARGE_VALUE_TRANSFERS")
    else:
        factors["large_transfers"] = 0

    # 6. Dormant Address Reactivation
    if tx_count <= 5 and total_received > 1:
        factors["dormant_reactivation"] = 30.0
        flags.append("LOW_ACTIVITY_HIGH_VALUE")
    else:
        factors["dormant_reactivation"] = 0

    # 7. Known Exchange/Service Detection
    if address in KNOWN_HIGH_RISK:
        factors["known_entity"] = 20.0
        flags.append(f"KNOWN_ENTITY: {KNOWN_HIGH_RISK[address]}")
    else:
        factors["known_entity"] = 0

    # 8. Sanctioned Address Check
    if address in SANCTIONED_ADDRESSES:
        factors["sanctioned"] = 100.0
        flags.append(f"SANCTIONED_ADDRESS: {SANCTIONED_ADDRESSES[address]}")
    else:
        factors["sanctioned"] = 0

    # 9. Peeling Chain Detection (many small outputs, one large change)
    peeling_score = 0
    for tx in txs[:10]:
        outputs = tx["outputs"]
        if len(outputs) >= 2:
            values = sorted([o["value"] for o in outputs], reverse=True)
            if len(values) >= 2 and values[0] > sum(values[1:]) * 5:
                peeling_score += 8
    factors["peeling_chain"] = min(peeling_score, 40)
    if peeling_score > 20:
        flags.append("PEELING_CHAIN_PATTERN")

    # 10. Fan-out Pattern (one input, many outputs)
    fanout_score = 0
    for tx in txs[:10]:
        if len(tx["inputs"]) <= 2 and len(tx["outputs"]) > 10:
            fanout_score += 10
    factors["fanout_pattern"] = min(fanout_score, 40)
    if fanout_score > 20:
        flags.append("DISTRIBUTION_PATTERN")

    # Calculate overall score (weighted average)
    weights = {
        "transaction_frequency": 1.0,
        "high_velocity": 1.2,
        "mixing_pattern": 1.5,
        "round_numbers": 0.8,
        "large_transfers": 1.0,
        "dormant_reactivation": 0.7,
        "known_entity": 0.5,
        "sanctioned": 2.0,
        "peeling_chain": 1.3,
        "fanout_pattern": 1.0,
    }

    weighted_sum = sum(factors[k] * weights.get(k, 1.0) for k in factors)
    total_weight = sum(weights.get(k, 1.0) for k in factors)
    overall = weighted_sum / total_weight if total_weight > 0 else 0

    # Determine risk level
    if overall >= 70 or "SANCTIONED_ADDRESS" in str(flags):
        level = "CRITICAL"
    elif overall >= 50:
        level = "HIGH"
    elif overall >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "address": address,
        "overall_score": round(overall, 1),
        "factors": {k: round(v, 1) for k, v in factors.items()},
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
