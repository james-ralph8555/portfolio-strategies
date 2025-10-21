import { For, Show } from 'solid-js';
import { useTerminalStore } from '../TerminalStore';

export default function ControlPane() {
  const store = useTerminalStore();

  const handleRunBacktest = (event: Event) => {
    event.preventDefault();
    void store.runBacktest();
  };

  const handleRunAll = (event: Event) => {
    event.preventDefault();
    void store.runAllStrategies();
  };

  const handleFetchMarket = (event: Event) => {
    event.preventDefault();
    void store.fetchMarketData();
  };

  const handleClearCache = (event: Event) => {
    event.preventDefault();
    void store.clearCache();
  };

  return (
    <div style={{ padding: '8px', display: 'flex', 'flex-direction': 'column', gap: '12px', color: '#d1d5db', 'font-size': '12px' }}>
      <section style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px' }}>
        <header style={{ 'font-size': '13px', 'font-weight': 600, 'margin-bottom': '6px', color: '#f9fafb' }}>Backtest Controls</header>
        <form style={{ display: 'grid', gap: '6px' }} onSubmit={handleRunBacktest}>
          <label style={{ display: 'flex', 'flex-direction': 'column', gap: '4px' }}>
            <span>Strategy</span>
            <select value={store.selectedStrategy()} onChange={(event) => store.setSelectedStrategy(event.currentTarget.value)} style={{ padding: '4px', 'background-color': '#0f1115', color: '#f9fafb', border: '1px solid #374151', 'border-radius': '3px' }}>
              <option value="">Select strategy…</option>
              <Show when={!store.strategies.loading} fallback={<option disabled>Loading…</option>}>
                <For each={store.strategies() || []}>
                  {(strategy) => (
                    <option value={strategy.name}>{strategy.name}</option>
                  )}
                </For>
              </Show>
            </select>
          </label>
          <div style={{ display: 'grid', gap: '6px', 'grid-template-columns': 'repeat(2, minmax(0, 1fr))' }}>
            <label style={{ display: 'flex', 'flex-direction': 'column', gap: '4px' }}>
              <span>Start</span>
              <input type="date" value={store.startDate()} onInput={(event) => store.setStartDate(event.currentTarget.value)} style={{ padding: '4px', 'background-color': '#0f1115', color: '#f9fafb', border: '1px solid #374151', 'border-radius': '3px' }} />
            </label>
            <label style={{ display: 'flex', 'flex-direction': 'column', gap: '4px' }}>
              <span>End</span>
              <input type="date" value={store.endDate()} onInput={(event) => store.setEndDate(event.currentTarget.value)} style={{ padding: '4px', 'background-color': '#0f1115', color: '#f9fafb', border: '1px solid #374151', 'border-radius': '3px' }} />
            </label>
          </div>
          <label style={{ display: 'flex', 'flex-direction': 'column', gap: '4px' }}>
            <span>Initial Capital</span>
            <input
              type="number"
              min="0"
              step="1000"
              value={store.initialCapital()}
              onInput={(event) => store.setInitialCapital(Number(event.currentTarget.value))}
              style={{ padding: '4px', 'background-color': '#0f1115', color: '#f9fafb', border: '1px solid #374151', 'border-radius': '3px' }}
            />
          </label>
          <div style={{ display: 'flex', gap: '6px', 'margin-top': '4px' }}>
            <button
              type="submit"
              style={{ flex: 1, padding: '6px', 'font-weight': 600, 'border-radius': '3px', border: '1px solid #2563eb', 'background-color': '#2563eb', color: '#fff', cursor: 'pointer' }}
              disabled={store.isRunning()}
            >
              {store.isRunning() ? 'Running…' : 'Run'}
            </button>
            <button
              style={{ flex: 1, padding: '6px', 'font-weight': 600, 'border-radius': '3px', border: '1px solid #4b5563', 'background-color': '#1f2937', color: '#f9fafb', cursor: 'pointer' }}
              onClick={handleRunAll}
              disabled={store.isRunning()}
            >
              {store.isRunning() ? 'Running…' : 'Run All'}
            </button>
          </div>
        </form>
        <Show when={store.backtestError()}>
          <div style={{ 'margin-top': '6px', padding: '6px', border: '1px solid #b91c1c', 'background-color': '#7f1d1d', color: '#fee2e2', 'border-radius': '3px' }}>
            {store.backtestError()}
          </div>
        </Show>
        <Show when={store.backtestResult()}>
          <div style={{ 'margin-top': '6px', padding: '6px', border: '1px solid #047857', 'background-color': '#064e3b', color: '#d1fae5', 'border-radius': '3px' }}>
            Backtest triggered successfully. Check results for details.
          </div>
        </Show>
      </section>

      <section style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px' }}>
        <header style={{ 'font-size': '13px', 'font-weight': 600, 'margin-bottom': '6px', color: '#f9fafb' }}>Market Data</header>
        <form style={{ display: 'grid', gap: '6px' }} onSubmit={handleFetchMarket}>
          <label style={{ display: 'flex', 'flex-direction': 'column', gap: '4px' }}>
            <span>Symbols (comma separated)</span>
            <input
              type="text"
              value={store.marketSymbols()}
              onInput={(event) => store.setMarketSymbols(event.currentTarget.value)}
              placeholder="AAPL,MSFT,SPY"
              style={{ padding: '4px', 'background-color': '#0f1115', color: '#f9fafb', border: '1px solid #374151', 'border-radius': '3px' }}
            />
          </label>
          <label style={{ display: 'flex', 'align-items': 'center', gap: '6px' }}>
            <input type="checkbox" checked={store.marketForceRefresh()} onChange={(event) => store.setMarketForceRefresh(event.currentTarget.checked)} />
            <span>Force refresh</span>
          </label>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              type="submit"
              style={{ flex: 1, padding: '6px', 'font-weight': 600, 'border-radius': '3px', border: '1px solid #10b981', 'background-color': '#059669', color: '#f0fdf4', cursor: 'pointer' }}
              disabled={store.marketDataLoading()}
            >
              {store.marketDataLoading() ? 'Fetching…' : 'Fetch'}
            </button>
            <button
              style={{ flex: 1, padding: '6px', 'font-weight': 600, 'border-radius': '3px', border: '1px solid #4b5563', 'background-color': '#1f2937', color: '#f9fafb', cursor: 'pointer' }}
              onClick={handleClearCache}
            >
              Clear Cache
            </button>
          </div>
        </form>
        <Show when={store.marketDataError()}>
          <div style={{ 'margin-top': '6px', padding: '6px', border: '1px solid #b91c1c', 'background-color': '#7f1d1d', color: '#fee2e2', 'border-radius': '3px' }}>
            {store.marketDataError()}
          </div>
        </Show>
        <Show when={store.marketData()}>
          <div style={{ 'margin-top': '6px', border: '1px solid #2a2f3a', padding: '6px', 'border-radius': '3px', display: 'grid', gap: '4px' }}>
            <For each={Object.entries(store.marketData()?.data || {})}>
              {([symbol, rows]: [string, any]) => (
                <div style={{ display: 'flex', 'justify-content': 'space-between' }}>
                  <span>{symbol}</span>
                  <span>{rows.length} pts · latest ${(rows[rows.length - 1]?.price ?? 0).toFixed(2)}</span>
                </div>
              )}
            </For>
          </div>
        </Show>
      </section>
    </div>
  );
}
