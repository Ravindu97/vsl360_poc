import React, { useState, useEffect } from 'react';
import { 
  Box, Paper, Typography, Button, TextField, CircularProgress, 
  Alert, Card, CardContent, Chip, IconButton, Divider, 
  Accordion, AccordionSummary, AccordionDetails, List, ListItem, ListItemText,
  Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import { 
  LocalHospital, Close, ExpandMore, Warning, CheckCircle, 
  Medication, HealthAndSafety, Info, ReportProblem, Phone, MyLocation
} from '@mui/icons-material';
import axios from 'axios';

const VirtualDoctor = () => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [symptoms, setSymptoms] = useState('');
  const [duration, setDuration] = useState('');
  const [location, setLocation] = useState('');
  const [diagnosis, setDiagnosis] = useState(null);
  const [commonAilments, setCommonAilments] = useState([]);
  const [error, setError] = useState('');
  const [medicalCenters, setMedicalCenters] = useState([]);
  const [medicalLoading, setMedicalLoading] = useState(false);
  const [showMedicalCenters, setShowMedicalCenters] = useState(false);

  useEffect(() => {
    if (open && commonAilments.length === 0) {
      fetchCommonAilments();
    }
  }, [open]);

  const fetchCommonAilments = async () => {
    try {
      const response = await axios.get('http://localhost:8000/common-ailments');
      setCommonAilments(response.data.ailments);
    } catch (err) {
      console.error('Error fetching common ailments:', err);
    }
  };

  const handleAssessment = async () => {
    if (!symptoms.trim()) {
      setError('Please describe your symptoms');
      return;
    }

    setLoading(true);
    setError('');
    setDiagnosis(null);

    try {
      const response = await axios.post('http://localhost:8000/virtual-doctor', {
        symptoms: symptoms,
        location: location || 'Unknown',
        duration: duration || 'Unknown'
      });

      setDiagnosis(response.data);
    } catch (err) {
      setError('Unable to assess symptoms. Please seek medical attention if symptoms are severe.');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'emergency': return 'error';
      case 'severe': return 'error';
      case 'moderate': return 'warning';
      case 'mild': return 'success';
      default: return 'info';
    }
  };

  const handleQuickSelect = (ailment) => {
    setSymptoms(ailment.symptoms);
  };

  const findNearbyMedicalCenters = () => {
    setMedicalLoading(true);
    setShowMedicalCenters(true);
    setError('');
    
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          console.log('Got location:', position.coords.latitude, position.coords.longitude);
          try {
            const response = await axios.post('http://localhost:8000/medical-support', {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              radius: 5000
            });
            console.log('Medical centers response:', response.data);
            const centers = response.data.medical_centers || [];
            setMedicalCenters(centers);
            if (centers.length === 0) {
              setError('No medical centers found nearby. Google Maps API may have restrictions.');
            }
          } catch (err) {
            console.error('Error fetching medical centers:', err);
            setError('Failed to fetch medical centers. Check backend logs.');
            setMedicalCenters([]);
          } finally {
            setMedicalLoading(false);
          }
        },
        (error) => {
          console.error('Geolocation error:', error);
          setError('Unable to get your location. Please enable location services.');
          setMedicalLoading(false);
          setShowMedicalCenters(false);
        }
      );
    } else {
      setError('Geolocation is not supported by your browser');
      setMedicalLoading(false);
      setShowMedicalCenters(false);
    }
  };

  return (
    <>
      <Button
        variant="contained"
        startIcon={<HealthAndSafety />}
        onClick={() => setOpen(!open)}
        sx={{
          position: 'fixed',
          top: 20,
          right: 20,
          zIndex: 1001,
          bgcolor: '#2e7d32',
          '&:hover': { bgcolor: '#1b5e20' }
        }}
      >
        Health Support
      </Button>

      {open && (
        <Paper
          elevation={8}
          sx={{
            position: 'fixed',
            top: 70,
            right: 20,
            width: 450,
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1001,
            overflow: 'hidden'
          }}
        >
          <Box sx={{ p: 2, bgcolor: '#2e7d32', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HealthAndSafety />
              <Typography variant="h6">Virtual Travel Doctor</Typography>
            </Box>
            <IconButton size="small" onClick={() => setOpen(false)} sx={{ color: 'white' }}>
              <Close />
            </IconButton>
          </Box>

          <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                Get first-aid guidance for common travel health issues. For emergencies, call local emergency services immediately.
              </Typography>
            </Alert>

            <Button
              fullWidth
              variant="contained"
              startIcon={<LocalHospital />}
              onClick={findNearbyMedicalCenters}
              sx={{ mb: 2, bgcolor: '#1976d2', '&:hover': { bgcolor: '#115293' } }}
            >
              Find Nearby Hospitals
            </Button>

            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                  Describe Your Symptoms
                </Typography>
                
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  placeholder="E.g., I have a headache, nausea, and feel dizzy..."
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  size="small"
                  placeholder="How long have you had these symptoms?"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  size="small"
                  placeholder="Your current location (optional)"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  sx={{ mb: 2 }}
                />

                <Button
                  fullWidth
                  variant="contained"
                  onClick={handleAssessment}
                  disabled={loading || !symptoms.trim()}
                  sx={{ bgcolor: '#2e7d32', '&:hover': { bgcolor: '#1b5e20' } }}
                >
                  {loading ? <CircularProgress size={24} /> : 'Get Medical Advice'}
                </Button>
              </CardContent>
            </Card>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            {showMedicalCenters && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                    Nearby Medical Centers
                  </Typography>
                  {medicalLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                      <CircularProgress size={30} />
                    </Box>
                  ) : medicalCenters.length > 0 ? (
                    medicalCenters.map((center, idx) => (
                      <Card key={idx} sx={{ mb: 2, bgcolor: center.is_fallback ? '#fff3e0' : '#f5f5f5' }}>
                        <CardContent>
                          <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>
                            {center.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {center.address}
                          </Typography>
                          {center.rating && (
                            <Chip label={`Rating: ${center.rating}`} size="small" color="warning" sx={{ mr: 1 }} />
                          )}
                          {center.open_now !== undefined && center.open_now !== null && (
                            <Chip 
                              label={center.open_now ? 'Open Now' : 'Closed'} 
                              size="small" 
                              color={center.open_now ? 'success' : 'error'}
                              sx={{ mr: 1 }}
                            />
                          )}
                          {center.phone && (
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              Phone: {center.phone}
                            </Typography>
                          )}
                          {center.google_maps_url && (
                            <Button
                              variant="contained"
                              size="small"
                              startIcon={<MyLocation />}
                              onClick={() => window.open(center.google_maps_url, '_blank')}
                              sx={{ mt: 1, bgcolor: '#4285f4', '&:hover': { bgcolor: '#357ae8' } }}
                            >
                              {center.is_fallback ? 'Open Google Maps' : 'View on Map'}
                            </Button>
                          )}
                        </CardContent>
                      </Card>
                    ))
                  ) : (
                    <Alert severity="info">No medical centers found nearby. Try emergency services.</Alert>
                  )}
                </CardContent>
              </Card>
            )}

            {diagnosis && (
              <Card sx={{ mb: 2, border: diagnosis.emergency_warning === 'true' ? '2px solid red' : 'none' }}>
                <CardContent>
                  {diagnosis.emergency_warning === 'true' && (
                    <Alert severity="error" icon={<Warning />} sx={{ mb: 2 }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        EMERGENCY: Seek immediate medical attention!
                      </Typography>
                    </Alert>
                  )}

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <Chip 
                      label={diagnosis.severity} 
                      color={getSeverityColor(diagnosis.severity)}
                      size="small"
                    />
                    <Typography variant="h6">{diagnosis.condition}</Typography>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Warning color="error" /> Immediate Actions:
                  </Typography>
                  <List dense>
                    {diagnosis.immediate_actions?.map((action, idx) => (
                      <ListItem key={idx}>
                        <ListItemText primary={`${idx + 1}. ${action}`} />
                      </ListItem>
                    ))}
                  </List>

                  <Divider sx={{ my: 2 }} />

                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LocalHospital color="primary" /> First Aid Steps:
                  </Typography>
                  <List dense>
                    {diagnosis.first_aid?.map((step, idx) => (
                      <ListItem key={idx}>
                        <ListItemText primary={`• ${step}`} />
                      </ListItem>
                    ))}
                  </List>

                  <Divider sx={{ my: 2 }} />

                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Medication color="secondary" /> Medications:
                  </Typography>
                  <List dense>
                    {diagnosis.medications?.map((med, idx) => (
                      <ListItem key={idx}>
                        <ListItemText primary={`• ${med}`} />
                      </ListItem>
                    ))}
                  </List>

                  <Divider sx={{ my: 2 }} />

                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      When to Seek Help:
                    </Typography>
                    <Typography variant="body2">{diagnosis.when_to_seek_help}</Typography>
                  </Alert>

                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography variant="subtitle2">Prevention & Travel Tips</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>Prevention:</Typography>
                      {diagnosis.prevention?.map((tip, idx) => (
                        <Typography key={idx} variant="body2" sx={{ mb: 0.5 }}>• {tip}</Typography>
                      ))}
                      <Typography variant="body2" sx={{ fontWeight: 'bold', mt: 2, mb: 1 }}>Travel Tips:</Typography>
                      {diagnosis.travel_tips?.map((tip, idx) => (
                        <Typography key={idx} variant="body2" sx={{ mb: 0.5 }}>• {tip}</Typography>
                      ))}
                    </AccordionDetails>
                  </Accordion>

                  <Alert severity="info" sx={{ mt: 2 }}>
                    <Typography variant="caption">{diagnosis.disclaimer}</Typography>
                  </Alert>
                </CardContent>
              </Card>
            )}

            {!diagnosis && commonAilments.length > 0 && (
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                    Common Travel Health Issues
                  </Typography>
                  {commonAilments.map((ailment, idx) => (
                    <Accordion key={idx}>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>{ailment.name}</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          <strong>Symptoms:</strong> {ailment.symptoms}
                        </Typography>
                        <Typography variant="body2" color="success.main">
                          <strong>Quick Action:</strong> {ailment.quick_action}
                        </Typography>
                        <Button 
                          size="small" 
                          onClick={() => handleQuickSelect(ailment)}
                          sx={{ mt: 1 }}
                        >
                          Get Detailed Advice
                        </Button>
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </CardContent>
              </Card>
            )}
          </Box>
        </Paper>
      )}
    </>
  );
};

export default VirtualDoctor;
