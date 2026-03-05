import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, Button, CircularProgress, Alert, Card, CardContent, Chip, IconButton, Divider } from '@mui/material';
import { LocalHospital, Phone, Language, MyLocation, Emergency, Close } from '@mui/icons-material';
import axios from 'axios';

const MedicalSupport = () => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [medicalCenters, setMedicalCenters] = useState([]);
  const [emergencyContacts, setEmergencyContacts] = useState(null);
  const [userLocation, setUserLocation] = useState(null);

  const getUserLocation = () => {
    setLoading(true);
    setError('');
    
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        setUserLocation({ latitude, longitude });
        await fetchMedicalCenters(latitude, longitude);
      },
      (error) => {
        setError('Unable to retrieve your location. Please enable location services.');
        setLoading(false);
      }
    );
  };

  const fetchMedicalCenters = async (lat, lng) => {
    try {
      console.log('Fetching medical centers for:', lat, lng);
      const response = await axios.post('http://localhost:8000/medical-support', {
        latitude: lat,
        longitude: lng,
        radius: 5000
      });
      
      console.log('Medical centers response:', response.data);
      
      if (response.data.medical_centers && response.data.medical_centers.length > 0) {
        setMedicalCenters(response.data.medical_centers);
      } else {
        // Open Google search in new tab
        const searchQuery = `hospitals near ${lat},${lng}`;
        const googleMapsUrl = `https://www.google.com/maps/search/${encodeURIComponent(searchQuery)}/@${lat},${lng},14z`;
        window.open(googleMapsUrl, '_blank');
        setError('No medical centers found via API. Opening Google Maps search in new tab...');
      }
    } catch (err) {
      console.error('Error fetching medical centers:', err);
      // Open Google search as fallback
      const searchQuery = `hospitals near ${lat},${lng}`;
      const googleMapsUrl = `https://www.google.com/maps/search/${encodeURIComponent(searchQuery)}/@${lat},${lng},14z`;
      window.open(googleMapsUrl, '_blank');
      setError('API unavailable. Opening Google Maps search in new tab...');
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = () => {
    setOpen(true);
    if (!userLocation) {
      getUserLocation();
    }
  };

  return (
    <>
      <Button
        variant="contained"
        startIcon={<LocalHospital />}
        onClick={handleOpen}
        sx={{
          position: 'fixed',
          bottom: 0,
          left: 240,
          zIndex: 1001,
          bgcolor: '#f44336',
          '&:hover': { bgcolor: '#d32f2f' },
          animation: 'blink 2s infinite',
          '@keyframes blink': {
            '0%, 100%': { opacity: 1 },
            '50%': { opacity: 0.3 }
          }
        }}
      >
        Emergency
      </Button>

      {open && (
        <Paper
          elevation={8}
          sx={{
            position: 'fixed',
            bottom: 70,
            left: 240,
            width: 400,
            maxHeight: 600,
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1001
          }}
        >
          <Box sx={{ p: 2, bgcolor: '#f44336', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <LocalHospital />
              <Typography variant="h6">Medical Support</Typography>
            </Box>
            <IconButton size="small" onClick={() => setOpen(false)} sx={{ color: 'white' }}>
              <Close />
            </IconButton>
          </Box>

          <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            )}

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            {!loading && !error && medicalCenters.length === 0 && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Click "Find Nearby Medical Centers" to locate hospitals and clinics near you.
              </Alert>
            )}

            {medicalCenters.length > 0 && (
              <>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                  📍 Nearby Medical Centers ({medicalCenters.length})
                </Typography>
                
                {medicalCenters.map((center, index) => (
                  <Card key={index} sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ mb: 1 }}>
                        {center.name}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        📍 {center.address}
                      </Typography>
                      
                      {center.rating && (
                        <Chip 
                          label={`⭐ ${center.rating}`} 
                          size="small" 
                          color="warning" 
                          sx={{ mb: 1 }}
                        />
                      )}
                      
                      {center.open_now !== undefined && (
                        <Chip 
                          label={center.open_now ? '🟢 Open Now' : '🔴 Closed'} 
                          size="small" 
                          color={center.open_now ? 'success' : 'error'}
                          sx={{ mb: 1, ml: 1 }}
                        />
                      )}
                      
                      <Divider sx={{ my: 1 }} />
                      
                      {center.phone && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Phone fontSize="small" color="primary" />
                          <Typography variant="body2">
                            <a href={`tel:${center.phone}`} style={{ textDecoration: 'none', color: '#1976d2' }}>
                              {center.phone}
                            </a>
                          </Typography>
                        </Box>
                      )}
                      
                      {center.website && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Language fontSize="small" color="primary" />
                          <Typography variant="body2">
                            <a href={center.website} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: '#1976d2' }}>
                              Visit Website
                            </a>
                          </Typography>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </>
            )}
          </Box>

          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<MyLocation />}
              onClick={getUserLocation}
              disabled={loading}
              sx={{ bgcolor: '#f44336', '&:hover': { bgcolor: '#d32f2f' } }}
            >
              {loading ? 'Locating...' : 'Find Nearby Medical Centers'}
            </Button>
          </Box>
        </Paper>
      )}
    </>
  );
};

export default MedicalSupport;
