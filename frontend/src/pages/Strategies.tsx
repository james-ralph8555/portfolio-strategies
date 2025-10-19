import { createResource, Show } from 'solid-js';
import { apiClient } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import type { Strategy } from '../types';
import { TrendingUp, Settings, Info } from 'lucide-solid';

const Strategies = () => {
  const [strategies] = createResource(() => apiClient.getStrategies());

  return (
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">Trading Strategies</h1>
      </div>

      <Show when={!strategies.loading} fallback={<LoadingSpinner />}>
        <Show
          when={strategies()?.length > 0}
          fallback={
            <div class="bg-white rounded-lg shadow p-8 text-center">
              <TrendingUp class="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 class="text-lg font-medium text-gray-900 mb-2">No strategies found</h3>
              <p class="text-gray-500">
                No trading strategies are currently available in the system.
              </p>
            </div>
          }
        >
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {strategies()?.map((strategy: Strategy) => (
              <div class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
                <div class="p-6">
                  <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">{strategy.name}</h3>
                    <div class="flex space-x-2">
                      <button class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                        <Settings class="h-4 w-4" />
                      </button>
                      <button class="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
                        <Info class="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  <p class="text-gray-600 text-sm mb-4">
                    {strategy.description || `A ${strategy.name} trading strategy`}
                  </p>

                  <div class="space-y-3">
                    <div>
                      <h4 class="text-sm font-medium text-gray-700 mb-1">Assets</h4>
                      <div class="flex flex-wrap gap-1">
                        {strategy.assets.map((asset) => (
                          <span class="inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                            {asset}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 class="text-sm font-medium text-gray-700 mb-1">Configuration</h4>
                      <div class="text-xs text-gray-500">
                        {Object.keys(strategy.config).length} parameters configured
                      </div>
                    </div>
                  </div>

                  <div class="mt-4 pt-4 border-t border-gray-200">
                    <button class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                      Run Backtest
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Show>
      </Show>
    </div>
  );
};

export default Strategies;
