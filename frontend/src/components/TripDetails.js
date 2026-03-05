import React, { useState, useEffect } from 'react';
import { 
  Card, CardContent, Typography, TextField, Button, 
  Grid, Autocomplete, Box, Alert 
} from '@mui/material';
import { FlightTakeoff } from '@mui/icons-material';
import axios from 'axios';

const TripDetails = ({ tripData, updateTripData, nextStep, prevStep }) => {
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchCountries();
  }, []);

  const fetchCountries = async () => {
    try {
      const response = await axios.get('http://localhost:8000/countries');
      setCountries(response.data.countries);
    } catch (err) {
      setError('Failed to load countries');
    }
  };

  const handleSubmit = () => {
    if (!tripData.departure_country || !tripData.arrival_country || !tripData.start_date || !tripData.end_date) {
      setError('Please fill in all fields');
      return;
    }
    
    const startDate = new Date(tripData.start_date);
    const endDate = new Date(tripData.end_date);
    const totalDays = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
    
    if (totalDays <= 0) {
      setError('End date must be after start date');
      return;
    }

    updateTripData({ total_days: totalDays });
    setError('');
    nextStep();
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <FlightTakeoff sx={{ mr: 2, fontSize: 30 }} />
          <Typography variant="h4" component="h2">
            Trip Details
          </Typography>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Autocomplete
              options={countries}
              value={tripData.departure_country}
              onChange={(event, newValue) => updateTripData({ departure_country: newValue })}
              renderInput={(params) => (
                <TextField {...params} label="Departure Country" fullWidth sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#87ceeb', borderWidth: '2px' }, '&:hover fieldset': { borderColor: '#1976d2' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }} />
              )}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Autocomplete
              options={countries}
              value={tripData.arrival_country}
              onChange={(event, newValue) => updateTripData({ arrival_country: newValue })}
              renderInput={(params) => (
                <TextField {...params} label="Destination Country" fullWidth sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#87ceeb', borderWidth: '2px' }, '&:hover fieldset': { borderColor: '#1976d2' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }} />
              )}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Start Date"
              type="date"
              value={tripData.start_date}
              onChange={(e) => updateTripData({ start_date: e.target.value })}
              fullWidth
              InputLabelProps={{ shrink: true }}
              sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#87ceeb', borderWidth: '2px' }, '&:hover fieldset': { borderColor: '#1976d2' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="End Date"
              type="date"
              value={tripData.end_date}
              onChange={(e) => updateTripData({ end_date: e.target.value })}
              fullWidth
              InputLabelProps={{ shrink: true }}
              sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#87ceeb', borderWidth: '2px' }, '&:hover fieldset': { borderColor: '#1976d2' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
            />
          </Grid>
        </Grid>

        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
          <Button 
            variant="outlined" 
            size="large" 
            onClick={prevStep}
          >
            Back
          </Button>
          <Button 
            variant="contained" 
            size="large" 
            onClick={handleSubmit}
            disabled={loading}
          >
            Get Destination Info
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default TripDetails;