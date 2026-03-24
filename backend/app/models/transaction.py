from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class TransactionInput(BaseModel):
    address: str
    value: float
    prev_hash: str
    output_index: int


class TransactionOutput(BaseModel):
    address: str
    value: float
    spent: bool = False


class Transaction(BaseModel):
    hash: str
    time: datetime
    inputs: List[TransactionInput]
    outputs: List[TransactionOutput]
    fee: float
    block_height: Optional[int] = None
    confirmations: int = 0
    total_input: float = 0
    total_output: float = 0


class Address(BaseModel):
    address: str
    balance: float
    total_received: float
    total_sent: float
    tx_count: int
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class RiskScore(BaseModel):
    address: str
    overall_score: float = Field(..., ge=0, le=100, description="Risk score from 0-100")
    factors: Dict[str, float] = Field(default_factory=dict)
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    flags: List[str] = Field(default_factory=list)


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # 'address' or 'transaction'
    risk_score: Optional[float] = None
    value: Optional[float] = None
    metadata: Dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    value: float
    timestamp: Optional[datetime] = None
    tx_hash: Optional[str] = None


class TransactionGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    root_address: str
    depth: int
    total_value: float
