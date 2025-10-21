import { createResource, createSignal, Show } from 'solid-js';
import { apiClient } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import type { Strategy, BacktestRequest, MarketDataRequest } from '../types';
import {
  BarChart3,
  TrendingUp,
  Database,
  PlayCircle,
  BarChart,
  Play,
  Calendar,
  DollarSign,
  RefreshCw,
  Trash2,
  Download,
  Settings,
  Info,
  Eye,
  Activity
} from 'lucide-solid';

const UnifiedInterface = () => {
  // Shared resources
  const [results] = createResource(() => apiClient.getBacktestResults());
  const [strategies] = createResource(() => apiClient.getStrategies());
  const [cacheInfo] = createResource(() => apiClient.getCacheInfo());

  // Backtest state
  const [selectedStrategy, setSelectedStrategy] = createSignal<string>('');
  const [startDate, setStartDate] = createSignal<string>('2020-01-01');
  const [endDate, setEndDate] = createSignal<string>('2024-12-31');
  const [initialCapital, setInitialCapital] = createSignal<number>(100000);
  const [isRunning, setIsRunning] = createSignal(false);
  const [backtestResult, setBacktestResult] = createSignal<any>(null);
  const [backtestError, setBacktestError] = createSignal<string>('');

  // Market data state
  const [symbols, setSymbols] = createSignal<string>('');
  const [forceRefresh, setForceRefresh] = createSignal<boolean>(false);
  const [marketData, setMarketData] = createSignal<any>(null);
  const [isMarketDataLoading, setIsMarketDataLoading] = createSignal(false);
  const [marketDataError, setMarketDataError] = createSignal<string>('');

  // Results state
  const [selectedResultStrategy, setSelectedResultStrategy] = createSignal<string>('');
  const [strategyResults, setStrategyResults] = createSignal<any>(null);
  const [isLoadingDetails, setIsLoadingDetails] = createSignal(false);

  // Backtest functions
  const runBacktest = async () => {
    if (!selectedStrategy()) {
      setBacktestError('Please select a strategy');
      return;
    }

    setIsRunning(true);
    setBacktestError('');
    setBacktestResult(null);

    try {
      const request: BacktestRequest = {
        strategy_name: selectedStrategy()!,
        start_date: startDate(),
        end_date: endDate(),
        initial_capital: initialCapital(),
      };

      const response = await apiClient.runBacktest(request);
      setBacktestResult(response);
      results.refetch(); // Refresh results
    } catch (err) {
      setBacktestError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsRunning(false);
    }
  };

  const runAllStrategies = async () => {
    setIsRunning(true);
    setBacktestError('');
    setBacktestResult(null);

    try {
      const response = await apiClient.runAllStrategies(
        startDate(),
        endDate(),
        initialCapital()
      );
      setBacktestResult({ type: 'all', data: response });
      results.refetch(); // Refresh results
    } catch (err) {
      setBacktestError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsRunning(false);
    }
  };

  // Market data functions
  const fetchMarketData = async () => {
    if (!symbols()) {
      setMarketDataError('Please enter at least one symbol');
      return;
    }

    setIsMarketDataLoading(true);
    setMarketDataError('');
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
      cacheInfo.refetch(); // Refresh cache info
    } catch (err) {
      setMarketDataError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsMarketDataLoading(false);
    }
  };

  const clearCache = async () => {
    try {
      const symbolList = symbols() ? symbols().split(',').map(s => s.trim().toUpperCase()) : undefined;
      await apiClient.clearCache(symbolList);
      cacheInfo.refetch();
      setMarketDataError('');
    } catch (err) {
      setMarketDataError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  // Results functions
  const loadStrategyDetails = async (strategyName: string) => {
    setIsLoadingDetails(true);
    setSelectedResultStrategy(strategyName);

    try {
      const details = await apiClient.getStrategyResults(strategyName);
      setStrategyResults(details);
    } catch (err) {
      console.error('Error loading strategy details:', err);
    } finally {
      setIsLoadingDetails(false);
    }
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  return (
    <div class="min-h-screen bg-gray-50">
      {/* Header */}
      <div class="bg-white shadow-lg">
        <div class="container mx-auto px-4 py-4">
          <div class="flex items-center space-x-2">
            <BarChart3 class="h-8 w-8 text-blue-600" />
            <h1 class="text-xl font-bold text-gray-800">Portfolio Manager</h1>
          </div>
        </div>
      </div>

      <main class="container mx-auto px-4 py-8 space-y-8">
        {/* Dashboard Summary */}
        <section>
          <h2 class="text-2xl font-bold text-gray-900 mb-6">Dashboard Overview</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="bg-white rounded-lg shadow p-6">
              <div class="flex items-center">
                <div class="p-2 bg-blue-100 rounded-lg">
                  <BarChart3 class="h-6 w-6 text-blue-600" />
                </div>
                <div class="ml-4">
                  <p class="text-sm font-medium text-gray-600">Total Strategies</p>
                  <p class="text-2xl font-semibold text-gray-900">
                    {results()?.length || 0}
                  </p>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
              <div class="flex items-center">
                <div class="p-2 bg-green-100 rounded-lg">
                  <TrendingUp class="h-6 w-6 text-green-600" />
                </div>
                <div class="ml-4">
                  <p class="text-sm font-medium text-gray-600">Best Performer</p>
                  <p class="text-lg font-semibold text-gray-900">
                    {results()?.[0]?.strategy_name || 'N/A'}
                  </p>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
              <div class="flex items-center">
                <div class="p-2 bg-yellow-100 rounded-lg">
                  <DollarSign class="h-6 w-6 text-yellow-600" />
                </div>
                <div class="ml-4">
                  <p class="text-sm font-medium text-gray-600">Avg Return</p>
                  <p class="text-lg font-semibold text-gray-900">
                    {results()?.length ?
                      `${(results().reduce((acc, r) => acc + (r.total_return || 0), 0) / results().length * 100).toFixed(2)}%`
                      : 'N/A'}
                  </p>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
              <div class="flex items-center">
                <div class="p-2 bg-purple-100 rounded-lg">
                  <Activity class="h-6 w-6 text-purple-600" />
                </div>
                <div class="ml-4">
                  <p class="text-sm font-medium text-gray-600">Cached Symbols</p>
                  <p class="text-lg font-semibold text-gray-900">
                    {cacheInfo()?.unique_symbols || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Strategies and Backtest */}
        <section>
          <h2 class="text-2xl font-bold text-gray-900 mb-6">Strategies & Backtesting</h2>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Strategies */}
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Available Strategies</h3>
              <Show when={!strategies.loading} fallback={<LoadingSpinner />}>
                <Show
                  when={strategies()?.length > 0}
                  fallback={
                    <div class="text-center py-8 text-gray-500">
                      <TrendingUp class="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p>No strategies found</p>
                    </div>
                  }
                >
                  <div class="space-y-3 max-h-96 overflow-y-auto">
                    {strategies()?.map((strategy: Strategy) => (
                      <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                        <div class="flex items-center justify-between mb-2">
                          <h4 class="font-medium text-gray-900">{strategy.name}</h4>
                          <div class="flex space-x-2">
                            <button class="p-1 text-blue-600 hover:bg-blue-50 rounded">
                              <Settings class="h-4 w-4" />
                            </button>
                            <button class="p-1 text-gray-600 hover:bg-gray-50 rounded">
                              <Info class="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                        <p class="text-sm text-gray-600 mb-2">
                          {strategy.description || `A ${strategy.name} trading strategy`}
                        </p>
                        <div class="flex flex-wrap gap-1">
                          {strategy.assets.map((asset) => (
                            <span class="inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                              {asset}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </Show>
              </Show>
            </div>

            {/* Backtest Configuration */}
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Run Backtest</h3>
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Strategy
                  </label>
                  <select
                    value={selectedStrategy()}
                    onInput={(e) => setSelectedStrategy(e.target.value)}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select a strategy</option>
                    {strategies()?.map((strategy) => (
                      <option value={strategy.name}>{strategy.name}</option>
                    ))}
                  </select>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      <Calendar class="h-4 w-4 inline mr-1" />
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
                      <Calendar class="h-4 w-4 inline mr-1" />
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

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    <DollarSign class="h-4 w-4 inline mr-1" />
                    Initial Capital
                  </label>
                  <input
                    type="number"
                    value={initialCapital()}
                    onInput={(e) => setInitialCapital(Number(e.target.value))}
                    min="1000"
                    step="1000"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div class="flex space-x-3">
                  <button
                    onClick={runBacktest}
                    disabled={isRunning() || !selectedStrategy()}
                    class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                  >
                    <Play class="h-4 w-4 mr-2" />
                    {isRunning() ? 'Running...' : 'Run Backtest'}
                  </button>

                  <button
                    onClick={runAllStrategies}
                    disabled={isRunning()}
                    class="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                  >
                    <TrendingUp class="h-4 w-4 mr-2" />
                    {isRunning() ? 'Running All...' : 'Run All'}
                  </button>
                </div>

                <Show when={backtestError()}>
                  <div class="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                    {backtestError()}
                  </div>
                </Show>

                <Show when={backtestResult()}>
                  <div class="p-3 bg-green-100 border border-green-400 text-green-700 rounded-lg">
                    Backtest completed successfully!
                  </div>
                </Show>
              </div>
            </div>
          </div>
        </section>

        {/* Market Data */}
        <section>
          <h2 class="text-2xl font-bold text-gray-900 mb-6">Market Data Management</h2>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Cache Info */}
            <div class="bg-white rounded-lg shadow p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-900">Cache Information</h3>
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
                </div>

                <button
                  onClick={clearCache}
                  class="w-full mt-4 bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center"
                >
                  <Trash2 class="h-4 w-4 mr-2" />
                  Clear Cache
                </button>
              </Show>
            </div>

            {/* Data Fetcher */}
            <div class="lg:col-span-2 bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Fetch Market Data</h3>

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
                  disabled={isMarketDataLoading()}
                  class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                >
                  <RefreshCw class={`h-4 w-4 mr-2 ${isMarketDataLoading() ? 'animate-spin' : ''}`} />
                  {isMarketDataLoading() ? 'Fetching...' : 'Fetch Data'}
                </button>

                <Show when={marketDataError()}>
                  <div class="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                    {marketDataError()}
                  </div>
                </Show>
              </div>
            </div>
          </div>

          {/* Market Data Results */}
          <Show when={marketData()}>
            <div class="mt-6 bg-white rounded-lg shadow">
              <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <h3 class="text-lg font-medium text-gray-900">Market Data Results</h3>
                <button class="text-blue-600 hover:text-blue-800 flex items-center text-sm">
                  <Download class="h-4 w-4 mr-1" />
                  Export CSV
                </button>
              </div>
              <div class="p-6">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(marketData().data).map(([symbol, data]: [string, any]) => (
                    <div class="border border-gray-200 rounded-lg p-4">
                      <h4 class="font-medium text-gray-900 mb-2">{symbol}</h4>
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
        </section>

        {/* Results */}
        <section>
          <h2 class="text-2xl font-bold text-gray-900 mb-6">Backtest Results</h2>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Results Table */}
            <div class="bg-white rounded-lg shadow">
              <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-900">All Results</h3>
              </div>
              <div class="p-6">
                <Show when={!results.loading} fallback={<LoadingSpinner />}>
                  <Show
                    when={results()?.length > 0}
                    fallback={
                      <div class="text-center py-8 text-gray-500">
                        No backtest results available. Run some backtests to see results here.
                      </div>
                    }
                  >
                    <div class="overflow-x-auto">
                      <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                          <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Strategy
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Return
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Sharpe
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                          {results()?.map((result) => (
                            <tr class="hover:bg-gray-50">
                              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {result.strategy_name}
                              </td>
                              <td class="px-6 py-4 whitespace-nowrap text-sm">
                                <span class={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                  (result.total_return || 0) > 0
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-red-100 text-red-800'
                                }`}>
                                  {formatPercentage(result.total_return || 0)}
                                </span>
                              </td>
                              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {(result.sharpe_ratio || 0).toFixed(2)}
                              </td>
                              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <button
                                  onClick={() => loadStrategyDetails(result.strategy_name)}
                                  class="text-blue-600 hover:text-blue-900 flex items-center"
                                >
                                  <Eye class="h-4 w-4 mr-1" />
                                  View
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Show>
                </Show>
              </div>
            </div>

            {/* Strategy Details */}
            <div class="bg-white rounded-lg shadow">
              <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-900">
                  Strategy Details {selectedResultStrategy() && `- ${selectedResultStrategy()}`}
                </h3>
              </div>
              <div class="p-6">
                <Show when={!selectedResultStrategy()}>
                  <div class="text-center py-8 text-gray-500">
                    <BarChart class="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p>Select a strategy from the table to view detailed results.</p>
                  </div>
                </Show>

                <Show when={isLoadingDetails()}>
                  <LoadingSpinner />
                </Show>

                <Show when={strategyResults() && !isLoadingDetails()}>
                  <div class="space-y-6">
                    {/* Portfolio Values Chart */}
                    <div>
                      <h4 class="text-md font-medium text-gray-900 mb-3">Portfolio Performance</h4>
                      <div class="bg-gray-50 p-4 rounded-lg">
                        <div class="grid grid-cols-2 gap-4">
                          <div>
                            <p class="text-sm text-gray-600">Initial Value</p>
                            <p class="text-lg font-semibold">
                              {formatCurrency(strategyResults().portfolio_values[0]?.portfolio_value || 0)}
                            </p>
                          </div>
                          <div>
                            <p class="text-sm text-gray-600">Final Value</p>
                            <p class="text-lg font-semibold">
                              {formatCurrency(
                                strategyResults().portfolio_values[strategyResults().portfolio_values.length - 1]?.portfolio_value || 0
                              )}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Recent Trades */}
                    <div>
                      <h4 class="text-md font-medium text-gray-900 mb-3">Recent Trades</h4>
                      <div class="max-h-64 overflow-y-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                          <thead class="bg-gray-50">
                            <tr>
                              <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                                Date
                              </th>
                              <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                                Symbol
                              </th>
                              <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                                Action
                              </th>
                              <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                                Value
                              </th>
                            </tr>
                          </thead>
                          <tbody class="bg-white divide-y divide-gray-200">
                            {strategyResults().trades.slice(0, 10).map((trade: any) => (
                              <tr>
                                <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                                  {trade.trade_date}
                                </td>
                                <td class="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                                  {trade.symbol}
                                </td>
                                <td class="px-3 py-2 whitespace-nowrap text-sm">
                                  <span class={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                    trade.action === 'BUY'
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-red-100 text-red-800'
                                  }`}>
                                    {trade.action}
                                  </span>
                                </td>
                                <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                                  {formatCurrency(trade.value)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <Show when={strategyResults().trades.length > 10}>
                          <div class="text-center py-2 text-sm text-gray-500">
                            Showing 10 of {strategyResults().trades.length} trades
                          </div>
                        </Show>
                      </div>
                    </div>
                  </div>
                </Show>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default UnifiedInterface;
