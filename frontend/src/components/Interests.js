import React, { useState } from 'react';
import { 
  Card, CardContent, Typography, Button, Box, 
  FormGroup, FormControlLabel, Checkbox, Alert, Grid, TextField 
} from '@mui/material';
import { Favorite } from '@mui/icons-material';

const Interests = ({ tripData, updateTripData, nextStep, prevStep }) => {
  const [error, setError] = useState('');
  const [customInterest, setCustomInterest] = useState('');

  const interestOptions = [
    "Adventure", "Architecture", "Art", "Beaches", "Culture", 
    "Festivals", "Food", "History", "Mountains", "Museums",
    "Nature", "Nightlife", "Photography", "Shopping", "Wildlife"
  ];

  const handleInterestChange = (interest, checked) => {
    const currentInterests = tripData.interests || [];
    let newInterests;
    
    if (checked) {
      newInterests = [...currentInterests, interest];
    } else {
      newInterests = currentInterests.filter(i => i !== interest);
    }
    
    updateTripData({ interests: newInterests });
  };

  const handleAddCustomInterest = () => {
    if (customInterest.trim()) {
      const currentInterests = tripData.interests || [];
      if (!currentInterests.includes(customInterest.trim())) {
        updateTripData({ interests: [...currentInterests, customInterest.trim()] });
      }
      setCustomInterest('');
    }
  };

  const handleSubmit = () => {
    if (!tripData.interests || tripData.interests.length === 0) {
      setError('Please select at least one interest');
      return;
    }
    setError('');
    nextStep();
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Favorite sx={{ mr: 2, fontSize: 30 }} />
          <Typography variant="h4" component="h2">
            Your Travel Interests
          </Typography>
        </Box>

        <Typography variant="body1" sx={{ mb: 3 }}>
          Select your travel interests to get personalized city recommendations:
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <FormGroup>
          <Grid container spacing={1}>
            {interestOptions.map((interest) => (
              <Grid item xs={12} sm={6} md={4} key={interest}>
                <Box 
                  onClick={() => handleInterestChange(interest, !tripData.interests?.includes(interest))}
                  sx={{ 
                    border: '2px solid #87ceeb', 
                    borderRadius: '8px', 
                    p: 1,
                    cursor: 'pointer',
                    '&:hover': { 
                      border: '2px solid #1976d2',
                      boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)', 
                      transform: 'translateY(-2px)', 
                      transition: 'all 0.3s' 
                    }
                  }}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={tripData.interests?.includes(interest) || false}
                      />
                    }
                    label={interest}
                    sx={{ pointerEvents: 'none', width: '100%' }}
                  />
                </Box>
              </Grid>
            ))}
          </Grid>
        </FormGroup>

        {tripData.interests && tripData.interests.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="primary">
              Selected interests: {tripData.interests.join(', ')}
            </Typography>
          </Box>
        )}

        <Box sx={{ mt: 3 }}>
          <Typography variant="body1" sx={{ mb: 1 }}>Add Custom Interest:</Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              placeholder="Enter your custom interest"
              value={customInterest}
              onChange={(e) => setCustomInterest(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddCustomInterest()}
            />
            <Button variant="outlined" onClick={handleAddCustomInterest}>
              Add
            </Button>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mt: 4 }}>
          <Button variant="outlined" onClick={prevStep}>
            Back
          </Button>
          <Button variant="contained" onClick={handleSubmit}>
            Get City Recommendations
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default Interests;