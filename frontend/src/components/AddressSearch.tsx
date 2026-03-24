import { useState } from 'react';
import { Search } from 'lucide-react';

interface AddressSearchProps {
  onSearch: (address: string) => void;
  loading?: boolean;
}

export function AddressSearch({ onSearch, loading }: AddressSearchProps) {
  const [address, setAddress] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (address.trim()) {
      onSearch(address.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl">
      <div className="relative">
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Enter Bitcoin address to trace..."
          className="w-full px-6 py-4 pr-12 text-lg border-2 border-gray-300 rounded-lg focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !address.trim()}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          <Search className="w-6 h-6" />
        </button>
      </div>
      <p className="mt-2 text-sm text-gray-600">
        Example: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa (Genesis block address)
      </p>
    </form>
  );
}
