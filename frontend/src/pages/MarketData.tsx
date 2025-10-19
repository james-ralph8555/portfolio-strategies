import { createResource, createSignal, Show } from 'solid-js';
import { apiClient } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import type { MarketDataRequest } from '../types';
import { Database, RefreshCw, Trash2, Download } from 'lucide-solid';

const MarketData = () => {
  const [cacheInfo] = createResource(() => apiClient.getCacheInfo());
  const [symbols, setSymbols] = createSignal<string>('');
  const [startDate, setStartDate] = createSignal<string>('2020-01-01');
  const [endDate, setEndDate] = createSignal<string>('2024-12-31');
  const [forceRefresh, setForceRefresh] = createSignal<boolean>(false);
  const [marketData, setMarketData] = createSignal<any>(null);
  const [isLoading, setIsLoading] = createSignal(false);
  const [error, setError] = createSignal<string>('');

  const fetchMarketData = async () => {
    if (!symbols()) {
      setError('Please enter at least one symbol');
      return;
    }

    setIsLoading(true);
    setError('');
    setMarketData(null);

    try {
      const symbolList = symbols().split(',').map(s => s.trim().toUpperCase());
      const request: MarketDataRequest = {
        symbols: symbolList,
        start_date: startDate(),
        end_date: endDate(),
        force_refresh: forceRefresh(),
      };

      const response = await apiClient.getMarketData(request);
      setMarketData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const clearCache = async () => {
    try {
      const symbolList = symbols() ? symbols().split(',').map(s => s.trim().toUpperCase()) : undefined;
      await apiClient.clearCache(symbolList);
      // Refresh cache info
      cacheInfo.refetch();
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  return (
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">Market Data</h1>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cache Info */}
        <div class="lg:col-span-1">
          <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-gray-900">Cache Information</h2>
              <Database class="h-5 w-5 text-gray-400" />
            </div>

            <Show when={!cacheInfo.loading} fallback={<LoadingSpinner />}>
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Unique Symbols</span>
                  <span class="text-sm font-medium">{cacheInfo()?.unique_symbols || 0}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Total Records</span>
                  <span class="text-sm font-medium">{cacheInfo()?.total_records || 0}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Earliest Date</span>
                  <span class="text-sm font-medium">{cacheInfo()?.earliest_date || 'N/A'}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Latest Date</span>
                  <span class="text-sm font-medium">{cacheInfo()?.latest_date || 'N/A'}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Cache Duration</span>
                  <span class="text-sm font-medium">{cacheInfo()?.cache_duration_days || 0} days</span>
                </div>
              </div>

              <div class="mt-4 pt-4 border-t border-gray-200">
                <button
                  onClick={clearCache}
                  class="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center"
                >
                  <Trash2 class="h-4 w-4 mr-2" />
                  Clear Cache
                </button>
              </div>
            </Show>
          </div>
        </div>

        {/* Data Fetcher */}
        <div class="lg:col-span-2">
          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Fetch Market Data</h2>

            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Symbols (comma-separated)
                </label>
                <input
                  type="text"
                  value={symbols()}
                  onInput={(e) => setSymbols(e.target.value)}
                  placeholder="AAPL, GOOGL, MSFT, TSLA"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={startDate()}
                    onInput={(e) => setStartDate(e.target.value)}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={endDate()}
                    onInput={(e) => setEndDate(e.target.value)}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="forceRefresh"
                  checked={forceRefresh()}
                  onChange={(e) => setForceRefresh(e.target.checked)}
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label for="forceRefresh" class="ml-2 text-sm text-gray-700">
                  Force refresh from API
                </label>
              </div>

              <button
                onClick={fetchMarketData}
                disabled={isLoading()}
                class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
              >
                <RefreshCw class={`h-4 w-4 mr-2 ${isLoading() ? 'animate-spin' : ''}`} />
                {isLoading() ? 'Fetching...' : 'Fetch Data'}
              </button>

              <Show when={error()}>
                <div class="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                  {error()}
                </div>
              </Show>
            </div>
          </div>
        </div>
      </div>

      {/* Data Results */}
      <Show when={marketData()}>
        <div class="bg-white rounded-lg shadow">
          <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 class="text-lg font-medium text-gray-900">Market Data Results</h2>
            <button class="text-blue-600 hover:text-blue-800 flex items-center text-sm">
              <Download class="h-4 w-4 mr-1" />
              Export CSV
            </button>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(marketData().data).map(([symbol, data]: [string, any]) => (
                <div class="border border-gray-200 rounded-lg p-4">
                  <h3 class="font-medium text-gray-900 mb-2">{symbol}</h3>
                  <div class="text-sm text-gray-600">
                    <p>Data points: {data.length}</p>
                    <p>Start: {data[0]?.date || 'N/A'}</p>
                    <p>End: {data[data.length - 1]?.date || 'N/A'}</p>
                    <p>Latest price: ${data[data.length - 1]?.price?.toFixed(2) || 'N/A'}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Show>
    </div>
  );
};

export default MarketData;
