import React, { useState, useRef, useEffect } from 'react';
import {
    Container,
    Paper,
    TextField,
    Button,
    Box,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    CircularProgress,
    Alert,
    IconButton,
    Chip,
} from '@mui/material';
import FolderOpen from '@mui/icons-material/FolderOpen';
import axios from 'axios';

const ItineraryTestPage = () => {
    const [testData, setTestData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [tripName, setTripName] = useState('');
    const [templateOptions, setTemplateOptions] = useState([]);
    const [templateName, setTemplateName] = useState('elegant_classic');
    const [draggedDay, setDraggedDay] = useState(null);

    // File input refs for image browsing
    const coverFileInputRef = useRef(null);
    const dayFileInputRefs = useRef({});

    const API_BASE_URL = 'http://localhost:8000/api/v1/test/itinerary';

    // Load data from sessionStorage on mount
    useEffect(() => {
        const savedData = sessionStorage.getItem('vsl360_itinerary_testdata');
        const savedTripName = sessionStorage.getItem('vsl360_itinerary_tripname');
        const savedTemplate = sessionStorage.getItem('vsl360_itinerary_template');

        if (savedData) {
            try {
                setTestData(JSON.parse(savedData));
                if (savedTripName) setTripName(savedTripName);
                if (savedTemplate) setTemplateName(savedTemplate);
            } catch (err) {
                console.error('Error loading saved data:', err);
                sessionStorage.removeItem('vsl360_itinerary_testdata');
            }
        }
    }, []); // Run only on mount

    // Save data to sessionStorage whenever testData changes
    useEffect(() => {
        if (testData) {
            sessionStorage.setItem('vsl360_itinerary_testdata', JSON.stringify(testData));
            sessionStorage.setItem('vsl360_itinerary_tripname', tripName);
            sessionStorage.setItem('vsl360_itinerary_template', templateName);
        }
    }, [testData, tripName, templateName]);

    const loadTemplates = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/templates`);
            const options = response.data.templates || [];
            setTemplateOptions(options);
            const selected = (testData && testData.template_name) || response.data.default || 'elegant_classic';
            setTemplateName(selected);
        } catch (err) {
            setTemplateOptions([]);
        }
    };

    // Normalize day object to ensure all fields are defined (not null/undefined)
    const normalizeDayData = (day) => {
        return {
            day: day.day || 1,
            title: day.title || '',
            city: day.city || '',
            image_path: day.image_path || '',
            image_url: day.image_url || '',
            activities: (day.activities || []).map(act => ({
                time: act.time || '',
                description: act.description || ''
            })),
            travel_time: day.travel_time || '',
            distance: day.distance || '',
            overnight_city: day.overnight_city || '',
            optional: day.optional || '',
            hotel: day.hotel || undefined
        };
    };

    // Load test data
    const loadTestData = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await axios.get(`${API_BASE_URL}/test-data`);
            const normalizedData = {
                ...response.data,
                days: (response.data.days || []).map(normalizeDayData)
            };
            setTestData(normalizedData);
            setTripName(response.data.trip_name);
            setTemplateName(response.data.template_name || 'elegant_classic');
            await loadTemplates();
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

            const payload = {
                ...(testData || {}),
                template_name: templateName,
            };
            const response = await axios.post(
                `${API_BASE_URL}/generate-pdf`,
                payload,
                { responseType: 'blob' }
            );

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${tripName || 'itinerary'}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);

            setSuccess('PDF downloaded successfully!');
            setTimeout(() => setSuccess(null), 3000);
        } catch (err) {
            setError('Failed to generate PDF: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    // Save PDF to server - REMOVED
    // Functionality removed as per user request

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

    // Add a new day at specific position
    const handleAddDay = (position = null) => {
        const insertIndex = position !== null ? position : testData.days.length;
        const newDay = normalizeDayData({
            day: insertIndex + 1,
            title: `Day ${insertIndex + 1}`,
            city: '',
            image_path: '',
            image_url: '',
            activities: [{ time: '', description: '' }],
            travel_time: '',
            distance: '',
            overnight_city: '',
            optional: ''
        });
        const newData = { ...testData };
        newData.days.splice(insertIndex, 0, newDay);
        // Renumber all days
        newData.days.forEach((day, idx) => {
            day.day = idx + 1;
        });
        newData.total_days = newData.days.length;
        setTestData(newData);
    };

    // Remove a day
    const handleRemoveDay = (dayIndex) => {
        const newData = { ...testData };
        newData.days.splice(dayIndex, 1);
        // Renumber days
        newData.days.forEach((day, idx) => {
            day.day = idx + 1;
        });
        newData.total_days = newData.days.length;
        setTestData(newData);
    };

    // Add an activity to a day
    const handleAddActivity = (dayIndex) => {
        const newData = { ...testData };
        newData.days[dayIndex].activities.push({ time: '', description: '' });
        setTestData(newData);
    };

    // Remove an activity from a day
    const handleRemoveActivity = (dayIndex, activityIndex) => {
        const newData = { ...testData };
        newData.days[dayIndex].activities.splice(activityIndex, 1);
        setTestData(newData);
    };

    // File handling for image browsing
    const handleBrowseImage = (fieldType, dayIndex = null) => {
        if (fieldType === 'cover') {
            coverFileInputRef.current?.click();
        } else if (fieldType === 'day') {
            dayFileInputRefs.current[dayIndex]?.click();
        }
    };

    const handleFileSelect = (e, fieldType, dayIndex = null) => {
        const file = e.target.files?.[0];
        if (file) {
            const filename = file.name;
            if (fieldType === 'cover') {
                handleDataChange('cover_image_path', filename);
            } else if (fieldType === 'day') {
                const newData = { ...testData };
                newData.days[dayIndex].image_path = filename;
                setTestData(newData);
            }
        }
        // Reset file input for reuse
        e.target.value = '';
    };

    // Drag and drop handlers for day reordering
    const handleDragStart = (dayIndex) => {
        setDraggedDay(dayIndex);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
    };

    const handleDrop = (targetIndex) => {
        if (draggedDay === null || draggedDay === targetIndex) {
            setDraggedDay(null);
            return;
        }

        const newData = { ...testData };
        const draggedDayObj = newData.days[draggedDay];
        newData.days.splice(draggedDay, 1);
        newData.days.splice(targetIndex, 0, draggedDayObj);

        // Renumber all days
        newData.days.forEach((day, idx) => {
            day.day = idx + 1;
        });

        setTestData(newData);
        setDraggedDay(null);
    };

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            <Paper sx={{ p: 4, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', borderRadius: 2 }}>
                <Box>
                    <h1 style={{ margin: '0 0 8px 0', fontSize: '2rem', fontWeight: 'bold' }}>VSL360 Itinerary Generator</h1>
                    <p style={{ margin: '0 0 12px 0', fontSize: '0.95rem', opacity: 0.9 }}>
                        Create and customize beautiful travel itinerary PDFs with drag-and-drop day management and live template switching.
                    </p>
                    <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
                        <Chip label="Template-based" size="small" variant="outlined" sx={{ color: 'white', borderColor: 'white' }} />
                        <Chip label="Drag to Reorder" size="small" variant="outlined" sx={{ color: 'white', borderColor: 'white' }} />
                    </Box>
                </Box>
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
                        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
                            <FormControl fullWidth>
                                <InputLabel id="template-label">Template</InputLabel>
                                <Select
                                    labelId="template-label"
                                    label="Template"
                                    value={templateName}
                                    onChange={(e) => {
                                        setTemplateName(e.target.value);
                                        handleDataChange('template_name', e.target.value);
                                    }}
                                >
                                    {(templateOptions.length ? templateOptions : [{ id: 'elegant_classic', label: 'Elegant Classic' }]).map((item) => (
                                        <MenuItem key={item.id} value={item.id}>
                                            {item.label || item.id}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            <TextField
                                label="Trip Name"
                                value={tripName}
                                onChange={(e) => {
                                    setTripName(e.target.value);
                                    handleDataChange('trip_name', e.target.value);
                                }}
                                fullWidth
                            />
                        </Box>
                        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
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
                            <Button
                                variant="outlined"
                                color="primary"
                                size="small"
                                fullWidth
                                onClick={() => handleBrowseImage('cover')}
                                startIcon={<FolderOpen />}
                            >
                                Select Cover Image
                            </Button>
                            {testData.cover_image_path && (
                                <Box sx={{ mt: 1, p: 1, backgroundColor: '#e8f5e9', borderRadius: 1, fontSize: '0.85rem', color: '#2e7d32' }}>
                                    ✓ {testData.cover_image_path}
                                </Box>
                            )}
                        </Box>
                    </Paper>

                    {/* Days Section */}
                    <Paper sx={{ p: 3, mb: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <h2>Itinerary Days</h2>
                            <Button variant="contained" color="success" onClick={handleAddDay}>
                                + Add Day
                            </Button>
                        </Box>
                        {testData.days.map((day, dayIndex) => (
                            <React.Fragment key={dayIndex}>
                                <Box
                                    draggable
                                    onDragStart={() => handleDragStart(dayIndex)}
                                    onDragOver={handleDragOver}
                                    onDrop={() => handleDrop(dayIndex)}
                                    sx={{
                                        mb: 3,
                                        p: 2,
                                        border: draggedDay === dayIndex ? '3px solid #1976d2' : '1px solid #ddd',
                                        borderRadius: '8px',
                                        backgroundColor: draggedDay === dayIndex ? '#e8f4ff' : '#f9f9f9',
                                        cursor: 'move',
                                        transition: 'all 0.2s ease',
                                        opacity: draggedDay === dayIndex ? 0.7 : 1
                                    }}
                                >
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexGrow: 1 }}>
                                        <Chip 
                                            label={`Day ${day.day}`} 
                                            color="primary" 
                                            variant="outlined"
                                            sx={{ fontWeight: 'bold', fontSize: '0.95rem' }}
                                        />
                                        <TextField
                                            label="Day Title"
                                            value={day.title}
                                            onChange={(e) => {
                                                const newData = { ...testData };
                                                newData.days[dayIndex].title = e.target.value;
                                                setTestData(newData);
                                            }}
                                            fullWidth
                                            size="small"
                                            sx={{ maxWidth: '300px' }}
                                        />
                                    </Box>
                                    <Button
                                        variant="outlined"
                                        color="error"
                                        size="small"
                                        onClick={() => handleRemoveDay(dayIndex)}
                                        sx={{ flexShrink: 0 }}
                                    >
                                        Remove Day
                                    </Button>
                                </Box>
                                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
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
                                    <Button
                                        variant="outlined"
                                        color="primary"
                                        size="small"
                                        fullWidth
                                        onClick={() => handleBrowseImage('day', dayIndex)}
                                        startIcon={<FolderOpen />}
                                        sx={{ mb: 1 }}
                                    >
                                        Select Day Image
                                    </Button>
                                    {day.image_path && (
                                        <Box sx={{ mb: 1, p: 1, backgroundColor: '#e8f5e9', borderRadius: 1, fontSize: '0.85rem', color: '#2e7d32' }}>
                                            ✓ {day.image_path}
                                        </Box>
                                    )}
                                </Box>

                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                    <h4>Activities</h4>
                                    <Button variant="outlined" color="primary" size="small" onClick={() => handleAddActivity(dayIndex)}>
                                        + Add Activity
                                    </Button>
                                </Box>
                                {day.activities.map((activity, actIndex) => (
                                    <Box key={actIndex} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'flex-start' }}>
                                        <Box sx={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 1, flexGrow: 1 }}>
                                            <TextField
                                                label="Time"
                                                type="time"
                                                value={activity.time}
                                                onChange={(e) => handleActivityChange(dayIndex, actIndex, 'time', e.target.value)}
                                                size="small"
                                                InputLabelProps={{ shrink: true }}
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
                                        <Button
                                            variant="outlined"
                                            color="error"
                                            size="small"
                                            onClick={() => handleRemoveActivity(dayIndex, actIndex)}
                                            sx={{ mt: 0.5 }}
                                        >
                                            ✕
                                        </Button>
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
                                {dayIndex < testData.days.length - 1 && (
                                    <Box sx={{ display: 'flex', justifyContent: 'center', my: 1 }}>
                                        <Button
                                            variant="text"
                                            size="small"
                                            onClick={() => handleAddDay(dayIndex + 1)}
                                            sx={{ textTransform: 'none', color: '#999' }}
                                        >
                                            + Insert day after
                                        </Button>
                                    </Box>
                                )}
                            </React.Fragment>
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
                            variant="outlined"
                            size="large"
                            onClick={() => {
                                setTestData(null);
                                setTripName('');
                                setTemplateName('elegant_classic');
                                // Clear sessionStorage
                                sessionStorage.removeItem('vsl360_itinerary_testdata');
                                sessionStorage.removeItem('vsl360_itinerary_tripname');
                                sessionStorage.removeItem('vsl360_itinerary_template');
                            }}
                            disabled={loading}
                        >
                            Clear & Reload
                        </Button>
                    </Paper>
                </>
            )}
            
            {/* Hidden file inputs for image browsing */}
            <input
                ref={coverFileInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => handleFileSelect(e, 'cover')}
            />
            {testData && testData.days.map((_, dayIndex) => (
                <input
                    key={`day-file-${dayIndex}`}
                    ref={(el) => {
                        if (el) dayFileInputRefs.current[dayIndex] = el;
                    }}
                    type="file"
                    accept="image/*"
                    style={{ display: 'none' }}
                    onChange={(e) => handleFileSelect(e, 'day', dayIndex)}
                />
            ))}
        </Container>
    );
};

export default ItineraryTestPage;
