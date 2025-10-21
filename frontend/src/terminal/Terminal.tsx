import { onCleanup, onMount } from 'solid-js';
import { render } from 'solid-js/web';
import {
  DockviewComponent,
  type DockviewComponentOptions,
  type IContentRenderer,
} from 'dockview-core';
import 'dockview-core/dist/styles/dockview.css';
import WatchlistPane from './WatchlistPane';
import ChartPane from './ChartPane';
import LogsPane from './LogsPane';
import ControlPane from './panes/ControlPane';
import ResultsPane from './panes/ResultsPane';
import DetailsPane from './panes/DetailsPane';
import ChartControlsPane from './panes/ChartControlsPane';
import CachePane from './panes/CachePane';
import { createTerminalStore, TerminalProvider } from './TerminalStore';

export default function Terminal() {
  const STORAGE_KEY = 'dockview-layout-v1';
  const store = createTerminalStore();
  const panelRegistry = {
    control: ControlPane,
    results: ResultsPane,
    details: DetailsPane,
    chartControls: ChartControlsPane,
    watch: WatchlistPane,
    chart: ChartPane,
    logs: LogsPane,
    cache: CachePane,
  };

  let containerRef!: HTMLDivElement;
  let dockview: DockviewComponent | undefined;
  let disposeLayoutListener: (() => void) | undefined;

  const createRenderer = (name: keyof typeof panelRegistry): IContentRenderer => {
    const element = document.createElement('div');
    element.classList.add('terminal-pane');
    element.style.height = '100%';
    element.style.width = '100%';

    let dispose: (() => void) | undefined;

    return {
      element,
      init: () => {
        const Component = panelRegistry[name];
        dispose = render(
          () => (
            <TerminalProvider value={store}>
              <Component />
            </TerminalProvider>
          ),
          element,
        );
      },
      dispose: () => {
        dispose?.();
        dispose = undefined;
        element.replaceChildren();
      },
    };
  };

  const buildOptions = (): DockviewComponentOptions => ({
    hideBorders: false,
    createComponent: ({ name }) => {
      if (name in panelRegistry) {
        return createRenderer(name as keyof typeof panelRegistry);
      }
      throw new Error(`Unknown dockview component: ${name}`);
    },
  });

  onMount(() => {
    if (!containerRef) return;

    dockview = new DockviewComponent(containerRef, buildOptions());
    // Ensure initial layout before any panels are added or restored.
    dockview.layout(containerRef.clientWidth, containerRef.clientHeight);

    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        dockview.fromJSON(JSON.parse(raw));
      } catch {
        // ignore malformed saved layouts
      }
    }

    if (!dockview.panels.length) {
      const control = dockview.addPanel({ id: 'control', title: 'Controls', component: 'control' });
      const results = dockview.addPanel({
        id: 'results',
        title: 'Results',
        component: 'results',
        position: { referencePanel: control, direction: 'right' },
      });
      const chartPanel = dockview.addPanel({
        id: 'chart',
        title: 'Chart',
        component: 'chart',
        position: { referencePanel: results, direction: 'right' },
      });
      dockview.addPanel({
        id: 'chartControls',
        title: 'Chart Series',
        component: 'chartControls',
        position: { referencePanel: chartPanel, direction: 'below' },
      });
      dockview.addPanel({
        id: 'details',
        title: 'Strategy Details',
        component: 'details',
        position: { referencePanel: results, direction: 'below' },
      });
      dockview.addPanel({
        id: 'watch',
        title: 'Watchlist',
        component: 'watch',
        position: { referencePanel: chartPanel, direction: 'right' },
      });
      const logs = dockview.addPanel({
        id: 'logs',
        title: 'Logs',
        component: 'logs',
        position: { referencePanel: control, direction: 'below' },
      });
      dockview.addPanel({
        id: 'cache',
        title: 'Cache',
        component: 'cache',
        position: { referencePanel: logs, direction: 'below' },
      });

      // ensure initial focus matches previous behaviour
      dockview.setActivePanel(chartPanel);
    }

    const layoutDisposable = dockview.onDidLayoutChange(() => {
      const json = dockview?.toJSON();
      if (json) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(json));
      }
    });
    disposeLayoutListener = () => layoutDisposable.dispose();
  });

  onCleanup(() => {
    disposeLayoutListener?.();
    dockview?.dispose();
    dockview = undefined;
  });

  return (
    <div
      ref={containerRef}
      class="dockview-theme-dark"
      style={{ height: '100%', width: '100%' }}
    />
  );
}
