import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Button, Box, CircularProgress, Alert, Grid, Paper, List, ListItem, ListItemText, Chip, Divider } from '@mui/material';
import { DirectionsBus, Train, Flight, DirectionsCar } from '@mui/icons-material';
import axios from 'axios';

const TransportationOptions = ({ tripData, nextStep, prevStep }) => {
  const [transportation, setTransportation] = useState('');
  const [parsedTransportation, setParsedTransportation] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (tripData.optimized_cities && tripData.optimized_cities.length > 0 && !transportation) {
      fetchTransportation();
    }
  }, [tripData]);

  const fetchTransportation = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post('http://localhost:8000/transportation-options', {
        cities: tripData.optimized_cities,
        country: tripData.arrival_country
      });
      setTransportation(response.data.transportation);
      parseTransportation(response.data.transportation);
    } catch (err) {
      setError('Failed to fetch transportation options');
    } finally {
      setLoading(false);
    }
  };

  const parseTransportation = (transportText) => {
    const routes = [];
    const routeBlocks = transportText.split('ROUTE:').filter(block => block.trim());
    
    routeBlocks.forEach(block => {
      const lines = block.trim().split('\n');
      const routeName = lines[0].trim();
      const options = [];
      let currentOption = null;
      let recommended = '';
      let booking = '';
      
      lines.forEach(line => {
        line = line.trim();
        if (line.startsWith('TRANSPORT_START')) {
          currentOption = {};
        } else if (line.startsWith('TRANSPORT_END')) {
          if (currentOption) options.push(currentOption);
          currentOption = null;
        } else if (line.startsWith('RECOMMENDED:')) {
          recommended = line.replace('RECOMMENDED:', '').trim();
        } else if (line.startsWith('BOOKING:')) {
          booking = line.replace('BOOKING:', '').trim();
        } else if (currentOption && line.includes(':')) {
          const [key, ...valueParts] = line.split(':');
          const value = valueParts.join(':').trim();
          currentOption[key.toLowerCase()] = value;
        }
      });
      
      if (options.length > 0) {
        routes.push({ routeName, options, recommended, booking });
      }
    });
    
    setParsedTransportation(routes);
  };

  const getTransportIcon = (type) => {
    const lowerType = type?.toLowerCase() || '';
    if (lowerType.includes('train')) return <Train color="primary" />;
    if (lowerType.includes('bus')) return <DirectionsBus color="primary" />;
    if (lowerType.includes('flight')) return <Flight color="primary" />;
    if (lowerType.includes('car')) return <DirectionsCar color="primary" />;
    return <DirectionsBus color="primary" />;
  };

  const getTypeColor = (type) => {
    const lowerType = type?.toLowerCase() || '';
    if (lowerType.includes('train')) return 'primary';
    if (lowerType.includes('bus')) return 'secondary';
    if (lowerType.includes('flight')) return 'error';
    if (lowerType.includes('car')) return 'success';
    return 'default';
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <DirectionsBus sx={{ mr: 2, fontSize: 30 }} />
          <Typography variant="h4" component="h2">
            Transportation Options
          </Typography>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {parsedTransportation.length > 0 ? (
          <Grid container spacing={3}>
            {parsedTransportation.map((route, index) => (
              <Grid item xs={12} key={index}>
                <Paper elevation={2} sx={{ p: 3 }}>
                  <Typography variant="h5" sx={{ mb: 2, color: 'primary.main' }}>
                    🚗 {route.routeName.replace(/\*\*/g, '')}
                  </Typography>
                  
                  <Grid container spacing={2}>
                    {route.options.map((option, optIndex) => (
                      <Grid item xs={12} md={4} key={optIndex}>
                        <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            {getTransportIcon(option.type)}
                            <Chip 
                              label={option.type} 
                              color={getTypeColor(option.type)} 
                              size="small" 
                              sx={{ ml: 1 }} 
                            />
                          </Box>
                          
                          <List dense>
                            {option.service && (
                              <ListItem sx={{ px: 0 }}>
                                <ListItemText primary="Service" secondary={option.service} />
                              </ListItem>
                            )}
                            {option.distance && (
                              <ListItem sx={{ px: 0 }}>
                                <ListItemText primary="Distance" secondary={option.distance} />
                              </ListItem>
                            )}
                            {option.duration && (
                              <ListItem sx={{ px: 0 }}>
                                <ListItemText primary="Duration" secondary={option.duration} />
                              </ListItem>
                            )}
                            {option.cost && (
                              <ListItem sx={{ px: 0 }}>
                                <ListItemText primary="Cost" secondary={option.cost} />
                              </ListItem>
                            )}
                            {option.frequency && (
                              <ListItem sx={{ px: 0 }}>
                                <ListItemText primary="Frequency" secondary={option.frequency} />
                              </ListItem>
                            )}
                          </List>
                          
                          {option.pros && (
                            <Box sx={{ mt: 1 }}>
                              <Typography variant="caption" color="success.main">✓ {option.pros}</Typography>
                            </Box>
                          )}
                          {option.cons && (
                            <Box sx={{ mt: 0.5 }}>
                              <Typography variant="caption" color="error.main">✗ {option.cons}</Typography>
                            </Box>
                          )}
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                  
                  {route.recommended && (
                    <Box sx={{ mt: 2, p: 2, bgcolor: 'success.50', borderRadius: 1 }}>
                      <Typography variant="subtitle2" color="success.main">
                        💡 Recommended: {route.recommended}
                      </Typography>
                    </Box>
                  )}
                  
                  {route.booking && (
                    <Box sx={{ mt: 1, p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
                      <Typography variant="subtitle2" color="info.main">
                        📱 Booking: {route.booking}
                      </Typography>
                    </Box>
                  )}
                </Paper>
              </Grid>
            ))}
          </Grid>
        ) : transportation && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
              {transportation}
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

export default TransportationOptions;