import React, { useState, useEffect } from 'react';
import { 
  Card, CardContent, Typography, Button, Box, 
  CircularProgress, Alert, Accordion, AccordionSummary, 
  AccordionDetails, Grid, Chip 
} from '@mui/material';
import { Flight, ExpandMore, Star, StarBorder } from '@mui/icons-material';
import axios from 'axios';

const FlightOptions = ({ tripData, nextStep, prevStep }) => {
  const [flightOptions, setFlightOptions] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [parsedFlights, setParsedFlights] = useState([]);

  useEffect(() => {
    fetchFlightOptions();
  }, []);

  const fetchFlightOptions = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post('http://localhost:8000/flight-options', {
        departure_country: tripData.departure_country,
        arrival_country: tripData.arrival_country,
        start_date: tripData.start_date,
        end_date: tripData.end_date
      });
      setFlightOptions(response.data.flight_options);
      parseFlights(response.data.flight_options);
    } catch (err) {
      setError('Failed to fetch flight options');
    } finally {
      setLoading(false);
    }
  };

  const getAirlineLogo = (airlineName) => {
    const airline = airlineName.toLowerCase();
    const logoMap = {
      'emirates': 'https://www.gstatic.com/flights/airline_logos/70px/EK.png',
      'qatar': 'https://www.gstatic.com/flights/airline_logos/70px/QR.png',
      'etihad': 'https://www.gstatic.com/flights/airline_logos/70px/EY.png',
      'lufthansa': 'https://www.gstatic.com/flights/airline_logos/70px/LH.png',
      'british': 'https://www.gstatic.com/flights/airline_logos/70px/BA.png',
      'air france': 'https://www.gstatic.com/flights/airline_logos/70px/AF.png',
      'klm': 'https://www.gstatic.com/flights/airline_logos/70px/KL.png',
      'turkish': 'https://www.gstatic.com/flights/airline_logos/70px/TK.png',
      'singapore': 'https://www.gstatic.com/flights/airline_logos/70px/SQ.png',
      'cathay': 'https://www.gstatic.com/flights/airline_logos/70px/CX.png',
      'american': 'https://www.gstatic.com/flights/airline_logos/70px/AA.png',
      'delta': 'https://www.gstatic.com/flights/airline_logos/70px/DL.png',
      'united': 'https://www.gstatic.com/flights/airline_logos/70px/UA.png',
      'southwest': 'https://www.gstatic.com/flights/airline_logos/70px/WN.png',
      'jetblue': 'https://www.gstatic.com/flights/airline_logos/70px/B6.png',
      'air canada': 'https://www.gstatic.com/flights/airline_logos/70px/AC.png',
      'qantas': 'https://www.gstatic.com/flights/airline_logos/70px/QF.png',
      'virgin': 'https://www.gstatic.com/flights/airline_logos/70px/VS.png',
      'japan airlines': 'https://www.gstatic.com/flights/airline_logos/70px/JL.png',
      'ana': 'https://www.gstatic.com/flights/airline_logos/70px/NH.png',
      'korean air': 'https://www.gstatic.com/flights/airline_logos/70px/KE.png',
      'china': 'https://www.gstatic.com/flights/airline_logos/70px/CA.png',
      'thai': 'https://www.gstatic.com/flights/airline_logos/70px/TG.png',
      'malaysia': 'https://www.gstatic.com/flights/airline_logos/70px/MH.png',
      'saudia': 'https://www.gstatic.com/flights/airline_logos/70px/SV.png',
      'swiss': 'https://www.gstatic.com/flights/airline_logos/70px/LX.png',
      'iberia': 'https://www.gstatic.com/flights/airline_logos/70px/IB.png',
      'alitalia': 'https://www.gstatic.com/flights/airline_logos/70px/AZ.png',
      'aeroflot': 'https://www.gstatic.com/flights/airline_logos/70px/SU.png',
      'finnair': 'https://www.gstatic.com/flights/airline_logos/70px/AY.png',
      'srilankan': 'https://www.gstatic.com/flights/airline_logos/70px/UL.png',
      'sri lankan': 'https://www.gstatic.com/flights/airline_logos/70px/UL.png',
      'air arabia': 'https://www.gstatic.com/flights/airline_logos/70px/G9.png',
      'air india': 'https://www.gstatic.com/flights/airline_logos/70px/AI.png',
      'indigo': 'https://www.gstatic.com/flights/airline_logos/70px/6E.png',
      'spicejet': 'https://www.gstatic.com/flights/airline_logos/70px/SG.png',
      'vistara': 'https://www.gstatic.com/flights/airline_logos/70px/UK.png',
      'air asia': 'https://www.gstatic.com/flights/airline_logos/70px/AK.png',
      'cebu pacific': 'https://www.gstatic.com/flights/airline_logos/70px/5J.png',
      'garuda': 'https://www.gstatic.com/flights/airline_logos/70px/GA.png',
      'vietnam airlines': 'https://www.gstatic.com/flights/airline_logos/70px/VN.png',
      'philippine airlines': 'https://www.gstatic.com/flights/airline_logos/70px/PR.png',
      'eva air': 'https://www.gstatic.com/flights/airline_logos/70px/BR.png',
      'china eastern': 'https://www.gstatic.com/flights/airline_logos/70px/MU.png',
      'china southern': 'https://www.gstatic.com/flights/airline_logos/70px/CZ.png',
      'asiana': 'https://www.gstatic.com/flights/airline_logos/70px/OZ.png',
      'air new zealand': 'https://www.gstatic.com/flights/airline_logos/70px/NZ.png',
      'egyptair': 'https://www.gstatic.com/flights/airline_logos/70px/MS.png',
      'ethiopian': 'https://www.gstatic.com/flights/airline_logos/70px/ET.png',
      'kenya airways': 'https://www.gstatic.com/flights/airline_logos/70px/KQ.png',
      'south african': 'https://www.gstatic.com/flights/airline_logos/70px/SA.png',
      'tap': 'https://www.gstatic.com/flights/airline_logos/70px/TP.png',
      'lot': 'https://www.gstatic.com/flights/airline_logos/70px/LO.png',
      'scandinavian': 'https://www.gstatic.com/flights/airline_logos/70px/SK.png',
      'norwegian': 'https://www.gstatic.com/flights/airline_logos/70px/DY.png',
      'ryanair': 'https://www.gstatic.com/flights/airline_logos/70px/FR.png',
      'easyjet': 'https://www.gstatic.com/flights/airline_logos/70px/U2.png',
      'wizz': 'https://www.gstatic.com/flights/airline_logos/70px/W6.png',
      'oman': 'https://www.gstatic.com/flights/airline_logos/70px/WY.png',
      'oman air': 'https://www.gstatic.com/flights/airline_logos/70px/WY.png',
      'malindo': 'https://www.gstatic.com/flights/airline_logos/70px/OD.png',
      'malindo air': 'https://www.gstatic.com/flights/airline_logos/70px/OD.png',
      'aerolineas argentinas': 'https://www.gstatic.com/flights/airline_logos/70px/AR.png',
      'aerolineas': 'https://www.gstatic.com/flights/airline_logos/70px/AR.png',
      'latam': 'https://www.gstatic.com/flights/airline_logos/70px/LA.png'
    };
    
    for (const [key, logo] of Object.entries(logoMap)) {
      if (airline.includes(key)) return logo;
    }
    return 'https://via.placeholder.com/70x70?text=✈';
  };

  const parseFlights = (content) => {
    const flights = [];
    const lines = content.split('\n');
    let currentFlight = {};
    let currentReview = {};
    let reviews = [];
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine.includes('Airline:')) {
        currentFlight.airline = trimmedLine.split('Airline:')[1].trim();
      } else if (trimmedLine.includes('Route:')) {
        currentFlight.route = trimmedLine.split('Route:')[1].trim();
      } else if (trimmedLine.includes('Duration:')) {
        currentFlight.duration = trimmedLine.split('Duration:')[1].trim();
      } else if (trimmedLine.includes('Price:')) {
        currentFlight.price = trimmedLine.split('Price:')[1].trim();
      } else if (trimmedLine.includes('Rating:')) {
        currentFlight.rating = trimmedLine.split('Rating:')[1].trim();
      } else if (trimmedLine.includes('REVIEW_START')) {
        currentReview = {};
      } else if (trimmedLine.includes('Stars:')) {
        currentReview.stars = parseInt(trimmedLine.split('Stars:')[1].trim());
      } else if (trimmedLine.includes('Title:')) {
        currentReview.title = trimmedLine.split('Title:')[1].trim();
      } else if (trimmedLine.includes('Text:')) {
        currentReview.text = trimmedLine.split('Text:')[1].trim();
      } else if (trimmedLine.includes('REVIEW_END')) {
        if (Object.keys(currentReview).length > 0) {
          reviews.push({ ...currentReview });
        }
      } else if (trimmedLine.includes('FLIGHT_OPTION_END') && Object.keys(currentFlight).length > 0) {
        currentFlight.reviews = reviews;
        flights.push({ ...currentFlight });
        currentFlight = {};
        reviews = [];
      }
    }
    setParsedFlights(flights);
  };

  const bookingWebsites = [
    { name: 'Expedia', url: 'https://www.expedia.com', description: 'Best for package deals', logo: '/images/expedia-logo.png' },
    { name: 'Kayak', url: 'https://www.kayak.com', description: 'Price comparison', logo: '/images/kayak-logo.png' },
    { name: 'Skyscanner', url: 'https://www.skyscanner.com', description: 'Budget options', logo: '/images/Skyscanner-logo.png' },
    { name: 'Google Flights', url: 'https://www.google.com/flights', description: 'Real-time prices', logo: '/images/GoogleFlights-logo.png' }
  ];

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Flight sx={{ mr: 2, fontSize: 30 }} />
          <Typography variant="h4" component="h2">
            Flight Options
          </Typography>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {parsedFlights.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>Available Flights</Typography>
            {parsedFlights.map((flight, index) => (
              <Accordion key={index} sx={{ mb: 1, border: '2px solid #87ceeb', borderRadius: '8px', '&:hover': { border: '2px solid #1976d2', boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)', transform: 'translateY(-2px)', transition: 'all 0.3s' } }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 2 }}>
                    <img 
                      src={getAirlineLogo(flight.airline)} 
                      alt={flight.airline}
                      style={{ height: '40px', width: '120px', objectFit: 'contain' }}
                      onError={(e) => e.target.src = 'https://via.placeholder.com/120x40?text=Airline'}
                    />
                    <Box>
                      <Typography variant="body2" color="text.secondary" fontWeight="bold">
                        {flight.airline}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        {flight.duration}
                      </Typography>
                    </Box>
                    <Chip label={flight.price} color="primary" sx={{ ml: 'auto' }} />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography><strong>Route:</strong> {flight.route}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography><strong>Duration:</strong> {flight.duration}</Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Box sx={{ mt: 2, mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="h6">Rating:</Typography>
                          <Box sx={{ display: 'flex' }}>
                            {[1, 2, 3, 4, 5].map((star) => (
                              <Star key={star} sx={{ color: star <= Math.floor(parseFloat(flight.rating || 4)) ? '#ffa500' : '#ddd', fontSize: 24 }} />
                            ))}
                          </Box>
                          <Typography variant="h6">{flight.rating || '4.0'}/5</Typography>
                        </Box>
                      </Box>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>Customer Reviews:</Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {(flight.reviews || []).map((review, idx) => (
                          <Box key={idx} sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                              <Box sx={{ display: 'flex' }}>
                                {[1, 2, 3, 4, 5].map((star) => (
                                  <Star key={star} sx={{ color: star <= review.stars ? '#ffa500' : '#ddd', fontSize: 18 }} />
                                ))}
                              </Box>
                              <Typography variant="body2" fontWeight="bold">{review.title}</Typography>
                            </Box>
                            <Typography variant="body2">{review.text}</Typography>
                          </Box>
                        ))}
                      </Box>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}

        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>Booking Websites</Typography>
          <Grid container spacing={2}>
            {bookingWebsites.map((site, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <Card variant="outlined" sx={{ height: '100%', cursor: 'pointer', border: '2px solid #87ceeb', borderRadius: '8px', '&:hover': { border: '2px solid #1976d2', boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)', transform: 'translateY(-2px)', transition: 'all 0.3s' } }} onClick={() => window.open(site.url, '_blank')}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60px' }}>
                      <img 
                        src={site.logo} 
                        alt={site.name}
                        style={{ maxHeight: '50px', maxWidth: '150px', objectFit: 'contain' }}
                        onError={(e) => e.target.style.display = 'none'}
                      />
                    </Box>
                    <Typography variant="h6" sx={{ color: 'primary.main' }}>
                      {site.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {site.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
          <Button variant="outlined" onClick={prevStep}>
            Back
          </Button>
          <Button variant="contained" onClick={nextStep} disabled={loading}>
            Continue to Interests
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default FlightOptions;