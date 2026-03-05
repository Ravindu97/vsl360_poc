# Integration Instructions for Itinerary PDF Generator (Test Endpoints)

## Backend Setup

### Step 1: Update requirements.txt
Add these packages to `backend/requirements.txt`:
```
reportlab==4.0.9
```

Then install:
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Add Itinerary Routes to main.py
At the top of `backend/main.py`, add:

```python
from itinerary_routes import router as itinerary_router

# ... other imports and setup code ...

# Include the itinerary test routes (separate test endpoints)
app.include_router(itinerary_router)
```

**Location:** Add this AFTER all other route inclusions, before `if __name__ == "__main__":`

Example of where to place it:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routes...
@app.get("/countries")
async def get_countries():
    ...

# ADD THE NEW LINE HERE:
from itinerary_routes import router as itinerary_router
app.include_router(itinerary_router)

# Continue with rest of main.py...
```

### Step 3: Verify Backend Files
Make sure these files exist in `backend/`:
- ✅ `itinerary_generator.py` - PDF generation logic using ReportLab
- ✅ `itinerary_routes.py` - Test endpoints

Note: `itinerary_template.html` is no longer needed (ReportLab generates PDFs programmatically)

---

## Frontend Setup

### Step 1: Add Test Route to App.js
In `frontend/src/App.js`, add a new route:

```javascript
import ItineraryTestPage from './pages/ItineraryTestPage';

// ... inside your Router/Routes component:

<Routes>
    {/* Existing routes */}
    
    {/* Add this new test route */}
    <Route path="/test/itinerary-generator" element={<ItineraryTestPage />} />
    
    {/* More routes... */}
</Routes>
```

### Step 2: Add Navigation Link (Optional)
Add a link in your navigation or footer to access the test page:

```javascript
<Link to="/test/itinerary-generator">Itinerary Generator (Test)</Link>
```

### Step 3: Verify Frontend Files
Make sure this file exists:
- ✅ `frontend/src/pages/ItineraryTestPage.js` - Test UI component

---

## Testing the Implementation

### 1. Start Backend
```bash
cd backend
source venv/bin/activate
python main.py
```
Backend will run on: `http://localhost:8000`

### 2. Start Frontend
```bash
cd frontend
npm start
```
Frontend will run on: `http://localhost:3000`

### 3. Access Test Page
Navigate to: `http://localhost:3000/test/itinerary-generator`

### 4. Test the Features
- Click "Load Sample Itinerary Data"
- Edit trip details as needed
- Click "Download PDF" to download
- Click "Save PDF to Server" to save on backend
- Check `backend/itineraries/` folder for saved PDFs

---

## API Endpoints (Test Only)

All endpoints are prefixed with `/api/v1/test/itinerary` to keep them separate:

### GET /api/v1/test/itinerary/test-data
Returns sample itinerary data for testing

### POST /api/v1/test/itinerary/generate-pdf
Generates and downloads PDF

**Request:**
```json
{
    "trip_name": "8 Days Sri Lanka Tour",
    "destination_country": "Sri Lanka",
    "start_date": "2024-03-15",
    "end_date": "2024-03-23",
    "days": [
        {
            "day": 1,
            "title": "Arrival",
            "city": "Colombo",
            "activities": [
                {
                    "time": "2:00 PM",
                    "description": "Arrive at airport"
                }
            ],
            "hotel": {
                "name": "Hotel Name",
                "description": "Hotel description"
            }
        }
    ]
}
```

### POST /api/v1/test/itinerary/save-pdf
Generates and saves PDF to server

---

## File Structure

```
backend/
├── main.py                    (update to include router)
├── itinerary_generator.py     (NEW - PDF generation with ReportLab)
├── itinerary_routes.py        (NEW - Test endpoints)
├── requirements.txt           (update to add reportlab)
└── itineraries/               (auto-created for saved PDFs)

frontend/
├── src/
│   ├── App.js                 (update to add test route)
│   ├── pages/
│   │   └── ItineraryTestPage.js  (NEW - Test UI)
│   └── ...
└── ...
```

---

## Key Design Decisions

✅ **Isolated Test Endpoints** - Uses `/api/v1/test/` prefix to keep separate from main system
✅ **No Interference** - Changes here won't affect existing functionality
✅ **Separate Route** - Test page at `/test/itinerary-generator` 
✅ **Reusable Template** - Beautiful, professional PDF design
✅ **Both Download & Save Options** - User choice for PDF delivery

---

## Troubleshooting

### PDF generation fails
- Verify ReportLab is installed: `pip show reportlab`
- Check if `itinerary_routes.py` has the correct import statement
- Check console for detailed error messages

### Endpoints not found (404)
- Make sure `app.include_router(itinerary_router)` is added to `main.py`
- Verify file names match (imports are case-sensitive)

### Frontend won't connect to backend
- Ensure backend is running on `http://localhost:8000`
- Check CORS middleware is enabled in `main.py`
- Check browser console for errors

### PDFs not saving
- Verify `backend/itineraries/` directory exists (auto-created)
- Check file permissions

---

## Next Steps (Integration)

Once testing is complete and you're happy with the design:
1. Move PDF generation logic into main trip planning flow
2. Integrate with existing backend endpoints
3. Add to final itinerary generation step
4. Remove the `/test/` routes when ready

