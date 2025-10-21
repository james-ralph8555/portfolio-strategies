import { createEffect, createResource, createSignal, Show } from 'solid-js';
import { apiClient } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import type { Strategy, BacktestRequest, MarketDataRequest } from '../types';
import TimeSeriesChart, { type ChartSeries } from '../components/TimeSeriesChart';
import {
  BarChart3,
  TrendingUp,
  Database,
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
  Activity,
  Bug,
  FileText
} from 'lucide-solid';

const UnifiedInterface = () => {
  // Shared resources
  const [results, refetchResults] = createResource(() => apiClient.getBacktestResults());
  const [strategies] = createResource(() => apiClient.getStrategies());
  const [cacheInfo, refetchCacheInfo] = createResource(() => apiClient.getCacheInfo());

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
  const [strategyTraces, setStrategyTraces] = createSignal<any>(null);
  const [expandedTraceLogs, setExpandedTraceLogs] = createSignal<Record<string, boolean>>({});
  const [traceFilters, setTraceFilters] = createSignal<{level: string, category: string}>({level: '', category: ''});

  // Time Series Viewer state
  type SeriesSource =
    | { kind: 'market'; symbol: string }
    | { kind: 'backtest'; strategyName: string };

  type SeriesEntry = {
    id: string;
    label: string;
    color: string;
    visible: boolean;
    source: SeriesSource;
  };

  const [seriesList, setSeriesList] = createSignal<SeriesEntry[]>([]);
  const [normalize, setNormalize] = createSignal<boolean>(true);

  // Simple color palette for series
  const palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#17becf', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22'];
  let colorIndex = 0;
  const nextColor = () => palette[(colorIndex++) % palette.length];

  // Cache strategy details to avoid refetching repeatedly
  const [strategyCache, setStrategyCache] = createSignal<Record<string, any>>({});
  const getStrategyCached = async (strategyName: string) => {
    const cache = strategyCache();
    if (cache[strategyName]) return cache[strategyName];
    const details = await apiClient.getStrategyResults(strategyName);
    setStrategyCache({ ...cache, [strategyName]: details });
    return details;
  };

  // Helpers: compute normalized y values
  const normalizeSeries = (values: number[]) => {
    if (!normalize() || values.length === 0) return values;
    const base = values[0] || 1;
    return values.map((v) => (v / base) * 100);
  };

  // Build Plotly series from seriesList + current data
  const buildChartSeries = async (): Promise<ChartSeries[]> => {
    const out: ChartSeries[] = [];
    for (const s of seriesList()) {
      if (s.source.kind === 'market') {
        const symbol = s.source.symbol;
        const md = marketData();
        const rows = md?.data?.[symbol] || [];
        const x = rows.map((r: any) => r.date);
        const yRaw = rows.map((r: any) => Number(r.price));
        const y = normalizeSeries(yRaw);
        out.push({ id: s.id, name: s.label, x, y, color: s.color, visible: s.visible, yaxis: 'y' });
      } else if (s.source.kind === 'backtest') {
        const details = strategyCache()[s.source.strategyName] || await getStrategyCached(s.source.strategyName);
        const rows = details?.portfolio_values || [];
        const x = rows.map((r: any) => r.date);
        const yRaw = rows.map((r: any) => Number(r.portfolio_value));
        const y = normalizeSeries(yRaw);
        out.push({ id: s.id, name: s.label, x, y, color: s.color, visible: s.visible, yaxis: 'y2' });
      }
    }
    return out;
  };

  const [chartSeries, setChartSeries] = createSignal<ChartSeries[]>([]);

  // Keep chartSeries in sync when inputs change
  const refreshChartSeries = async () => {
    const traces = await buildChartSeries();
    setChartSeries(traces);
  };

  createEffect(() => {
    // Track dependencies
    void seriesList().length;
    void normalize();
    void marketData();
    void strategyCache();
    refreshChartSeries();
  });

  // Adders/removers
  const addMarketSymbolToChart = (symbol: string) => {
    if (!marketData()?.data?.[symbol]) return;
    if (seriesList().some((s) => s.source.kind === 'market' && s.source.symbol === symbol)) return;
    setSeriesList((prev) => [
      ...prev,
      { id: `m-${symbol}`, label: `${symbol} (Price)`, color: nextColor(), visible: true, source: { kind: 'market', symbol } },
    ]);
  };

  const addBacktestToChart = async (strategyName: string) => {
    if (seriesList().some((s) => s.source.kind === 'backtest' && s.source.strategyName === strategyName)) return;
    // Load cache if needed
    await getStrategyCached(strategyName);
    setSeriesList((prev) => [
      ...prev,
      { id: `b-${strategyName}`, label: `${strategyName} (Portfolio)`, color: nextColor(), visible: true, source: { kind: 'backtest', strategyName } },
    ]);
  };

  const removeSeries = (id: string) => {
    setSeriesList(seriesList().filter((s) => s.id !== id));
  };

  const toggleSeriesVisibility = (id: string) => {
    setSeriesList(seriesList().map((s) => (s.id === id ? { ...s, visible: !s.visible } : s)));
  };

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
      refetchResults(); // Refresh results
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
      refetchResults(); // Refresh results
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
      refetchCacheInfo(); // Refresh cache info
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
      refetchCacheInfo();
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

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'text-red-600 bg-red-50';
      case 'WARNING': return 'text-yellow-600 bg-yellow-50';
      case 'INFO': return 'text-blue-600 bg-blue-50';
      case 'DEBUG': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'REBALANCE': return '🔄';
      case 'WEIGHT_CALC': return '⚖️';
      case 'PORTFOLIO': return '💼';
      case 'TRADE': return '💱';
      case 'PERFORMANCE': return '📊';
      case 'BACKTEST': return '🚀';
      default: return '📝';
    }
  };

  const setTraceFilter = (type: 'level' | 'category', value: string) => {
    setTraceFilters(prev => ({
      ...prev,
      [type]: value
    }));
  };

  const toggleTraceLogs = async (strategyName: string) => {
    const isExpanded = expandedTraceLogs()[strategyName];

    // Toggle the expanded state
    setExpandedTraceLogs(prev => ({
      ...prev,
      [strategyName]: !isExpanded
    }));

    // Always ensure the strategy is selected when toggling traces
    if (selectedResultStrategy() !== strategyName) {
      await loadStrategyDetails(strategyName);
    }

    // If we're expanding and haven't loaded traces yet, load them
    if (!isExpanded && (!strategyTraces() || selectedResultStrategy() !== strategyName)) {
      try {
        const traces = await apiClient.getStrategyTraces(strategyName);
        setStrategyTraces(traces);
      } catch (err) {
        console.error('Error loading trace logs:', err);
      }
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

  // WebSocket: refresh on server events
  createEffect(() => {
    // Resolve WS base similar to API base
    const envBase = (import.meta as any).env?.VITE_API_BASE_URL as string | undefined;
    let base = envBase && envBase.trim() ? envBase.replace(/\/$/, '') : '/api';
    const isAbsolute = /^https?:\/\//i.test(base);
    let wsUrl: string;
    if (isAbsolute) {
      wsUrl = base.replace(/^http/i, 'ws') + '/ws';
    } else {
      // Relative to current host
      wsUrl = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + base + '/ws';
    }
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = async () => {
        // On any message, refresh results and any backtest series in cache
        refetchResults();
        const backtests = seriesList().filter((s) => s.source.kind === 'backtest');
        if (backtests.length) {
          const cache = { ...strategyCache() };
          for (const s of backtests) {
            delete cache[(s.source as any).strategyName];
          }
          setStrategyCache(cache);
          // Trigger refresh
          await refreshChartSeries();
        }
      };
    } catch (e) {
      console.warn('WS init failed', e);
    }
    return () => {
      if (ws) {
        try { ws.close(); } catch {}
      }
    };
  });

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
          <h2 class="text-2xl font-bold text-gray-900 mb-6">Time Series Viewer</h2>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Controls */}
            <div class="bg-white rounded-lg shadow p-6 space-y-4">
              <h3 class="text-lg font-semibold text-gray-900">Add Series</h3>

              {/* Market symbols */}
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm font-medium text-gray-700">Market Symbols</span>
                  <button
                    class="text-blue-600 text-sm hover:underline"
                    onClick={() => {
                      const md = marketData();
                      if (!md) return;
                      Object.keys(md.data || {}).forEach((sym) => addMarketSymbolToChart(sym));
                    }}
                  >
                    Add All
                  </button>
                </div>
                <div class="max-h-40 overflow-y-auto border rounded">
                  <Show when={marketData() && Object.keys(marketData()!.data || {}).length > 0} fallback={<div class="p-3 text-sm text-gray-500">Fetch market data above to enable.</div>}>
                    <ul class="divide-y">
                      {Object.keys(marketData()!.data).map((sym) => (
                        <li class="flex items-center justify-between px-3 py-2">
                          <span class="text-sm">{sym}</span>
                          <button class="text-blue-600 text-sm hover:underline" onClick={() => addMarketSymbolToChart(sym)}>Add</button>
                        </li>
                      ))}
                    </ul>
                  </Show>
                </div>
              </div>

              {/* Backtest strategies */}
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm font-medium text-gray-700">Backtests</span>
                </div>
                <div class="max-h-40 overflow-y-auto border rounded">
                  <Show when={!results.loading && (results()?.length || 0) > 0} fallback={<div class="p-3 text-sm text-gray-500">Run backtests to enable.</div>}>
                    <ul class="divide-y">
                      {results()?.map((r: any) => (
                        <li class="flex items-center justify-between px-3 py-2">
                          <span class="text-sm">{r.strategy_name}</span>
                          <button class="text-blue-600 text-sm hover:underline" onClick={() => addBacktestToChart(r.strategy_name)}>Add</button>
                        </li>
                      ))}
                    </ul>
                  </Show>
                </div>
              </div>

              {/* Options */}
              <div class="pt-2 border-t">
                <label class="inline-flex items-center space-x-2 text-sm text-gray-700">
                  <input type="checkbox" checked={normalize()} onChange={(e) => setNormalize(e.currentTarget.checked)} class="h-4 w-4 text-blue-600" />
                  <span>Normalize series to 100</span>
                </label>
                <button class="ml-4 text-sm text-red-600 hover:underline" onClick={() => setSeriesList([])}>Clear Chart</button>
              </div>
            </div>

            {/* Chart + Series list */}
            <div class="lg:col-span-2 space-y-4">
              <div class="bg-white rounded-lg shadow p-4">
                <TimeSeriesChart
                  series={chartSeries()}
                  height={460}
                  layout={{
                    yaxis: { title: normalize() ? 'Index (100 = start)' : 'Value' },
                    yaxis2: { title: normalize() ? 'Index (100 = start)' : 'Value (axis 2)' },
                  }}
                />
              </div>

              <div class="bg-white rounded-lg shadow p-4">
                <h4 class="text-md font-medium text-gray-900 mb-3">Series</h4>
                <Show when={seriesList().length > 0} fallback={<div class="text-sm text-gray-500">No series added yet.</div>}>
                  <ul class="divide-y">
                    {seriesList().map((s) => (
                      <li class="flex items-center justify-between py-2">
                        <div class="flex items-center space-x-3">
                          <span class="inline-block h-3 w-3 rounded-full" style={{ background: s.color }} />
                          <span class="text-sm">{s.label}</span>
                          <span class="text-xs text-gray-500">{s.source.kind === 'market' ? 'Market' : 'Backtest'}</span>
                        </div>
                        <div class="flex items-center space-x-3">
                          <button class="text-sm text-gray-700 hover:underline" onClick={() => toggleSeriesVisibility(s.id)}>
                            {s.visible ? 'Hide' : 'Show'}
                          </button>
                          <button class="text-sm text-red-600 hover:underline" onClick={() => removeSeries(s.id)}>Remove</button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </Show>
              </div>
            </div>
          </div>
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
                                 <div class="flex gap-2">
                                   <button
                                     onClick={() => loadStrategyDetails(result.strategy_name)}
                                     class="text-blue-600 hover:text-blue-900 flex items-center px-2 py-1 rounded border border-blue-300 hover:bg-blue-50 transition-colors"
                                   >
                                     <Eye class="h-4 w-4 mr-1" />
                                     Details
                                   </button>
                                   <button
                                     onClick={() => {
                                       loadStrategyDetails(result.strategy_name);
                                       // Expand trace logs after loading details
                                       setTimeout(() => toggleTraceLogs(result.strategy_name), 100);
                                     }}
                                     class={`flex items-center px-2 py-1 rounded text-xs transition-colors ${
                                       expandedTraceLogs()[result.strategy_name]
                                         ? 'bg-orange-600 text-white hover:bg-orange-700 border border-orange-300'
                                         : 'bg-orange-100 text-orange-700 hover:bg-orange-200 border border-orange-300'
                                     }`}
                                     title="View debug trace logs"
                                   >
                                     <Bug class="h-4 w-4 mr-1" />
                                     Debug Log
                                   </button>
                                 </div>
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

                  {/* Debug Trace Logs Section */}
                  <Show when={selectedResultStrategy() && expandedTraceLogs()[selectedResultStrategy()!]}>
                    <div class="border-t-2 border-orange-200 pt-4">
                      <div class="flex items-center justify-between mb-3">
                        <h4 class="text-lg font-medium text-gray-900">
                          Debug Trace Logs - {selectedResultStrategy()}
                        </h4>
                        <button
                          onClick={() => toggleTraceLogs(selectedResultStrategy()!)}
                          class="text-sm text-gray-500 hover:text-gray-700"
                        >
                          Close
                        </button>
                      </div>

                      {/* Filters */}
                      <div class="flex gap-2 mb-3">
                        <select
                          class="text-xs border border-gray-300 rounded px-2 py-1"
                          onChange={(e) => setTraceFilter('level', e.currentTarget.value)}
                        >
                          <option value="">All Levels</option>
                          <option value="DEBUG">DEBUG</option>
                          <option value="INFO">INFO</option>
                          <option value="WARNING">WARNING</option>
                          <option value="ERROR">ERROR</option>
                        </select>
                        <select
                          class="text-xs border border-gray-300 rounded px-2 py-1"
                          onChange={(e) => setTraceFilter('category', e.currentTarget.value)}
                        >
                          <option value="">All Categories</option>
                          <option value="BACKTEST">BACKTEST</option>
                          <option value="PORTFOLIO">PORTFOLIO</option>
                          <option value="REBALANCE">REBALANCE</option>
                          <option value="WEIGHT_CALC">WEIGHT_CALC</option>
                          <option value="TRADE">TRADE</option>
                          <option value="PERFORMANCE">PERFORMANCE</option>
                        </select>
                      </div>

                      <div class="max-h-96 overflow-y-auto bg-gray-50 rounded border border-gray-200">
                        <Show
                          when={strategyTraces() && strategyTraces()!.traces.length > 0}
                          fallback={
                            <div class="text-center py-8 text-gray-500">
                              No debug trace logs available for this strategy.
                            </div>
                          }
                        >
                          <div class="divide-y divide-gray-200">
                            {strategyTraces()!.traces
                              .filter((trace: any) => {
                                if (traceFilters().level && trace.level !== traceFilters().level) return false;
                                if (traceFilters().category && trace.category !== traceFilters().category) return false;
                                return true;
                              })
                              .map((trace: any) => (
                              <div class="px-2 py-1 hover:bg-gray-100">
                                <div class="flex items-center gap-2 text-xs">
                                  <span class={`inline-flex px-1 py-0.5 text-xs font-semibold rounded ${getLevelColor(trace.level)}`}>
                                    {trace.level}
                                  </span>
                                  <span class="text-gray-500">
                                    {new Date(trace.trace_timestamp).toLocaleDateString()}
                                  </span>
                                  <span class="text-gray-500">
                                    {trace.category}
                                  </span>
                                  <span class="text-gray-900 font-medium truncate flex-1">
                                    {trace.message}
                                  </span>
                                  <Show when={trace.data && Object.keys(trace.data).length > 0}>
                                    <details class="text-xs">
                                      <summary class="cursor-pointer text-orange-600 hover:text-orange-800">
                                        View Data
                                      </summary>
                                      <pre class="absolute z-10 bg-white border border-gray-300 rounded p-2 mt-1 text-xs overflow-x-auto max-w-md shadow-lg">
                                        {JSON.stringify(trace.data, null, 2)}
                                      </pre>
                                    </details>
                                  </Show>
                                </div>
                              </div>
                            ))}
                          </div>
                        </Show>
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
