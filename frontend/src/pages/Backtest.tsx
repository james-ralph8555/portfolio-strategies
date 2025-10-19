import { createResource, createSignal, Show } from 'solid-js';
import { apiClient } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import type { Strategy, BacktestRequest } from '../types';
import { Play, Calendar, DollarSign, TrendingUp } from 'lucide-solid';

const Backtest = () => {
  const [strategies] = createResource(() => apiClient.getStrategies());
  const [selectedStrategy, setSelectedStrategy] = createSignal<string>('');
  const [startDate, setStartDate] = createSignal<string>('2020-01-01');
  const [endDate, setEndDate] = createSignal<string>('2024-12-31');
  const [initialCapital, setInitialCapital] = createSignal<number>(100000);
  const [isRunning, setIsRunning] = createSignal(false);
  const [result, setResult] = createSignal<any>(null);
  const [error, setError] = createSignal<string>('');

  const runBacktest = async () => {
    if (!selectedStrategy()) {
      setError('Please select a strategy');
      return;
    }

    setIsRunning(true);
    setError('');
    setResult(null);

    try {
      const request: BacktestRequest = {
        strategy_name: selectedStrategy()!,
        start_date: startDate(),
        end_date: endDate(),
        initial_capital: initialCapital(),
      };

      const response = await apiClient.runBacktest(request);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsRunning(false);
    }
  };

  const runAllStrategies = async () => {
    setIsRunning(true);
    setError('');
    setResult(null);

    try {
      const response = await apiClient.runAllStrategies(
        startDate(),
        endDate(),
        initialCapital()
      );
      setResult({ type: 'all', data: response });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">Backtesting</h1>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Panel */}
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Backtest Configuration</h2>

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
                {isRunning() ? 'Running All...' : 'Run All Strategies'}
              </button>
            </div>
          </div>

          <Show when={error()}>
            <div class="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error()}
            </div>
          </Show>
        </div>

        {/* Results Panel */}
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Results</h2>

          <Show when={!result() && !isRunning()}>
            <div class="text-center py-8 text-gray-500">
              <TrendingUp class="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p>Configure and run a backtest to see results here.</p>
            </div>
          </Show>

          <Show when={isRunning()}>
            <div class="text-center py-8">
              <LoadingSpinner />
              <p class="mt-4 text-gray-600">Running backtest...</p>
            </div>
          </Show>

          <Show when={result()}>
            <div class="space-y-4">
              <Show when={result().type === 'all'}>
                <div>
                  <h3 class="font-medium text-gray-900 mb-2">All Strategies Results</h3>
                  <div class="space-y-2">
                    {Object.entries(result().data).map(([name, data]: [string, any]) => (
                      <div class="p-3 bg-gray-50 rounded-lg">
                        <div class="flex justify-between items-center">
                          <span class="font-medium">{name}</span>
                          <span class={`text-sm ${
                            data.error ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {data.error ? 'Error' : `${(data.metrics?.total_return * 100).toFixed(2)}%`}
                          </span>
                        </div>
                        <Show when={data.error}>
                          <p class="text-xs text-red-600 mt-1">{data.error}</p>
                        </Show>
                      </div>
                    ))}
                  </div>
                </div>
              </Show>

              <Show when={result().type !== 'all'}>
                <div>
                  <h3 class="font-medium text-gray-900 mb-2">
                    {result().strategy_name} Results
                  </h3>
                  <div class="grid grid-cols-2 gap-4">
                    <div class="bg-gray-50 p-3 rounded-lg">
                      <p class="text-sm text-gray-600">Total Return</p>
                      <p class="text-lg font-semibold text-green-600">
                        {(result().metrics.total_return * 100).toFixed(2)}%
                      </p>
                    </div>
                    <div class="bg-gray-50 p-3 rounded-lg">
                      <p class="text-sm text-gray-600">Sharpe Ratio</p>
                      <p class="text-lg font-semibold">
                        {result().metrics.sharpe_ratio.toFixed(2)}
                      </p>
                    </div>
                    <div class="bg-gray-50 p-3 rounded-lg">
                      <p class="text-sm text-gray-600">Max Drawdown</p>
                      <p class="text-lg font-semibold text-red-600">
                        {(result().metrics.max_drawdown * 100).toFixed(2)}%
                      </p>
                    </div>
                    <div class="bg-gray-50 p-3 rounded-lg">
                      <p class="text-sm text-gray-600">Final Value</p>
                      <p class="text-lg font-semibold">
                        ${result().final_value.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              </Show>
            </div>
          </Show>
        </div>
      </div>
    </div>
  );
};

export default Backtest;
