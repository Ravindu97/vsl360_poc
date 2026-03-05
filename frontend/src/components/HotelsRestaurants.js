import React, { useState, useEffect } from 'react';
import { 
  Card, CardContent, Typography, Button, Box, 
  CircularProgress, Alert, Tabs, Tab, Accordion,
  AccordionSummary, AccordionDetails, Grid, Chip
} from '@mui/material';
import { Hotel, ExpandMore } from '@mui/icons-material';
import axios from 'axios';

const HotelsRestaurants = ({ tripData, nextStep, prevStep }) => {
  const [hotels, setHotels] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [parsedHotels, setParsedHotels] = useState({});

  useEffect(() => {
    const cities = tripData.optimized_cities || tripData.selected_cities;
    console.log('HotelsRestaurants useEffect - tripData:', tripData);
    console.log('Available cities:', cities);
    console.log('Arrival country:', tripData.arrival_country);
    
    // Auto-fetch if we have the required data and no existing data
    if (cities && cities.length > 0 && tripData.arrival_country && !hotels) {
      console.log('Auto-fetching hotels...');
      setTimeout(() => fetchHotelsRestaurants(), 100); // Small delay to ensure state is ready
    }
  }, [tripData]);

  // Manual fetch function for testing
  const handleManualFetch = () => {
    console.log('Manual fetch triggered');
    fetchHotelsRestaurants();
  };

  const fetchHotelsRestaurants = async () => {
    setLoading(true);
    setError('');
    setParsedHotels({}); // Clear previous data
    
    try {
      const cities = tripData.optimized_cities || tripData.selected_cities;
      console.log('Fetching hotels for cities:', cities, 'in country:', tripData.arrival_country);
      
      if (!cities || cities.length === 0) {
        setError('No cities available for hotel search');
        return;
      }
      
      if (!tripData.arrival_country) {
        setError('No destination country specified');
        return;
      }
      
      const response = await axios.post('http://localhost:8000/hotels-restaurants', {
        country: tripData.arrival_country,
        cities: cities
      }, {
        timeout: 60000 // 60 second timeout
      });
      
      console.log('Hotels response:', response.data);
      
      if (response.data && response.data.hotels) {
        setHotels(response.data.hotels);
        parseHotels(response.data.hotels);
      } else {
        setError('No hotel data received from server');
      }
    } catch (err) {
      console.error('Hotels fetch error:', err);
      if (err.code === 'ECONNABORTED') {
        setError('Request timed out. Please try again.');
      } else if (err.response) {
        setError(`Server error: ${err.response.status}`);
      } else {
        setError('Failed to fetch hotels and restaurants');
      }
    } finally {
      setLoading(false);
    }
  };

  const parseHotels = (content) => {
    console.log('Parsing hotels content:', content);
    
    if (!content) {
      console.log('Invalid content for parsing');
      return;
    }
    
    try {
      // Try parsing as JSON first
      const jsonData = JSON.parse(content);
      
      if (jsonData.hotels_by_city && Array.isArray(jsonData.hotels_by_city)) {
        const hotelsByCity = {};
        
        jsonData.hotels_by_city.forEach(cityData => {
          const cityName = cityData.city;
          hotelsByCity[cityName] = cityData.hotels.map(hotel => ({
            hotel: hotel.name,
            category: hotel.category,
            stars: hotel.stars.toString(),
            location: hotel.location,
            price: hotel.price,
            tripAdvisor: hotel.tripadvisor_url
          }));
        });
        
        console.log('Parsed JSON hotels by city:', hotelsByCity);
        setParsedHotels(hotelsByCity);
        return;
      }
    } catch (e) {
      console.log('Not JSON format, trying text parsing:', e);
    }
    
    // Fallback to text parsing if JSON parsing fails
    if (typeof content !== 'string') {
      console.log('Content is not a string');
      return;
    }
    
    const hotelsByCity = {};
    const lines = content.split('\n');
    let currentCity = '';
    let currentHotel = {};
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      if (trimmedLine.endsWith(':') && trimmedLine.toUpperCase() === trimmedLine) {
        currentCity = trimmedLine.replace(':', '').trim();
        hotelsByCity[currentCity] = [];
      } else if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**')) {
        currentCity = trimmedLine.replace(/\*\*/g, '').trim();
        hotelsByCity[currentCity] = [];
      } else if (trimmedLine.includes('Hotel:')) {
        currentHotel.hotel = trimmedLine.split('Hotel:')[1].trim();
      } else if (trimmedLine.includes('Category:')) {
        currentHotel.category = trimmedLine.split('Category:')[1].trim();
      } else if (trimmedLine.includes('Stars:')) {
        currentHotel.stars = trimmedLine.split('Stars:')[1].trim();
      } else if (trimmedLine.includes('Location:')) {
        currentHotel.location = trimmedLine.split('Location:')[1].trim();
      } else if (trimmedLine.includes('Price:')) {
        currentHotel.price = trimmedLine.split('Price:')[1].trim();
      } else if (trimmedLine.includes('TripAdvisor:')) {
        currentHotel.tripAdvisor = trimmedLine.split('TripAdvisor:')[1].trim();
      } else if (trimmedLine.includes('HOTEL_END') && Object.keys(currentHotel).length > 0 && currentCity) {
        hotelsByCity[currentCity].push({ ...currentHotel });
        currentHotel = {};
      }
    }
    
    console.log('Parsed text hotels by city:', hotelsByCity);
    setParsedHotels(hotelsByCity);
  };



  const getCategoryColor = (category) => {
    switch (category?.toLowerCase()) {
      case 'budget': return 'success';
      case 'mid-range': return 'warning';
      case 'luxury': return 'error';
      default: return 'default';
    }
  };

  const getTripAdvisorLink = (hotelName, city) => {
    if (hotelName?.toLowerCase().includes('jetwing beach') && city?.toLowerCase().includes('negombo')) {
      return 'https://www.tripadvisor.com/Hotel_Review-g297896-d301067-Reviews-Jetwing_Beach-Negombo.html';
    }
    return null;
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };



  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Hotel sx={{ mr: 2, fontSize: 30 }} />
          <Typography variant="h4" component="h2">
            Hotels & Accommodations
          </Typography>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {!loading && !error && !hotels && (
          <Box sx={{ mb: 2 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              {!tripData.optimized_cities && !tripData.selected_cities 
                ? 'No cities selected. Please complete the city selection process first.'
                : !tripData.arrival_country 
                ? 'No destination country selected. Please complete the trip details first.'
                : 'No hotel data loaded yet.'}
            </Alert>
            <Button variant="contained" onClick={handleManualFetch} disabled={loading}>
              {loading ? 'Loading...' : 'Load Hotels'}
            </Button>
          </Box>
        )}



        {Object.keys(parsedHotels).length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
              {Object.keys(parsedHotels).map((city, index) => (
                <Tab key={city} label={city} />
              ))}
            </Tabs>

            {Object.entries(parsedHotels).map(([city, cityHotels], cityIndex) => {
              // Sort hotels by category: Luxury > Mid-Range > Budget
              const categoryOrder = { 'luxury': 1, 'mid-range': 2, 'budget': 3 };
              const sortedHotels = [...cityHotels].sort((a, b) => {
                const orderA = categoryOrder[a.category?.toLowerCase()] || 999;
                const orderB = categoryOrder[b.category?.toLowerCase()] || 999;
                return orderA - orderB;
              });
              
              return (
              <Box key={city} hidden={tabValue !== cityIndex} sx={{ mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Hotels in {city}
                </Typography>
                
                {sortedHotels.map((hotel, hotelIndex) => (
                  <Accordion key={hotelIndex} sx={{ mb: 1, border: '2px solid', borderColor: '#87ceeb', transition: 'all 0.3s ease', '&:hover': { borderColor: '#1976d2', boxShadow: '0 4px 12px rgba(135, 206, 235, 0.3)' } }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                        <Typography variant="h6" sx={{ flexGrow: 1 }}>
                          {hotel.hotel}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Chip 
                            label={hotel.category} 
                            color={getCategoryColor(hotel.category)}
                            size="small"
                          />
                          <Chip 
                            label={`${hotel.stars} ⭐`} 
                            variant="outlined"
                            size="small"
                          />
                          <Chip 
                            label={hotel.price} 
                            color="info"
                            size="small"
                          />
                        </Box>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                          <Box sx={{ p: 2, bgcolor: '#e3f2fd', borderRadius: 2, border: '2px solid #1976d2' }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                              📍 Location: <span style={{ fontWeight: 'normal' }}>{hotel.location}</span>
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Box sx={{ p: 2, bgcolor: '#fff3e0', borderRadius: 2, border: '2px solid #ff9800' }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#ff9800' }}>
                              💰 Price: <span style={{ fontWeight: 'normal' }}>{hotel.price}</span>
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Box sx={{ p: 2, bgcolor: '#e3f2fd', borderRadius: 2, border: '2px solid #1976d2' }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                              🏨 Category: <span style={{ fontWeight: 'normal' }}>{hotel.category}</span>
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Box sx={{ p: 2, bgcolor: '#fff3e0', borderRadius: 2, border: '2px solid #ff9800' }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#ff9800' }}>
                              ⭐ Rating: <span style={{ fontWeight: 'normal' }}>{hotel.stars} stars</span>
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12}>
                          <Box sx={{ mt: 2, textAlign: 'center' }}>
                            <Button 
                              variant="contained" 
                              size="small"
                              href={hotel.tripAdvisor || `https://www.tripadvisor.com/Search?q=${encodeURIComponent(hotel.hotel + ' ' + city)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              sx={{ 
                                bgcolor: '#00aa6c',
                                '&:hover': { bgcolor: '#008c5a' }
                              }}
                            >
                              View on TripAdvisor
                            </Button>
                          </Box>
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                ))}
                
                <Box sx={{ mt: 3, textAlign: 'center' }}>
                  <Button 
                    variant="contained" 
                    size="large"
                    onClick={() => window.open(`https://www.booking.com/searchresults.html?ss=${encodeURIComponent(city)}`, '_blank')}
                    sx={{ 
                      bgcolor: '#1976d2',
                      color: 'white',
                      '&:hover': { 
                        bgcolor: '#1565c0'
                      }
                    }}
                  >
                    See More Hotels in {city}
                  </Button>
                </Box>
              </Box>
            );
            })}
          </Box>
        )}



        {tripData.city_schedule && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>Your Travel Summary</Typography>
            <Card variant="outlined" sx={{ border: '2px solid', borderColor: '#87ceeb', transition: 'all 0.3s ease', '&:hover': { borderColor: '#1976d2', boxShadow: '0 4px 12px rgba(135, 206, 235, 0.3)' } }}>
              <CardContent>
                <Typography variant="body1" gutterBottom>
                  <strong>Trip Duration:</strong> {tripData.total_days} days
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Countries:</strong> {tripData.departure_country} → {tripData.arrival_country}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Cities:</strong> {tripData.optimized_cities?.join(' → ')}
                </Typography>
                <Typography variant="body1">
                  <strong>Interests:</strong> {tripData.interests?.join(', ')}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
          <Button variant="outlined" onClick={prevStep}>
            Back
          </Button>
          <Button variant="contained" onClick={nextStep}>
            Next
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default HotelsRestaurants;