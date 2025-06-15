import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import GenerateWords from './pages/GenerateWords';
import TrendingAnalysis from './pages/TrendingAnalysis';

function Navigation() {
  const location = useLocation();
  return (
    <nav className="bg-blue-600 shadow">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16 items-center">
          <div className="flex-shrink-0 flex items-center">
            <span className="text-white text-xl font-bold tracking-wide">BARTA - IMLI</span>
          </div>
          <div className="flex space-x-2">
            <Link
              to="/"
              className={`px-4 py-1 rounded font-semibold transition ${location.pathname === '/' ? 'bg-white text-blue-600' : 'text-white hover:bg-blue-700'}`}
            >
              হোম
            </Link>
            <Link
              to="/trending"
              className={`px-4 py-1 rounded font-semibold transition ${location.pathname === '/trending' ? 'bg-white text-blue-600' : 'text-white hover:bg-blue-700'}`}
            >
              ট্রেন্ডিং
            </Link>
            <Link
              to="/generate"
              className={`px-4 py-1 rounded font-semibold transition ${location.pathname === '/generate' ? 'bg-white text-blue-600' : 'text-white hover:bg-blue-700'}`}
            >
              জেনারেট
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <Navigation />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/generate" element={<GenerateWords />} />
          <Route path="/trending" element={<TrendingAnalysis />} />
        </Routes>
      </main>
    </Router>
  );
}

export default App;
