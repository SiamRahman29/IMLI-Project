import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Box,
  Alert,
  CircularProgress,
  Divider,
  Chip,
  Grid,
  Paper
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CheckIcon from '@mui/icons-material/Check';
import { apiV2, api } from '../api';

function GenerateWords() {
  const [loading, setLoading] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [aiCandidates, setAiCandidates] = useState('');
  const [selectedWord, setSelectedWord] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const runAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      // Run the comprehensive analysis
      const response = await apiV2.generateCandidates();
      setAnalysisComplete(true);
      setAiCandidates(response.data.ai_candidates || 'কোনো AI প্রার্থী পাওয়া যায়নি');
    } catch (err) {
      let msg = 'বিশ্লেষণ চালাতে ব্যর্থ';
      if (err.response && err.response.data && err.response.data.detail) {
        msg += `: ${err.response.data.detail}`;
      }
      setError(msg);
      setAnalysisComplete(false);
      setAiCandidates('');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Utility to strip leading numbers, dots, and titles (like ড., ডঃ, ড:)
  const cleanCandidate = (candidate) => {
    let cleaned = candidate
      .replace(/^\d+[.:][\s\-–—]*/u, '') // Remove leading numbers and dot/colon
      .replace(/^[\d\u09E6-\u09EF]+[.:][\s\-–—]*/u, '') // Bengali digits
      .replace(/^(ড\.|ডঃ|ড:)[\s\-–—]*/u, '') // Remove Bengali "Dr." titles
      .trim();
    return cleaned;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedWord.trim()) return;
    const sanitizedWord = cleanCandidate(selectedWord);
    try {
      setSubmitting(true);
      setError(null);
      
      // Use legacy API for setting word of the day
      await api.setWordOfTheDay(sanitizedWord);
      
      setSuccess(true);
      setTimeout(() => {
        navigate('/');
      }, 2000);
      
    } catch (err) {
      setError('শব্দ সেট করতে ব্যর্থ হয়েছে');
      console.error('Submit error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const parseCandidates = (candidatesText) => {
    if (!candidatesText) return [];
    return candidatesText.split('\n')
      .map(line => line.trim())
      .filter(line => line && !line.includes(':') && line.length > 1)
      .slice(0, 10); // Limit to 10 candidates
  };

  if (success) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, textAlign: 'center' }}>
        <Alert severity="success" sx={{ mb: 2 }}>
          <Typography variant="h6">সফলভাবে সম্পন্ন!</Typography>
          <Typography>আজকের শব্দ নির্ধারণ করা হয়েছে: <strong>{selectedWord}</strong></Typography>
        </Alert>
        <CircularProgress sx={{ mt: 2 }} />
        <Typography sx={{ mt: 2 }}>হোম পেজে ফিরে যাচ্ছি...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box textAlign="center" mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          <AutoAwesomeIcon sx={{ fontSize: '1.2em', mr: 1 }} />
          ট্রেন্ডিং শব্দ উৎপাদন
        </Typography>
        <Typography variant="h6" color="text.secondary">
          AI এবং NLP বিশ্লেষণ ব্যবহার করে বর্তমান ট্রেন্ডিং শব্দ খুঁজে বের করুন
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                ১. বিশ্লেষণ চালান
              </Typography>
              <Typography variant="body1" paragraph color="text.secondary">
                সংবাদ ও সোশ্যাল মিডিয়া ডেটা থেকে ট্রেন্ডিং শব্দ বিশ্লেষণ শুরু করুন
              </Typography>
              
              <Button
                variant="contained"
                size="large"
                onClick={runAnalysis}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <RefreshIcon />}
                fullWidth
              >
                {loading ? 'বিশ্লেষণ চলছে...' : 'বিশ্লেষণ শুরু করুন'}
              </Button>
              
              {analysisComplete && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    ✅ বিশ্লেষণ সম্পূর্ণ! AI প্রার্থী তৈরি হয়েছে।
                  </Typography>
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                ২. শব্দ নির্বাচন
              </Typography>
              <Typography variant="body1" paragraph color="text.secondary">
                AI দ্বারা প্রস্তাবিত শব্দ থেকে আজকের শব্দ নির্বাচন করুন
              </Typography>
              
              <Box component="form" onSubmit={handleSubmit}>
                <TextField
                  fullWidth
                  label="আজকের শব্দ"
                  value={selectedWord}
                  onChange={(e) => setSelectedWord(e.target.value)}
                  placeholder="একটি শব্দ টাইপ করুন..."
                  disabled={submitting}
                  sx={{ mb: 2 }}
                />
                
                <Button
                  type="submit"
                  variant="contained"
                  color="success"
                  disabled={!selectedWord.trim() || submitting}
                  startIcon={submitting ? <CircularProgress size={20} /> : <CheckIcon />}
                  fullWidth
                  size="large"
                >
                  {submitting ? 'সেট করা হচ্ছে...' : 'আজকের শব্দ নির্ধারণ করুন'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {analysisComplete && aiCandidates && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              AI প্রার্থী শব্দসমূহ
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            {parseCandidates(aiCandidates).length > 0 ? (
              <Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  নিচের শব্দগুলো থেকে বেছে নিয়ে উপরের ফর্মে টাইপ করুন:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  {parseCandidates(aiCandidates).map((candidate, index) => (
                    <Chip
                      key={index}
                      label={candidate}
                      onClick={() => setSelectedWord(cleanCandidate(candidate))}
                      variant={selectedWord === cleanCandidate(candidate) ? "filled" : "outlined"}
                      color={selectedWord === cleanCandidate(candidate) ? "primary" : "default"}
                      sx={{ cursor: 'pointer' }}
                    />
                  ))}
                </Box>
                <Divider />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  সম্পূর্ণ AI প্রতিক্রিয়া:
                </Typography>
              </Box>
            ) : null}
            
            <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.50', maxHeight: 300, overflow: 'auto' }}>
              <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                {aiCandidates}
              </Typography>
            </Paper>
          </CardContent>
        </Card>
      )}

      <Box textAlign="center" mt={4}>
        <Button variant="outlined" onClick={() => navigate('/')}>
          হোম পেজে ফিরে যান
        </Button>
      </Box>
    </Container>
  );
}

export default GenerateWords;
