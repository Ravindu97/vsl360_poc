from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from itinerary_generator import generate_itinerary_pdf

router = APIRouter(
    prefix="/api/v1/test/itinerary",
    tags=["Itinerary Testing"]
)

class ActivitySchema(BaseModel):
    time: str
    description: str

class HotelSchema(BaseModel):
    name: str
    description: str

class DaySchema(BaseModel):
    day: int
    title: str
    city: str
    activities: List[ActivitySchema]
    hotel: Optional[HotelSchema] = None

class ItineraryRequestSchema(BaseModel):
    trip_name: str
    destination_country: str
    start_date: str
    end_date: str
    days: List[DaySchema]

@router.post("/generate-pdf")
def generate_itinerary(request: ItineraryRequestSchema):
    """
    TEST ENDPOINT: Generate and download a beautiful PDF itinerary
    This is for testing purposes and won't affect the main system
    """
    try:
        trip_data = request.dict()
        pdf_path = generate_itinerary_pdf(trip_data)
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"{request.trip_name}.pdf"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating PDF: {str(e)}"
        )

@router.post("/save-pdf")
def save_itinerary(request: ItineraryRequestSchema):
    """
    TEST ENDPOINT: Generate and save PDF, return file path
    This is for testing purposes and won't affect the main system
    """
    try:
        trip_data = request.dict()
        pdf_path = generate_itinerary_pdf(trip_data)
        
        return {
            "success": True,
            "file_path": pdf_path,
            "message": f"Itinerary saved successfully",
            "trip_name": request.trip_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error saving PDF: {str(e)}"
        )

