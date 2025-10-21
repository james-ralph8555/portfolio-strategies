import { createEffect, onCleanup, onMount } from 'solid-js';
import { createChart, type ISeriesApi } from 'lightweight-charts';
import { useTerminalStore } from './TerminalStore';

export default function ChartPane() {
  const store = useTerminalStore();
  let el!: HTMLDivElement;
  let seriesMap = new Map<string, ISeriesApi<'Line'>>();
  let chart: ReturnType<typeof createChart> | null = null;

  const syncSeries = () => {
    if (!chart) return;
    const incoming = store.chartSeries();
    const alive = new Set<string>();
    const chartApi = chart as unknown as {
      addLineSeries: (...args: any[]) => ISeriesApi<'Line'>;
      removeSeries: (series: ISeriesApi<'Line'>) => void;
    };

    incoming.forEach((series) => {
      alive.add(series.id);
      let line = seriesMap.get(series.id);
      if (!line) {
        line = chartApi.addLineSeries({ color: series.color || '#4ea1ff', priceLineVisible: false, lastValueVisible: true });
        seriesMap.set(series.id, line);
      }

      const data = series.x.map((t, index) => ({
        time: typeof t === 'string' ? (t as string) : Math.floor((t as Date).getTime() / 1000),
        value: series.y[index],
      }));
      line!.setData(data as any);
      line!.applyOptions({ visible: series.visible !== false });
    });

    for (const [id, series] of seriesMap) {
      if (!alive.has(id)) {
        chartApi.removeSeries(series);
        seriesMap.delete(id);
      }
    }
  };

  onMount(() => {
    chart = createChart(el, {
      width: el.clientWidth,
      height: el.clientHeight,
      layout: { background: { color: '#0f1115' }, textColor: '#c7d0df' },
      grid: { horzLines: { color: '#1c2128' }, vertLines: { color: '#1c2128' } },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
      crosshair: { vertLine: { labelBackgroundColor: '#111827' }, horzLine: { labelBackgroundColor: '#111827' } },
    });

    syncSeries();
    const ro = new ResizeObserver(() => chart?.applyOptions({ width: el.clientWidth, height: el.clientHeight }));
    ro.observe(el);
    onCleanup(() => {
      ro.disconnect();
      chart?.remove();
      chart = null;
      seriesMap.clear();
    });
  });

  createEffect(() => {
    if (!chart) return;
    syncSeries();
  });

  return <div ref={el} style={{ width: '100%', height: '100%' }} />;
}
