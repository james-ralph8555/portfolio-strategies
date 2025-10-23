import { createContext, useContext, createEffect, createMemo, createResource, createSignal, onCleanup } from 'solid-js';
import type { Accessor, Resource } from 'solid-js';
import { apiClient } from '../utils/api';
import type { BacktestRequest, MarketDataRequest, Strategy, StrategyResults } from '../types';

type TraceFilters = {
  level: string;
  category: string;
};

type SeriesSource =
  | { kind: 'market'; symbol: string }
  | { kind: 'backtest'; backtestName: string };

export type ChartPaneSeries = {
  id: string;
  name: string;
  x: (string | Date)[];
  y: number[];
  color: string;
  visible: boolean;
};

export type SeriesEntry = {
  id: string;
  label: string;
  color: string;
  visible: boolean;
  source: SeriesSource;
};

type TerminalStore = {
  strategies: Resource<Strategy[]>;
  results: Resource<any[]>;
  cacheInfo: Resource<Record<string, any>>;
  refetchResults: () => Promise<any[] | undefined> | any[] | null | undefined;
  refetchCacheInfo: () => Promise<Record<string, any> | undefined> | Record<string, any> | null | undefined;

  selectedStrategy: Accessor<string>;
  setSelectedStrategy: (value: string) => void;
  startDate: Accessor<string>;
  setStartDate: (value: string) => void;
  endDate: Accessor<string>;
  setEndDate: (value: string) => void;
  backtestName: Accessor<string>;
  setBacktestName: (value: string) => void;
  initialCapital: Accessor<number>;
  setInitialCapital: (value: number) => void;
  isRunning: Accessor<boolean>;
  backtestResult: Accessor<any>;
  backtestError: Accessor<string>;
  runBacktest: () => Promise<void>;
  runAllStrategies: () => Promise<void>;

  marketSymbols: Accessor<string>;
  setMarketSymbols: (value: string) => void;
  marketForceRefresh: Accessor<boolean>;
  setMarketForceRefresh: (value: boolean) => void;
  marketData: Accessor<any>;
  marketDataLoading: Accessor<boolean>;
  marketDataError: Accessor<string>;
  fetchMarketData: () => Promise<void>;
  clearCache: () => Promise<void>;

  selectedResultStrategy: Accessor<string>;
  strategyResults: Accessor<StrategyResults | null>;
  strategyDetailsLoading: Accessor<boolean>;
  loadStrategyDetails: (strategyName: string) => Promise<void>;

  strategyTraces: Accessor<{ traces: any[] } | null>;
  traceFilters: Accessor<TraceFilters>;
  setTraceFilter: (type: keyof TraceFilters, value: string) => void;
  traceLoading: Accessor<boolean>;
  loadStrategyTraces: (strategyName: string) => Promise<void>;
  expandedTraceData: Accessor<Record<string, boolean>>;
  toggleTraceData: (traceId: string) => void;

  normalizeSeries: Accessor<boolean>;
  setNormalizeSeries: (value: boolean) => void;
  seriesList: Accessor<SeriesEntry[]>;
  addMarketSeries: (symbol: string) => void;
  addBacktestSeries: (strategyName: string) => Promise<void>;
  removeSeries: (id: string) => void;
  toggleSeriesVisibility: (id: string) => void;
  chartSeries: Accessor<ChartPaneSeries[]>;

  availableMarketSymbols: Accessor<string[]>;
  watchlistRows: Accessor<Array<{ symbol: string; last: number; chg: number; volume?: number }>>;

  strategyDocumentation: Accessor<{
    strategy_name: string;
    readme: string;
    source_code: string;
    has_readme: boolean;
    has_source: boolean;
  } | null>;
  strategyDocumentationLoading: Accessor<boolean>;
  loadStrategyDocumentation: (strategyName: string) => Promise<void>;
};

const TerminalContext = createContext<TerminalStore>();

const palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#17becf', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22'];

const normalizeValues = (values: number[], normalize: boolean) => {
  if (!normalize || values.length === 0) return values;
  const base = values[0] || 1;
  return values.map((v) => (v / base) * 100);
};

