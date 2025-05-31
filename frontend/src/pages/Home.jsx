import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  Card, 
  CardContent, 
  Box, 
  Button, 
  Grid,
  Alert,
  CircularProgress
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import { apiV2 } from '../api';

function Home() {
  const [word, setWord] = useState('');
  const [date, setDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWordOfTheDay();
  }, []);

  const fetchWordOfTheDay = async () => {
    try {
      setLoading(true);
      const response = await apiV2.getWordOfTheDay();
      if (response.data.words) {
        setWord(response.data.words);
        setDate(response.data.date);
      }
    } catch (err) {
      setError('আজকের শব্দ এখনো নির্ধারণ করা হয়নি');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          লোড হচ্ছে...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box textAlign="center" mb={4}>
        <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
          বার্তা - ইমলি
        </Typography>
        <Typography variant="h5" color="text.secondary" gutterBottom>
          বাংলা ট্রেন্ডিং শব্দ বিশ্লেষণ সিস্টেম
        </Typography>
      </Box>

      {error ? (
        <Alert severity="info" sx={{ mb: 4 }}>
          {error}
        </Alert>
      ) : (
        <Card sx={{ mb: 4, textAlign: 'center', py: 4 }}>
          <CardContent>
            <Typography variant="h4" component="h2" gutterBottom>
              আজকের শব্দ
            </Typography>
            {date && (
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {new Date(date).toLocaleDateString('bn-BD')}
              </Typography>
            )}
            <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'primary.main', mt: 2 }}>
              {word}
            </Typography>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <TrendingUpIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                ট্রেন্ডিং বিশ্লেষণ
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                সংবাদ ও সোশ্যাল মিডিয়া থেকে বর্তমান ট্রেন্ডিং শব্দ ও বাক্যাংশ দেখুন
              </Typography>
              <Button 
                component={Link} 
                to="/trending" 
                variant="contained" 
                size="large"
                sx={{ mt: 2 }}
              >
                বিশ্লেষণ দেখুন
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <AutoAwesomeIcon sx={{ fontSize: 60, color: 'secondary.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                শব্দ উৎপাদন
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                AI ব্যবহার করে নতুন ট্রেন্ডিং শব্দের প্রার্থী তৈরি করুন
              </Typography>
              <Button 
                component={Link} 
                to="/generate" 
                variant="outlined" 
                size="large"
                sx={{ mt: 2 }}
              >
                শব্দ তৈরি করুন
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box textAlign="center" mt={6} py={3}>
        <Typography variant="body2" color="text.secondary">
          N-gram Frequency Analysis এবং TF-IDF পদ্ধতি ব্যবহার করে তৈরি
        </Typography>
      </Box>
    </Container>
  );
}

export default Home;
