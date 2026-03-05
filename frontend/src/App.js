import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import UserInfo from './components/UserInfo';
import TripDetails from './components/TripDetails';
import CountryInfo from './components/CountryInfo';
import FlightOptions from './components/FlightOptions';
import Interests from './components/Interests';
import CitySelection from './components/CitySelection';
import HotelsRestaurants from './components/HotelsRestaurants';
import TravelPreparation from './components/TravelPreparation';
import TransportationOptions from './components/TransportationOptions';
import FinalItinerary from './components/FinalItinerary';
import CustomStepper from './components/Stepper';
import Chatbot from './components/Chatbot';
import VirtualDoctor from './components/VirtualDoctor';
import Emergency from './components/Emergency';
import ItineraryTestPage from './pages/ItineraryTestPage';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const [tripData, setTripData] = useState({
    full_name: '',
    country: '',
    mobile_no: '',
    email: '',
    departure_country: '',
    arrival_country: '',
    start_date: '',
    end_date: '',
    interests: [],
    selected_cities: [],
    optimized_cities: [],
    city_schedule: {}
  });

  const steps = [
    'User Info',
    'Trip Details',
    'Country Info',
    'Flight Options',
    'Your Interests',
    'City Selection',
    'Hotels & Restaurants',
    'Travel Preparation',
    'Transportation',
    'Final Itinerary'
  ];

  const updateTripData = (newData) => {
    setTripData(prev => ({ ...prev, ...newData }));
  };

  const nextStep = () => {
    setCurrentStep(prev => Math.min(prev + 1, steps.length - 1));
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  const goToStep = (stepIndex) => {
    setCurrentStep(stepIndex);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <UserInfo tripData={tripData} updateTripData={updateTripData} nextStep={nextStep} />;
      case 1:
        return <TripDetails tripData={tripData} updateTripData={updateTripData} nextStep={nextStep} prevStep={prevStep} />;
      case 2:
        return <CountryInfo tripData={tripData} updateTripData={updateTripData} nextStep={nextStep} prevStep={prevStep} />;
      case 3:
        return <FlightOptions tripData={tripData} updateTripData={updateTripData} nextStep={nextStep} prevStep={prevStep} />;
      case 4:
        return <Interests tripData={tripData} updateTripData={updateTripData} nextStep={nextStep} prevStep={prevStep} />;
      case 5:
        return <CitySelection tripData={tripData} updateTripData={updateTripData} nextStep={nextStep} prevStep={prevStep} />;
      case 6:
        return <HotelsRestaurants tripData={tripData} updateTripData={updateTripData} nextStep={nextStep} prevStep={prevStep} />;
      case 7:
        return <TravelPreparation tripData={tripData} updateTripData={updateTripData} nextStep={nextStep} prevStep={prevStep} />;
      case 8:
        return <TransportationOptions tripData={tripData} updateTripData={updateTripData} nextStep={nextStep} prevStep={prevStep} />;
      case 9:
        return <FinalItinerary tripData={tripData} updateTripData={updateTripData} prevStep={prevStep} />;
      default:
        return <UserInfo tripData={tripData} updateTripData={updateTripData} nextStep={nextStep} />;
    }
  };

  const MainApp = () => (
    <Box sx={{ display: 'flex' }}>
      <CustomStepper steps={steps} currentStep={currentStep} onStepClick={goToStep} />
      <Box sx={{ flexGrow: 1, ml: '220px', p: 4 }}>
        {renderStep()}
      </Box>
    </Box>
  );

  return (
    <Router>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Routes>
          <Route path="/" element={<><MainApp /><Chatbot /><VirtualDoctor /><Emergency /></>} />
          <Route path="/test/itinerary-generator" element={<ItineraryTestPage />} />
        </Routes>
      </ThemeProvider>
    </Router>
  );
}

export default App;