@router.get("/test-data")
def get_test_data():
    """
    TEST ENDPOINT: Get sample itinerary data for testing with enhanced fields
    """
    return {
        "trip_name": "8 Days Enchanting Sri Lanka Tour",
        "destination_country": "Sri Lanka",
        "start_date": "March 15, 2024",
        "end_date": "March 23, 2024",
        "days": [
            {
                "day": 1,
                "title": "Arrival in Colombo",
                "city": "Colombo",
                "activities": [
                    {
                        "time": "2:00 PM",
                        "description": "Arrive at Bandaranaike International Airport, meet and greet by tour representative"
                    },
                    {
                        "time": "3:30 PM",
                        "description": "Transfer to hotel in Colombo (approx. 30 minutes)"
                    },
                    {
                        "time": "6:00 PM",
                        "description": "Check-in and relax at the hotel"
                    },
                    {
                        "time": "7:30 PM",
                        "description": "Welcome dinner at hotel with traditional Sri Lankan cuisine"
                    }
                ],
                "meals": {
                    "dinner": "Traditional Sri Lankan welcome dinner at hotel restaurant"
                },
                "hotel": {
                    "name": "The Kingsbury Hotel",
                    "description": "5-star luxury hotel in Colombo with stunning ocean views, spa facilities, and rooftop pool",
                    "rating": 5
                }
            },
            {
                "day": 2,
                "title": "Colombo City Exploration",
                "city": "Colombo",
                "activities": [
                    {
                        "time": "8:00 AM",
                        "description": "Buffet breakfast at hotel"
                    },
                    {
                        "time": "10:00 AM",
                        "description": "Guided city tour: Visit Galle Face Green, Independence Square, and colonial architecture"
                    },
                    {
                        "time": "12:30 PM",
                        "description": "Lunch at Ministry of Crab - famous seafood restaurant"
                    },
                    {
                        "time": "3:00 PM",
                        "description": "Visit Colombo National Museum and Gangaramaya Temple"
                    },
                    {
                        "time": "6:00 PM",
                        "description": "Shopping at Barefoot Gallery and Odel"
                    }
                ],
                "meals": {
                    "breakfast": "International buffet at hotel",
                    "lunch": "Seafood specialties at Ministry of Crab",
                    "dinner": "Dinner at your leisure (recommendations provided)"
                },
                "hotel": {
                    "name": "The Kingsbury Hotel",
                    "description": "5-star luxury hotel in Colombo with stunning ocean views",
                    "rating": 5
                }
            },
            {
                "day": 3,
                "title": "Journey to Kandy - Cultural Capital",
                "city": "Kandy",
                "activities": [
                    {
                        "time": "7:00 AM",
                        "description": "Early breakfast and check-out"
                    },
                    {
                        "time": "8:00 AM",
                        "description": "Depart for Kandy via scenic route (3.5 hours)"
                    },
                    {
                        "time": "10:30 AM",
                        "description": "En-route visit: Pinnawala Elephant Orphanage"
                    },
                    {
                        "time": "12:30 PM",
                        "description": "Arrive in Kandy, lunch at local restaurant"
                    },
                    {
                        "time": "3:00 PM",
                        "description": "Visit Temple of the Sacred Tooth Relic (UNESCO World Heritage Site)"
                    },
                    {
                        "time": "5:30 PM",
                        "description": "Sunset walk around scenic Kandy Lake"
                    },
                    {
                        "time": "7:00 PM",
                        "description": "Traditional Kandyan dance performance"
                    }
                ],
                "meals": {
                    "breakfast": "Hotel breakfast",
                    "lunch": "Traditional Sri Lankan rice and curry",
                    "dinner": "Dinner at hotel with lake views"
                },
                "hotel": {
                    "name": "The Kandy House",
                    "description": "Luxury boutique hotel with panoramic views of Kandy Lake and surrounding hills",
                    "rating": 5
                }
            },
            {
                "day": 4,
                "title": "Kandy & Peradeniya Gardens",
                "city": "Kandy",
                "activities": [
                    {
                        "time": "8:30 AM",
                        "description": "Breakfast at hotel"
                    },
                    {
                        "time": "10:00 AM",
                        "description": "Visit Royal Botanical Gardens at Peradeniya - 147 acres of tropical paradise"
                    },
                    {
                        "time": "12:30 PM",
                        "description": "Lunch at garden restaurant"
                    },
                    {
                        "time": "2:30 PM",
                        "description": "Visit Ceylon Tea Museum and tea plantation"
                    },
                    {
                        "time": "4:00 PM",
                        "description": "Tea tasting experience with scenic views"
                    },
                    {
                        "time": "6:00 PM",
                        "description": "Explore Kandy's local markets and craft shops"
                    }
                ],
                "meals": {
                    "breakfast": "Continental breakfast at hotel",
                    "lunch": "Garden restaurant with local & international cuisine",
                    "dinner": "Authentic Sri Lankan curry dinner"
                },
                "hotel": {
                    "name": "The Kandy House",
                    "description": "Luxury boutique hotel with panoramic views",
                    "rating": 5
                }
            },
            {
                "day": 5,
                "title": "Scenic Train to Nuwara Eliya",
                "city": "Nuwara Eliya",
                "activities": [
                    {
                        "time": "7:00 AM",
                        "description": "Early breakfast at hotel"
                    },
                    {
                        "time": "8:30 AM",
                        "description": "Train journey from Kandy to Nuwara Eliya - one of the world's most scenic train rides"
                    },
                    {
                        "time": "12:30 PM",
                        "description": "Arrive in Nuwara Eliya, transfer to hotel"
                    },
                    {
                        "time": "2:00 PM",
                        "description": "Lunch at hotel"
                    },
                    {
                        "time": "3:30 PM",
                        "description": "City tour: Visit Gregory Lake, Victoria Park, and colonial-era buildings"
                    },
                    {
                        "time": "6:00 PM",
                        "description": "Relax and enjoy the cool mountain climate"
                    }
                ],
                "meals": {
                    "breakfast": "Early breakfast at hotel",
                    "lunch": "English-style lunch at hotel",
                    "dinner": "Dinner at hotel with fireplace"
                },
                "hotel": {
                    "name": "Jetwing St. Andrew's",
                    "description": "Colonial-era hotel with English country charm, nestled in the hill country",
                    "rating": 4
                }
            },
            {
                "day": 6,
                "title": "Horton Plains & World's End",
                "city": "Nuwara Eliya",
                "activities": [
                    {
                        "time": "4:30 AM",
                        "description": "Very early breakfast box"
                    },
                    {
                        "time": "5:00 AM",
                        "description": "Depart for Horton Plains National Park"
                    },
                    {
                        "time": "7:00 AM",
                        "description": "Trek to World's End viewpoint - 4000ft sheer drop with spectacular views"
                    },
                    {
                        "time": "10:30 AM",
                        "description": "Visit Baker's Falls waterfall"
                    },
                    {
                        "time": "12:00 PM",
                        "description": "Return to hotel for brunch"
                    },
                    {
                        "time": "3:00 PM",
                        "description": "Visit a working tea factory and learn about Ceylon tea production"
                    },
                    {
                        "time": "5:00 PM",
                        "description": "High tea at Grand Hotel - colonial tradition"
                    }
                ],
                "meals": {
                    "breakfast": "Early breakfast box for trek",
                    "lunch": "Late brunch at hotel",
                    "dinner": "International buffet dinner"
                },
                "hotel": {
                    "name": "Jetwing St. Andrew's",
                    "description": "Colonial-era hotel with English country charm",
                    "rating": 4
                }
            },
            {
                "day": 7,
                "title": "Coastal Journey to Galle",
                "city": "Galle",
                "activities": [
                    {
                        "time": "8:00 AM",
                        "description": "Breakfast at hotel and check-out"
                    },
                    {
                        "time": "9:00 AM",
                        "description": "Drive to Galle (approximately 5 hours through scenic landscapes)"
                    },
                    {
                        "time": "2:00 PM",
                        "description": "Arrive in Galle, lunch at beachside restaurant"
                    },
                    {
                        "time": "4:00 PM",
                        "description": "Explore Galle Fort (UNESCO World Heritage Site) - Dutch colonial architecture"
                    },
                    {
                        "time": "6:00 PM",
                        "description": "Sunset walk along the fort ramparts"
                    },
                    {
                        "time": "7:30 PM",
                        "description": "Dinner at boutique restaurant in the fort"
                    }
                ],
                "meals": {
                    "breakfast": "Hotel breakfast",
                    "lunch": "Fresh seafood at beachside restaurant",
                    "dinner": "Fine dining at fort restaurant"
                },
                "hotel": {
                    "name": "Amangalla",
                    "description": "Historic luxury hotel within Galle Fort, formerly the New Oriental Hotel dating back to 1684",
                    "rating": 5
                }
            },
            {
                "day": 8,
                "title": "Departure from Colombo",
                "city": "Colombo",
                "activities": [
                    {
                        "time": "7:00 AM",
                        "description": "Breakfast at hotel"
                    },
                    {
                        "time": "9:00 AM",
                        "description": "Check-out and depart for Colombo airport (2.5 hours)"
                    },
                    {
                        "time": "11:30 AM",
                        "description": "Arrive at Bandaranaike International Airport"
                    },
                    {
                        "time": "1:00 PM",
                        "description": "Departure flight - farewell to Sri Lanka with wonderful memories"
                    }
                ],
                "meals": {
                    "breakfast": "Final breakfast at hotel"
                },
                "hotel": None
            }
        ]
    }
