import { Wallet, ArrowUpRight, ArrowDownLeft, Activity } from 'lucide-react';
import type { Address } from '../types';

interface AddressInfoCardProps {
  address: Address;
}

export function AddressInfoCard({ address }: AddressInfoCardProps) {
  const formatBTC = (value: number) => {
    return value.toFixed(8);
  };

  const formatUSD = (btc: number, btcPrice: number = 45000) => {
    return (btc * btcPrice).toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 border-2 border-gray-200">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-primary-100 rounded-lg">
          <Wallet className="w-6 h-6 text-primary-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold text-gray-800">Address Info</h2>
          <p className="text-xs text-gray-500 font-mono truncate">{address.address}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
          <div className="flex items-center gap-2 text-green-700 mb-2">
            <ArrowDownLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Total Received</span>
          </div>
          <p className="text-xl font-bold text-green-900">
            {formatBTC(address.total_received)} BTC
          </p>
          <p className="text-xs text-green-600">
            {formatUSD(address.total_received)}
          </p>
        </div>

        <div className="p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200">
          <div className="flex items-center gap-2 text-red-700 mb-2">
            <ArrowUpRight className="w-4 h-4" />
            <span className="text-sm font-medium">Total Sent</span>
          </div>
          <p className="text-xl font-bold text-red-900">
            {formatBTC(address.total_sent)} BTC
          </p>
          <p className="text-xs text-red-600">
            {formatUSD(address.total_sent)}
          </p>
        </div>

        <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2 text-blue-700 mb-2">
            <Wallet className="w-4 h-4" />
            <span className="text-sm font-medium">Current Balance</span>
          </div>
          <p className="text-xl font-bold text-blue-900">
            {formatBTC(address.balance)} BTC
          </p>
          <p className="text-xs text-blue-600">
            {formatUSD(address.balance)}
          </p>
        </div>

        <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
          <div className="flex items-center gap-2 text-purple-700 mb-2">
            <Activity className="w-4 h-4" />
            <span className="text-sm font-medium">Transactions</span>
          </div>
          <p className="text-xl font-bold text-purple-900">
            {address.tx_count.toLocaleString()}
          </p>
          <p className="text-xs text-purple-600">
            Total activity
          </p>
        </div>
      </div>
    </div>
  );
}
