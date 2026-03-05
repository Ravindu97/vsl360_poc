import React, { useState } from 'react';
import {
    Container,
    Paper,
    TextField,
    Button,
    Box,
    CircularProgress,
    Alert,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
} from '@mui/material';
import axios from 'axios';

const ItineraryTestPage = () => {
    const [testData, setTestData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [tripName, setTripName] = useState('');

    const API_BASE_URL = 'http://localhost:8000/api/v1/test/itinerary';

    // Load test data
    const loadTestData = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await axios.get(`${API_BASE_URL}/test-data`);
            setTestData(response.data);
            setTripName(response.data.trip_name);
        } catch (err) {
            setError('Failed to load test data: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    // Generate and download PDF
    const handleDownloadPDF = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await axios.post(
                `${API_BASE_URL}/generate-pdf`,
                testData || {},
                { responseType: 'blob' }
            );

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${tripName || 'itinerary'}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.parentURL.removeChild(link);
            window.URL.revokeObjectURL(url);

            setSuccess('PDF downloaded successfully!');
            setTimeout(() => setSuccess(null), 3000);
        } catch (err) {
            setError('Failed to generate PDF: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    // Save PDF to server
    const handleSavePDF = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await axios.post(
                `${API_BASE_URL}/save-pdf`,
                testData || {}
            );

            setSuccess(`PDF saved successfully! Location: ${response.data.file_path}`);
            setTimeout(() => setSuccess(null), 5000);
        } catch (err) {
            setError('Failed to save PDF: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    // Update trip data in state
    const handleDataChange = (field, value) => {
        setTestData({
            ...testData,
            [field]: value
        });
    };

    // Update day activity
    const handleActivityChange = (dayIndex, activityIndex, field, value) => {
        const newData = { ...testData };
        newData.days[dayIndex].activities[activityIndex][field] = value;
        setTestData(newData);
    };

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            <Paper sx={{ p: 3, mb: 3 }}>
                <h1>🧪 Itinerary PDF Generator - Test Page</h1>
                <p style={{ color: '#666', marginTop: '10px' }}>
                    This is a separate testing environment. Changes here won't affect the main system.
                </p>
            </Paper>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {success && (
                <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
                    {success}
                </Alert>
            )}

            {!testData ? (
                <Paper sx={{ p: 3, textAlign: 'center' }}>
                    <Button
                        variant="contained"
                        size="large"
                        onClick={loadTestData}
                        disabled={loading}
                    >
                        {loading ? <CircularProgress size={24} /> : 'Load Sample Itinerary Data'}
                    </Button>
                </Paper>
            ) : (
                <>
                    {/* Trip Info Section */}
                    <Paper sx={{ p: 3, mb: 3 }}>
                        <h2>Trip Information</h2>
                        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                            <TextField
                                label="Trip Name"
                                value={tripName}
                                onChange={(e) => {
                                    setTripName(e.target.value);
                                    handleDataChange('trip_name', e.target.value);
                                }}
                                fullWidth
                            />
                            <TextField
                                label="Destination Country"
                                value={testData.destination_country}
                                onChange={(e) => handleDataChange('destination_country', e.target.value)}
                                fullWidth
                            />
                            <TextField
                                label="Start Date"
                                type="date"
                                value={testData.start_date}
                                onChange={(e) => handleDataChange('start_date', e.target.value)}
                                InputLabelProps={{ shrink: true }}
                                fullWidth
                            />
                            <TextField
                                label="End Date"
                                type="date"
                                value={testData.end_date}
                                onChange={(e) => handleDataChange('end_date', e.target.value)}
                                InputLabelProps={{ shrink: true }}
                                fullWidth
                            />
                        </Box>
                    </Paper>

                    {/* Days Section */}
                    <Paper sx={{ p: 3, mb: 3 }}>
                        <h2>Itinerary Days</h2>
                        {testData.days.map((day, dayIndex) => (
                            <Box
                                key={dayIndex}
                                sx={{
                                    mb: 3,
                                    p: 2,
                                    border: '1px solid #ddd',
                                    borderRadius: '8px',
                                    backgroundColor: '#f9f9f9'
                                }}
                            >
                                <h3>Day {day.day}: {day.city}</h3>
                                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
                                    <TextField
                                        label="Day Title"
                                        value={day.title}
                                        onChange={(e) => {
                                            const newData = { ...testData };
                                            newData.days[dayIndex].title = e.target.value;
                                            setTestData(newData);
                                        }}
                                        fullWidth
                                    />
                                    <TextField
                                        label="City"
                                        value={day.city}
                                        onChange={(e) => {
                                            const newData = { ...testData };
                                            newData.days[dayIndex].city = e.target.value;
                                            setTestData(newData);
                                        }}
                                        fullWidth
                                    />
                                </Box>

                                <h4>Activities</h4>
                                {day.activities.map((activity, actIndex) => (
                                    <Box key={actIndex} sx={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 1, mb: 1 }}>
                                        <TextField
                                            label="Time"
                                            value={activity.time}
                                            onChange={(e) => handleActivityChange(dayIndex, actIndex, 'time', e.target.value)}
                                            size="small"
                                        />
                                        <TextField
                                            label="Description"
                                            value={activity.description}
                                            onChange={(e) => handleActivityChange(dayIndex, actIndex, 'description', e.target.value)}
                                            multiline
                                            rows={2}
                                            size="small"
                                        />
                                    </Box>
                                ))}

                                {day.hotel && (
                                    <Box sx={{ mt: 2, p: 2, backgroundColor: '#fff3cd', borderRadius: '4px' }}>
                                        <h4>🏨 Hotel</h4>
                                        <TextField
                                            label="Hotel Name"
                                            value={day.hotel.name}
                                            onChange={(e) => {
                                                const newData = { ...testData };
                                                newData.days[dayIndex].hotel.name = e.target.value;
                                                setTestData(newData);
                                            }}
                                            fullWidth
                                            size="small"
                                            sx={{ mb: 1 }}
                                        />
                                        <TextField
                                            label="Hotel Description"
                                            value={day.hotel.description}
                                            onChange={(e) => {
                                                const newData = { ...testData };
                                                newData.days[dayIndex].hotel.description = e.target.value;
                                                setTestData(newData);
                                            }}
                                            fullWidth
                                            multiline
                                            rows={2}
                                            size="small"
                                        />
                                    </Box>
                                )}
                            </Box>
                        ))}
                    </Paper>

                    {/* Action Buttons */}
                    <Paper sx={{ p: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
                        <Button
                            variant="contained"
                            color="primary"
                            size="large"
                            onClick={handleDownloadPDF}
                            disabled={loading}
                        >
                            {loading ? <CircularProgress size={24} /> : '📥 Download PDF'}
                        </Button>
                        <Button
                            variant="contained"
                            color="success"
                            size="large"
                            onClick={handleSavePDF}
                            disabled={loading}
                        >
                            {loading ? <CircularProgress size={24} /> : '💾 Save PDF to Server'}
                        </Button>
                        <Button
                            variant="outlined"
                            size="large"
                            onClick={() => {
                                setTestData(null);
                                setTripName('');
                            }}
                            disabled={loading}
                        >
                            Clear & Reload
                        </Button>
                    </Paper>
                </>
            )}
        </Container>
    );
};

export default ItineraryTestPage;
