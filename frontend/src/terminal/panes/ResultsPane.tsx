import { createEffect, onCleanup, onMount } from 'solid-js';
import { createGrid, type GridApi, type GridOptions } from 'ag-grid-community';
import type { ColDef } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import { ensureAgGridModules } from '../../utils/ensureAgGridModules';
import { useTerminalStore } from '../TerminalStore';

const columns: ColDef[] = [
  { field: 'name', headerName: 'Backtest Name', minWidth: 180 },
  {
    field: 'total_return',
    headerName: 'Return %',
    type: 'rightAligned',
    valueFormatter: (params) => {
      const value = params.value ?? 0;
      return `${(value * 100).toFixed(2)}%`;
    },
  },
  {
    field: 'sharpe_ratio',
    headerName: 'Sharpe',
    type: 'rightAligned',
    valueFormatter: (params) => (params.value ?? 0).toFixed(2),
  },
  {
    field: 'max_drawdown',
    headerName: 'Max DD %',
    type: 'rightAligned',
    valueFormatter: (params) => `${((params.value ?? 0) * 100).toFixed(2)}%`,
    minWidth: 110,
  },
  {
    field: 'final_value',
    headerName: 'Final Value',
    type: 'rightAligned',
    valueFormatter: (params) =>
      new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(params.value ?? 0),
    minWidth: 140,
  },
  {
    field: 'status',
    headerName: 'Status',
    minWidth: 90,
  },
];

export default function ResultsPane() {
  const store = useTerminalStore();
  let containerRef: HTMLDivElement | undefined;
  let gridApi: GridApi | undefined;

  const initGrid = () => {
    ensureAgGridModules();
    if (!containerRef) return;

    const options: GridOptions = {
      columnDefs: columns,
      rowData: store.results() || [],
      animateRows: true,
      rowHeight: 26,
      headerHeight: 26,
      rowSelection: 'single',
      onRowClicked: (event) => {
        if (!event.data?.strategy_name) return;
        void store.loadStrategyDetails(event.data.strategy_name);
        void store.loadStrategyDocumentation(event.data.strategy_name);
      },
      onRowDoubleClicked: (event) => {
        if (!event.data?.name) return;
        void store.loadStrategyDetails(event.data.strategy_name);
        void store.loadStrategyDocumentation(event.data.strategy_name);
        void store.addBacktestSeries(event.data.name);
      },
    };

    gridApi = createGrid(containerRef, options);
  };

  onMount(initGrid);

  onCleanup(() => {
    gridApi?.destroy();
    gridApi = undefined;
  });

  createEffect(() => {
    const data = store.results() || [];
    if (gridApi) {
      gridApi.setGridOption('rowData', data);
    }
  });

  return (
    <div style={{ height: '100%', width: '100%', display: 'flex', 'flex-direction': 'column' }}>
      <div style={{ padding: '6px', 'border-bottom': '1px solid #2a2f3a', display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'font-size': '12px' }}>
        <span>Backtest Results {store.results.loading ? '(loading…)' : `(${store.results()?.length || 0})`}</span>
        <button
          style={{ padding: '4px 8px', 'font-size': '11px', 'background-color': '#1f6feb', color: '#fff', border: 'none', 'border-radius': '3px', cursor: 'pointer' }}
          onClick={() => { void store.refetchResults(); }}
          disabled={store.results.loading}
        >
          Refresh
        </button>
      </div>
      <div class="ag-theme-quartz" style={{ flex: 1 }}>
        <div ref={containerRef} style={{ height: '100%', width: '100%' }} />
      </div>
      <div style={{ padding: '6px', 'border-top': '1px solid #2a2f3a', 'font-size': '11px', color: '#9ca3af' }}>
        Tip: double-click a row to open detailed metrics and add its equity curve to the chart.
      </div>
    </div>
  );
}
