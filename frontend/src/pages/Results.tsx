import { createResource, createSignal, Show } from 'solid-js';
import { apiClient } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { BarChart, TrendingUp, TrendingDown, Eye } from 'lucide-solid';

const Results = () => {
  const [results] = createResource(() => apiClient.getBacktestResults());
  const [selectedStrategy, setSelectedStrategy] = createSignal<string>('');
  const [strategyResults, setStrategyResults] = createSignal<any>(null);
  const [isLoadingDetails, setIsLoadingDetails] = createSignal(false);

  const loadStrategyDetails = async (strategyName: string) => {
    setIsLoadingDetails(true);
    setSelectedStrategy(strategyName);

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
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">Backtest Results</h1>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Results Table */}
        <div class="bg-white rounded-lg shadow">
          <div class="px-6 py-4 border-b border-gray-200">
            <h2 class="text-lg font-medium text-gray-900">All Results</h2>
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
            <h2 class="text-lg font-medium text-gray-900">
              Strategy Details {selectedStrategy() && `- ${selectedStrategy()}`}
            </h2>
          </div>
          <div class="p-6">
            <Show when={!selectedStrategy()}>
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
                  <h3 class="text-md font-medium text-gray-900 mb-3">Portfolio Performance</h3>
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
                  <h3 class="text-md font-medium text-gray-900 mb-3">Recent Trades</h3>
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

                {/* Performance Metrics */}
                <div>
                  <h3 class="text-md font-medium text-gray-900 mb-3">Performance Metrics</h3>
                  <div class="grid grid-cols-2 gap-4">
                    <div class="bg-gray-50 p-3 rounded-lg">
                      <div class="flex items-center">
                        <TrendingUp class="h-4 w-4 text-green-600 mr-2" />
                        <span class="text-sm text-gray-600">Win Rate</span>
                      </div>
                      <p class="text-lg font-semibold mt-1">
                        {((results()?.find(r => r.strategy_name === selectedStrategy())?.win_rate || 0) * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div class="bg-gray-50 p-3 rounded-lg">
                      <div class="flex items-center">
                        <TrendingDown class="h-4 w-4 text-red-600 mr-2" />
                        <span class="text-sm text-gray-600">Max Drawdown</span>
                      </div>
                      <p class="text-lg font-semibold mt-1">
                        {formatPercentage(results()?.find(r => r.strategy_name === selectedStrategy())?.max_drawdown || 0)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </Show>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Results;
