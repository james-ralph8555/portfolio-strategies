import { createEffect, onCleanup, onMount } from 'solid-js';
import { createGrid, type GridApi, type GridOptions } from 'ag-grid-community';
import type { ColDef } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import { ensureAgGridModules } from '../utils/ensureAgGridModules';
import { useTerminalStore } from './TerminalStore';

const cols: ColDef[] = [
  { field: 'symbol', headerName: 'Symbol', minWidth: 80 },
  { field: 'last', headerName: 'Last', type: 'rightAligned', valueFormatter: (p) => p.value?.toFixed?.(2) },
  { field: 'chg', headerName: 'Chg %', type: 'rightAligned', valueFormatter: (p) => `${p.value?.toFixed?.(2)}%` },
  { field: 'volume', headerName: 'Vol', type: 'rightAligned', valueFormatter: (p) => (p.value ?? 0).toLocaleString() },
];

export default function WatchlistPane() {
  const store = useTerminalStore();
  let containerRef: HTMLDivElement | undefined;
  let gridApi: GridApi | undefined;

  const initialiseGrid = () => {
    ensureAgGridModules();
    if (!containerRef) return;

    const options: GridOptions = {
      columnDefs: cols,
      rowData: store.watchlistRows(),
      animateRows: true,
      rowHeight: 26,
      headerHeight: 26,
      onRowDoubleClicked: (event) => {
        if (event.data?.symbol) {
          store.addMarketSeries(event.data.symbol);
        }
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
    const data = store.watchlistRows();
    if (gridApi) {
      gridApi.setGridOption('rowData', data);
    }
  });

  return (
    <div class="ag-theme-quartz" style={{ height: '100%', width: '100%' }}>
      <div ref={containerRef} style={{ height: '100%', width: '100%' }} />
    </div>
  );
}
