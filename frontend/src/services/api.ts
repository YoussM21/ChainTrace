import axios from 'axios';
import type {
  Address,
  Transaction,
  RiskScore,
  TransactionGraph,
  ClusteringResult,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const apiService = {
  // Address endpoints
  async getAddressInfo(address: string): Promise<Address> {
    const response = await api.get<Address>(`/address/${address}`);
    return response.data;
  },

  async getAddressTransactions(
    address: string,
    limit: number = 50,
    before?: number
  ): Promise<Transaction[]> {
    const params: any = { limit };
    if (before) params.before = before;
    const response = await api.get<Transaction[]>(
      `/address/${address}/transactions`,
      { params }
    );
    return response.data;
  },

  async getAddressRiskScore(address: string): Promise<RiskScore> {
    const response = await api.get<RiskScore>(`/address/${address}/risk`);
    return response.data;
  },

  // Transaction endpoints
  async getTransaction(txHash: string): Promise<Transaction> {
    const response = await api.get<Transaction>(`/transaction/${txHash}`);
    return response.data;
  },

  // Graph endpoints
  async buildTransactionGraph(
    address: string,
    depth: number = 2,
    maxNodes: number = 100,
    minValue: number = 0.0001
  ): Promise<TransactionGraph> {
    const response = await api.get<TransactionGraph>(`/graph/${address}`, {
      params: { depth, max_nodes: maxNodes, min_value: minValue },
      timeout: 120000, // 2 minutes for graph building (can be slow at higher depths)
    });
    return response.data;
  },

  async getGraphMetrics(
    address: string,
    depth: number = 2,
    maxNodes: number = 100
  ): Promise<any> {
    const response = await api.get(`/graph/${address}/metrics`, {
      params: { depth, max_nodes: maxNodes },
    });
    return response.data;
  },

  // Clustering endpoints
  async getAddressClustering(address: string): Promise<ClusteringResult> {
    const response = await api.get<ClusteringResult>(
      `/address/${address}/clustering`
    );
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<any> {
    const response = await api.get('/health');
    return response.data;
  },
};
