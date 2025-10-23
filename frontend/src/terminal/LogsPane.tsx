import { createEffect, createMemo, createSignal, onCleanup, onMount } from 'solid-js';
import { createGrid, type GridApi, type GridOptions } from 'ag-grid-community';
import type { ColDef } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import { ensureAgGridModules } from '../utils/ensureAgGridModules';
import { useTerminalStore } from './TerminalStore';

const baseCols: ColDef[] = [
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
  const [availableAttributes, setAvailableAttributes] = createSignal<string[]>([]);
  const [selectedAttributes, setSelectedAttributes] = createSignal<Set<string>>(new Set());

  let containerRef: HTMLDivElement | undefined;
  let gridApi: GridApi | undefined;

  const filteredTraces = createMemo(() => {
    const raw = store.strategyTraces()?.traces || [];
    const filters = store.traceFilters();

    // Extract all available attributes from trace data
    const attributes = new Set<string>();
    raw.forEach((trace) => {
      if (trace.data && typeof trace.data === 'object') {
        Object.keys(trace.data).forEach(key => attributes.add(key));
      }
    });
    const attrArray = Array.from(attributes).sort();
    setAvailableAttributes(attrArray);

    return raw.filter((trace) => {
      if (filters.level && trace.level !== filters.level) return false;
      if (filters.category && trace.category !== filters.category) return false;
      return true;
    });
  });

  // Auto-select all attributes by default if none are selected
  createEffect(() => {
    const attrArray = availableAttributes();
    const currentSelected = selectedAttributes();
    if (attrArray.length > 0 && currentSelected.size === 0) {
      setSelectedAttributes(new Set(attrArray));
    }
  });

  createEffect(() => {
    setStrategyInput(store.selectedResultStrategy());
  });

  const dynamicColumns = createMemo(() => {
    const cols = [...baseCols];
    const selected = selectedAttributes();

    selected.forEach(attr => {
      cols.push({
        field: `data.${attr}`,
        headerName: attr,
        minWidth: 120,
        valueFormatter: (p) => {
          const value = p.value;
          if (value === null || value === undefined) return '';
          if (typeof value === 'object') return JSON.stringify(value);
          return String(value);
        },
        comparator: (valueA, valueB) => {
          // Handle null/undefined values
          if (valueA == null && valueB == null) return 0;
          if (valueA == null) return -1;
          if (valueB == null) return 1;

          // Try numeric comparison first
          const numA = Number(valueA);
          const numB = Number(valueB);
          if (!isNaN(numA) && !isNaN(numB)) {
            return numA - numB;
          }

          // Fall back to string comparison
          const strA = String(valueA);
          const strB = String(valueB);
          return strA.localeCompare(strB);
        }
      });
    });

    return cols;
  });

  const initialiseGrid = () => {
    ensureAgGridModules();
    if (!containerRef) return;

    const options: GridOptions = {
      columnDefs: dynamicColumns(),
      rowData: filteredTraces(),
      rowSelection: 'single',
      rowHeight: 24,
      headerHeight: 24,
      suppressCellFocus: true,
      enableCellTextSelection: true,
      ensureDomOrder: true,
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
    const cols = dynamicColumns();
    if (gridApi) {
      gridApi.setGridOption('columnDefs', cols);
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

  const toggleAttribute = (attr: string) => {
    setSelectedAttributes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(attr)) {
        newSet.delete(attr);
      } else {
        newSet.add(attr);
      }
      return newSet;
    });
  };

  const copyAllToClipboard = async () => {
    const traces = filteredTraces();
    const jsonlLines = traces.map(trace => {
      const copyData = {
        trace_timestamp: trace.trace_timestamp,
        level: trace.level,
        category: trace.category,
        message: trace.message,
        ...trace.data
      };
      return JSON.stringify(copyData);
    }).join('\n');

    try {
      await navigator.clipboard.writeText(jsonlLines);
      // Optional: Show feedback that copy was successful
      console.log('Copied all traces to clipboard');
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = jsonlLines;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
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
        <button
          style={{ padding: '4px 8px', 'font-size': '11px', 'background-color': '#059669', color: '#fff', border: 'none', 'border-radius': '3px', cursor: 'pointer' }}
          onClick={copyAllToClipboard}
          title="Copy all traces as JSONL"
        >
          Copy All
        </button>
        {availableAttributes().length > 0 && (
          <details style={{ position: 'relative' }}>
            <summary style={{ cursor: 'pointer', 'font-size': '11px', padding: '2px 4px', 'background-color': '#374151', 'border-radius': '3px' }}>
              Attributes ({selectedAttributes().size})
            </summary>
            <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, 'background-color': '#1f2937', border: '1px solid #374151', 'border-radius': '3px', 'z-index': 1000, 'max-height': '200px', 'overflow-y': 'auto', padding: '4px' }}>
              {availableAttributes().map(attr => (
                <label style={{ display: 'block', 'font-size': '11px', padding: '2px 4px', cursor: 'pointer', 'border-radius': '2px' }}>
                  <input
                    type="checkbox"
                    checked={selectedAttributes().has(attr)}
                    onChange={() => toggleAttribute(attr)}
                    style={{ 'margin-right': '6px' }}
                  />
                  {attr}
                </label>
              ))}
            </div>
          </details>
        )}
      </div>
      <div class="ag-theme-quartz" style={{ flex: 1 }}>
        <div ref={containerRef} style={{ height: '100%', width: '100%' }} />
      </div>
    </div>
  );
}
