# AI Travel Planner 

A full-stack travel planning application with Python FastAPI backend and React frontend.

## Features

- **Trip Planning**: Select departure/destination countries and travel dates
- **Country Information**: Get detailed information about your destination
- **Flight Options**: View flight suggestions and booking websites
- **Interest-based Recommendations**: Get city suggestions based on your interests
- **Route Optimization**: Optimize travel route using distance-based algorithms
- **Hotel Recommendations**: Get hotel suggestions for each city

## Tech Stack

### Backend
- FastAPI
- LangChain with Groq LLM
- Geopy for geocoding
- Uvicorn server

### Frontend
- React 18
- Material-UI (MUI)
- Axios for API calls

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python run.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

- `GET /countries` - Get list of available countries
- `POST /country-info` - Get destination country information
- `POST /flight-options` - Get flight options and booking websites
- `POST /city-suggestions` - Get city recommendations based on interests
- `POST /optimize-route` - Optimize travel route by distance
- `POST /hotels-restaurants` - Get hotel recommendations

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Follow the step-by-step travel planning process:
   - Enter trip details (countries and dates)
   - Review destination information
   - View flight options
   - Select your travel interests
   - Choose cities and optimize route
   - Get hotel recommendations
   - Prepare for travel with gear and tips
   - Review transportation options
   - Get your final itinerary

## Environment Variables

Make sure to set your Groq API key in the backend `main.py` file or use environment variables for production.