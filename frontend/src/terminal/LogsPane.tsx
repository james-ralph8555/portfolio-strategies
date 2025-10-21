import { createEffect, createMemo, createSignal, onCleanup, onMount } from 'solid-js';
import { createGrid, type GridApi, type GridOptions } from 'ag-grid-community';
import type { ColDef } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import { ensureAgGridModules } from '../utils/ensureAgGridModules';
import { useTerminalStore } from './TerminalStore';

const cols: ColDef[] = [
  {
    field: 'trace_timestamp',
    headerName: 'Time',
    valueFormatter: (p) => new Date(p.value).toLocaleString(),
    minWidth: 160,
  },
  { field: 'level', headerName: 'Lvl', minWidth: 70 },
  { field: 'category', headerName: 'Cat', minWidth: 90 },
  { field: 'message', headerName: 'Message', flex: 1, minWidth: 220 },
];

export default function LogsPane() {
  const store = useTerminalStore();
  const [strategyInput, setStrategyInput] = createSignal(store.selectedResultStrategy());
  const [selectedTrace, setSelectedTrace] = createSignal<any | null>(null);

  let containerRef: HTMLDivElement | undefined;
  let gridApi: GridApi | undefined;

  const filteredTraces = createMemo(() => {
    const raw = store.strategyTraces()?.traces || [];
    const filters = store.traceFilters();
    return raw.filter((trace) => {
      if (filters.level && trace.level !== filters.level) return false;
      if (filters.category && trace.category !== filters.category) return false;
      return true;
    });
  });

  createEffect(() => {
    setStrategyInput(store.selectedResultStrategy());
  });

  const initialiseGrid = () => {
    ensureAgGridModules();
    if (!containerRef) return;

    const options: GridOptions = {
      columnDefs: cols,
      rowData: filteredTraces(),
      rowSelection: 'single',
      rowHeight: 24,
      headerHeight: 24,
      suppressCellFocus: true,
      onRowClicked: (event) => {
        setSelectedTrace(event.data);
      },
    };

    gridApi = createGrid(containerRef, options);
  };

  onMount(initialiseGrid);

  onCleanup(() => {
    gridApi?.destroy();
    gridApi = undefined;
  });

  createEffect(() => {
    const data = filteredTraces();
    if (gridApi) {
      gridApi.setGridOption('rowData', data);
      if (data.length === 0) {
        setSelectedTrace(null);
      }
    }
  });

  const handleLoad = () => {
    const name = strategyInput().trim();
    if (!name) return;
    void store.loadStrategyDetails(name);
    void store.loadStrategyTraces(name);
  };

  return (
    <div style={{ height: '100%', width: '100%', display: 'flex', 'flex-direction': 'column' }}>
      <div style={{ padding: '6px', 'border-bottom': '1px solid #2a2f3a', display: 'flex', gap: '6px', 'align-items': 'center' }}>
        <input
          style={{ flex: 1 }}
          placeholder="Strategy…"
          value={strategyInput() || ''}
          onInput={(event) => setStrategyInput(event.currentTarget.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              handleLoad();
            }
          }}
        />
        <button
          style={{ padding: '4px 8px', 'font-size': '11px', 'background-color': '#1f6feb', color: '#fff', border: 'none', 'border-radius': '3px', cursor: 'pointer' }}
          onClick={handleLoad}
        >
          Load
        </button>
        <label style={{ display: 'flex', 'align-items': 'center', gap: '4px', 'font-size': '11px' }}>
          Level
          <select value={store.traceFilters().level} onChange={(event) => store.setTraceFilter('level', event.currentTarget.value)}>
            <option value="">All</option>
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
          </select>
        </label>
        <label style={{ display: 'flex', 'align-items': 'center', gap: '4px', 'font-size': '11px' }}>
          Category
          <select value={store.traceFilters().category} onChange={(event) => store.setTraceFilter('category', event.currentTarget.value)}>
            <option value="">All</option>
            <option value="BACKTEST">BACKTEST</option>
            <option value="PORTFOLIO">PORTFOLIO</option>
            <option value="REBALANCE">REBALANCE</option>
            <option value="WEIGHT_CALC">WEIGHT_CALC</option>
            <option value="TRADE">TRADE</option>
            <option value="PERFORMANCE">PERFORMANCE</option>
          </select>
        </label>
      </div>
      <div class="ag-theme-quartz" style={{ flex: 1 }}>
        <div ref={containerRef} style={{ height: '100%', width: '100%' }} />
      </div>
      <div style={{ padding: '6px', 'border-top': '1px solid #2a2f3a', 'font-size': '12px', 'line-height': 1.4, 'min-height': '110px', 'max-height': '140px', overflow: 'auto' }}>
        {selectedTrace() ? (
          <div>
            <div style={{ display: 'flex', 'justify-content': 'space-between', 'margin-bottom': '4px', 'font-size': '11px', color: '#9ca3af' }}>
              <span>{new Date(selectedTrace().trace_timestamp).toLocaleString()}</span>
              <span>{selectedTrace().level} · {selectedTrace().category}</span>
            </div>
            <div style={{ 'margin-bottom': '4px' }}>{selectedTrace().message}</div>
            {selectedTrace().data && Object.keys(selectedTrace().data).length > 0 && (
              <pre style={{ 'white-space': 'pre-wrap', margin: 0, 'font-family': 'ui-monospace', 'font-size': '11px' }}>
                {JSON.stringify(selectedTrace().data, null, 2)}
              </pre>
            )}
          </div>
        ) : (
          <span style={{ color: '#6b7280' }}>Select a row to inspect log details.</span>
        )}
      </div>
    </div>
  );
}
