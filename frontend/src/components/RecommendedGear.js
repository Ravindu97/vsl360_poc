import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Button, Box, CircularProgress, Alert } from '@mui/material';
import { Backpack } from '@mui/icons-material';
import axios from 'axios';

const RecommendedGear = ({ tripData, nextStep, prevStep }) => {
  const [gear, setGear] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (tripData.optimized_cities && tripData.optimized_cities.length > 0) {
      fetchGear();
    }
  }, [tripData]);

  const fetchGear = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post('http://localhost:8000/recommended-gear', {
        cities: tripData.optimized_cities,
        country: tripData.arrival_country,
        interests: tripData.interests,
        start_date: tripData.start_date,
        end_date: tripData.end_date
      });
      setGear(response.data.gear);
    } catch (err) {
      setError('Failed to fetch gear recommendations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Backpack sx={{ mr: 2, fontSize: 30 }} />
          <Typography variant="h4" component="h2">
            Recommended Gears
          </Typography>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {gear && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
              {gear}
            </Typography>
          </Box>
        )}

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

export default RecommendedGear;