import { AlertTriangle, Shield, AlertCircle, XCircle } from 'lucide-react';
import type { RiskScore } from '../types';

interface RiskScoreCardProps {
  riskScore: RiskScore;
}

export function RiskScoreCard({ riskScore }: RiskScoreCardProps) {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'MEDIUM':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'HIGH':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'CRITICAL':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'LOW':
        return <Shield className="w-8 h-8" />;
      case 'MEDIUM':
        return <AlertCircle className="w-8 h-8" />;
      case 'HIGH':
        return <AlertTriangle className="w-8 h-8" />;
      case 'CRITICAL':
        return <XCircle className="w-8 h-8" />;
      default:
        return <Shield className="w-8 h-8" />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score < 25) return 'bg-green-500';
    if (score < 50) return 'bg-yellow-500';
    if (score < 75) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 border-2 border-gray-200">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Risk Assessment</h2>

      <div
        className={`flex items-center gap-4 p-4 rounded-lg border-2 ${getRiskColor(
          riskScore.risk_level
        )}`}
      >
        {getRiskIcon(riskScore.risk_level)}
        <div className="flex-1">
          <div className="flex justify-between items-center mb-2">
            <span className="text-lg font-semibold">{riskScore.risk_level} RISK</span>
            <span className="text-2xl font-bold">{riskScore.overall_score.toFixed(1)}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${getScoreColor(
                riskScore.overall_score
              )}`}
              style={{ width: `${riskScore.overall_score}%` }}
            />
          </div>
        </div>
      </div>

      {riskScore.flags.length > 0 && (
        <div className="mt-6">
          <h3 className="font-semibold text-gray-700 mb-3">Risk Flags</h3>
          <div className="space-y-2">
            {riskScore.flags.map((flag, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm"
              >
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{flag.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-6">
        <h3 className="font-semibold text-gray-700 mb-3">Risk Factors</h3>
        <div className="space-y-2">
          {Object.entries(riskScore.factors).map(([factor, score]) => (
            <div key={factor}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">
                  {factor.replace(/_/g, ' ').toUpperCase()}
                </span>
                <span className="font-medium">{score.toFixed(1)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${getScoreColor(score)}`}
                  style={{ width: `${score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
