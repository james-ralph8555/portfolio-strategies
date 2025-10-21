import { Suspense } from 'solid-js';
import Terminal from './terminal/Terminal';
import LoadingSpinner from './components/LoadingSpinner';

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Terminal />
    </Suspense>
  );
}

export default App;
