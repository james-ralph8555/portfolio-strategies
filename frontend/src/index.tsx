/* @refresh reload */
import { render } from 'solid-js/web';
import { Route, Router } from '@solidjs/router';
import './index.css';
import App from './App';
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import Backtest from './pages/Backtest';
import MarketData from './pages/MarketData';
import Results from './pages/Results';

const root = document.getElementById('root');

if (import.meta.env.DEV && !(root instanceof HTMLElement)) {
  throw new Error(
    'Root element not found. Did you forget to add it to your index.html? Or maybe the id attribute got misspelled?',
  );
}

render(
  () => (
    <Router root={App}>
      <Route path="/" component={Dashboard} />
      <Route path="/strategies" component={Strategies} />
      <Route path="/backtest" component={Backtest} />
      <Route path="/market-data" component={MarketData} />
      <Route path="/results" component={Results} />
    </Router>
  ),
  root!,
);
