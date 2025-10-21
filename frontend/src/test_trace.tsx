import { render } from 'solid-js/web';
import { createSignal } from 'solid-js';

function TestComponent() {
  const [expandedTraceLogs, setExpandedTraceLogs] = createSignal<Record<string, boolean>>({});

  const toggleTraceLogs = (strategyName: string) => {
    const isExpanded = expandedTraceLogs()[strategyName];

    setExpandedTraceLogs(prev => ({
      ...prev,
      [strategyName]: !isExpanded
    }));

    console.log('Toggled trace logs for', strategyName, 'now expanded:', !isExpanded);
  };

  return (
    <div>
      <h1>Test Trace Logs Toggle</h1>
      <button onClick={() => toggleTraceLogs('test_strategy')}>
        📋 Trace
      </button>
      <p>Expanded: {expandedTraceLogs()['test_strategy'] ? 'Yes' : 'No'}</p>
    </div>
  );
}

render(() => <TestComponent />, document.getElementById('root')!);
