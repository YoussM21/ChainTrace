import { useEffect, useRef, useState, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { TransactionGraph } from '../types';
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

interface GraphVisualizationProps {
  graph: TransactionGraph;
  onNodeClick?: (node: any) => void;
}

interface InternalNode {
  id: string;
  label: string;
  type: string;
  risk_score: number;
  value: number;
  partial?: boolean;
  [key: string]: any;
}

export function GraphVisualization({ graph, onNodeClick }: GraphVisualizationProps) {
  const graphRef = useRef<any>();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const updateDimensions = () => {
      const container = document.getElementById('graph-container');
      if (container) {
        setDimensions({
          width: container.clientWidth,
          height: Math.max(600, window.innerHeight - 300),
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Memoize graph data to prevent unnecessary re-renders and ensure stability
  const graphData = useMemo(() => {
    // Build a set of node IDs for validation
    const nodeIds = new Set(graph.nodes.map((node) => node.id));

    // Create nodes from the graph data
    const nodes: InternalNode[] = graph.nodes.map((node) => ({
      id: node.id,
      label: node.label,
      type: node.type,
      risk_score: node.risk_score || 0,
      value: node.value || 0,
      ...node.metadata,
    }));

    // Find any missing nodes referenced in edges
    const missingNodeIds = new Set<string>();
    for (const edge of graph.edges) {
      if (!nodeIds.has(edge.source)) missingNodeIds.add(edge.source);
      if (!nodeIds.has(edge.target)) missingNodeIds.add(edge.target);
    }

    // Add placeholder nodes for missing addresses
    for (const id of missingNodeIds) {
      nodes.push({
        id,
        label: `${id.slice(0, 8)}...${id.slice(-8)}`,
        type: 'address',
        risk_score: 0,
        value: 0,
        partial: true,
      });
    }

    return {
      nodes,
      links: graph.edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
        value: edge.value,
        tx_hash: edge.tx_hash,
      })),
    };
  }, [graph]);

  const getNodeColor = (node: any) => {
    if (node.id === graph.root_address) {
      return '#3b82f6'; // Blue for root
    }

    // Gray for partial/unvisited nodes
    if (node.partial) {
      return '#6b7280';
    }

    const riskScore = node.risk_score || 0;
    if (riskScore >= 75) return '#ef4444'; // Red - Critical
    if (riskScore >= 50) return '#f97316'; // Orange - High
    if (riskScore >= 25) return '#eab308'; // Yellow - Medium
    return '#22c55e'; // Green - Low
  };

  const getNodeVal = (node: any) => {
    if (node.id === graph.root_address) return 8;
    if (node.partial) return 2;
    const value = node.value || 0;
    return Math.max(2, Math.min(10, Math.log(value + 1) * 2));
  };

  const handleZoomIn = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() * 1.2, 400);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() * 0.8, 400);
    }
  };

  const handleFitView = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 50);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg border-2 border-gray-200 overflow-hidden">
      <div className="p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Transaction Graph</h2>
          <p className="text-sm text-gray-600">
            {graphData.nodes.length} nodes, {graphData.links.length} edges, depth: {graph.depth}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleZoomIn}
            className="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50"
            title="Zoom In"
          >
            <ZoomIn className="w-5 h-5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50"
            title="Zoom Out"
          >
            <ZoomOut className="w-5 h-5" />
          </button>
          <button
            onClick={handleFitView}
            className="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50"
            title="Fit View"
          >
            <Maximize2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div id="graph-container" className="bg-gray-900">
        <ForceGraph2D
          key={`${graph.root_address}-${graph.depth}`}
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          nodeLabel={(node: any) =>
            `${node.label}\nRisk: ${node.risk_score?.toFixed(1) || 'N/A'}\nValue: ${
              node.value?.toFixed(4) || '0'
            } BTC`
          }
          nodeColor={getNodeColor}
          nodeVal={getNodeVal}
          linkColor={() => '#4b5563'}
          linkWidth={(link: any) => Math.max(1, Math.log(link.value + 1))}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.15}
          onNodeClick={onNodeClick}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          cooldownTicks={100}
          onEngineStop={() => graphRef.current?.zoomToFit(400, 50)}
        />
      </div>

      <div className="p-4 bg-gray-50 border-t border-gray-200">
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-500" />
            <span>Root Address</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500" />
            <span>Low Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500" />
            <span>Medium Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-orange-500" />
            <span>High Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500" />
            <span>Critical Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gray-500" />
            <span>Not Analyzed</span>
          </div>
        </div>
      </div>
    </div>
  );
}
