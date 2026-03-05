import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Button, CircularProgress, Alert, Tabs, Tab,
  Accordion, AccordionSummary, AccordionDetails, Chip, Link
} from '@mui/material';
import { Restaurant, ExpandMore } from '@mui/icons-material';

function Restaurants({ tripData, updateTripData, nextStep, prevStep }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [restaurants, setRestaurants] = useState('');
  const [parsedRestaurants, setParsedRestaurants] = useState({});
  const [tabValue, setTabValue] = useState(0);

  const fetchRestaurants = async () => {
    if (!tripData.optimized_cities || tripData.optimized_cities.length === 0) {
      setError('Please complete city selection first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/restaurants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          country: tripData.arrival_country,
          cities: tripData.optimized_cities
        })
      });

      if (!response.ok) throw new Error('Failed to fetch restaurants');

      const data = await response.json();
      setRestaurants(data.restaurants);
      parseRestaurants(data.restaurants);
      updateTripData({ restaurants: data.restaurants });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const parseRestaurants = (restaurantText) => {
    const cityRestaurants = {};
    const cities = restaurantText.split('CITY:').filter(section => section.trim());

    cities.forEach(citySection => {
      const lines = citySection.trim().split('\n');
      const cityName = lines[0].trim();
      const restaurants = [];

      let currentRestaurant = null;
      lines.forEach(line => {
        line = line.trim();
        if (line.startsWith('RESTAURANT_START')) {
          currentRestaurant = {};
        } else if (line.startsWith('RESTAURANT_END')) {
          if (currentRestaurant) restaurants.push(currentRestaurant);
          currentRestaurant = null;
        } else if (currentRestaurant && line.includes(':')) {
          const [key, ...valueParts] = line.split(':');
          const value = valueParts.join(':').trim();
          currentRestaurant[key.toLowerCase()] = value;
        }
      });

      if (restaurants.length > 0) {
        cityRestaurants[cityName] = restaurants;
      }
    });

    setParsedRestaurants(cityRestaurants);
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const getPriceColor = (price) => {
    if (price === '$') return 'success';
    if (price === '$$') return 'warning';
    if (price === '$$$') return 'error';
    return 'default';
  };

  useEffect(() => {
    if (tripData.restaurants) {
      setRestaurants(tripData.restaurants);
      parseRestaurants(tripData.restaurants);
    }
  }, [tripData.restaurants]);

  const cityNames = Object.keys(parsedRestaurants);

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Restaurant color="primary" />
        Restaurants
      </Typography>

      {!restaurants && (
        <Button
          variant="contained"
          onClick={fetchRestaurants}
          disabled={loading}
          sx={{ mb: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Get Restaurant Recommendations'}
        </Button>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {restaurants && (
        <Box>
          <Button variant="outlined" onClick={fetchRestaurants} disabled={loading} sx={{ mb: 2 }}>
            {loading ? <CircularProgress size={20} /> : 'Refresh Restaurants'}
          </Button>

          {cityNames.length > 0 && (
            <Box>
              <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 2 }}>
                {cityNames.map((city, index) => (
                  <Tab key={city} label={city} />
                ))}
              </Tabs>

              {cityNames.map((city, index) => (
                <Box key={city} hidden={tabValue !== index}>
                  <Typography variant="h6" sx={{ mb: 2 }}>Restaurants in {city}</Typography>
                  {parsedRestaurants[city].map((restaurant, idx) => (
                    <Accordion key={idx} sx={{ mb: 1 }}>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                          <Typography variant="h6">{restaurant.restaurant}</Typography>
                          {restaurant.cuisine && (
                            <Chip label={restaurant.cuisine} size="small" color="primary" />
                          )}
                          {restaurant.price && (
                            <Chip label={restaurant.price} size="small" color={getPriceColor(restaurant.price)} />
                          )}
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                          {restaurant.location && (
                            <Typography><strong>Location:</strong> {restaurant.location}</Typography>
                          )}
                          {restaurant.specialty && (
                            <Typography><strong>Specialty:</strong> {restaurant.specialty}</Typography>
                          )}
                          {restaurant.atmosphere && (
                            <Typography><strong>Atmosphere:</strong> {restaurant.atmosphere}</Typography>
                          )}
                          {restaurant.tripadvisor && (
                            <Link href={restaurant.tripadvisor} target="_blank" rel="noopener">
                              View on TripAdvisor
                            </Link>
                          )}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </Box>
              ))}
            </Box>
          )}
        </Box>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
        <Button variant="outlined" onClick={prevStep}>
          Previous
        </Button>
        {nextStep && (
          <Button variant="contained" onClick={nextStep}>
            Next
          </Button>
        )}
      </Box>
    </Box>
  );
}

export default Restaurants;