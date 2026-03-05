import React, { useState, useEffect } from 'react';
import { 
  Card, CardContent, Typography, Button, Box, 
  CircularProgress, Alert, FormGroup, FormControlLabel, 
  Checkbox, Grid, Select, MenuItem, FormControl, 
  InputLabel, TextField, Divider, List, ListItem, 
  ListItemText, Chip, Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import { LocationCity, Route, Schedule, Explore } from '@mui/icons-material';
import axios from 'axios';
import RouteMap from './RouteMap';

const CitySelection = ({ tripData, updateTripData, nextStep, prevStep }) => {
  const [cities, setCities] = useState([]);
  const [cityDetails, setCityDetails] = useState([]);
  const [cityImages, setCityImages] = useState({});
  const [loading, setLoading] = useState(false);
  const [imagesLoading, setImagesLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1); // 1: Select Cities, 2: Select Start City, 3: Route Optimization, 4: Days per City, 5: Schedule
  const [startCity, setStartCity] = useState('');
  const [optimizedRoute, setOptimizedRoute] = useState([]);
  const [routeDistances, setRouteDistances] = useState([]);
  const [cityCoordinates, setCityCoordinates] = useState([]);
  const [daysPerCity, setDaysPerCity] = useState({});
  const [schedule, setSchedule] = useState({});
  const [selectedCityDetails, setSelectedCityDetails] = useState(null);
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [placeImages, setPlaceImages] = useState({});
  const [additionalCityDetails, setAdditionalCityDetails] = useState({});
  const [cityVideos, setCityVideos] = useState({});
  const [videosModalOpen, setVideosModalOpen] = useState(false);
  const [selectedCityForVideos, setSelectedCityForVideos] = useState(null);
  const [slideshowOpen, setSlideshowOpen] = useState(false);
  const [slideshowImages, setSlideshowImages] = useState([]);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);

  useEffect(() => {
    if (tripData.interests && tripData.interests.length > 0 && step === 1) {
      fetchCities();
    }
  }, [tripData.interests, step]);

  const fetchCities = async () => {
    setLoading(true);
    setImagesLoading(true);
    setError('');
    try {
      const response = await axios.post('http://localhost:8000/city-suggestions', {
        country: tripData.arrival_country,
        interests: tripData.interests
      });
      
      // Parse cities from response
      const cityData = response.data.suggested_cities || '';
      const parsedCities = parseCities(cityData);
      setCities(parsedCities);
    } catch (err) {
      setError('Failed to fetch city recommendations');
      setImagesLoading(false);
    } finally {
      setLoading(false);
    }
  };

  const parseCities = (cityData) => {
    if (typeof cityData === 'string') {
      const cityBlocks = cityData.split('CITY_START').filter(block => block.trim());
      const cities = [];
      const details = [];
      
      cityBlocks.forEach(block => {
        const lines = block.trim().split('\n');
        const cityInfo = {};
        
        let inCitySection = true;
        lines.forEach(line => {
          line = line.trim();
          if (line === 'CITY_END') {
            inCitySection = false;
          } else if (inCitySection && line.includes(':')) {
            const [key, ...valueParts] = line.split(':');
            const value = valueParts.join(':').trim();
            cityInfo[key.toLowerCase()] = value;
          }
        });
        
        if (cityInfo.city) {
          cities.push(cityInfo.city);
          details.push(cityInfo);
        }
      });
      
      // Sort by compatibility: Perfect Match > Very High > High
      const compatibilityOrder = { 'perfect match': 1, 'very high': 2, 'high': 3 };
      details.sort((a, b) => {
        const orderA = compatibilityOrder[a.compatibility?.toLowerCase()] || 999;
        const orderB = compatibilityOrder[b.compatibility?.toLowerCase()] || 999;
        return orderA - orderB;
      });
      
      const sortedCities = details.map(d => d.city);
      
      setCityDetails(details);
      // Fetch images after setting city details
      setTimeout(() => fetchCityImages(details), 100);
      return sortedCities;
    }
    return Array.isArray(cityData) ? cityData : [];
  };

  const handleCityChange = (cityName, checked) => {
    const currentCities = tripData.selected_cities || [];
    let newCities;
    
    if (checked) {
      newCities = [...currentCities, cityName];
    } else {
      newCities = currentCities.filter(c => c !== cityName);
    }
    
    updateTripData({ selected_cities: newCities });
  };

  const getCompatibilityColor = (compatibility) => {
    switch (compatibility?.toLowerCase()) {
      case 'perfect match': return 'success';
      case 'very high': return 'primary';
      case 'high': return 'secondary';
      default: return 'default';
    }
  };

  const fetchCityImages = async (details = cityDetails) => {
    const images = {};
    for (const cityInfo of details) {
      try {
        const response = await axios.post('http://localhost:8000/free-media', {
          country: cityInfo.city
        });
        if (response.data && response.data.length > 0) {
          images[cityInfo.city] = response.data[0].url;
        }
      } catch (err) {
        console.log(`Failed to fetch image for ${cityInfo.city}`);
      }
    }
    setCityImages(images);
    setImagesLoading(false);
  };

  const fetchPlaceImages = async (places) => {
    const images = {};
    for (const place of places) {
      try {
        const response = await axios.post('http://localhost:8000/free-media', {
          country: place.trim()
        });
        if (response.data && response.data.length > 0) {
          images[place.trim()] = response.data.slice(0, 3).map(img => img.url);
        }
      } catch (err) {
        console.log(`Failed to fetch image for ${place}`);
      }
    }
    return images;
  };

  const fetchAdditionalCityDetails = async (cityName) => {
    try {
      const response = await axios.post('http://localhost:8000/city-additional-details', {
        city: cityName,
        country: tripData.arrival_country
      });
      return response.data;
    } catch (err) {
      console.log(`Failed to fetch additional details for ${cityName}`);
      return {};
    }
  };

  const fetchCityVideos = async (cityName) => {
    try {
      const response = await axios.get(`http://localhost:8000/youtube-videos/${encodeURIComponent(cityName + ' travel guide')}`, {
        params: { max_results: 3 }
      });
      return response.data.videos || [];
    } catch (err) {
      console.log(`Failed to fetch videos for ${cityName}`);
      return [];
    }
  };

  const handleCitySelectionNext = () => {
    if (!tripData.selected_cities || tripData.selected_cities.length === 0) {
      setError('Please select at least one city');
      return;
    }
    setError('');
    setStep(2);
  };

  const handleStartCityNext = () => {
    if (!startCity) {
      setError('Please select a starting city');
      return;
    }
    setError('');
    optimizeRoute();
  };

  const optimizeRoute = async () => {
    setLoading(true);
    setError('');
    try {
      const totalDays = Math.ceil((new Date(tripData.end_date) - new Date(tripData.start_date)) / (1000 * 60 * 60 * 24));
      const response = await axios.post('http://localhost:8000/optimize-route', {
        country: tripData.arrival_country,
        selected_cities: tripData.selected_cities,
        start_city: startCity,
        total_days: totalDays
      });
      
      setOptimizedRoute(response.data.optimized_cities);
      setRouteDistances(response.data.route_distances || []);
      setCityCoordinates(response.data.city_coordinates || []);
      setSchedule(response.data.city_schedule);
      updateTripData({ 
        optimized_cities: response.data.optimized_cities,
        city_schedule: response.data.city_schedule
      });
      
      // Initialize days per city from schedule
      const initialDays = {};
      response.data.optimized_cities.forEach(city => {
        initialDays[city] = response.data.city_schedule[city]?.days || 1;
      });
      setDaysPerCity(initialDays);
      
      setStep(3);
    } catch (err) {
      setError('Failed to optimize route');
    } finally {
      setLoading(false);
    }
  };

  const handleDaysChange = (city, days) => {
    setDaysPerCity(prev => ({ ...prev, [city]: parseInt(days) || 1 }));
  };

  const handleDaysNext = () => {
    const totalDays = Object.values(daysPerCity).reduce((sum, days) => sum + days, 0);
    const tripDays = Math.ceil((new Date(tripData.end_date) - new Date(tripData.start_date)) / (1000 * 60 * 60 * 24));
    
    if (totalDays !== tripDays) {
      setError(`Total days (${totalDays}) must equal trip duration (${tripDays} days)`);
      return;
    }
    
    // Recalculate schedule with custom days
    const newSchedule = {};
    let currentDate = new Date(tripData.start_date);
    
    optimizedRoute.forEach(city => {
      const days = daysPerCity[city];
      const endDate = new Date(currentDate);
      endDate.setDate(endDate.getDate() + days - 1);
      
      newSchedule[city] = {
        days: days,
        start_date: currentDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0]
      };
      
      currentDate.setDate(endDate.getDate() + 1);
    });
    
    setSchedule(newSchedule);
    updateTripData({ city_schedule: newSchedule });
    setError('');
    setStep(5);
  };

  const handleFinalNext = () => {
    nextStep();
  };

  const renderStepContent = () => {
    switch (step) {
      case 1:
        return (
          <>
            <Typography variant="body1" sx={{ mb: 3 }}>
              Based on Your Interests, Here are Recommended Cities to Visit:
            </Typography>

            {cityDetails.length > 0 && (
              <Grid container spacing={3}>
                {cityDetails.map((cityInfo, index) => (
                  <Grid item xs={12} md={6} key={index}>
                    <Card variant="outlined" sx={{ 
                      height: '100%', 
                      position: 'relative', 
                      overflow: 'hidden',
                      border: '2px solid',
                      borderColor: '#87ceeb',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        borderColor: '#1976d2',
                        boxShadow: '0 8px 16px rgba(135, 206, 235, 0.3)',
                        transform: 'translateY(-4px)'
                      }
                    }}>
                      {cityImages[cityInfo.city] && (
                        <Box sx={{ height: 200, position: 'relative' }}>
                          <img 
                            src={cityImages[cityInfo.city]} 
                            alt={cityInfo.city}
                            style={{ 
                              width: '100%', 
                              height: '100%', 
                              objectFit: 'cover'
                            }}
                          />
                          <Box sx={{ 
                            position: 'absolute', 
                            top: 8, 
                            right: 8,
                            bgcolor: 'rgba(255,255,255,0.9)',
                            borderRadius: 1
                          }}>
                            <Checkbox
                              checked={tripData.selected_cities?.includes(cityInfo.city) || false}
                              onChange={(e) => handleCityChange(cityInfo.city, e.target.checked)}
                              color="primary"
                            />
                          </Box>
                        </Box>
                      )}
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                          <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
                            {cityInfo.city}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Chip 
                              label={cityInfo.compatibility || 'High'} 
                              color={getCompatibilityColor(cityInfo.compatibility)}
                              size="small"
                            />
                            {!cityImages[cityInfo.city] && (
                              <Checkbox
                                checked={tripData.selected_cities?.includes(cityInfo.city) || false}
                                onChange={(e) => handleCityChange(cityInfo.city, e.target.checked)}
                                color="primary"
                              />
                            )}
                          </Box>
                        </Box>
                        
                        {cityInfo['best for'] && (
                          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold', color: 'text.secondary', fontStyle: 'italic' }}>
                            ✨ Perfect for {cityInfo['best for']}
                          </Typography>
                        )}
                        
                        {cityInfo['why visit'] && (
                          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary', fontStyle: 'italic', fontSize: '0.9rem' }}>
                            "{cityInfo['why visit'].split('.')[0]}."
                          </Typography>
                        )}
                        
                        {cityInfo['places to visit'] && (
                          <Box sx={{ mt: 2, p: 2, bgcolor: 'primary.50', borderRadius: 2, border: '1px solid', borderColor: 'primary.200' }}>
                            <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 'bold', color: 'primary.main', textAlign: 'center' }}>
                              🏛️ Places to Visit
                            </Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
                              {cityInfo['places to visit'].split(';').map((place, idx) => (
                                <Chip 
                                  key={idx}
                                  label={place.trim()} 
                                  size="small"
                                  sx={{ 
                                    fontSize: '0.75rem',
                                    fontWeight: 'medium',
                                    bgcolor: 'white',
                                    border: '1px solid #87ceeb',
                                    color: '#1976d2',
                                    boxShadow: 1,
                                    transition: 'all 0.3s ease',
                                    '&:hover': {
                                      boxShadow: 3,
                                      bgcolor: '#f0f8ff',
                                      transform: 'scale(1.05)'
                                    }
                                  }}
                                />
                              ))}
                            </Box>
                          </Box>
                        )}
                        
                        <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'center' }}>
                          <Button 
                            variant="contained" 
                            size="small"
                            onClick={async () => {
                              setSelectedCityDetails(cityInfo);
                              setDetailsModalOpen(true);
                              
                              // Fetch place images
                              if (cityInfo['places to visit']) {
                                const places = cityInfo['places to visit'].split(';').slice(0, 4);
                                const images = await fetchPlaceImages(places);
                                setPlaceImages(images);
                              }
                              
                              // Fetch additional city details
                              const additionalDetails = await fetchAdditionalCityDetails(cityInfo.city);
                              setAdditionalCityDetails(additionalDetails);
                            }}
                          >
                            View Details
                          </Button>
                          <Button 
                            variant="outlined" 
                            size="small"
                            onClick={async () => {
                              setSelectedCityForVideos(cityInfo.city);
                              setVideosModalOpen(true);
                              const videos = await fetchCityVideos(cityInfo.city);
                              setCityVideos(videos);
                            }}
                          >
                            Watch More
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}

            {tripData.selected_cities && tripData.selected_cities.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="primary">
                  Selected Cities: {tripData.selected_cities.join(', ')}
                </Typography>
              </Box>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mt: 4 }}>
              <Button variant="outlined" onClick={prevStep}>
                Back
              </Button>
              <Button variant="contained" onClick={handleCitySelectionNext} disabled={loading}>
                Next: Select Starting City
              </Button>
            </Box>
          </>
        );

      case 2:
        return (
          <>
            <Typography variant="body1" sx={{ mb: 3 }}>
              Select Your Starting City for Route Optimization:
            </Typography>

            <FormControl fullWidth sx={{ mb: 3, '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#87ceeb', borderWidth: '2px' }, '&:hover fieldset': { borderColor: '#1976d2' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}>
              <InputLabel>Starting City</InputLabel>
              <Select
                value={startCity}
                onChange={(e) => setStartCity(e.target.value)}
                label="Starting City"
              >
                {tripData.selected_cities?.map((city) => (
                  <MenuItem key={city} value={city}>{city}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mt: 4 }}>
              <Button variant="outlined" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button variant="contained" onClick={handleStartCityNext} disabled={loading}>
                Optimize Route
              </Button>
            </Box>
          </>
        );

      case 3:
        return (
          <>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
              <Route sx={{ mr: 1 }} /> Optimized Route
            </Typography>
            
            <Box sx={{ 
              mb: 3, 
              p: 2, 
              bgcolor: 'grey.50', 
              borderRadius: 1,
              border: '2px solid',
              borderColor: '#87ceeb',
              transition: 'all 0.3s ease',
              '&:hover': {
                borderColor: '#1976d2',
                boxShadow: '0 4px 12px rgba(135, 206, 235, 0.3)'
              }
            }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
                {optimizedRoute.map((city, index) => {
                  const distance = routeDistances[index]; // Use index to get corresponding distance
                  return (
                    <React.Fragment key={city}>
                      <Chip label={city} color="primary" variant="outlined" />
                      {index < optimizedRoute.length - 1 && (
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mx: 1 }}>
                          <Typography variant="h6">→</Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.7rem', color: 'text.secondary' }}>
                            {distance ? `${distance.distance_km} km` : '50 km'}
                          </Typography>
                        </Box>
                      )}
                    </React.Fragment>
                  );
                })}
              </Typography>
            </Box>

            {/* Route Map */}
            {cityCoordinates.length > 0 && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Route Map
                </Typography>
                <RouteMap cityCoordinates={cityCoordinates} routeDistances={routeDistances} />
              </>
            )}

            {optimizedRoute.length > 0 && (
              <>
                <Divider sx={{ my: 2 }} />
                <Box sx={{ 
                  p: 2, 
                  bgcolor: 'info.50', 
                  borderRadius: 2, 
                  border: '2px solid', 
                  borderColor: '#87ceeb',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    borderColor: '#1976d2',
                    boxShadow: '0 4px 12px rgba(135, 206, 235, 0.3)'
                  }
                }}>
                  <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 'bold', color: 'info.main', textAlign: 'center' }}>
                    🚕 Transport & Taxi Services
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1.5, bgcolor: 'white', borderRadius: 1, border: '2px solid #1976d2', cursor: 'pointer', transition: 'all 0.2s', '&:hover': { boxShadow: 2, borderColor: '#1565c0' } }} onClick={() => window.open('https://www.pickme.lk', '_blank')}>
                        <Typography sx={{ fontSize: '1.5rem' }}>🚗</Typography>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>PickMe</Typography>
                          <Typography variant="body2" sx={{ fontSize: '0.85rem', color: 'text.secondary' }}>Ride-hailing service</Typography>
                        </Box>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1.5, bgcolor: 'white', borderRadius: 1, border: '2px solid #1976d2', cursor: 'pointer', transition: 'all 0.2s', '&:hover': { boxShadow: 2, borderColor: '#1565c0' } }} onClick={() => window.open('https://www.uber.com/lk/en/', '_blank')}>
                        <Typography sx={{ fontSize: '1.5rem' }}>🚖</Typography>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Uber</Typography>
                          <Typography variant="body2" sx={{ fontSize: '0.85rem', color: 'text.secondary' }}>Global ride service</Typography>
                        </Box>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1.5, bgcolor: 'white', borderRadius: 1, border: '2px solid #1976d2', cursor: 'pointer', transition: 'all 0.2s', '&:hover': { boxShadow: 2, borderColor: '#1565c0' } }} onClick={() => window.open('https://www.kangaroocabs.com', '_blank')}>
                        <Typography sx={{ fontSize: '1.5rem' }}>🦘</Typography>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Kangaroo Cabs</Typography>
                          <Typography variant="body2" sx={{ fontSize: '0.85rem', color: 'text.secondary' }}>Airport & city transfers</Typography>
                        </Box>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1.5, bgcolor: 'white', borderRadius: 1, border: '2px solid #1976d2', cursor: 'pointer', transition: 'all 0.2s', '&:hover': { boxShadow: 2, borderColor: '#1565c0' } }} onClick={() => window.open('https://www.booking.com/cars', '_blank')}>
                        <Typography sx={{ fontSize: '1.5rem' }}>🚙</Typography>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Booking.com Cars</Typography>
                          <Typography variant="body2" sx={{ fontSize: '0.85rem', color: 'text.secondary' }}>Car rentals</Typography>
                        </Box>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              </>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mt: 4 }}>
              <Button variant="outlined" onClick={() => setStep(2)}>
                Back
              </Button>
              <Button variant="contained" onClick={() => setStep(4)}>
                Customize Days per City
              </Button>
            </Box>
          </>
        );

      case 4:
        const totalDays = Math.ceil((new Date(tripData.end_date) - new Date(tripData.start_date)) / (1000 * 60 * 60 * 24));
        const currentTotal = Object.values(daysPerCity).reduce((sum, days) => sum + days, 0);
        
        return (
          <>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Customize Days per City (Total: {totalDays} days)
            </Typography>
            
            <Typography variant="body2" sx={{ mb: 2, color: currentTotal === totalDays ? 'success.main' : 'error.main' }}>
              Current Total: {currentTotal} days
            </Typography>

            <Grid container spacing={2}>
              {optimizedRoute.map((city) => (
                <Grid item xs={12} sm={6} key={city}>
                  <TextField
                    fullWidth
                    label={`Days in ${city}`}
                    type="number"
                    value={daysPerCity[city] || 1}
                    onChange={(e) => handleDaysChange(city, e.target.value)}
                    inputProps={{ min: 1, max: totalDays }}
                  />
                </Grid>
              ))}
            </Grid>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mt: 4 }}>
              <Button variant="outlined" onClick={() => setStep(3)}>
                Back
              </Button>
              <Button variant="contained" onClick={handleDaysNext}>
                Generate Schedule
              </Button>
            </Box>
          </>
        );

      case 5:
        return (
          <>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
              <Schedule sx={{ mr: 1 }} /> Travel Schedule
            </Typography>
            
            <Grid container spacing={2}>
              {optimizedRoute.map((city, index) => (
                <Grid item xs={12} md={6} key={city}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        {index + 1}. {city}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Duration:</strong> {schedule[city]?.days} days
                      </Typography>
                      <Typography variant="body2">
                        <strong>Dates:</strong> {schedule[city]?.start_date} to {schedule[city]?.end_date}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mt: 4 }}>
              <Button variant="outlined" onClick={() => setStep(4)}>
                Back
              </Button>
              <Button variant="contained" onClick={handleFinalNext}>
                Continue to Hotels
              </Button>
            </Box>
          </>
        );

      default:
        return null;
    }
  };

  const getStepTitle = () => {
    switch (step) {
      case 1: return 'City Selection';
      case 2: return 'Select Starting City';
      case 3: return 'Route Optimization';
      case 4: return 'Days per City';
      case 5: return 'Travel Schedule';
      default: return 'City Selection';
    }
  };

  return (
    <>
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <LocationCity sx={{ mr: 2, fontSize: 30 }} />
            <Typography variant="h4" component="h2">
              {getStepTitle()}
            </Typography>
            <Chip label={`Step ${step}/5`} sx={{ ml: 2 }} />
          </Box>

          {(loading || imagesLoading) && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', my: 4, p: 3, border: '2px solid', borderColor: '#87ceeb', borderRadius: 2, transition: 'all 0.3s ease', '&:hover': { borderColor: '#1976d2', boxShadow: '0 4px 12px rgba(135, 206, 235, 0.3)' } }}>
              <img 
                src={step === 2 && loading ? "/images/Route.png" : "/images/City.png"}
                alt={step === 2 && loading ? "Optimizing Route" : "Discovering Cities"}
                style={{ width: '130px', height: '130px', marginBottom: '16px', animation: 'blink 1.5s ease-in-out infinite' }}
              />
              <Typography variant="h5" color="primary" sx={{ fontWeight: 'bold' }}>
                {step === 2 && loading ? "Optimizing Your Route" : "Discovering Cities Just for You"}
                <span className="dot1" style={{ animation: 'dot1 1.5s infinite' }}>.</span>
                <span className="dot2" style={{ animation: 'dot2 1.5s infinite' }}>.</span>
                <span className="dot3" style={{ animation: 'dot3 1.5s infinite' }}>.</span>
                <span className="dot4" style={{ animation: 'dot2 1.5s infinite' }}>.</span>
                <span className="dot5" style={{ animation: 'dot3 1.5s infinite' }}>.</span>
              </Typography>
              <style>
                {`
                  @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
                  @keyframes dot1 { 0%, 33%, 100% { opacity: 0; } 0%, 33% { opacity: 1; } }
                  @keyframes dot2 { 0%, 33%, 66%, 100% { opacity: 0; } 33%, 66% { opacity: 1; } }
                  @keyframes dot3 { 0%, 66%, 100% { opacity: 0; } 66%, 100% { opacity: 1; } }
                `}
              </style>
            </Box>
          )}

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          {!loading && !imagesLoading && renderStepContent()}
        </CardContent>
      </Card>
      
      <Dialog open={detailsModalOpen} onClose={() => setDetailsModalOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedCityDetails?.city} Details</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            {selectedCityDetails?.['why visit'] && (
              <Grid item xs={12}>
                <Card sx={{ p: 2, bgcolor: '#f8f9fa', border: '1px solid #e9ecef' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: 'primary.main' }}>📝 Description</Typography>
                  <Typography variant="body2">{selectedCityDetails['why visit']}</Typography>
                </Card>
              </Grid>
            )}
            {selectedCityDetails?.['days recommended'] && (
              <Grid item xs={12} sm={6}>
                <Card sx={{ p: 2, bgcolor: '#e8f5e8', border: '1px solid #c8e6c9' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: 'success.main' }}>⏰ Duration</Typography>
                  <Typography variant="body2">{selectedCityDetails['days recommended']} days</Typography>
                </Card>
              </Grid>
            )}
            {additionalCityDetails?.best_time_to_visit && (
              <Grid item xs={12} sm={6}>
                <Card sx={{ p: 2, bgcolor: '#fff3e0', border: '1px solid #ffcc02' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: 'warning.main' }}>🌤️ Best Time</Typography>
                  <Typography variant="body2">{additionalCityDetails.best_time_to_visit}</Typography>
                </Card>
              </Grid>
            )}
            {additionalCityDetails?.weather && (
              <Grid item xs={12} sm={6}>
                <Card sx={{ p: 2, bgcolor: '#e3f2fd', border: '1px solid #90caf9' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: 'info.main' }}>🌡️ Weather</Typography>
                  <Typography variant="body2">{additionalCityDetails.weather}</Typography>
                </Card>
              </Grid>
            )}
            {additionalCityDetails?.must_try_foods && (
              <Grid item xs={12} sm={6}>
                <Card sx={{ p: 2, bgcolor: '#fce4ec', border: '1px solid #f8bbd9' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: 'secondary.main' }}>🍽️ Must Try Foods</Typography>
                  <Typography variant="body2">{additionalCityDetails.must_try_foods}</Typography>
                </Card>
              </Grid>
            )}
            {additionalCityDetails?.insider_tips && (
              <Grid item xs={12}>
                <Card sx={{ p: 2, bgcolor: '#f3e5f5', border: '1px solid #ce93d8' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: 'secondary.dark' }}>💎 Insider Tips</Typography>
                  <Typography variant="body2">{additionalCityDetails.insider_tips}</Typography>
                </Card>
              </Grid>
            )}
          </Grid>
          {selectedCityDetails?.['places to visit'] && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>Gallery:</Typography>
              <Box sx={{ display: 'flex', overflowX: 'auto', gap: 1, pb: 1 }}>
                {selectedCityDetails['places to visit'].split(';').slice(0, 4).map((place, idx) => (
                  <Box key={idx} sx={{ minWidth: 120, textAlign: 'center' }}>
                    <Box sx={{ width: 120, height: 80, borderRadius: 1, mb: 1, overflow: 'hidden', position: 'relative' }}>
                      {placeImages[place.trim()] && placeImages[place.trim()][0] ? (
                        <img 
                          src={placeImages[place.trim()][0]} 
                          alt={place.trim()}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      ) : (
                        <Box sx={{ width: '100%', height: '100%', bgcolor: 'grey.200', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Typography variant="caption" sx={{ fontSize: '0.7rem', textAlign: 'center', p: 1 }}>
                            {place.trim()}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                    <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>
                      {place.trim()}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsModalOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      
      <Dialog open={videosModalOpen} onClose={() => setVideosModalOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{selectedCityForVideos} - Travel Videos</DialogTitle>
        <DialogContent>
          {cityVideos.length > 0 ? (
            <Grid container spacing={2}>
              {cityVideos.map((video, idx) => (
                <Grid item xs={12} sm={6} md={4} key={idx}>
                  <Card 
                    sx={{ cursor: 'pointer', '&:hover': { boxShadow: 3 } }}
                    onClick={() => window.open(`https://www.youtube.com/watch?v=${video.videoId}`, '_blank')}
                  >
                    <Box sx={{ position: 'relative', paddingTop: '56.25%' }}>
                      <img 
                        src={video.thumbnail}
                        alt={video.title}
                        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    </Box>
                    <CardContent>
                      <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.85rem' }}>
                        {video.title}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Typography>Loading videos...</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVideosModalOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      
      <Dialog open={slideshowOpen} onClose={() => setSlideshowOpen(false)} maxWidth="md" fullWidth>
        <DialogContent sx={{ p: 0, position: 'relative' }}>
          {slideshowImages.length > 0 && (
            <>
              <Box sx={{ position: 'relative', width: '100%', height: '500px' }}>
                <img 
                  src={slideshowImages[currentSlideIndex]}
                  alt={`Slide ${currentSlideIndex + 1}`}
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
                {slideshowImages.length > 1 && (
                  <>
                    <Button 
                      onClick={() => setCurrentSlideIndex((prev) => (prev - 1 + slideshowImages.length) % slideshowImages.length)}
                      sx={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', bgcolor: 'rgba(0,0,0,0.5)', color: 'white', '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' } }}
                    >
                      ‹
                    </Button>
                    <Button 
                      onClick={() => setCurrentSlideIndex((prev) => (prev + 1) % slideshowImages.length)}
                      sx={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', bgcolor: 'rgba(0,0,0,0.5)', color: 'white', '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' } }}
                    >
                      ›
                    </Button>
                  </>
                )}
              </Box>
              <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'grey.100' }}>
                <Typography variant="caption">{currentSlideIndex + 1} / {slideshowImages.length}</Typography>
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSlideshowOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default CitySelection;