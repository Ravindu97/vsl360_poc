import React, { useState, useEffect } from 'react';
import { 
  Card, CardContent, Typography, Button, Box, 
  CircularProgress, Alert, Divider, Grid 
} from '@mui/material';
import { Info, CheckCircle, Cancel, LocationOn, Language, LocalHospital } from '@mui/icons-material';
import axios from 'axios';

const CountryInfo = ({ tripData, updateTripData, nextStep, prevStep }) => {
  const [countryInfo, setCountryInfo] = useState('');
  const [media, setMedia] = useState([]);
  const [attractionImages, setAttractionImages] = useState({});
  const [loading, setLoading] = useState(false);
  const [mediaLoading, setMediaLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (tripData.arrival_country && !countryInfo) {
      fetchCountryInfo();
    }
  }, [tripData.arrival_country]);

  const fetchCountryInfo = async () => {
    setLoading(true);
    setError('');
    try {
      const [infoResponse, mediaResponse] = await Promise.all([
        axios.post('http://localhost:8000/country-info', {
          departure_country: tripData.departure_country,
          arrival_country: tripData.arrival_country,
          start_date: tripData.start_date,
          end_date: tripData.end_date
        }),
        axios.post('http://localhost:8000/free-media', {
          country: tripData.arrival_country
        })
      ]);
      
      setCountryInfo(infoResponse.data.country_info);
      setMedia(mediaResponse.data || []);
    } catch (err) {
      setError('Failed to fetch country information');
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = () => {
    updateTripData({ user_likes_country: true });
    nextStep();
  };

  const handleReject = () => {
    updateTripData({ user_likes_country: false });
    prevStep();
  };

  const parseCountryInfo = (info) => {
    const cleanInfo = info.replace(/[*]/g, '').replace(/\n\s*\n/g, '\n');
    
    // Parse Overview
    const overviewMatch = cleanInfo.match(/OVERVIEW_START([\s\S]*?)OVERVIEW_END/);
    const overview = overviewMatch ? overviewMatch[1].trim() : '';
    
    // Parse Attractions
    const attractionsMatch = cleanInfo.match(/ATTRACTIONS_START([\s\S]*?)ATTRACTIONS_END/);
    const attractionsText = attractionsMatch ? attractionsMatch[1].trim() : '';
    const attractions = [];
    if (attractionsText) {
      const attractionBlocks = attractionsText.split(/(?=Attraction:)/).filter(block => block.trim());
      attractionBlocks.forEach(block => {
        const nameMatch = block.match(/Attraction:\s*(.+)/);
        const descMatch = block.match(/Description:\s*(.+)/);
        if (nameMatch && descMatch) {
          attractions.push({
            name: nameMatch[1].trim(),
            description: descMatch[1].trim()
          });
        }
      });
    }
    
    // Parse Visitor Info
    const visitorMatch = cleanInfo.match(/VISITOR_INFO_START([\s\S]*?)VISITOR_INFO_END/);
    const visitorText = visitorMatch ? visitorMatch[1].trim() : '';
    const visitorInfo = {};
    if (visitorText) {
      const visaMatch = visitorText.match(/Visa:\s*(.+)/);
      const langMatch = visitorText.match(/Language:\s*(.+)/);
      const currMatch = visitorText.match(/Currency:\s*(.+)/);
      const healthMatch = visitorText.match(/Healthcare:\s*(.+)/);
      const timeMatch = visitorText.match(/Best Time:\s*(.+)/);
      
      if (visaMatch) visitorInfo.visa = visaMatch[1].trim();
      if (langMatch) visitorInfo.language = langMatch[1].trim();
      if (currMatch) visitorInfo.currency = currMatch[1].trim();
      if (healthMatch) visitorInfo.healthcare = healthMatch[1].trim();
      if (timeMatch) visitorInfo.bestTime = timeMatch[1].trim();
    }
    
    // If no structured data found, show fallback
    if (!overview && attractions.length === 0 && Object.keys(visitorInfo).length === 0) {
      return (
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom color="primary">
              🌍 About {tripData.arrival_country}
            </Typography>
            <Typography variant="body1" sx={{ lineHeight: 1.8, whiteSpace: 'pre-line' }}>
              {cleanInfo}
            </Typography>
          </CardContent>
        </Card>
      );
    }
    
    return (
      <>
        {overview && (
          <Card variant="outlined" sx={{ mb: 3, border: '2px solid', borderColor: '#87ceeb', transition: 'all 0.3s ease', '&:hover': { borderColor: '#1976d2', boxShadow: '0 4px 12px rgba(135, 206, 235, 0.3)' } }}>
            <CardContent>
              <Typography variant="h5" gutterBottom color="primary" sx={{ display: 'flex', alignItems: 'center' }}>
                🌍 Country Overview
              </Typography>
              <Typography variant="body1" component="div" sx={{ lineHeight: 2, fontSize: '1.05rem' }}>
                {overview.split('\n').map((line, idx) => {
                  if (line.trim().startsWith('•')) {
                    const match = line.match(/•\s*([^:]+):\s*(.+)/);
                    if (match) {
                      return (
                        <div key={idx}>
                          • <strong>{match[1]}:</strong> {match[2]}
                        </div>
                      );
                    }
                  }
                  return <div key={idx}>{line}</div>;
                })}
              </Typography>
            </CardContent>
          </Card>
        )}
        
        {attractions.length > 0 && (
          <Card variant="outlined" sx={{ mb: 3, border: '2px solid', borderColor: '#87ceeb', transition: 'all 0.3s ease', '&:hover': { borderColor: '#1976d2', boxShadow: '0 4px 12px rgba(135, 206, 235, 0.3)' } }}>
            <CardContent>
              <Typography variant="h5" gutterBottom color="primary" sx={{ display: 'flex', alignItems: 'center' }}>
                🏛️ Key Attractions
              </Typography>
              <Grid container spacing={2}>
                {attractions.map((attraction, idx) => (
                  <Grid item xs={12} md={6} key={idx}>
                    <Card variant="outlined" sx={{ height: '100%', bgcolor: 'grey.50' }}>
                      {attractionImages[attraction.name] && (
                        <img 
                          src={attractionImages[attraction.name]} 
                          alt={attraction.name}
                          style={{ width: '100%', height: '200px', objectFit: 'cover' }}
                        />
                      )}
                      <CardContent>
                        <Typography variant="h6" color="primary" gutterBottom>
                          {attraction.name}
                        </Typography>
                        <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                          {attraction.description}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        )}
        
        {Object.keys(visitorInfo).length > 0 && (
          <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom color="primary" sx={{ display: 'flex', alignItems: 'center' }}>
                ℹ️ Visitor Information
              </Typography>
              <Grid container spacing={3}>
                {visitorInfo.visa && (
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                      <LocationOn sx={{ mr: 1, color: 'primary.main', mt: 0.5 }} />
                      <Box>
                        <Typography variant="subtitle1" fontWeight="bold">Visa Policy</Typography>
                        <Typography variant="body2">{visitorInfo.visa}</Typography>
                      </Box>
                    </Box>
                  </Grid>
                )}
                {visitorInfo.language && (
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                      <Language sx={{ mr: 1, color: 'primary.main', mt: 0.5 }} />
                      <Box>
                        <Typography variant="subtitle1" fontWeight="bold">Language</Typography>
                        <Typography variant="body2">{visitorInfo.language}</Typography>
                      </Box>
                    </Box>
                  </Grid>
                )}
                {visitorInfo.currency && (
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="subtitle1" fontWeight="bold" sx={{ mr: 1 }}>💰</Typography>
                      <Box>
                        <Typography variant="subtitle1" fontWeight="bold">Currency</Typography>
                        <Typography variant="body2">{visitorInfo.currency}</Typography>
                      </Box>
                    </Box>
                  </Grid>
                )}
                {visitorInfo.healthcare && (
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                      <LocalHospital sx={{ mr: 1, color: 'primary.main', mt: 0.5 }} />
                      <Box>
                        <Typography variant="subtitle1" fontWeight="bold">Healthcare</Typography>
                        <Typography variant="body2">{visitorInfo.healthcare}</Typography>
                      </Box>
                    </Box>
                  </Grid>
                )}
                {visitorInfo.bestTime && (
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                      <Typography variant="subtitle1" fontWeight="bold" sx={{ mr: 1 }}>🌤️</Typography>
                      <Box>
                        <Typography variant="subtitle1" fontWeight="bold">Best Time to Visit</Typography>
                        <Typography variant="body2">{visitorInfo.bestTime}</Typography>
                      </Box>
                    </Box>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        )}
      </>
    );
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Info sx={{ mr: 2, fontSize: 30 }} />
          <Typography variant="h4" component="h2">
            About {tripData.arrival_country}
          </Typography>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', my: 4, p: 4, border: '2px solid', borderColor: '#87ceeb', borderRadius: 2, transition: 'all 0.3s ease', '&:hover': { borderColor: '#1976d2', boxShadow: '0 4px 12px rgba(135, 206, 235, 0.3)' } }}>
            <CircularProgress size={60} />
            <Typography variant="h6" sx={{ mt: 3, color: '#1976d2', fontWeight: 'bold' }}>
              🌍 Exploring Your Destination...
            </Typography>
          </Box>
        )}

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {countryInfo && (
          <Box sx={{ mb: 3 }}>
            {parseCountryInfo(countryInfo)}
          </Box>
        )}
        
        {media.length > 0 && (
          <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom color="primary">
                📷 Explore {tripData.arrival_country}
              </Typography>
              <Grid container spacing={3}>
                {media.slice(0, 6).map((image, index) => (
                  <Grid item xs={12} sm={6} md={4} key={index}>
                    <Card sx={{ height: 280, position: 'relative', overflow: 'hidden', cursor: 'pointer', transition: 'transform 0.2s', '&:hover': { transform: 'scale(1.02)' } }}>
                      <img 
                        src={image.url} 
                        alt={image.title || `${tripData.arrival_country} location`}
                        style={{ 
                          width: '100%', 
                          height: '100%', 
                          objectFit: 'cover'
                        }}
                        onClick={() => window.open(image.url, '_blank')}
                      />
                      {image.title && (
                        <Box sx={{ 
                          position: 'absolute', 
                          bottom: 0, 
                          left: 0, 
                          right: 0, 
                          bgcolor: 'rgba(0,0,0,0.8)', 
                          color: 'white', 
                          p: 1.5 
                        }}>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {image.title}
                          </Typography>
                        </Box>
                      )}
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        )}
        
        {!countryInfo && !loading && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Please select a destination country to see information.
          </Alert>
        )}

        <Divider sx={{ my: 3 }} />

        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
          <Button 
            variant="outlined" 
            startIcon={<Cancel />}
            onClick={handleReject}
            color="error"
          >
            Choose Different Destination
          </Button>
          
          <Button 
            variant="contained" 
            startIcon={<CheckCircle />}
            onClick={handleAccept}
            disabled={loading || !countryInfo}
          >
            I Want to Visit This Country
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default CountryInfo;