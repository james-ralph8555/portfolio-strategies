export interface Strategy {
  name: string;
  description?: string;
  assets: string[];
  config: Record<string, any>;
}

export interface BacktestRequest {
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  name?: string;
}

export interface BacktestResponse {
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_value: number;
  metrics: Record<string, number>;
  status: string;
  message?: string;
}

export interface MarketDataRequest {
  symbols: string[];
  start_date: string;
  end_date: string;
  force_refresh?: boolean;
}

export interface MarketDataResponse {
  symbols: string[];
  data: Record<string, Array<{ date: string; price: number }>>;
  metadata: Record<string, any>;
}

export interface PortfolioValue {
  date: string;
  portfolio_value: number;
  cash: number;
  weights: string;
}

export interface Trade {
  trade_date: string;
  symbol: string;
  action: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  value: number;
}

export interface StrategyResults {
  portfolio_values: PortfolioValue[];
  trades: Trade[];
}
