import React, { useState } from 'react';
import { 
  Box, Paper, Typography, Button, CircularProgress, 
  Alert, Card, CardContent, IconButton, Divider, Fab
} from '@mui/material';
import { 
  ReportProblem, Close, Phone, Warning
} from '@mui/icons-material';
import axios from 'axios';

const Emergency = () => {
  const [open, setOpen] = useState(false);
  const [emergencyNumbers, setEmergencyNumbers] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleOpen = () => {
    setOpen(true);
    getEmergencyNumbers();
  };

  const getEmergencyNumbers = () => {
    setLoading(true);
    
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const response = await axios.post('http://localhost:8000/emergency-numbers', {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude
            });
            setEmergencyNumbers(response.data);
          } catch (err) {
            console.error('Error fetching emergency numbers:', err);
            setEmergencyNumbers({
              country: 'Unknown',
              numbers: { police: '112', ambulance: '112', fire: '112' },
              note: '112 works in most countries'
            });
          } finally {
            setLoading(false);
          }
        },
        (error) => {
          setEmergencyNumbers({
            country: 'Unknown',
            numbers: { police: '112', ambulance: '112', fire: '112' },
            note: '112 works in most countries. Enable location for accurate numbers.'
          });
          setLoading(false);
        }
      );
    } else {
      setEmergencyNumbers({
        country: 'Unknown',
        numbers: { police: '112', ambulance: '112', fire: '112' },
        note: 'Geolocation not supported'
      });
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        variant="contained"
        startIcon={<ReportProblem />}
        onClick={handleOpen}
        sx={{
          position: 'fixed',
          bottom: 90,
          right: 20,
          zIndex: 1001,
          bgcolor: '#d32f2f',
          '&:hover': { bgcolor: '#b71c1c' },
          animation: 'blink 2s infinite',
          '@keyframes blink': {
            '0%, 100%': { opacity: 1 },
            '50%': { opacity: 0.3 }
          }
        }}
      >
        EMERGENCY
      </Button>

      {open && (
        <Paper
          elevation={8}
          sx={{
            position: 'fixed',
            bottom: 160,
            right: 20,
            width: 400,
            maxHeight: 500,
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1001,
            overflow: 'hidden'
          }}
        >
          <Box sx={{ p: 2, bgcolor: '#d32f2f', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ReportProblem />
              <Typography variant="h6">Emergency Services</Typography>
            </Box>
            <IconButton size="small" onClick={() => setOpen(false)} sx={{ color: 'white' }}>
              <Close />
            </IconButton>
          </Box>

          <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : emergencyNumbers ? (
              <>
                <Alert severity="error" sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    Call emergency services immediately if you are in danger!
                  </Typography>
                </Alert>

                <Typography variant="h6" sx={{ mb: 2 }}>
                  Location: {emergencyNumbers.country}
                </Typography>

                <Card sx={{ mb: 2, bgcolor: '#ffebee' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Phone color="error" />
                      <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                        {emergencyNumbers.numbers.ambulance}
                      </Typography>
                      <Typography variant="body1">Ambulance</Typography>
                    </Box>
                    <Divider sx={{ my: 1 }} />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Phone color="error" />
                      <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                        {emergencyNumbers.numbers.police}
                      </Typography>
                      <Typography variant="body1">Police</Typography>
                    </Box>
                    <Divider sx={{ my: 1 }} />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Warning color="error" />
                      <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                        {emergencyNumbers.numbers.fire}
                      </Typography>
                      <Typography variant="body1">Fire</Typography>
                    </Box>
                  </CardContent>
                </Card>

                {emergencyNumbers.note && (
                  <Alert severity="info">
                    <Typography variant="body2">{emergencyNumbers.note}</Typography>
                  </Alert>
                )}
              </>
            ) : null}
          </Box>
        </Paper>
      )}
    </>
  );
};

export default Emergency;
