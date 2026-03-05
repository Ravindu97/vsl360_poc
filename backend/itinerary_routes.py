from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import os
from itinerary_generator_playwright import generate_vsl360_itinerary_pdf_playwright, list_template_presets

router = APIRouter(
    prefix="/api/v1/test/itinerary",
    tags=["Itinerary Testing"]
)

class ActivitySchema(BaseModel):
    time: Optional[str] = ""
    description: str

class HotelSchema(BaseModel):
    night: str
    name: str
    city: str
    room_type: str

class LocationSummarySchema(BaseModel):
    city: str
    nights: int

class DaySchema(BaseModel):
    day: int
    title: str
    city: str
    activities: List[ActivitySchema]
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    travel_time: Optional[str] = ""
    distance: Optional[str] = ""
    overnight_city: Optional[str] = None
    optional: Optional[str] = None

class ItineraryRequestSchema(BaseModel):
    template_name: Optional[str] = "elegant_classic"
    customer_name: Optional[str] = None
    trip_name: str
    destination_country: str
    cover_image_path: Optional[str] = None
    cover_image_url: Optional[str] = None
    total_nights: int
    total_days: int
    start_date: str
    end_date: str
    overview_text: Optional[str] = ""
    location_summary: Optional[List[LocationSummarySchema]] = []
    days: List[DaySchema]
    activities_included: Optional[List[str]] = []
    hotels: Optional[List[HotelSchema]] = []
    tour_includes: Optional[List[str]] = []
    tour_excludes: Optional[List[str]] = []
    cost_per_person: Optional[str] = None
    payment_info: Optional[List[str]] = []
    cancellation_policy: Optional[List[str]] = []

@router.post("/generate-pdf")
def generate_itinerary(request: ItineraryRequestSchema):
    """
    TEST ENDPOINT: Generate and download a beautiful PDF itinerary
    This is for testing purposes and won't affect the main system
    """
    try:
        trip_data = request.dict()
        pdf_path = generate_vsl360_itinerary_pdf_playwright(trip_data)
        
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
        pdf_path = generate_vsl360_itinerary_pdf_playwright(trip_data)
        
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


@router.post("/generate-pdf-v2")
def generate_itinerary_v2(request: ItineraryRequestSchema):
    """
    TEST ENDPOINT V2: Generate and download itinerary PDF using HTML/CSS + Playwright.
    """
    try:
        trip_data = request.dict()
        pdf_path = generate_vsl360_itinerary_pdf_playwright(trip_data)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"{request.trip_name}_v2.pdf"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating V2 PDF: {str(e)}"
        )


@router.post("/save-pdf-v2")
def save_itinerary_v2(request: ItineraryRequestSchema):
    """
    TEST ENDPOINT V2: Generate and save itinerary PDF using HTML/CSS + Playwright.
    """
    try:
        trip_data = request.dict()
        pdf_path = generate_vsl360_itinerary_pdf_playwright(trip_data)

        return {
            "success": True,
            "file_path": pdf_path,
            "message": "Itinerary V2 saved successfully",
            "trip_name": request.trip_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving V2 PDF: {str(e)}"
        )

