import { createResource, Show } from 'solid-js';
import { apiClient } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { TrendingUp, DollarSign, Activity, BarChart3 } from 'lucide-solid';

const Dashboard = () => {
  const [results] = createResource(() => apiClient.getBacktestResults());
  const [cacheInfo] = createResource(() => apiClient.getCacheInfo());

  return (
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">Dashboard</h1>
      </div>

      {/* Summary Cards */}
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

      {/* Recent Results */}
      <div class="bg-white rounded-lg shadow">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-medium text-gray-900">Recent Backtest Results</h2>
        </div>
        <div class="p-6">
          <Show when={!results.loading} fallback={<LoadingSpinner />}>
            <Show
              when={results()?.length > 0}
              fallback={
                <div class="text-center py-8 text-gray-500">
                  No backtest results available. Run your first backtest to see results here.
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
                        Period
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total Return
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sharpe Ratio
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Max Drawdown
                      </th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    {results()?.slice(0, 5).map((result) => (
                      <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {result.strategy_name}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {result.start_date} - {result.end_date}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span class={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            (result.total_return || 0) > 0
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {((result.total_return || 0) * 100).toFixed(2)}%
                          </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {(result.sharpe_ratio || 0).toFixed(2)}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {((result.max_drawdown || 0) * 100).toFixed(2)}%
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
    </div>
  );
};

export default Dashboard;
