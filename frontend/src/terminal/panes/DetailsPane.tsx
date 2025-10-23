import { For, Show, createMemo, createSignal } from 'solid-js';
import { useTerminalStore } from '../TerminalStore';

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value ?? 0);

const formatPercent = (value: number) => `${(value * 100).toFixed(2)}%`;

export default function DetailsPane() {
  const store = useTerminalStore();
  const [activeTab, setActiveTab] = createSignal<'details' | 'documentation'>('details');
  const [documentationTab, setDocumentationTab] = createSignal<'readme' | 'source'>('readme');

  const summaryRow = createMemo(() => {
    const strategy = store.selectedResultStrategy();
    if (!strategy) return null;
    const results = store.strategyResults();
    if (!results) return null;
    const values = results.portfolio_values || [];
    if (!values.length) return null;
    const first = values[0]?.portfolio_value ?? 0;
    const last = values[values.length - 1]?.portfolio_value ?? 0;
    return {
      first,
      last,
      changePct: first ? (last - first) / first : 0,
    };
  });

  const overviewMetrics = createMemo(() => {
    const strategy = store.selectedResultStrategy();
    if (!strategy) return null;
    const match = (store.results() || []).find((row) => row.name === strategy);
    return match || null;
  });

  const handleAddToChart = () => {
    const strategy = store.selectedResultStrategy();
    if (strategy) {
      void store.addBacktestSeries(strategy);
    }
  };

  const handleOpenLogs = () => {
    const strategy = store.selectedResultStrategy();
    if (strategy) {
      void store.loadStrategyTraces(strategy);
    }
  };

  const handleViewDocumentation = () => {
    const strategy = store.selectedResultStrategy();
    if (strategy) {
      void store.loadStrategyDocumentation(strategy);
      setActiveTab('documentation');
    }
  };

  const handleTabClick = (tab: 'details' | 'documentation') => {
    setActiveTab(tab);
    if (tab === 'documentation') {
      const strategy = store.selectedResultStrategy();
      if (strategy) {
        void store.loadStrategyDocumentation(strategy);
      }
    }
  };

  const handleDocumentationTabClick = (tab: 'readme' | 'source') => {
    setDocumentationTab(tab);
  };

  return (
    <div style={{ padding: '8px', color: '#d1d5db', 'font-size': '12px', height: '100%', display: 'flex', 'flex-direction': 'column', gap: '8px' }}>
      <header style={{ 'font-size': '13px', 'font-weight': 600, color: '#f9fafb' }}>
        Backtest Details
        <Show when={store.selectedResultStrategy()}>
          <span style={{ color: '#9ca3af', 'margin-left': '6px' }}>({store.selectedResultStrategy()})</span>
        </Show>
      </header>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', 'border-bottom': '1px solid #374151', 'margin-bottom': '8px' }}>
        <button
          style={{
            padding: '6px 12px',
            'background-color': activeTab() === 'details' ? '#1f2937' : 'transparent',
            color: activeTab() === 'details' ? '#f9fafb' : '#9ca3af',
            border: 'none',
            'border-bottom': activeTab() === 'details' ? '2px solid #3b82f6' : '2px solid transparent',
            cursor: 'pointer',
            'font-size': '12px',
            'font-weight': 500,
          }}
          onClick={() => handleTabClick('details')}
        >
          Details
        </button>
        <button
          style={{
            padding: '6px 12px',
            'background-color': activeTab() === 'documentation' ? '#1f2937' : 'transparent',
            color: activeTab() === 'documentation' ? '#f9fafb' : '#9ca3af',
            border: 'none',
            'border-bottom': activeTab() === 'documentation' ? '2px solid #3b82f6' : '2px solid transparent',
            cursor: 'pointer',
            'font-size': '12px',
            'font-weight': 500,
            'margin-left': '8px',
          }}
          onClick={() => handleTabClick('documentation')}
        >
          Documentation
        </button>
      </div>
      {/* Details Tab Content */}
      <Show when={activeTab() === 'details'}>
        <Show when={store.strategyDetailsLoading()}>
          <div style={{ color: '#9ca3af' }}>Loading…</div>
        </Show>
        <Show when={!store.selectedResultStrategy()}>
          <div style={{ color: '#6b7280' }}>Select a strategy in the results table to view detail metrics.</div>
        </Show>
        <Show when={store.strategyResults() && !store.strategyDetailsLoading()}>
          <div style={{ display: 'flex', 'flex-direction': 'column', gap: '10px', flex: 1, overflow: 'auto' }}>
            <section style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px' }}>
              <header style={{ 'margin-bottom': '6px', 'font-size': '12px', color: '#f9fafb' }}>Performance Snapshot</header>
              <Show when={summaryRow()}>
                {(row) => (
                  <div style={{ display: 'grid', 'grid-template-columns': 'repeat(3, minmax(0, 1fr))', gap: '8px' }}>
                    <div>
                      <div style={{ color: '#9ca3af' }}>Initial Value</div>
                      <div style={{ 'font-size': '13px', 'font-weight': 600 }}>{formatCurrency(row().first)}</div>
                    </div>
                    <div>
                      <div style={{ color: '#9ca3af' }}>Final Value</div>
                      <div style={{ 'font-size': '13px', 'font-weight': 600 }}>{formatCurrency(row().last)}</div>
                    </div>
                    <div>
                      <div style={{ color: '#9ca3af' }}>Total Return</div>
                      <div style={{ 'font-size': '13px', 'font-weight': 600, color: row().changePct >= 0 ? '#4ade80' : '#f87171' }}>
                        {formatPercent(row().changePct)}
                      </div>
                    </div>
                  </div>
                )}
              </Show>
              <Show when={overviewMetrics()}>
                {(metrics) => (
                  <div style={{ display: 'grid', 'grid-template-columns': 'repeat(4, minmax(0, 1fr))', gap: '8px', 'margin-top': '10px' }}>
                    <div>
                      <div style={{ color: '#9ca3af' }}>Sharpe</div>
                      <div style={{ 'font-size': '12px' }}>{(metrics().sharpe_ratio ?? 0).toFixed(2)}</div>
                    </div>
                    <div>
                      <div style={{ color: '#9ca3af' }}>Max Drawdown</div>
                      <div style={{ 'font-size': '12px' }}>{formatPercent(metrics().max_drawdown ?? 0)}</div>
                    </div>
                    <div>
                      <div style={{ color: '#9ca3af' }}>Volatility</div>
                      <div style={{ 'font-size': '12px' }}>{formatPercent(metrics().volatility ?? 0)}</div>
                    </div>
                    <div>
                      <div style={{ color: '#9ca3af' }}>Win Rate</div>
                      <div style={{ 'font-size': '12px' }}>{formatPercent(metrics().win_rate ?? 0)}</div>
                    </div>
                  </div>
                )}
              </Show>
              <div style={{ display: 'flex', gap: '6px', 'margin-top': '10px' }}>
                <button
                  style={{ padding: '6px 10px', 'font-size': '11px', 'background-color': '#2563eb', color: '#fff', border: 'none', 'border-radius': '3px', cursor: 'pointer' }}
                  onClick={handleAddToChart}
                >
                  Add to Chart
                </button>
                <button
                  style={{ padding: '6px 10px', 'font-size': '11px', 'background-color': '#1f2937', color: '#f9fafb', border: '1px solid #374151', 'border-radius': '3px', cursor: 'pointer' }}
                  onClick={handleOpenLogs}
                >
                  Load Logs
                </button>
                <button
                  style={{ padding: '6px 10px', 'font-size': '11px', 'background-color': '#1f2937', color: '#f9fafb', border: '1px solid #374151', 'border-radius': '3px', cursor: 'pointer' }}
                  onClick={handleViewDocumentation}
                >
                  View Docs
                </button>
              </div>
            </section>

            <section style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px' }}>
              <header style={{ 'margin-bottom': '6px', 'font-size': '12px', color: '#f9fafb' }}>Recent Trades</header>
              <div style={{ 'max-height': '180px', overflow: 'auto' }}>
                <table style={{ width: '100%', 'border-collapse': 'collapse', 'font-size': '11px' }}>
                  <thead>
                    <tr style={{ color: '#9ca3af', 'text-align': 'left' }}>
                      <th style={{ 'padding-bottom': '4px' }}>Date</th>
                      <th style={{ 'padding-bottom': '4px' }}>Symbol</th>
                      <th style={{ 'padding-bottom': '4px' }}>Action</th>
                      <th style={{ 'padding-bottom': '4px', 'text-align': 'right' }}>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <For each={(store.strategyResults()?.trades || []).slice(0, 15)}>
                      {(trade) => (
                        <tr>
                          <td style={{ padding: '2px 0', color: '#d1d5db' }}>{trade.trade_date}</td>
                          <td style={{ padding: '2px 0', color: '#f9fafb' }}>{trade.symbol}</td>
                          <td style={{ padding: '2px 0', color: trade.action === 'BUY' ? '#34d399' : '#f87171' }}>{trade.action}</td>
                          <td style={{ padding: '2px 0', 'text-align': 'right', color: '#d1d5db' }}>{formatCurrency(trade.value)}</td>
                        </tr>
                      )}
                    </For>
                    <Show when={(store.strategyResults()?.trades || []).length === 0}>
                      <tr>
                        <td colspan="4" style={{ padding: '4px 0', color: '#6b7280' }}>No trades recorded.</td>
                      </tr>
                    </Show>
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </Show>
      </Show>

      {/* Documentation Tab Content */}
      <Show when={activeTab() === 'documentation'}>
        <div style={{ display: 'flex', 'flex-direction': 'column', gap: '10px', flex: 1, overflow: 'auto' }}>
          <Show when={!store.selectedResultStrategy()}>
            <div style={{ padding: '20px', 'text-align': 'center', color: '#9ca3af' }}>
              Select a strategy in the results table to view documentation
            </div>
          </Show>

          <Show when={store.selectedResultStrategy() && store.strategyDocumentationLoading()}>
            <div style={{ padding: '20px', 'text-align': 'center', color: '#9ca3af' }}>
              Loading documentation...
            </div>
          </Show>

          <Show when={store.selectedResultStrategy() && !store.strategyDocumentationLoading() && !store.strategyDocumentation()}>
            <div style={{ padding: '20px', 'text-align': 'center', color: '#9ca3af' }}>
              No documentation available for this strategy
            </div>
          </Show>

          <Show when={!store.strategyDocumentationLoading() && store.strategyDocumentation()}>
            <div style={{ display: 'flex', 'border-bottom': '1px solid #374151', 'margin-bottom': '8px' }}>
              <Show when={store.strategyDocumentation().has_readme}>
                <button
                  style={{
                    padding: '6px 12px',
                    'background-color': documentationTab() === 'readme' ? '#1f2937' : 'transparent',
                    color: documentationTab() === 'readme' ? '#f9fafb' : '#9ca3af',
                    border: 'none',
                    'border-bottom': documentationTab() === 'readme' ? '2px solid #3b82f6' : '2px solid transparent',
                    cursor: 'pointer',
                    'font-size': '12px',
                    'font-weight': 500,
                  }}
                  onClick={() => handleDocumentationTabClick('readme')}
                >
                  README
                </button>
              </Show>
              <Show when={store.strategyDocumentation().has_source}>
                <button
                  style={{
                    padding: '6px 12px',
                    'background-color': documentationTab() === 'source' ? '#1f2937' : 'transparent',
                    color: documentationTab() === 'source' ? '#f9fafb' : '#9ca3af',
                    border: 'none',
                    'border-bottom': documentationTab() === 'source' ? '2px solid #3b82f6' : '2px solid transparent',
                    cursor: 'pointer',
                    'font-size': '12px',
                    'font-weight': 500,
                    'margin-left': store.strategyDocumentation().has_readme ? '8px' : '0',
                  }}
                  onClick={() => handleDocumentationTabClick('source')}
                >
                  Source Code
                </button>
              </Show>
            </div>

            <div style={{ 'flex-grow': 1, overflow: 'auto', 'font-family': 'monospace', 'font-size': '11px', 'line-height': '1.4' }}>
              <Show when={documentationTab() === 'readme' && store.strategyDocumentation().has_readme}>
                <div style={{ 'white-space': 'pre-wrap', 'word-break': 'break-word' }}>
                  {store.strategyDocumentation().readme}
                </div>
              </Show>
              <Show when={documentationTab() === 'source' && store.strategyDocumentation().has_source}>
                <div style={{ 'white-space': 'pre-wrap', 'word-break': 'break-word' }}>
                  {store.strategyDocumentation().source_code}
                </div>
              </Show>
            </div>
          </Show>
        </div>
      </Show>
    </div>
  );
}
