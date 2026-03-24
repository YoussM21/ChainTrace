import { useState } from 'react';
import { AddressSearch } from '../components/AddressSearch';
import { AddressInfoCard } from '../components/AddressInfoCard';
import { RiskScoreCard } from '../components/RiskScoreCard';
import { GraphVisualization } from '../components/GraphVisualization';
import { apiService } from '../services/api';
import type { Address, RiskScore, TransactionGraph } from '../types';
import { Network, AlertCircle, Loader2 } from 'lucide-react';

export function HomePage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [address, setAddress] = useState<Address | null>(null);
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);
  const [graph, setGraph] = useState<TransactionGraph | null>(null);
  const [graphSettings, setGraphSettings] = useState({
    depth: 2,
    maxNodes: 100,
    minValue: 0.0001,
  });

  const handleSearch = async (searchAddress: string) => {
    setLoading(true);
    setError(null);
    setAddress(null);
    setRiskScore(null);
    setGraph(null);

    try {
      const [addressData, riskData, graphData] = await Promise.all([
        apiService.getAddressInfo(searchAddress),
        apiService.getAddressRiskScore(searchAddress),
        apiService.buildTransactionGraph(
          searchAddress,
          graphSettings.depth,
          graphSettings.maxNodes,
          graphSettings.minValue
        ),
      ]);

      setAddress(addressData);
      setRiskScore(riskData);
      setGraph(graphData);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = async (node: any) => {
    if (node.type === 'address' && node.id !== address?.address) {
      handleSearch(node.id);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-600 rounded-lg">
              <Network className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">ChainTrace</h1>
              <p className="text-gray-600">Bitcoin Transaction Forensics</p>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        <div className="flex flex-col items-center mb-8">
          <AddressSearch onSearch={handleSearch} loading={loading} />
        </div>

        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-12 h-12 text-primary-600 animate-spin" />
            <p className="mt-4 text-gray-600">Analyzing blockchain data...</p>
          </div>
        )}

        {error && (
          <div className="max-w-2xl mx-auto p-6 bg-red-50 border-2 border-red-200 rounded-lg">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-red-600" />
              <div>
                <h3 className="font-semibold text-red-900">Error</h3>
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {!loading && address && riskScore && graph && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AddressInfoCard address={address} />
              <RiskScoreCard riskScore={riskScore} />
            </div>

            <div>
              <GraphVisualization graph={graph} onNodeClick={handleNodeClick} />
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6 border-2 border-gray-200">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                Graph Settings
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Depth (hops)
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="4"
                    value={graphSettings.depth}
                    onChange={(e) =>
                      setGraphSettings({ ...graphSettings, depth: Number(e.target.value) })
                    }
                    className="w-full"
                  />
                  <span className="text-sm text-gray-600">{graphSettings.depth}</span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Nodes
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="500"
                    step="10"
                    value={graphSettings.maxNodes}
                    onChange={(e) =>
                      setGraphSettings({
                        ...graphSettings,
                        maxNodes: Number(e.target.value),
                      })
                    }
                    className="w-full"
                  />
                  <span className="text-sm text-gray-600">{graphSettings.maxNodes}</span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Min Value (BTC)
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0"
                    value={graphSettings.minValue}
                    onChange={(e) =>
                      setGraphSettings({
                        ...graphSettings,
                        minValue: Number(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded"
                  />
                </div>
              </div>
              <button
                onClick={() => address && handleSearch(address.address)}
                className="mt-4 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Rebuild Graph
              </button>
            </div>
          </div>
        )}

        {!loading && !address && !error && (
          <div className="text-center py-20">
            <Network className="w-20 h-20 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-gray-700 mb-2">
              Start Your Investigation
            </h2>
            <p className="text-gray-600 max-w-md mx-auto">
              Enter a Bitcoin address above to analyze transaction patterns, assess risk
              scores, and visualize the flow of funds across the network.
            </p>
          </div>
        )}
      </main>

      <footer className="bg-white border-t border-gray-200 mt-20">
        <div className="container mx-auto px-6 py-6 text-center text-gray-600 text-sm">
          <p>ChainTrace - Bitcoin Forensics Tool</p>
          <p className="mt-1">Educational purposes only. Not financial advice.</p>
        </div>
      </footer>
    </div>
  );
}
