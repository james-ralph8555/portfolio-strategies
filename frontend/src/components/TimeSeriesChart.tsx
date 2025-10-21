import { JSX, createEffect, onCleanup, onMount } from 'solid-js';
import Plotly from 'plotly.js-dist-min';

export type ChartSeries = {
  id: string;
  name: string;
  x: Array<string | Date>;
  y: number[];
  color?: string;
  visible?: boolean;
  yaxis?: 'y' | 'y2';
};

type Props = {
  series: ChartSeries[];
  height?: number;
  layout?: any;
  config?: any;
};

export default function TimeSeriesChart(props: Props): JSX.Element {
  let container!: HTMLDivElement;

  const baseLayout = () => ({
    autosize: true,
    margin: { l: 50, r: 50, t: 20, b: 40 },
    xaxis: { title: 'Date', type: 'date' },
    yaxis: { title: 'Value', rangemode: 'tozero' },
    yaxis2: {
      title: 'Value (axis 2)',
      overlaying: 'y',
      side: 'right',
      showgrid: false,
      rangemode: 'tozero',
    },
    legend: { orientation: 'h' as const, x: 0, y: 1.1 },
    ...props.layout,
    height: props.height ?? props.layout?.height ?? 420,
  });

  const toTraces = () =>
    props.series.map((s) => ({
      type: 'scatter',
      mode: 'lines',
      name: s.name,
      x: s.x,
      y: s.y,
      line: { color: s.color || undefined },
      visible: s.visible === false ? 'legendonly' : true,
      yaxis: s.yaxis ?? 'y',
    }));

  const render = async () => {
    const traces = toTraces();
    const layout = baseLayout();
    const config = {
      displaylogo: false,
      responsive: true,
      scrollZoom: true,
      modeBarButtonsToRemove: [
        'select2d',
        'lasso2d',
        'toggleSpikelines',
      ],
      ...(props.config || {}),
    };
    await Plotly.react(container, traces as any, layout as any, config as any);
  };

  onMount(() => {
    render();
    const onResize = () => Plotly.Plots.resize(container);
    window.addEventListener('resize', onResize);
    onCleanup(() => {
      window.removeEventListener('resize', onResize);
      Plotly.purge(container);
    });
  });

  createEffect(() => {
    // Track reactive dependencies
    void props.series.length;
    void props.height;
    void props.layout;
    void props.config;
    render();
  });

  return <div ref={container} />;
}
