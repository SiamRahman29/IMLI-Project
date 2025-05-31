import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, AppBar, Toolbar, Typography, Button } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import GenerateWords from './pages/GenerateWords';
import TrendingAnalysis from './pages/TrendingAnalysis';

// Create a Bengali-friendly theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Kalpurush", "SolaimanLipi", sans-serif',
    h1: {
      fontSize: '2.5rem',
    },
    h2: {
      fontSize: '2rem',
    },
    h3: {
      fontSize: '1.75rem',
    },
  },
});

function Navigation() {
  const location = useLocation();
  
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          বার্তা - ইমলি
        </Typography>
        <Button 
          color="inherit" 
          component={Link} 
          to="/"
          variant={location.pathname === '/' ? 'outlined' : 'text'}
          sx={{ mr: 2 }}
        >
          হোম
        </Button>
        <Button 
          color="inherit" 
          component={Link} 
          to="/trending"
          variant={location.pathname === '/trending' ? 'outlined' : 'text'}
          sx={{ mr: 2 }}
        >
          ট্রেন্ডিং
        </Button>
        <Button 
          color="inherit" 
          component={Link} 
          to="/generate"
          variant={location.pathname === '/generate' ? 'outlined' : 'text'}
        >
          জেনারেট
        </Button>
      </Toolbar>
    </AppBar>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <Navigation />
          <div className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/generate" element={<GenerateWords />} />
              <Route path="/trending" element={<TrendingAnalysis />} />
            </Routes>
          </div>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
