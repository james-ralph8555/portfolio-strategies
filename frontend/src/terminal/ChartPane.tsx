import { createEffect, onCleanup, onMount } from 'solid-js';
import { createChart, type IChartApi, type ISeriesApi, LineSeries } from 'lightweight-charts';
import { useTerminalStore } from './TerminalStore';

export default function ChartPane() {
  const store = useTerminalStore();
  let el!: HTMLDivElement;
  let seriesMap = new Map<string, ISeriesApi<'Line'>>();
  let chart: IChartApi | null = null;

  const syncSeries = () => {
    if (!chart) return;
    const incoming = store.chartSeries();
    const alive = new Set<string>();

    console.log('ChartPane: syncSeries called with', incoming.length, 'series');

    incoming.forEach((series) => {
      alive.add(series.id);
      let line = seriesMap.get(series.id);

      if (!line) {
        console.log('ChartPane: Creating new series for', series.id, 'visible:', series.visible);
        line = chart!.addSeries(LineSeries, {
          color: series.color || '#4ea1ff',
          priceLineVisible: false,
          lastValueVisible: series.visible,
          visible: series.visible,
          lineWidth: 2,
        });
        seriesMap.set(series.id, line);
      }

      // Convert data to proper format
      const data = series.x.map((t, index) => {
        let timeValue: string | number;
        if (typeof t === 'string') {
          // Extract date part from ISO string or use as-is if already in correct format
          timeValue = t.includes('T') ? t.split('T')[0] : t;
        } else {
          // Convert Date to yyyy-mm-dd format
          const date = new Date(t);
          timeValue = date.toISOString().split('T')[0];
        }
        const value = series.y[index];
        return { time: timeValue, value };
      }).filter(item => !isNaN(item.value) && item.value !== null && item.value !== undefined);

      console.log('ChartPane: Setting data for', series.id, 'with', data.length, 'points, visible:', series.visible);
      if (data.length > 0) {
        console.log('ChartPane: Sample data points:', data.slice(0, 3));
      }

      // Set data first, then apply visibility options
      line.setData(data);
      line.applyOptions({
        visible: series.visible,
        lastValueVisible: series.visible,
        priceLineVisible: false
      });
    });

    // Remove series that are no longer in the incoming data
    for (const [id, series] of seriesMap) {
      if (!alive.has(id)) {
        console.log('ChartPane: Removing series', id);
        chart!.removeSeries(series);
        seriesMap.delete(id);
      }
    }

    // Fit content after all series are updated
    if (incoming.length > 0) {
      setTimeout(() => {
        chart?.timeScale().fitContent();
      }, 0);
    }
  };

  onMount(() => {
    // Create chart with proper configuration
    chart = createChart(el, {
      width: el.clientWidth,
      height: el.clientHeight,
      layout: {
        background: { color: '#0f1115' },
        textColor: '#c7d0df'
      },
      grid: {
        horzLines: { color: '#1c2128' },
        vertLines: { color: '#1c2128' }
      },
      rightPriceScale: {
        borderVisible: false,
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        vertLine: { labelBackgroundColor: '#111827' },
        horzLine: { labelBackgroundColor: '#111827' }
      },
      watermark: {
        visible: false,
      },
    });

    // Initial sync
    syncSeries();

    // Handle resize
    const resizeObserver = new ResizeObserver(() => {
      if (chart && el) {
        chart.applyOptions({
          width: el.clientWidth,
          height: el.clientHeight
        });
      }
    });
    resizeObserver.observe(el);

    onCleanup(() => {
      resizeObserver.disconnect();
      if (chart) {
        chart.remove();
        chart = null;
      }
      seriesMap.clear();
    });
  });

  // React to series changes
  createEffect(() => {
    const series = store.chartSeries();
    if (chart && series.length > 0) {
      // Use setTimeout to ensure DOM is ready
      setTimeout(() => {
        syncSeries();
      }, 0);
    }
  });

  return <div ref={el} style={{ width: '100%', height: '100%', position: 'relative' }} />;
}
