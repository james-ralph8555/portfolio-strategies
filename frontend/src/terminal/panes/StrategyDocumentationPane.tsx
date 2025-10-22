import { For, Show, createSignal } from 'solid-js';
import { useTerminalStore } from '../TerminalStore';

export default function StrategyDocumentationPane() {
  const store = useTerminalStore();
  const [activeTab, setActiveTab] = createSignal<'readme' | 'source'>('readme');

  const documentation = store.strategyDocumentation();
  const loading = store.strategyDocumentationLoading();
  const selectedStrategy = store.selectedResultStrategy();

  const handleTabClick = (tab: 'readme' | 'source') => {
    setActiveTab(tab);
  };

  return (
    <div style={{ padding: '8px', display: 'flex', 'flex-direction': 'column', gap: '12px', color: '#d1d5db', 'font-size': '12px', height: '100%' }}>
      <section style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px', 'flex-grow': 1, display: 'flex', 'flex-direction': 'column' }}>
        <header style={{ 'font-size': '13px', 'font-weight': 600, 'margin-bottom': '6px', color: '#f9fafb' }}>
          Strategy Documentation
          <Show when={selectedStrategy}>
            <span style={{ 'margin-left': '8px', 'font-weight': 400, 'font-size': '11px', color: '#9ca3af' }}>
              {selectedStrategy}
            </span>
          </Show>
        </header>

        <Show when={!selectedStrategy}>
          <div style={{ padding: '20px', 'text-align': 'center', color: '#9ca3af' }}>
            Select a strategy in the results table to view documentation
          </div>
        </Show>

        <Show when={selectedStrategy && loading}>
          <div style={{ padding: '20px', 'text-align': 'center', color: '#9ca3af' }}>
            Loading documentation...
          </div>
        </Show>

        <Show when={selectedStrategy && !loading && !documentation}>
          <div style={{ padding: '20px', 'text-align': 'center', color: '#9ca3af' }}>
            No documentation available for this strategy
          </div>
        </Show>

        <Show when={!loading && documentation}>
          <div style={{ display: 'flex', 'border-bottom': '1px solid #374151', 'margin-bottom': '8px' }}>
            <Show when={documentation.has_readme}>
              <button
                style={{
                  padding: '6px 12px',
                  'background-color': activeTab() === 'readme' ? '#1f2937' : 'transparent',
                  color: activeTab() === 'readme' ? '#f9fafb' : '#9ca3af',
                  border: 'none',
                  'border-bottom': activeTab() === 'readme' ? '2px solid #3b82f6' : '2px solid transparent',
                  cursor: 'pointer',
                  'font-size': '12px',
                  'font-weight': 500,
                }}
                onClick={() => handleTabClick('readme')}
              >
                README
              </button>
            </Show>
            <Show when={documentation.has_source}>
              <button
                style={{
                  padding: '6px 12px',
                  'background-color': activeTab() === 'source' ? '#1f2937' : 'transparent',
                  color: activeTab() === 'source' ? '#f9fafb' : '#9ca3af',
                  border: 'none',
                  'border-bottom': activeTab() === 'source' ? '2px solid #3b82f6' : '2px solid transparent',
                  cursor: 'pointer',
                  'font-size': '12px',
                  'font-weight': 500,
                  'margin-left': documentation.has_readme ? '8px' : '0',
                }}
                onClick={() => handleTabClick('source')}
              >
                Source Code
              </button>
            </Show>
          </div>

          <div style={{ 'flex-grow': 1, overflow: 'auto', 'font-family': 'monospace', 'font-size': '11px', 'line-height': '1.4' }}>
            <Show when={activeTab() === 'readme' && documentation.has_readme}>
              <div style={{ 'white-space': 'pre-wrap', 'word-break': 'break-word' }}>
                {documentation.readme}
              </div>
            </Show>
            <Show when={activeTab() === 'source' && documentation.has_source}>
              <div style={{ 'white-space': 'pre-wrap', 'word-break': 'break-word' }}>
                {documentation.source_code}
              </div>
            </Show>
          </div>
        </Show>
      </section>
    </div>
  );
}