@router.get("/test-data")
def get_test_data():
    """
    TEST ENDPOINT: Get sample itinerary data in VSL 360 format
    """
    return {
        "template_name": "elegant_classic",
        "customer_name": "Mr. Shery Jain",
        "trip_name": "8 Days Tour in Sri Lanka",
        "destination_country": "Sri Lanka",
        "cover_image_path": "08 Days Tour in Sri Lanka for Mr. Shery Jain_page-0001.jpg",
        "total_nights": 7,
        "total_days": 8,
        "start_date": "March 15, 2024",
        "end_date": "March 23, 2024",
        "overview_text": "Embark on an unforgettable journey through Sri Lanka, the Pearl of the Indian Ocean. This carefully curated 8-day adventure takes you from the bustling streets of Colombo to the ancient cultural wonders of Kandy, through the misty tea plantations of Nuwara Eliya, and down to the pristine southern coast. Experience the perfect blend of cultural heritage, natural beauty, and authentic Sri Lankan hospitality.",
        "location_summary": [
            {"city": "Colombo", "nights": 2},
            {"city": "Kandy", "nights": 2},
            {"city": "Nuwara Eliya", "nights": 2},
            {"city": "Galle", "nights": 1}
        ],
        "days": [
            {
                "day": 1,
                "title": "Welcome to Sri Lanka",
                "city": "Colombo",
                "image_path": "08 Days Tour in Sri Lanka for Mr. Shery Jain_page-0004.jpg",
                "activities": [
                    {"description": "Arrive at Bandaranaike International Airport"},
                    {"description": "Meet and greet by VSL 360 representative"},
                    {"description": "Transfer to hotel in Colombo (30 mins)"},
                    {"description": "Check-in and freshen up"},
                    {"description": "Welcome dinner featuring traditional Sri Lankan cuisine"}
                ],
                "travel_time": "30 minutes",
                "distance": "35 km",
                "overnight_city": "Colombo"
            },
            {
                "day": 2,
                "title": "Discovering Colombo",
                "city": "Colombo",
                "image_path": "08 Days Tour in Sri Lanka for Mr. Shery Jain_page-0004.jpg",
                "activities": [
                    {"description": "Breakfast at hotel"},
                    {"description": "Guided city tour: Galle Face Green, Independence Square & colonial buildings"},
                    {"description": "Visit Gangaramaya Temple - Buddhist temple complex"},
                    {"description": "Lunch at Ministry of Crab (famous seafood restaurant)"},
                    {"description": "Colombo National Museum - explore Sri Lankan history"},
                    {"description": "Shopping at Barefoot Gallery and Odel"},
                    {"description": "Evening at leisure"}
                ],
                "travel_time": "N/A",
                "distance": "City tour",
                "overnight_city": "Colombo"
            },
            {
                "day": 3,
                "title": "Journey to the Cultural Capital",
                "city": "Kandy",
                "image_path": "08 Days Tour in Sri Lanka for Mr. Shery Jain_page-0005.jpg",
                "activities": [
                    {"description": "Breakfast and check-out"},
                    {"description": "Scenic drive to Kandy through lush landscapes"},
                    {"description": "En-route visit: Pinnawala Elephant Orphanage"},
                    {"description": "Watch elephants bathing in the river"},
                    {"description": "Arrive in Kandy and check-in to hotel"},
                    {"description": "Evening visit to Temple of the Sacred Tooth Relic (UNESCO Site)"},
                    {"description": "Attend traditional Kandyan dance performance"}
                ],
                "travel_time": "3.5 hours",
                "distance": "115 km",
                "overnight_city": "Kandy"
            },
            {
                "day": 4,
                "title": "Kandy & Royal Botanical Gardens",
                "city": "Kandy",
                "image_path": "08 Days Tour in Sri Lanka for Mr. Shery Jain_page-0005.jpg",
                "activities": [
                    {"description": "Breakfast at hotel"},
                    {"description": "Visit Royal Botanical Gardens at Peradeniya (147 acres)"},
                    {"description": "Walk among orchid collections and giant bamboo groves"},
                    {"description": "Lunch at garden restaurant"},
                    {"description": "Ceylon Tea Museum and working tea plantation visit"},
                    {"description": "Tea tasting experience with panoramic views"},
                    {"description": "Sunset walk around Kandy Lake"}
                ],
                "travel_time": "30 minutes",
                "distance": "15 km",
                "overnight_city": "Kandy",
                "optional": "Evening spa treatment at hotel (additional cost)"
            },
            {
                "day": 5,
                "title": "Scenic Train to Hill Country",
                "city": "Nuwara Eliya",
                "image_path": "08 Days Tour in Sri Lanka for Mr. Shery Jain_page-0006.jpg",
                "activities": [
                    {"description": "Early breakfast and check-out"},
                    {"description": "Board famous Kandy to Nuwara Eliya train"},
                    {"description": "Journey through tea plantations and mountain scenery"},
                    {"description": "One of the world's most scenic train rides"},
                    {"description": "Arrive in Nuwara Eliya - 'Little England' of Sri Lanka"},
                    {"description": "Check-in to colonial-era hotel"},
                    {"description": "City tour: Gregory Lake & Victoria Park"}
                ],
                "travel_time": "4 hours",
                "distance": "80 km",
                "overnight_city": "Nuwara Eliya"
            },
            {
                "day": 6,
                "title": "Horton Plains & World's End",
                "city": "Nuwara Eliya",
                "image_path": "08 Days Tour in Sri Lanka for Mr. Shery Jain_page-0006.jpg",
                "activities": [
                    {"description": "Very early breakfast box (4:30 AM)"},
                    {"description": "Drive to Horton Plains National Park"},
                    {"description": "Trek to World's End viewpoint - breathtaking 4000ft drop"},
                    {"description": "Visit Baker's Falls waterfall"},
                    {"description": "Return to hotel for late brunch"},
                    {"description": "Visit working tea factory - learn Ceylon tea production"},
                    {"description": "High tea at Grand Hotel - colonial tradition"}
                ],
                "travel_time": "1.5 hours",
                "distance": "35 km",
                "overnight_city": "Nuwara Eliya"
            },
            {
                "day": 7,
                "title": "Coastal Beauty of Galle",
                "city": "Galle",
                "image_path": "08 Days Tour in Sri Lanka for Mr. Shery Jain_page-0007.jpg",
                "activities": [
                    {"description": "Breakfast and check-out"},
                    {"description": "Scenic drive to southern coast through hill country"},
                    {"description": "Lunch at beachside restaurant"},
                    {"description": "Explore UNESCO-listed Galle Fort"},
                    {"description": "Walk through Dutch colonial architecture"},
                    {"description": "Visit lighthouse and fort ramparts"},
                    {"description": "Sunset photography along the fort walls"},
                    {"description": "Dinner at boutique restaurant in the fort"}
                ],
                "travel_time": "5 hours",
                "distance": "175 km",
                "overnight_city": "Galle"
            },
            {
                "day": 8,
                "title": "Farewell Sri Lanka",
                "city": "Colombo",
                "image_path": "08 Days Tour in Sri Lanka for Mr. Shery Jain_page-0008.jpg",
                "activities": [
                    {"description": "Breakfast at hotel"},
                    {"description": "Morning at leisure - optional beach time"},
                    {"description": "Check-out and drive to Colombo airport"},
                    {"description": "Last-minute shopping if time permits"},
                    {"description": "Departure from Bandaranaike International Airport"},
                    {"description": "End of memorable Sri Lankan journey"}
                ],
                "travel_time": "3 hours",
                "distance": "145 km",
                "overnight_city": "N/A"
            }
        ],
        "activities_included": [
            "Pinnawala Elephant Orphanage visit",
            "Temple of the Sacred Tooth Relic tour",
            "Kandyan cultural dance performance",
            "Royal Botanical Gardens at Peradeniya",
            "Ceylon Tea Museum and factory tour",
            "Tea tasting experience with expert",
            "Scenic train ride Kandy to Nuwara Eliya",
            "Horton Plains National Park trek",
            "World's End viewpoint",
            "Baker's Falls waterfall",
            "High tea at Grand Hotel",
            "Galle Fort UNESCO World Heritage Site tour",
            "Colombo city sightseeing tour",
            "Gangaramaya Temple visit",
            "Colombo National Museum"
        ],
        "hotels": [
            {"night": "Night 1-2", "name": "The Kingsbury Hotel", "city": "Colombo", "room_type": "Deluxe Ocean View"},
            {"night": "Night 3-4", "name": "The Kandy House", "city": "Kandy", "room_type": "Luxury Suite"},
            {"night": "Night 5-6", "name": "Jetwing St. Andrew's", "city": "Nuwara Eliya", "room_type": "Colonial Room"},
            {"night": "Night 7", "name": "Amangalla", "city": "Galle Fort", "room_type": "Heritage Suite"}
        ],
        "tour_includes": [
            "7 nights accommodation in 4 & 5 star hotels",
            "Daily breakfast at all hotels",
            "Welcome dinner on Day 1",
            "3 lunches at select restaurants",
            "All entrance fees to monuments and sites",
            "English-speaking professional guide throughout",
            "Private air-conditioned vehicle for all transfers",
            "Airport meet and greet service",
            "Train tickets for Kandy to Nuwara Eliya scenic route",
            "All activities mentioned in itinerary",
            "High tea at Grand Hotel Nuwara Eliya",
            "Bottled water during transfers",
            "Hotel taxes and service charges"
        ],
        "tour_excludes": [
            "International and domestic airfare",
            "Sri Lankan visa fees (ETA)",
            "Travel insurance",
            "Lunches and dinners not mentioned in itinerary",
            "Optional activities and spa treatments",
            "Personal expenses and shopping",
            "Tips for guides and drivers",
            "Camera fees at certain sites",
            "Any services not mentioned in inclusions"
        ],
        "cost_per_person": "₹48,500",
        "payment_info": [
            "25% advance payment at time of booking",
            "50% payment 30 days before travel date",
            "Final 25% payment 15 days before travel date",
            "Payments accepted via bank transfer, credit card, or UPI",
            "All prices in Indian Rupees (INR)",
            "Prices subject to availability at time of booking"
        ],
        "cancellation_policy": [
            "More than 45 days before travel: 10% cancellation fee",
            "30-45 days before travel: 25% cancellation fee",
            "15-30 days before travel: 50% cancellation fee",
            "7-15 days before travel: 75% cancellation fee",
            "Less than 7 days before travel: 100% cancellation fee (no refund)",
            "Cancellations must be submitted in writing",
            "Refunds processed within 15 working days"
        ]
    }


@router.get("/local-images")
def get_local_images():
    """
    TEST ENDPOINT: List local template images that can be used in the PDF.
    """
    images_dir = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample_itinerary", "images")
    )

    if not os.path.isdir(images_dir):
        return {"images": [], "images_dir": images_dir}

    allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
    files = []
    for name in sorted(os.listdir(images_dir)):
        _, ext = os.path.splitext(name.lower())
        if ext in allowed_ext:
            files.append(name)

    return {"images": files, "images_dir": images_dir}


@router.get("/templates")
def get_templates():
    """
    TEST ENDPOINT: List available PDF template presets and tunable defaults.
    """
    return list_template_presets()
