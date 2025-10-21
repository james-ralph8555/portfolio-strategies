import { Show } from 'solid-js';
import { useTerminalStore } from '../TerminalStore';

export default function CachePane() {
  const store = useTerminalStore();

  const handleRefresh = () => {
    void store.refetchCacheInfo();
  };

  const info = () => store.cacheInfo() || {};

  return (
    <div style={{ padding: '8px', color: '#d1d5db', 'font-size': '12px', height: '100%', display: 'flex', 'flex-direction': 'column', gap: '10px' }}>
      <header style={{ 'font-size': '13px', 'font-weight': 600, color: '#f9fafb' }}>Cache Overview</header>
      <div style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px', display: 'grid', gap: '6px' }}>
        <div style={{ display: 'flex', 'justify-content': 'space-between' }}>
          <span>Unique symbols</span>
          <span>{info().unique_symbols ?? 0}</span>
        </div>
        <div style={{ display: 'flex', 'justify-content': 'space-between' }}>
          <span>Total records</span>
          <span>{info().total_records ?? 0}</span>
        </div>
        <div style={{ display: 'flex', 'justify-content': 'space-between' }}>
          <span>Earliest date</span>
          <span>{info().earliest_date ?? 'N/A'}</span>
        </div>
        <div style={{ display: 'flex', 'justify-content': 'space-between' }}>
          <span>Latest date</span>
          <span>{info().latest_date ?? 'N/A'}</span>
        </div>
      </div>
      <div style={{ display: 'flex', gap: '6px' }}>
        <button
          style={{ flex: 1, padding: '6px', 'font-size': '11px', 'background-color': '#1f6feb', color: '#fff', border: 'none', 'border-radius': '3px', cursor: 'pointer' }}
          onClick={handleRefresh}
        >
          Refresh
        </button>
        <button
          style={{ flex: 1, padding: '6px', 'font-size': '11px', 'background-color': '#1f2937', color: '#f9fafb', border: '1px solid #374151', 'border-radius': '3px', cursor: 'pointer' }}
          onClick={() => void store.clearCache()}
        >
          Clear Cache
        </button>
      </div>
      <Show when={store.marketData()}>
        <div style={{ border: '1px solid #2a2f3a', padding: '8px', 'border-radius': '4px' }}>
          <div style={{ color: '#9ca3af', 'margin-bottom': '4px' }}>Fetched symbols in session</div>
          <div style={{ display: 'flex', 'flex-wrap': 'wrap', gap: '6px' }}>
            {(store.marketData()?.symbols || []).map((symbol: string) => (
              <span style={{ padding: '2px 6px', border: '1px solid #374151', 'border-radius': '3px', background: '#111827' }}>
                {symbol}
              </span>
            ))}
          </div>
        </div>
      </Show>
    </div>
  );
}
