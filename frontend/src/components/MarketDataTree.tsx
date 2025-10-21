import { createSignal, For, Show } from 'solid-js';
import { ChevronRight, ChevronDown, Database, Calendar, BarChart3 } from 'lucide-solid';

interface CachedSymbol {
  symbol: string;
  start_date: string;
  end_date: string;
  record_count: number;
  last_updated: string;
}

interface MarketDataTreeProps {
  symbols: CachedSymbol[];
  onSymbolSelect: (symbol: string) => void;
  selectedSymbol?: string;
}

const MarketDataTree = (props: MarketDataTreeProps) => {
  const [expandedSymbols, setExpandedSymbols] = createSignal<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = createSignal('');

  const filteredSymbols = () => {
    const term = searchTerm().toLowerCase();
    if (!term) return props.symbols;
    return props.symbols.filter(symbol =>
      symbol.symbol.toLowerCase().includes(term)
    );
  };

  const toggleExpanded = (symbol: string) => {
    const expanded = new Set(expandedSymbols());
    if (expanded.has(symbol)) {
      expanded.delete(symbol);
    } else {
      expanded.add(symbol);
    }
    setExpandedSymbols(expanded);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div class="bg-white rounded-lg shadow">
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-lg font-semibold text-gray-900 flex items-center">
            <Database class="h-5 w-5 mr-2 text-blue-600" />
            Cached Market Data
          </h3>
          <span class="text-sm text-gray-500">
            {filteredSymbols().length} symbols
          </span>
        </div>

        <input
          type="text"
          placeholder="Search symbols..."
          value={searchTerm()}
          onInput={(e) => setSearchTerm(e.target.value)}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div class="max-h-96 overflow-y-auto">
        <Show
          when={filteredSymbols().length > 0}
          fallback={
            <div class="p-8 text-center text-gray-500">
              <Database class="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p>No cached market data found</p>
              <p class="text-sm">Fetch market data to populate the cache</p>
            </div>
          }
        >
          <div class="divide-y divide-gray-200">
            <For each={filteredSymbols()}>
              {(symbolData) => {
                const isExpanded = () => expandedSymbols().has(symbolData.symbol);
                const isSelected = () => props.selectedSymbol === symbolData.symbol;

                return (
                  <div class="hover:bg-gray-50">
                    <div
                      class={`flex items-center justify-between p-3 cursor-pointer ${
                        isSelected() ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                      }`}
                      onClick={() => {
                        toggleExpanded(symbolData.symbol);
                        props.onSymbolSelect(symbolData.symbol);
                      }}
                    >
                      <div class="flex items-center space-x-3">
                        <button class="p-1 hover:bg-gray-200 rounded">
                          {isExpanded() ? (
                            <ChevronDown class="h-4 w-4 text-gray-600" />
                          ) : (
                            <ChevronRight class="h-4 w-4 text-gray-600" />
                          )}
                        </button>
                        <div>
                          <div class="font-medium text-gray-900">{symbolData.symbol}</div>
                          <div class="text-sm text-gray-500">
                            {symbolData.record_count} records
                          </div>
                        </div>
                      </div>
                      <div class="text-right">
                        <div class="text-sm text-gray-500">
                          {formatDate(symbolData.start_date)} - {formatDate(symbolData.end_date)}
                        </div>
                      </div>
                    </div>

                    <Show when={isExpanded()}>
                      <div class="px-3 pb-3 pl-12 bg-gray-50 border-t border-gray-200">
                        <div class="grid grid-cols-2 gap-4 text-sm">
                          <div class="flex items-center space-x-2">
                            <Calendar class="h-4 w-4 text-gray-400" />
                            <span class="text-gray-600">Start:</span>
                            <span class="font-medium">{formatDate(symbolData.start_date)}</span>
                          </div>
                          <div class="flex items-center space-x-2">
                            <Calendar class="h-4 w-4 text-gray-400" />
                            <span class="text-gray-600">End:</span>
                            <span class="font-medium">{formatDate(symbolData.end_date)}</span>
                          </div>
                          <div class="flex items-center space-x-2">
                            <BarChart3 class="h-4 w-4 text-gray-400" />
                            <span class="text-gray-600">Records:</span>
                            <span class="font-medium">{symbolData.record_count.toLocaleString()}</span>
                          </div>
                          <div class="flex items-center space-x-2">
                            <Database class="h-4 w-4 text-gray-400" />
                            <span class="text-gray-600">Updated:</span>
                            <span class="font-medium">{formatDateTime(symbolData.last_updated)}</span>
                          </div>
                        </div>
                      </div>
                    </Show>
                  </div>
                );
              }}
            </For>
          </div>
        </Show>
      </div>
    </div>
  );
};

export default MarketDataTree;
