import { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  Badge,
  Container,
  Paper,
  Divider,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import LanguageIcon from '@mui/icons-material/Language';
import NewspaperIcon from '@mui/icons-material/Newspaper';
import GroupIcon from '@mui/icons-material/Group';
import RefreshIcon from '@mui/icons-material/Refresh';
import FilterListIcon from '@mui/icons-material/FilterList';
import { apiV2, formatDate, getScoreColor, groupPhrasesByType, groupPhrasesBySource } from '../api';

function TrendingAnalysis() {
  const [trendingData, setTrendingData] = useState(null);
  const [dailyData, setDailyData] = useState(null);
  const [stats, setStats] = useState(null);
  const [sources, setSources] = useState({ sources: [], phrase_types: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  
  // Filter states
  const [filters, setFilters] = useState({
    start_date: formatDate(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)), // 7 days ago
    end_date: formatDate(new Date()),
    source: '',
    phrase_type: '',
    limit: 50
  });

  useEffect(() => {
    fetchAllData();
    fetchSources();
  }, []);

  useEffect(() => {
    if (tabValue === 0) {
      fetchTrendingData();
    } else if (tabValue === 1) {
      fetchDailyData();
    } else if (tabValue === 2) {
      fetchStats();
    }
  }, [filters, tabValue]);

  const fetchAllData = async () => {
    await Promise.all([
      fetchTrendingData(),
      fetchDailyData(),
      fetchStats()
    ]);
  };

  const fetchTrendingData = async () => {
    try {
      setLoading(true);
      const response = await apiV2.getTrendingPhrases(filters);
      setTrendingData(response.data);
    } catch (err) {
      let msg = 'ট্রেন্ডিং ডেটা লোড করতে ব্যর্থ';
      if (err.response && err.response.data && err.response.data.detail) {
        msg += `: ${err.response.data.detail}`;
      }
      setError(msg);
      console.error('Trending data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDailyData = async () => {
    try {
      setLoading(true);
      const response = await apiV2.getDailyTrending(filters.end_date);
      setDailyData(response.data);
    } catch (err) {
      let msg = 'দৈনিক ডেটা লোড করতে ব্যর্থ';
      if (err.response && err.response.data && err.response.data.detail) {
        msg += `: ${err.response.data.detail}`;
      }
      setError(msg);
      console.error('Daily data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await apiV2.getStats();
      setStats(response.data);
    } catch (err) {
      let msg = 'পরিসংখ্যান লোড করতে ব্যর্থ';
      if (err.response && err.response.data && err.response.data.detail) {
        msg += `: ${err.response.data.detail}`;
      }
      setError(msg);
      console.error('Stats error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSources = async () => {
    try {
      const response = await apiV2.getSources();
      setSources(response.data);
    } catch (err) {
      console.error('Sources error:', err);
    }
  };

  const runNewAnalysis = async () => {
    try {
      setLoading(true);
      await apiV2.runAnalysis();
      await fetchAllData();
      setError(null);
    } catch (err) {
      setError('নতুন বিশ্লেষণ চালাতে ব্যর্থ');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setError(null);
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const renderFilters = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          <FilterListIcon sx={{ mr: 1 }} />
          ফিল্টার অপশন
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={2}>
            <TextField
              fullWidth
              label="শুরুর তারিখ"
              type="date"
              value={filters.start_date}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              InputLabelProps={{ shrink: true }}
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <TextField
              fullWidth
              label="শেষ তারিখ"
              type="date"
              value={filters.end_date}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              InputLabelProps={{ shrink: true }}
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>উৎস</InputLabel>
              <Select
                value={filters.source}
                label="উৎস"
                onChange={(e) => handleFilterChange('source', e.target.value)}
              >
                <MenuItem value="">সব</MenuItem>
                {sources.sources.map((source) => (
                  <MenuItem key={source} value={source}>{source}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>ধরন</InputLabel>
              <Select
                value={filters.phrase_type}
                label="ধরন"
                onChange={(e) => handleFilterChange('phrase_type', e.target.value)}
              >
                <MenuItem value="">সব</MenuItem>
                {sources.phrase_types.map((type) => (
                  <MenuItem key={type} value={type}>{type}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <TextField
              fullWidth
              label="সীমা"
              type="number"
              value={filters.limit}
              onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
              size="small"
              inputProps={{ min: 10, max: 200 }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button
              variant="outlined"
              onClick={runNewAnalysis}
              disabled={loading}
              startIcon={<RefreshIcon />}
              fullWidth
            >
              নতুন বিশ্লেষণ
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

  const renderTrendingTab = () => {
    if (!trendingData || !trendingData.phrases) {
      return (
        <Alert severity="info">
          কোনো ট্রেন্ডিং ডেটা পাওয়া যায়নি। প্রথমে বিশ্লেষণ চালান।
        </Alert>
      );
    }

    const phrasesByType = groupPhrasesByType(trendingData.phrases);
    const phrasesBySource = groupPhrasesBySource(trendingData.phrases);

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                শীর্ষ ট্রেন্ডিং ফ্রেজ
              </Typography>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {trendingData.start_date} থেকে {trendingData.end_date} | মোট: {trendingData.total_count}টি
                </Typography>
                <List>
                  {trendingData.phrases.slice(0, 20).map((phrase, index) => (
                    <ListItem key={index} divider>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="h6">{phrase.phrase}</Typography>
                            <Chip 
                              label={phrase.score.toFixed(2)} 
                              size="small" 
                              color={getScoreColor(phrase.score)} 
                            />
                          </Box>
                        }
                        secondary={
                          <Box display="flex" gap={1} mt={1}>
                            <Chip label={`ফ্রিকোয়েন্সি: ${phrase.frequency}`} size="small" variant="outlined" />
                            <Chip label={phrase.phrase_type} size="small" color="primary" variant="outlined" />
                            <Chip label={phrase.source} size="small" color="secondary" variant="outlined" />
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <LanguageIcon sx={{ mr: 1 }} />
                ধরন অনুযায়ী
              </Typography>
              {Object.entries(phrasesByType).map(([type, phrases]) => (
                <Box key={type} sx={{ mb: 1 }}>
                  <Chip 
                    label={`${type}: ${phrases.length}`} 
                    variant="outlined" 
                    sx={{ mr: 1, mb: 1 }}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <NewspaperIcon sx={{ mr: 1 }} />
                উৎস অনুযায়ী
              </Typography>
              {Object.entries(phrasesBySource).map(([source, phrases]) => (
                <Box key={source} sx={{ mb: 1 }}>
                  <Chip 
                    label={`${source}: ${phrases.length}`} 
                    variant="outlined" 
                    sx={{ mr: 1, mb: 1 }}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  const renderDailyTab = () => {
    if (!dailyData) {
      return (
        <Alert severity="info">
          দৈনিক ডেটা লোড করা হচ্ছে...
        </Alert>
      );
    }

    return (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom>
            দৈনিক সারসংক্ষেপ - {dailyData.date}
          </Typography>
          <Typography variant="h6" color="text.secondary" paragraph>
            মোট ফ্রেজ: {dailyData.total_phrases}টি
          </Typography>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                শীর্ষ ১০ ট্রেন্ডিং
              </Typography>
              <List>
                {dailyData.top_phrases.map((phrase, index) => (
                  <ListItem key={index} dense>
                    <ListItemText
                      primary={phrase.phrase}
                      secondary={`স্কোর: ${phrase.score.toFixed(2)} | ফ্রিকোয়েন্সি: ${phrase.frequency}`}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>উৎস অনুযায়ী</Typography>
              {Object.entries(dailyData.by_source).map(([source, phrases]) => (
                <Chip 
                  key={source}
                  label={`${source}: ${phrases.length}`} 
                  sx={{ mr: 1, mb: 1 }}
                  variant="outlined"
                />
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>ধরন অনুযায়ী</Typography>
              {Object.entries(dailyData.by_phrase_type).map(([type, phrases]) => (
                <Chip 
                  key={type}
                  label={`${type}: ${phrases.length}`} 
                  sx={{ mr: 1, mb: 1 }}
                  variant="outlined"
                />
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  const renderStatsTab = () => {
    if (!stats) {
      return (
        <Alert severity="info">
          পরিসংখ্যান লোড করা হচ্ছে...
        </Alert>
      );
    }

    if (stats.total_phrases === 0) {
      return (
        <Alert severity="warning">
          {stats.message || 'কোনো পরিসংখ্যান পাওয়া যায়নি। প্রথমে বিশ্লেষণ চালান।'}
        </Alert>
      );
    }

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                সামগ্রিক পরিসংখ্যান
              </Typography>
              <Typography variant="h3" color="primary">
                {stats.total_phrases}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                মোট ট্রেন্ডিং ফ্রেজ
              </Typography>
              <Typography variant="h4" color="secondary" sx={{ mt: 2 }}>
                {stats.recent_phrases_7_days}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                গত ৭ দিনের ফ্রেজ
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                উৎস অনুযায়ী পরিসংখ্যান
              </Typography>
              {stats.by_source.map((sourceStat, index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  <Typography variant="subtitle1">{sourceStat.source}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    সংখ্যা: {sourceStat.count} | গড় স্কোর: {sourceStat.avg_score}
                  </Typography>
                  <Divider sx={{ mt: 1 }} />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ধরন অনুযায়ী পরিসংখ্যান
              </Typography>
              <Grid container spacing={2}>
                {stats.by_phrase_type.map((typeStat, index) => (
                  <Grid item xs={12} sm={6} md={4} key={index}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h6">{typeStat.phrase_type}</Typography>
                      <Typography variant="h4" color="primary">
                        {typeStat.count}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        গড় স্কোর: {typeStat.avg_score}
                      </Typography>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  if (loading && tabValue === 0) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" height="400px">
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ ml: 2 }}>
            বিশ্লেষণ চলছে...
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box textAlign="center" mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          <TrendingUpIcon sx={{ fontSize: '1.2em', mr: 1 }} />
          ট্রেন্ডিং বিশ্লেষণ
        </Typography>
        <Typography variant="h6" color="text.secondary">
          বাংলা সংবাদ ও সোশ্যাল মিডিয়া থেকে ট্রেন্ডিং শব্দ ও বাক্যাংশ
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {renderFilters()}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab 
            label="ট্রেন্ডিং ফ্রেজ" 
            icon={<TrendingUpIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="দৈনিক সারসংক্ষেপ" 
            icon={<NewspaperIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="পরিসংখ্যান" 
            icon={<GroupIcon />} 
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {loading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {tabValue === 0 && renderTrendingTab()}
          {tabValue === 1 && renderDailyTab()}
          {tabValue === 2 && renderStatsTab()}
        </>
      )}
    </Container>
  );
}

export default TrendingAnalysis;
