import React from 'react';
import { Stepper as MuiStepper, Step, StepLabel, Box, Typography, Paper } from '@mui/material';

const CustomStepper = ({ steps, currentStep, onStepClick }) => {
  return (
    <Paper 
      elevation={3} 
      sx={{ 
        position: 'fixed',
        left: 0,
        top: 0,
        height: '100vh',
        width: 220,
        overflowY: 'auto',
        bgcolor: '#f5f5f5',
        borderRight: '2px solid #1976d2',
        zIndex: 1000
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" component="h1" gutterBottom sx={{ mb: 3, ml: 0, color: 'primary.main', fontWeight: 'bold' }}>
          🌍 TravelHub
        </Typography>
        <MuiStepper activeStep={currentStep} orientation="vertical">
          {steps.map((label, index) => (
            <Step key={label}>
              <StepLabel 
                sx={{ cursor: 'pointer' }}
                onClick={() => onStepClick && onStepClick(index)}
              >
                <Typography variant="body2">{label}</Typography>
              </StepLabel>
            </Step>
          ))}
        </MuiStepper>
      </Box>
    </Paper>
  );
};

export default CustomStepper;