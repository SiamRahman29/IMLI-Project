import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import GenerateWords from './pages/GenerateWords';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/generate" element={<GenerateWords />} />
      </Routes>
    </Router>
  );
}

export default App;