export const createTerminalStore = (): TerminalStore => {
  const [strategies] = createResource(() => apiClient.getStrategies());
  const [results, { refetch: refetchResults }] = createResource(() => apiClient.getBacktestResults());
  const [cacheInfo, { refetch: refetchCacheInfo }] = createResource(() => apiClient.getCacheInfo());

  const [selectedStrategy, setSelectedStrategy] = createSignal<string>('');
  const [startDate, setStartDate] = createSignal<string>('2020-01-01');
  const [endDate, setEndDate] = createSignal<string>('2024-12-31');
  const [backtestName, setBacktestName] = createSignal<string>('');
  const [initialCapital, setInitialCapital] = createSignal<number>(100000);
  const [isRunning, setIsRunning] = createSignal(false);
  const [backtestResult, setBacktestResult] = createSignal<any>(null);
  const [backtestError, setBacktestError] = createSignal<string>('');

  const [marketSymbols, setMarketSymbols] = createSignal<string>('');
  const [marketForceRefresh, setMarketForceRefresh] = createSignal<boolean>(false);
  const [marketData, setMarketData] = createSignal<any>(null);
  const [marketDataLoading, setMarketDataLoading] = createSignal(false);
  const [marketDataError, setMarketDataError] = createSignal<string>('');

  const [selectedResultStrategy, setSelectedResultStrategy] = createSignal<string>('');
  const [strategyCache, setStrategyCache] = createSignal<Record<string, StrategyResults>>({});
  const [strategyResults, setStrategyResults] = createSignal<StrategyResults | null>(null);
  const [strategyDetailsLoading, setStrategyDetailsLoading] = createSignal(false);

  const [strategyTraces, setStrategyTraces] = createSignal<{ traces: any[] } | null>(null);
  const [traceFilters, setTraceFilters] = createSignal<TraceFilters>({ level: '', category: '' });
  const [traceLoading, setTraceLoading] = createSignal(false);
  const [expandedTraceData, setExpandedTraceData] = createSignal<Record<string, boolean>>({});

  const [normalizeSeries, setNormalizeSeries] = createSignal<boolean>(true);
  const [seriesList, setSeriesList] = createSignal<SeriesEntry[]>([]);
  const [chartSeries, setChartSeries] = createSignal<ChartPaneSeries[]>([]);

  let colorIndex = 0;
  const nextColor = () => palette[(colorIndex++) % palette.length];

  const getStrategyCached = async (strategyName: string) => {
    const cache = strategyCache();
    if (cache[strategyName]) return cache[strategyName];
    const details = await apiClient.getStrategyResults(strategyName);
    setStrategyCache({ ...cache, [strategyName]: details });
    return details;
  };

  const buildChartSeries = async (): Promise<ChartPaneSeries[]> => {
    const list = seriesList();
    if (!list.length) return [];
    const out: ChartPaneSeries[] = [];
    for (const entry of list) {
      if (entry.source.kind === 'market') {
        const symbol = entry.source.symbol;
        const data = marketData()?.data?.[symbol] || [];
        const x = data.map((row: any) => row.date);
        const yRaw = data.map((row: any) => Number(row.price));
        const y = normalizeValues(yRaw, normalizeSeries());
        out.push({ id: entry.id, name: entry.label, x, y, color: entry.color, visible: entry.visible });
      } else {
        // Extract strategy name from backtest name if it follows the pattern "strategy-timestamp"
        const backtestName = entry.source.backtestName;
        const strategyName = backtestName.includes('-') ? backtestName.split('-').slice(0, -1).join('-') : backtestName;
        const details = strategyCache()[strategyName] || await getStrategyCached(strategyName);
        const rows = details?.portfolio_values || [];
        const x = rows.map((row) => row.date);
        const yRaw = rows.map((row) => Number(row.portfolio_value));
        const y = normalizeValues(yRaw, normalizeSeries());
        out.push({ id: entry.id, name: entry.label, x, y, color: entry.color, visible: entry.visible });
      }
    }
    return out;
  };

  const refreshChartSeries = async () => {
    const data = await buildChartSeries();
    setChartSeries(data);
  };

  createEffect(() => {
    // dependencies
    void seriesList();
    void normalizeSeries();
    void marketData();
    void strategyCache();
    void refreshChartSeries();
  });

  const addMarketSeries = (symbol: string) => {
    const md = marketData();
    if (!md?.data?.[symbol]) return;
    if (seriesList().some((item) => item.source.kind === 'market' && item.source.symbol === symbol)) return;
    setSeriesList((prev) => [
      ...prev,
      { id: `market-${symbol}`, label: `${symbol} (Price)`, color: nextColor(), visible: true, source: { kind: 'market', symbol } },
    ]);
  };

  const addBacktestSeries = async (backtestName: string) => {
    if (seriesList().some((item) => item.source.kind === 'backtest' && item.source.backtestName === backtestName)) return;
    // Extract strategy name from backtest name if it follows the pattern "strategy-timestamp"
    const strategyName = backtestName.includes('-') ? backtestName.split('-').slice(0, -1).join('-') : backtestName;
    await getStrategyCached(strategyName);
    setSeriesList((prev) => [
      ...prev,
      { id: `backtest-${backtestName}`, label: `${backtestName} (Portfolio)`, color: nextColor(), visible: true, source: { kind: 'backtest', backtestName } },
    ]);
  };

  const removeSeries = (id: string) => {
    setSeriesList((prev) => prev.filter((item) => item.id !== id));
  };

  const toggleSeriesVisibility = (id: string) => {
    setSeriesList((prev) => prev.map((item) => (item.id === id ? { ...item, visible: !item.visible } : item)));
  };

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
        strategy_name: selectedStrategy(),
        start_date: startDate(),
        end_date: endDate(),
        initial_capital: initialCapital(),
        name: backtestName() || undefined,
      };
      const response = await apiClient.runBacktest(request);
      setBacktestResult(response);
      await refetchResults();
    } catch (error) {
      setBacktestError(error instanceof Error ? error.message : 'Failed to run backtest');
    } finally {
      setIsRunning(false);
    }
  };

  const runAllStrategies = async () => {
    setIsRunning(true);
    setBacktestError('');
    setBacktestResult(null);
    try {
      const response = await apiClient.runAllStrategies(startDate(), endDate(), initialCapital());
      setBacktestResult({ type: 'all', data: response });
      await refetchResults();
    } catch (error) {
      setBacktestError(error instanceof Error ? error.message : 'Failed to run all strategies');
    } finally {
      setIsRunning(false);
    }
  };

  const fetchMarketData = async () => {
    const raw = marketSymbols().trim();
    if (!raw) {
      setMarketDataError('Please enter at least one symbol');
      return;
    }

    const symbolList = raw.split(',').map((sym) => sym.trim().toUpperCase()).filter(Boolean);
    if (!symbolList.length) {
      setMarketDataError('Please enter valid symbols');
      return;
    }

    setMarketDataLoading(true);
    setMarketDataError('');
    setMarketData(null);

    try {
      const request: MarketDataRequest = {
        symbols: symbolList,
        start_date: startDate(),
        end_date: endDate(),
        force_refresh: marketForceRefresh(),
      };
      const response = await apiClient.getMarketData(request);
      setMarketData(response);
      await refetchCacheInfo();
    } catch (error) {
      setMarketDataError(error instanceof Error ? error.message : 'Failed to fetch market data');
    } finally {
      setMarketDataLoading(false);
    }
  };

  const clearCache = async () => {
    const raw = marketSymbols().trim();
    const symbolList = raw ? raw.split(',').map((sym) => sym.trim().toUpperCase()).filter(Boolean) : undefined;
    try {
      await apiClient.clearCache(symbolList);
      await refetchCacheInfo();
      setMarketDataError('');
    } catch (error) {
      setMarketDataError(error instanceof Error ? error.message : 'Failed to clear cache');
    }
  };

  const loadStrategyDetails = async (strategyName: string) => {
    setSelectedResultStrategy(strategyName);
    setStrategyDetailsLoading(true);
    try {
      const details = await getStrategyCached(strategyName);
      setStrategyResults(details);
    } catch (error) {
      console.error('Failed to load strategy details', error);
    } finally {
      setStrategyDetailsLoading(false);
    }
  };

  const loadStrategyTraces = async (strategyName: string) => {
    if (!strategyName) {
      setStrategyTraces(null);
      return;
    }
    setTraceLoading(true);
    try {
      const response = await apiClient.getStrategyTraces(strategyName);
      setStrategyTraces(response);
    } catch (error) {
      console.error('Failed to load trace logs', error);
    } finally {
      setTraceLoading(false);
    }
  };

  const toggleTraceData = (traceId: string) => {
    setExpandedTraceData((prev) => ({
      ...prev,
      [traceId]: !prev[traceId],
    }));
  };

  createEffect(() => {
    const strategyName = selectedResultStrategy();
    if (strategyName) {
      void loadStrategyTraces(strategyName);
      void loadStrategyDocumentation(strategyName);
    }
  });

  const availableMarketSymbols = createMemo(() => {
    const md = marketData();
    if (!md?.data) return [];
    return Object.keys(md.data);
  });

  const watchlistRows = createMemo(() => {
    const md = marketData();
    if (!md?.data) return [];
    return Object.entries(md.data).map(([symbol, rows]: [string, any]) => {
      const entries = rows as Array<{ price: number }>;
      if (!entries.length) return { symbol, last: 0, chg: 0 };
      const first = entries[0]?.price ?? 0;
      const last = entries[entries.length - 1]?.price ?? 0;
      const chg = first ? ((last - first) / first) * 100 : 0;
      return { symbol, last, chg };
    });
  });

  const [strategyDocumentation, setStrategyDocumentation] = createSignal<{
    strategy_name: string;
    readme: string;
    source_code: string;
    has_readme: boolean;
    has_source: boolean;
  } | null>(null);
  const [strategyDocumentationLoading, setStrategyDocumentationLoading] = createSignal(false);

  const loadStrategyDocumentation = async (strategyName: string) => {
    console.log('loadStrategyDocumentation called with:', strategyName);
    if (!strategyName) {
      setStrategyDocumentation(null);
      return;
    }
    setStrategyDocumentationLoading(true);
    try {
      console.log('Fetching documentation from API...');
      const documentation = await apiClient.getStrategyDocumentation(strategyName);
      console.log('Documentation received:', documentation ? 'success' : 'null');
      setStrategyDocumentation(documentation);
    } catch (error) {
      console.error('Failed to load strategy documentation', error);
      setStrategyDocumentation(null);
    } finally {
      setStrategyDocumentationLoading(false);
    }
  };

  // Auto-refresh via WebSocket events
  let ws: WebSocket | null = null;
  if (typeof window !== 'undefined') {
    const envBase = (import.meta as any)?.env?.VITE_API_BASE_URL as string | undefined;
    const base = envBase && envBase.trim() ? envBase.replace(/\/$/, '') : '/api';
    const absolute = /^https?:\/\//i.test(base);
    const wsUrl = absolute
      ? base.replace(/^http/i, 'ws') + '/ws'
      : `${window.location.protocol === 'https:' ? 'wss://' : 'ws://'}${window.location.host}${base}/ws`;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = async () => {
        await refetchResults();
        const cache = { ...strategyCache() };
        for (const entry of seriesList()) {
          if (entry.source.kind === 'backtest') {
            // Extract strategy name from backtest name if it follows the pattern "strategy-timestamp"
            const backtestName = entry.source.backtestName;
            const strategyName = backtestName.includes('-') ? backtestName.split('-').slice(0, -1).join('-') : backtestName;
            delete cache[strategyName];
          }
        }
        setStrategyCache(cache);
        await refreshChartSeries();
      };
    } catch (error) {
      console.warn('Failed to initialise WebSocket connection', error);
    }
  }

  onCleanup(() => {
    if (ws) {
      try {
        ws.close();
      } catch (error) {
        console.warn('Failed to close WebSocket', error);
      }
    }
  });

  return {
    strategies,
    results,
    cacheInfo,
    refetchResults,
    refetchCacheInfo,

    selectedStrategy,
    setSelectedStrategy,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    backtestName,
    setBacktestName,
    initialCapital,
    setInitialCapital,
    isRunning,
    backtestResult,
    backtestError,
    runBacktest,
    runAllStrategies,

    marketSymbols,
    setMarketSymbols,
    marketForceRefresh,
    setMarketForceRefresh,
    marketData,
    marketDataLoading,
    marketDataError,
    fetchMarketData,
    clearCache,

    selectedResultStrategy,
    strategyResults,
    strategyDetailsLoading,
    loadStrategyDetails,

    strategyTraces,
    traceFilters,
    setTraceFilter: (type: keyof TraceFilters, value: string) => {
      setTraceFilters((prev) => ({ ...prev, [type]: value }));
    },
    traceLoading,
    loadStrategyTraces,
    expandedTraceData,
    toggleTraceData,

    normalizeSeries,
    setNormalizeSeries,
    seriesList,
    addMarketSeries,
    addBacktestSeries,
    removeSeries,
    toggleSeriesVisibility,
    chartSeries,

    availableMarketSymbols,
    watchlistRows,

    strategyDocumentation,
    strategyDocumentationLoading,
    loadStrategyDocumentation,
  };
};

export const TerminalProvider = (props: { value: TerminalStore; children: any }) => (
  <TerminalContext.Provider value={props.value}>
    {props.children}
  </TerminalContext.Provider>
);

export const useTerminalStore = () => {
  const ctx = useContext(TerminalContext);
  if (!ctx) {
    throw new Error('useTerminalStore must be used within a TerminalProvider');
  }
  return ctx;
};
