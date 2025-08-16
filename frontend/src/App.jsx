import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import GenerateWords from './pages/GenerateWords';
import TrendingAnalysis from './pages/TrendingAnalysis';
import Login from './pages/Login';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import UserManagement from './pages/UserManagement';
import UserProfile from './pages/UserProfile';
import Footer from './components/Footer';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Navbar />
        <main>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<Home />} />
            <Route path="/trending" element={<TrendingAnalysis />} />
            <Route path="/login" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            {/* Protected routes - All authenticated users */}
            <Route 
              path="/profile" 
              element={
                <ProtectedRoute>
                  <UserProfile />
                </ProtectedRoute>
              } 
            />
            {/* Protected routes - Admin only */}
            <Route 
              path="/generate-words" 
              element={
                <ProtectedRoute adminOnly={true}>
                  <GenerateWords />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/users" 
              element={
                <ProtectedRoute adminOnly={true}>
                  <UserManagement />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </main>
        {/* Show footer on all pages except login, forgot-password, reset-password */}
        {!["/login", "/forgot-password", "/reset-password"].includes(window.location.pathname) && <Footer />}
      </Router>
    </AuthProvider>
  );
}

export default App;
