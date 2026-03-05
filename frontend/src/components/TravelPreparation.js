import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Button, Box, CircularProgress, Alert, Tabs, Tab, Grid, Paper, List, ListItem, ListItemIcon, ListItemText, Divider, Chip } from '@mui/material';
import { Backpack, Info, CheckCircle, LocationOn, VideoLibrary, TipsAndUpdates } from '@mui/icons-material';
import axios from 'axios';

const TravelPreparation = ({ tripData, nextStep, prevStep }) => {
  const [keyPoints, setKeyPoints] = useState([]);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (tripData.optimized_cities && tripData.optimized_cities.length > 0 && keyPoints.length === 0) {
      fetchData();
    }
  }, [tripData]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post('http://localhost:8000/key-points', {
        cities: tripData.optimized_cities,
        country: tripData.arrival_country,
        interests: tripData.interests,
        start_date: tripData.start_date,
        end_date: tripData.end_date
      });
      
      setKeyPoints(response.data.key_points || []);
      fetchYouTubeVideos();
    } catch (err) {
      setError('Failed to fetch travel preparation data');
    } finally {
      setLoading(false);
    }
  };

  const fetchYouTubeVideos = async () => {
    try {
      const queries = [
        `${tripData.arrival_country} travel tips`,
        `${tripData.arrival_country} packing guide`,
        `${tripData.arrival_country} travel gear essentials`
      ];
      
      const videoPromises = queries.map(query => 
        axios.get(`http://localhost:8000/youtube-videos/${encodeURIComponent(query)}`, {
          params: { max_results: 2 }
        })
      );
      
      const responses = await Promise.all(videoPromises);
      const allVideos = responses.flatMap(res => res.data.videos);
      setVideos(allVideos.slice(0, 6));
    } catch (err) {
      console.error('Failed to fetch YouTube videos:', err);
    }
  };



  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Backpack sx={{ mr: 2, fontSize: 30 }} />
          <Typography variant="h4" component="h2">
            Travel Preparation
          </Typography>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {/* Key Points Section */}
        {keyPoints.length > 0 && (
          <Paper elevation={3} sx={{ p: 3, mb: 3, bgcolor: '#f0f7ff', border: '2px solid #1976d2' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TipsAndUpdates sx={{ mr: 1, color: 'primary.main', fontSize: 28 }} />
              <Typography variant="h5" color="primary.main" fontWeight="bold">
                Top 5 Essential Points
              </Typography>
            </Box>
            <Grid container spacing={2}>
              {keyPoints.map((point, index) => (
                <Grid item xs={12} key={index}>
                  <Paper elevation={2} sx={{ 
                    p: 2, 
                    bgcolor: point.type === 'gear' ? '#e8f5e9' : '#fff3e0',
                    borderLeft: `4px solid ${point.type === 'gear' ? '#4caf50' : '#ff9800'}`
                  }}>
                    <Box sx={{ display: 'flex', alignItems: 'start', gap: 1 }}>
                      <Chip 
                        label={point.type === 'gear' ? '🎒 GEAR' : '💡 TIP'} 
                        size="small" 
                        color={point.type === 'gear' ? 'success' : 'warning'}
                        sx={{ fontWeight: 'bold' }}
                      />
                      <Typography variant="body1" sx={{ flex: 1, fontWeight: 500 }}>
                        {point.text}
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Paper>
        )}

        {/* Video Guides Section */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
            <VideoLibrary sx={{ fontSize: 30, color: 'primary.main' }} />
            <Typography variant="h5" fontWeight="bold">Video Guides for {tripData.arrival_country}</Typography>
          </Box>
          {videos.length > 0 ? (
            <Grid container spacing={3}>
              {videos.map((video, index) => (
                <Grid item xs={12} md={6} key={index}>
                  <Paper elevation={3} sx={{ 
                    overflow: 'hidden',
                    transition: 'transform 0.2s',
                    '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 }
                  }}>
                    <Box sx={{ position: 'relative', paddingTop: '56.25%' }}>
                      <iframe
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: '100%',
                          height: '100%',
                          border: 'none'
                        }}
                        src={`https://www.youtube.com/embed/${video.videoId}`}
                        title={video.title}
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      />
                    </Box>
                    <Box sx={{ p: 2 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                        {video.title}
                      </Typography>
                      <Chip label={video.channelTitle} size="small" color="primary" variant="outlined" />
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info">Loading travel videos...</Alert>
          )}
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mt: 4 }}>
          <Button variant="outlined" onClick={prevStep}>
            Back
          </Button>
          <Button variant="contained" onClick={nextStep}>
            Continue
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default TravelPreparation;