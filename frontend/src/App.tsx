import type { RouteSectionProps } from '@solidjs/router';
import { Suspense } from 'solid-js';
import Navbar from './components/Navbar';
import LoadingSpinner from './components/LoadingSpinner';

function App(props: RouteSectionProps) {
  return (
    <div class="min-h-screen bg-gray-50">
      <Navbar />
      <main class="container mx-auto px-4 py-8">
        <Suspense fallback={<LoadingSpinner />}>
          {props.children}
        </Suspense>
      </main>
    </div>
  );
}

export default App;
