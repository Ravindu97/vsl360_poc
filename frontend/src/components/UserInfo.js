import React, { useState } from 'react';
import { 
  Card, CardContent, Typography, TextField, Button, 
  Grid, Box, Alert 
} from '@mui/material';
import { Person } from '@mui/icons-material';
import axios from 'axios';

const UserInfo = ({ tripData, updateTripData, nextStep }) => {
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!tripData.full_name || !tripData.country || !tripData.mobile_no || !tripData.email) {
      setError('Please fill in all fields');
      return;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(tripData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    try {
      await axios.post('http://localhost:8000/save-user', {
        full_name: tripData.full_name,
        country: tripData.country,
        mobile_no: tripData.mobile_no,
        email: tripData.email
      });
      setError('');
      nextStep();
    } catch (err) {
      setError('Failed to save user information');
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Person sx={{ mr: 2, fontSize: 30 }} />
          <Typography variant="h4" component="h2">
            User Information
          </Typography>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              label="Full Name"
              value={tripData.full_name || ''}
              onChange={(e) => updateTripData({ full_name: e.target.value })}
              fullWidth
              required
              sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#87ceeb', borderWidth: '2px' }, '&:hover fieldset': { borderColor: '#1976d2' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              label="Country"
              value={tripData.country || ''}
              onChange={(e) => updateTripData({ country: e.target.value })}
              fullWidth
              required
              sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#87ceeb', borderWidth: '2px' }, '&:hover fieldset': { borderColor: '#1976d2' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Mobile No"
              value={tripData.mobile_no || ''}
              onChange={(e) => updateTripData({ mobile_no: e.target.value })}
              fullWidth
              required
              sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#87ceeb', borderWidth: '2px' }, '&:hover fieldset': { borderColor: '#1976d2' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Email"
              type="email"
              value={tripData.email || ''}
              onChange={(e) => updateTripData({ email: e.target.value })}
              fullWidth
              required
              sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#87ceeb', borderWidth: '2px' }, '&:hover fieldset': { borderColor: '#1976d2' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
            />
          </Grid>
        </Grid>

        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Button 
            variant="contained" 
            size="large" 
            onClick={handleSubmit}
          >
            Continue
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default UserInfo;
