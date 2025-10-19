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

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/health');
  }
}

export const apiClient = new ApiClient();
