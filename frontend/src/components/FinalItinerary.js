import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Button, Box, CircularProgress, Alert, Paper, Divider, Chip } from '@mui/material';
import { Event, Print, Download, AttachMoney } from '@mui/icons-material';
import axios from 'axios';

const FinalItinerary = ({ tripData, prevStep }) => {
  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (tripData.optimized_cities && tripData.optimized_cities.length > 0 && !itinerary) {
      fetchItinerary();
    }
  }, [tripData]);

  const fetchItinerary = async () => {
    setLoading(true);
    setError('');
    try {
      console.log('Fetching itinerary with data:', {
        country: tripData.arrival_country,
        start_date: tripData.start_date,
        end_date: tripData.end_date,
        city_schedule: tripData.city_schedule
      });
      
      const response = await axios.post('http://localhost:8000/final-itinerary', {
        country: tripData.arrival_country,
        start_date: tripData.start_date,
        end_date: tripData.end_date,
        city_date_distribution: tripData.city_schedule || {},
        hotels: tripData.hotels || '',
        transportation: tripData.transportation || ''
      });
      
      console.log('Itinerary response:', response.data);
      setItinerary(response.data);
    } catch (err) {
      console.error('Itinerary error:', err.response?.data || err.message);
      setError(`Failed to generate final itinerary: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownload = async () => {
    try {
      const { jsPDF } = await import('jspdf');
      const pdf = new jsPDF();
      let yPos = 20;
      
      // Header - Company Info
      pdf.setFontSize(10);
      pdf.setTextColor(100, 100, 100);
      pdf.text('PCS Techno Pvt Ltd', 20, yPos);
      pdf.text('Travel Web', 20, yPos + 5);
      
      // Generated Date/Time
      const now = new Date();
      const dateTime = now.toLocaleString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      pdf.text(`Generated: ${dateTime}`, 150, yPos, { align: 'right' });
      yPos += 15;
      
      // Title
      pdf.setFontSize(20);
      pdf.setTextColor(25, 118, 210);
      pdf.text(`${tripData.arrival_country} Travel Itinerary`, 105, yPos, { align: 'center' });
      yPos += 15;
      
      // Total Budget
      if (itinerary?.total_estimated_budget) {
        pdf.setFontSize(14);
        pdf.setTextColor(76, 175, 80);
        pdf.text(`Total Budget: ${itinerary.total_estimated_budget}`, 105, yPos, { align: 'center' });
        yPos += 15;
      }
      
      // Itinerary Days
      itinerary?.itinerary?.forEach((day) => {
        if (yPos > 250) {
          pdf.addPage();
          yPos = 20;
        }
        
        pdf.setFontSize(12);
        pdf.setTextColor(0, 0, 0);
        pdf.text(`Day ${day.day} - ${day.date} - ${day.city}`, 20, yPos);
        yPos += 7;
        
        if (day.estimated_budget) {
          pdf.setFontSize(10);
          pdf.setTextColor(76, 175, 80);
          pdf.text(`Budget: ${day.estimated_budget}`, 20, yPos);
          yPos += 7;
        }
        
        pdf.setFontSize(9);
        pdf.setTextColor(100, 100, 100);
        
        const sections = [
          { label: 'Morning', text: day.morning },
          { label: 'Lunch', text: day.lunch },
          { label: 'Afternoon', text: day.afternoon },
          { label: 'Dinner', text: day.dinner },
          { label: 'Evening', text: day.evening }
        ];
        
        sections.forEach(section => {
          if (section.text) {
            const lines = pdf.splitTextToSize(`${section.label}: ${section.text}`, 170);
            lines.forEach(line => {
              if (yPos > 280) {
                pdf.addPage();
                yPos = 20;
              }
              pdf.text(line, 20, yPos);
              yPos += 5;
            });
          }
        });
        
        yPos += 5;
      });
      
      // Summary
      if (itinerary?.summary) {
        if (yPos > 240) {
          pdf.addPage();
          yPos = 20;
        }
        pdf.setFontSize(12);
        pdf.setTextColor(25, 118, 210);
        pdf.text('Trip Summary', 20, yPos);
        yPos += 7;
        pdf.setFontSize(9);
        pdf.setTextColor(0, 0, 0);
        const summaryLines = pdf.splitTextToSize(itinerary.summary, 170);
        summaryLines.forEach(line => {
          if (yPos > 280) {
            pdf.addPage();
            yPos = 20;
          }
          pdf.text(line, 20, yPos);
          yPos += 5;
        });
      }
      
      pdf.save(`${tripData.arrival_country}_itinerary.pdf`);
    } catch (error) {
      console.error('PDF generation failed:', error);
      alert('Failed to generate PDF. Please try again.');
    }
  };

  const renderDayCard = (day, index) => (
    <Paper key={index} elevation={2} sx={{ p: 3, mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Event color="primary" sx={{ mr: 1 }} />
          <Typography variant="h5" color="primary.main">
            Day {day.day} - {day.date}
          </Typography>
        </Box>
        {day.estimated_budget && (
          <Box sx={{ bgcolor: '#e8f5e9', px: 2, py: 1, borderRadius: 2 }}>
            <Typography variant="subtitle1" color="success.main" fontWeight="bold">
              💰 {day.estimated_budget}
            </Typography>
          </Box>
        )}
      </Box>
      
      {day.city && (
        <Typography variant="h6" sx={{ mb: 1 }}>
          📍 {day.city}
        </Typography>
      )}
      
      {day.weather && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          🌤️ Weather: {day.weather}
        </Typography>
      )}
      
      {day.hotel && (
        <Typography variant="body2" sx={{ mb: 1 }}>
          🏨 <strong>Hotel:</strong> {day.hotel}
        </Typography>
      )}
      
      <Divider sx={{ my: 2 }} />
      
      {day.morning && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" color="primary.main">🌅 Morning</Typography>
          <Typography variant="body2">{day.morning}</Typography>
        </Box>
      )}
      
      {day.lunch && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" color="primary.main">🍽️ Lunch</Typography>
          <Typography variant="body2">{day.lunch}</Typography>
        </Box>
      )}
      
      {day.afternoon && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" color="primary.main">☀️ Afternoon</Typography>
          <Typography variant="body2">{day.afternoon}</Typography>
        </Box>
      )}
      
      {day.dinner && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" color="primary.main">🌙 Dinner</Typography>
          <Typography variant="body2">{day.dinner}</Typography>
        </Box>
      )}
      
      {day.evening && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" color="primary.main">🌃 Evening</Typography>
          <Typography variant="body2">{day.evening}</Typography>
        </Box>
      )}
      
      {day.travel && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" color="info.main">
            🚗 Travel: {day.travel}
          </Typography>
        </Box>
      )}
    </Paper>
  );

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Event sx={{ mr: 2, fontSize: 30 }} />
            <Typography variant="h4" component="h2">
              Final Itinerary
            </Typography>
          </Box>
          
          {itinerary && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button variant="outlined" startIcon={<Print />} onClick={handlePrint}>
                Print
              </Button>
              <Button variant="outlined" startIcon={<Download />} onClick={handleDownload}>
                Download PDF
              </Button>
            </Box>
          )}
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {itinerary?.total_estimated_budget && (
          <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: '#f0f7ff', borderRadius: 2, border: '2px solid #1976d2' }}>
            <AttachMoney sx={{ fontSize: 40, color: 'success.main' }} />
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Estimated Total Trip Budget
              </Typography>
              <Typography variant="h4" color="success.main" fontWeight="bold">
                {itinerary.total_estimated_budget}
              </Typography>
            </Box>
          </Box>
        )}

        {itinerary?.itinerary?.length > 0 ? (
          <Box>
            <Typography variant="h6" sx={{ mb: 2, color: 'text.secondary' }}>
              Your complete day-by-day travel itinerary for {tripData.arrival_country}
            </Typography>
            {itinerary.itinerary.map((day, index) => renderDayCard(day, index))}
            
            {itinerary.summary && (
              <Paper elevation={3} sx={{ p: 3, mt: 3, bgcolor: '#f0f7ff' }}>
                <Typography variant="h6" color="primary.main" sx={{ mb: 2 }}>
                  📋 Trip Summary
                </Typography>
                <Typography variant="body1">{itinerary.summary}</Typography>
              </Paper>
            )}
          </Box>
        ) : null}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mt: 4 }}>
          <Button variant="outlined" onClick={prevStep}>
            Back
          </Button>
          <Button variant="contained" color="success" disabled>
            Trip Planning Complete! 🎉
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default FinalItinerary;