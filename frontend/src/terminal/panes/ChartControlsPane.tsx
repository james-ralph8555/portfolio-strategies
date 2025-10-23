import { For, Show, createMemo } from 'solid-js';
import { useTerminalStore } from '../TerminalStore';

export default function ChartControlsPane() {
  const store = useTerminalStore();

  const backtestNames = createMemo(() => (store.results() || []).map((row) => row.name));

  const remove = (id: string) => store.removeSeries(id);
  const toggle = (id: string) => store.toggleSeriesVisibility(id);

  return (
    <div style={{ padding: '8px', display: 'flex', 'flex-direction': 'column', gap: '10px', color: '#d1d5db', 'font-size': '12px' }}>
      <section style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px', display: 'flex', 'justify-content': 'space-between', 'align-items': 'center' }}>
        <div>
          <div style={{ 'font-size': '12px', 'font-weight': 600, color: '#f9fafb' }}>Normalisation</div>
          <div style={{ color: '#9ca3af' }}>Scale series to start at 100</div>
        </div>
        <label style={{ display: 'flex', 'align-items': 'center', gap: '6px' }}>
          <input type="checkbox" checked={store.normalizeSeries()} onChange={(event) => store.setNormalizeSeries(event.currentTarget.checked)} />
          <span>Normalize</span>
        </label>
      </section>

      <section style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px' }}>
        <header style={{ 'font-size': '12px', 'font-weight': 600, color: '#f9fafb', 'margin-bottom': '4px' }}>Market Symbols</header>
        <Show when={store.availableMarketSymbols().length > 0} fallback={<div style={{ color: '#6b7280' }}>Fetch market data to populate symbols.</div>}>
          <div style={{ display: 'flex', 'flex-wrap': 'wrap', gap: '6px' }}>
            <For each={store.availableMarketSymbols()}>
              {(symbol) => (
                <button
                  style={{ padding: '4px 6px', border: '1px solid #374151', 'border-radius': '3px', background: '#111827', color: '#f9fafb', cursor: 'pointer', 'font-size': '11px' }}
                  onClick={() => store.addMarketSeries(symbol)}
                >
                  {symbol}
                </button>
              )}
            </For>
          </div>
        </Show>
        <Show when={store.availableMarketSymbols().length > 1}>
          <button
            style={{ 'margin-top': '6px', padding: '4px 6px', 'font-size': '11px', border: '1px solid #4b5563', 'background-color': '#1f2937', color: '#f9fafb', 'border-radius': '3px', cursor: 'pointer' }}
            onClick={() => store.availableMarketSymbols().forEach((symbol) => store.addMarketSeries(symbol))}
          >
            Add All
          </button>
        </Show>
      </section>

      <section style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px' }}>
        <header style={{ 'font-size': '12px', 'font-weight': 600, color: '#f9fafb', 'margin-bottom': '4px' }}>Backtests</header>
        <Show when={(backtestNames() || []).length > 0} fallback={<div style={{ color: '#6b7280' }}>Run a backtest to enable chart overlays.</div>}>
          <div style={{ display: 'flex', 'flex-wrap': 'wrap', gap: '6px' }}>
            <For each={backtestNames()}>
              {(name) => (
                <button
                  style={{ padding: '4px 6px', border: '1px solid #374151', 'border-radius': '3px', background: '#111827', color: '#f9fafb', cursor: 'pointer', 'font-size': '11px' }}
                  onClick={() => { void store.addBacktestSeries(name); }}
                >
                  {name}
                </button>
              )}
            </For>
          </div>
        </Show>
      </section>

      <section style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px', flex: 1, display: 'flex', 'flex-direction': 'column' }}>
        <header style={{ 'font-size': '12px', 'font-weight': 600, color: '#f9fafb', 'margin-bottom': '4px' }}>Active Series</header>
        <Show when={store.seriesList().length > 0} fallback={<div style={{ color: '#6b7280' }}>No series plotted.</div>}>
          <div style={{ display: 'flex', 'flex-direction': 'column', gap: '6px', overflow: 'auto' }}>
            <For each={store.seriesList()}>
              {(series) => (
                <div style={{ display: 'flex', 'align-items': 'center', gap: '6px', border: '1px solid #374151', 'border-radius': '3px', padding: '4px 6px', background: '#111827' }}>
                  <span style={{ width: '10px', height: '10px', 'background-color': series.color, 'border-radius': '2px', display: 'inline-block' }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#f9fafb' }}>{series.label}</div>
                    <div style={{ color: '#6b7280', 'font-size': '10px' }}>
                      {series.source.kind === 'market' ? 'Market' : 'Backtest'} · {series.source.kind === 'market' ? series.source.symbol : series.source.backtestName}
                    </div>
                  </div>
                  <label style={{ display: 'flex', 'align-items': 'center', gap: '4px', 'font-size': '11px' }}>
                    <input type="checkbox" checked={series.visible} onChange={() => toggle(series.id)} />
                    Visible
                  </label>
                  <button
                    style={{ padding: '3px 6px', 'font-size': '10px', border: '1px solid #dc2626', 'border-radius': '3px', background: 'transparent', color: '#f87171', cursor: 'pointer' }}
                    onClick={() => remove(series.id)}
                  >
                    Remove
                  </button>
                </div>
              )}
            </For>
          </div>
          <button
            style={{ 'margin-top': '6px', padding: '4px 6px', 'font-size': '11px', border: '1px solid #dc2626', 'border-radius': '3px', background: 'transparent', color: '#f87171', cursor: 'pointer' }}
            onClick={() => {
              const ids = store.seriesList().map((series) => series.id);
              ids.forEach((id) => remove(id));
            }}
          >
            Clear All
          </button>
        </Show>
      </section>
    </div>
  );
}
