export interface Address {
  address: string;
  balance: number;
  total_received: number;
  total_sent: number;
  tx_count: number;
  first_seen?: string;
  last_seen?: string;
}

export interface TransactionInput {
  address: string;
  value: number;
  prev_hash: string;
  output_index: number;
}

export interface TransactionOutput {
  address: string;
  value: number;
  spent: boolean;
}

export interface Transaction {
  hash: string;
  time: string;
  inputs: TransactionInput[];
  outputs: TransactionOutput[];
  fee: number;
  block_height?: number;
  confirmations: number;
  total_input: number;
  total_output: number;
}

export interface RiskScore {
  address: string;
  overall_score: number;
  factors: Record<string, number>;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  flags: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'address' | 'transaction';
  risk_score?: number;
  value?: number;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  value: number;
  timestamp?: string;
  tx_hash?: string;
}

export interface TransactionGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  root_address: string;
  depth: number;
  total_value: number;
}

export interface ClusteringResult {
  address: string;
  clusters: Record<string, string[]>;
  peeling_chain: string[];
  mixing_behavior: {
    mixing_score: number;
    indicators: string[];
    is_likely_mixing: boolean;
  };
}
