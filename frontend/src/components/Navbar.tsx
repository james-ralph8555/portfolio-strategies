import { A } from '@solidjs/router';
import { BarChart3, TrendingUp, Database, PlayCircle, BarChart } from 'lucide-solid';

const Navbar = () => {
  return (
    <nav class="bg-white shadow-lg">
      <div class="container mx-auto px-4">
        <div class="flex justify-between items-center py-4">
          <div class="flex items-center space-x-2">
            <BarChart3 class="h-8 w-8 text-blue-600" />
            <A href="/" class="text-xl font-bold text-gray-800 hover:text-blue-600">
              Portfolio Manager
            </A>
          </div>

          <div class="flex space-x-6">
            <A
              href="/"
              class="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
              activeClass="text-blue-600 font-semibold"
            >
              <BarChart class="h-4 w-4" />
              <span>Dashboard</span>
            </A>

            <A
              href="/strategies"
              class="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
              activeClass="text-blue-600 font-semibold"
            >
              <TrendingUp class="h-4 w-4" />
              <span>Strategies</span>
            </A>

            <A
              href="/backtest"
              class="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
              activeClass="text-blue-600 font-semibold"
            >
              <PlayCircle class="h-4 w-4" />
              <span>Backtest</span>
            </A>

            <A
              href="/market-data"
              class="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
              activeClass="text-blue-600 font-semibold"
            >
              <Database class="h-4 w-4" />
              <span>Market Data</span>
            </A>

            <A
              href="/results"
              class="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
              activeClass="text-blue-600 font-semibold"
            >
              <BarChart class="h-4 w-4" />
              <span>Results</span>
            </A>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
