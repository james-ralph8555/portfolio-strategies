import { Suspense } from 'solid-js';
import UnifiedInterface from './pages/UnifiedInterface';
import LoadingSpinner from './components/LoadingSpinner';

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <UnifiedInterface />
    </Suspense>
  );
}

export default App;
