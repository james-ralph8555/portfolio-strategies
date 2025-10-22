import type {
  Strategy,
  BacktestRequest,
  BacktestResponse,
  MarketDataRequest,
  MarketDataResponse,
  StrategyResults
} from '../types';

const resolveApiBaseUrl = (): string => {
  const envValue = import.meta.env.VITE_API_BASE_URL?.trim();
  if (envValue) {
    return envValue.replace(/\/$/, '');
  }

  if (import.meta.env.DEV) {
    return '/api';
  }

  if (typeof window !== 'undefined' && window.location) {
    return `${window.location.origin.replace(/\/$/, '')}/api`;
  }

  return '/api';
};

const API_BASE_URL = resolveApiBaseUrl();

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${API_BASE_URL}${normalizedEndpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  // Strategy endpoints
  async getStrategies(): Promise<Strategy[]> {
    return this.request<Strategy[]>('/strategies');
  }

  async getStrategy(name: string): Promise<Strategy> {
    return this.request<Strategy>(`/strategies/${name}`);
  }

  async getStrategyDocumentation(name: string): Promise<{
    strategy_name: string;
    readme: string;
    source_code: string;
    has_readme: boolean;
    has_source: boolean;
  }> {
    return this.request(`/strategies/${name}/documentation`);
  }

  // Backtest endpoints
  async runBacktest(request: BacktestRequest): Promise<BacktestResponse> {
    return this.request<BacktestResponse>('/backtest', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getBacktestResults(): Promise<any[]> {
    return this.request<any[]>('/backtest/results');
  }

  async getStrategyResults(strategyName: string): Promise<StrategyResults> {
    return this.request<StrategyResults>(`/backtest/results/${strategyName}`);
  }

  async getStrategyTraces(strategyName: string, startDate?: string, endDate?: string): Promise<{ traces: any[] }> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const queryString = params.toString();
    return this.request<{ traces: any[] }>(`/backtest/traces/${strategyName}${queryString ? `?${queryString}` : ''}`);
  }

  async runAllStrategies(startDate: string, endDate: string, initialCapital: number = 100000): Promise<Record<string, any>> {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      initial_capital: initialCapital.toString(),
    });

    return this.request<Record<string, any>>(`/backtest/run-all?${params}`, {
      method: 'POST',
    });
  }

  // Market data endpoints
  async getMarketData(request: MarketDataRequest): Promise<MarketDataResponse> {
    return this.request<MarketDataResponse>('/market/data', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getCacheInfo(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>('/market/cache/info');
  }

  async clearCache(symbols?: string[]): Promise<{ message: string }> {
    const url = symbols ? `/market/cache?symbols=${symbols.join(',')}` : '/market/cache';
    return this.request<{ message: string }>(url, {
      method: 'DELETE',
    });
  }

  async getCachedSymbols(): Promise<{ symbols: Array<{ symbol: string; start_date: string; end_date: string; record_count: number; last_updated: string }> }> {
    return this.request<{ symbols: Array<{ symbol: string; start_date: string; end_date: string; record_count: number; last_updated: string }> }>('/market/cache/symbols');
  }

  async getCachedSymbolData(symbol: string, startDate?: string, endDate?: string): Promise<{ symbol: string; start_date: string; end_date: string; data: Array<{ date: string; open: number; high: number; low: number; close: number; volume: number; adjusted_close: number }> }> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const queryString = params.toString();
    return this.request<{ symbol: string; start_date: string; end_date: string; data: Array<{ date: string; open: number; high: number; low: number; close: number; volume: number; adjusted_close: number }> }>(`/market/cache/data/${symbol}${queryString ? `?${queryString}` : ''}`);
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/health');
  }
}

export const apiClient = new ApiClient();
