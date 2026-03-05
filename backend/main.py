from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uvicorn
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import re
from dotenv import load_dotenv
import os
import requests
from sqlalchemy.orm import Session
from database import get_db, User
from chatbot import get_chatbot_response, get_travel_suggestion
from medical_support import search_nearby_medical_centers, get_emergency_contacts
from virtual_doctor import get_virtual_doctor_response, get_common_travel_ailments, get_emergency_numbers_by_location, get_emergency_numbers_by_country

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("groq_api_key")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize the app 
app = FastAPI(
    title="Travel Web Agent API",
    description="API for plan trip itineraries using LLM",          
    docs_url="/",               
    redoc_url=None,
    openapi_url="/openapi.json" 
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM
llm = ChatGroq(
    temperature=0.7,
    groq_api_key=groq_api_key,
    model_name="llama-3.1-8b-instant"
)

# Pydantic models
class TripRequest(BaseModel):
    departure_country: str
    arrival_country: str
    start_date: str
    end_date: str

class InterestsRequest(BaseModel):
    country: str
    interests: List[str]

class CitySelectionRequest(BaseModel):
    country: str
    selected_cities: List[str]
    start_city: str
    total_days: int

class HotelRestaurantRequest(BaseModel):
    country: str
    cities: List[str]

class KeyPointsRequest(BaseModel):
    country: str
    cities: List[str]
    interests: List[str]
    start_date: str
    end_date: str

class TransportationRequest(BaseModel):
    country: str
    cities: List[str]  # Optimized route order

class TravelTipsRequest(BaseModel):
    country: str
    cities: List[str]
    start_date: str
    end_date: str
    interests: List[str]

class CityDateInfo(BaseModel):
    days: int
    start_date: str
    end_date: str

class FinalItineraryRequest(BaseModel):
    country: str
    start_date: str
    end_date: str
    city_date_distribution: Optional[Dict[str, CityDateInfo]] = {}
    hotels: Optional[str] = ''
    transportation: Optional[str] = ''
    
class GoogleMediaRequest(BaseModel):
    country: str

class UserInfoRequest(BaseModel):
    full_name: str
    country: str
    mobile_no: str
    email: str

class CityAdditionalDetailsRequest(BaseModel):
    city: str
    country: str

class YouTubeSearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 3

class ChatbotRequest(BaseModel):
    message: str
    conversation_history: Optional[List[str]] = None

class TravelSuggestionRequest(BaseModel):
    destination: str
    interests: List[str]

class MedicalSupportRequest(BaseModel):
    latitude: float
    longitude: float
    radius: Optional[int] = 5000

class EmergencyContactRequest(BaseModel):
    country: str

class VirtualDoctorRequest(BaseModel):
    symptoms: str
    location: Optional[str] = "Unknown"
    duration: Optional[str] = "Unknown"

class EmergencyNumberRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None

# Country list
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan",
    "Bahrain", "Bangladesh", "Belarus", "Belgium", "Bolivia", "Brazil", "Bulgaria", "Cambodia",
    "Canada", "Chile", "China", "Colombia", "Croatia", "Czech Republic", "Denmark", "Ecuador",
    "Egypt", "Estonia", "Finland", "France", "Georgia", "Germany", "Greece", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy",
    "Japan", "Jordan", "Kazakhstan", "Kenya", "South Korea", "Kuwait", "Latvia", "Lebanon",
    "Lithuania", "Luxembourg", "Malaysia", "Mexico", "Morocco", "Nepal", "Netherlands", "New Zealand",
    "Norway", "Pakistan", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania",
    "Russia", "Saudi Arabia", "Singapore", "Slovakia", "Slovenia", "South Africa", "Spain", "Sri Lanka",
    "Sweden", "Switzerland", "Thailand", "Turkey", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
    "Uruguay", "Venezuela", "Vietnam"
]

# Prompts
country_info_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a knowledgeable travel expert. Provide comprehensive information about {country}.
    
    Format your response EXACTLY as follows:
    
    OVERVIEW_START
    [Write ONE short sentence about the country - what it's known for]
    
    • UNESCO Sites: [Brief description with specific examples if applicable]
    • Cultural Heritage: [Brief description of cultural blend and influences]
    • Climate: [Brief description of climate and seasons]
    • Region: [Geographic region]
    • Landscape: [Key landscape features separated by commas, e.g., "Beaches, Mountains, Rainforests, Plains"]
    • Famous For: [What the country is famous for]
    OVERVIEW_END
    
    ATTRACTIONS_START
    Attraction: [Name]
    Description: [Brief description without asterisks or bullets]
    
    Attraction: [Name]
    Description: [Brief description without asterisks or bullets]
    
    [Continue for 5-6 attractions]
    ATTRACTIONS_END
    
    VISITOR_INFO_START
    Visa: [Clear visa policy information]
    Language: [Main languages spoken]
    Currency: [Local currency]
    Healthcare: [Healthcare recommendations]
    Best Time: [Best time to visit]
    VISITOR_INFO_END
    
    IMPORTANT: Always provide exactly 6 bullet points. For Landscape, use commas to separate items, NOT bullet points."""),
    ("human", "Tell me about {country}")
])

flight_options_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a flight booking expert. Suggest 3-4 realistic flight options from {departure} to {arrival}.
    
    For each flight option, provide EXACTLY in this format with DIFFERENT ratings for each airline:
    
    FLIGHT_OPTION_START
    Airline: [Name]
    Route: [Full Departure Airport Name (Code)] → [Full Arrival Airport Name (Code)]
    Duration: [X hours Y minutes]
    Price: [USD price range like $800-$1200]
    Rating: [Unique rating between 3.5-4.8, e.g., 4.3, 3.8, 4.6]
    REVIEW_START
    Stars: [5 or 4]
    Title: [Unique positive review title]
    Text: [Unique detailed positive review]
    REVIEW_END
    REVIEW_START
    Stars: [4 or 3]
    Title: [Unique mixed review title]
    Text: [Unique detailed mixed review]
    REVIEW_END
    REVIEW_START
    Stars: [3 or 2]
    Title: [Unique critical review title]
    Text: [Unique detailed critical review]
    REVIEW_END
    FLIGHT_OPTION_END
    
    IMPORTANT: 
    - Each airline must have a DIFFERENT rating (e.g., 4.5, 3.9, 4.2, 4.7)
    - Make reviews realistic and varied
    - Use FULL airport names with codes in parentheses (e.g., "John F. Kennedy International Airport (JFK) → Los Angeles International Airport (LAX)")
    
    After all flight options, provide:
    
    BOOKING_WEBSITES:
    - Expedia: Best for package deals
    - Kayak: Price comparison
    - Skyscanner: Budget options
    - Google Flights: Real-time prices"""),
    ("human", "Show me flight options with unique ratings and 3 different customer reviews for each")
])

city_suggestion_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a travel planner expert. Based on the traveler's interests: {interests}, suggest 8-10 cities in {country}.
    
    IMPORTANT: You MUST provide exactly 8-10 different cities. Do not repeat cities.
    CRITICAL: You MUST include at least 1-2 cities with "Perfect Match" compatibility that strongly align with the user's interests.
    
    For each city, provide in this EXACT format:
    
    CITY_START
    City: [Name]
    Compatibility: [Perfect Match/Very High/High]
    Days Recommended: [Number]
    Best For: [Short description]
    Why Visit: [2-3 sentences]
    Places to Visit: [List 4-5 specific attractions/places separated by semicolons]
    CITY_END
    
    Make sure to include CITY_START and CITY_END markers for EVERY city.
    Ensure the first 1-2 cities have "Perfect Match" compatibility."""),
    ("human", "Suggest the most compatible cities for my interests")
])

hotels_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a hotel expert. Suggest 5 hotels for EACH city in {country}: {cities}

    Return ONLY a valid JSON object with this EXACT structure:
    {{
        "hotels_by_city": [
            {{
                "city": "City Name",
                "hotels": [
                    {{
                        "name": "Hotel Name",
                        "category": "Budget/Mid-range/Luxury",
                        "stars": 4,
                        "location": "Area/District",
                        "price": "$80-$120",
                        "tripadvisor_url": "https://www.tripadvisor.com/Search?q=Hotel+Name+City+Name"
                    }}
                ]
            }}
        ]
    }}
    
    IMPORTANT: 
    - Return ONLY valid JSON, no additional text
    - Replace spaces with + in TripAdvisor URLs
    - Provide exactly 5 hotels per city
    - Use proper JSON formatting with double quotes"""),
    ("human", "Suggest hotels for each city")
])

transportation_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a transportation expert. Provide options between cities in {country}.

    Cities in order: {cities}

    For EACH route, provide in this EXACT format:

    ROUTE: [City A] → [City B]

    TRANSPORT_START
    Type: [Train/Bus/Flight/Car]
    Service: [Company name]
    Distance: [km / miles]
    Duration: [hours:minutes]
    Cost: [USD range]
    Frequency: [per day]
    Pros: [advantages]
    Cons: [disadvantages]
    TRANSPORT_END

    Provide 2-3 options per route, then add:
    RECOMMENDED: [Best option and why]
    BOOKING: [Website/info]"""),
    ("human", "What are the transportation options between cities?")
])

key_points_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a travel expert. Provide exactly 5 essential points for traveling to {country}.
    
    Cities: {cities}
    Interests: {interests}
    Travel dates: {start_date} to {end_date}
    
    Return ONLY a valid JSON object with this EXACT structure:
    {{
        "key_points": [
            {{
                "type": "gear",
                "text": "Essential gear recommendation"
            }},
            {{
                "type": "gear",
                "text": "Clothing recommendation"
            }},
            {{
                "type": "gear",
                "text": "Health/safety gear recommendation"
            }},
            {{
                "type": "tip",
                "text": "Important travel tip"
            }},
            {{
                "type": "tip",
                "text": "Budget or cultural tip"
            }}
        ]
    }}
    
    IMPORTANT:
    - Return ONLY valid JSON, no additional text
    - Provide exactly 3 gear points and 2 tip points
    - Keep each point concise (1-2 sentences)
    - Make points specific to the country and interests"""),
    ("human", "Provide 5 essential travel points")
])



final_itinerary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a master travel planner. Create a comprehensive day-by-day itinerary from {start_date} to {end_date} for {country}.

    Cities with dates:
    {city_date_info}

    Hotels: {hotels}
    Transportation: {transportation}

    Return ONLY a valid JSON object with this EXACT structure:
    {{
        "total_estimated_budget": "$XXXX",
        "itinerary": [
            {{
                "day": 1,
                "date": "YYYY-MM-DD",
                "city": "City Name",
                "weather": "Temperature and conditions",
                "hotel": "Hotel name",
                "morning": "8:00 AM - 12:00 PM activity with location",
                "lunch": "12:00 PM - 2:00 PM dining suggestion",
                "afternoon": "2:00 PM - 6:00 PM activity with location",
                "dinner": "7:00 PM onwards dining suggestion",
                "evening": "Optional activities or rest",
                "travel": "Transportation details if changing cities",
                "estimated_budget": "$XXX (breakdown: accommodation $XX, food $XX, activities $XX, transport $XX)"
            }}
        ],
        "summary": "Key tips and budget advice"
    }}
    
    IMPORTANT:
    - Return ONLY valid JSON, no additional text
    - Calculate total_estimated_budget as sum of all daily budgets
    - Create one entry per day from start to end date
    - Include all fields for each day including estimated_budget
    - Provide realistic daily budget estimates in USD
    - Use proper JSON formatting with double quotes"""),
    ("human", "Create my complete final itinerary")
])

city_additional_details_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a travel expert. Provide additional detailed information about {city} in {country}.
    
    Provide information in this EXACT JSON format:
    {{
        "best_time_to_visit": "[Best months to visit with weather info]",
        "weather": "[Current weather patterns and what to expect]",
        "must_try_foods": "[Local dishes and where to find them - provide as simple text, not objects]",
        "insider_tips": "[Hidden gems and local tips like 'Visit the Temple of the Tooth during the evening Pooja (6:30 PM) for the drumming ceremony']"
    }}
    
    IMPORTANT: All values must be simple strings, not arrays or objects. Make sure the response is valid JSON format."""),
    ("human", "Tell me additional details about this city")
])

def search_pexels_images(country: str, num=3):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": f"{country} travel", "per_page": num}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "title": photo.get("alt", ""),
            "url": photo["src"]["original"],
            "thumbnail": photo["src"]["small"]
        }
        for photo in data.get("photos", [])[:num]
    ]

def search_youtube_videos(query: str, max_results=3):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "videoDuration": "short",
        "relevanceLanguage": "en"
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "videoId": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            "channelTitle": item["snippet"]["channelTitle"]
        }
        for item in data.get("items", [])
    ]
    
# Utility functions
def get_coordinates(city_name: str, country: str = None):
    """Get coordinates for a city"""
    if not city_name:
        return None
    
    geolocator = Nominatim(user_agent="travel_planner_api_v2")
    
    # Try multiple query formats for better results
    queries = [
        f"{city_name}, {country}" if country else city_name,
        f"{city_name} city, {country}" if country else f"{city_name} city",
        f"{city_name}, {country}, city" if country else f"{city_name}, city",
        city_name
    ]
    
    for query in queries:
        try:
            print(f"Trying to geocode: {query}")  # Debug logging
            location = geolocator.geocode(query, timeout=20, exactly_one=True)
            if location:
                print(f"Found coordinates for {city_name}: {location.latitude}, {location.longitude}")
                return (location.latitude, location.longitude)
            time.sleep(1)  # Increased rate limiting
        except Exception as e:
            print(f"Geocoding failed for {query}: {str(e)}")
            time.sleep(1)
            continue
    
    print(f"Could not find coordinates for {city_name}")
    return None

def reorder_cities_by_distance(selected_cities: List[str], start_city: str, country: str):
    """Reorder cities by distance using nearest neighbor"""
    if not selected_cities or start_city not in selected_cities:
        return selected_cities
    
    coords_map = {}
    for city in selected_cities:
        coords = get_coordinates(city, country)
        if coords:
            coords_map[city] = coords
        time.sleep(0.3)  # Rate limiting
    
    if start_city not in coords_map:
        return selected_cities
    
    ordered = [start_city]
    remaining = [c for c in selected_cities if c != start_city]
    current = start_city
    
    while remaining:
        current_coords = coords_map[current]
        nearest = min(remaining, key=lambda c: geodesic(current_coords, coords_map[c]).km if c in coords_map else float('inf'))
        ordered.append(nearest)
        remaining.remove(nearest)
        current = nearest
    
    return ordered

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Travel Planner API"}

@app.get("/countries")
async def get_countries():
    return {"countries": COUNTRIES}

@app.post("/save-user")
async def save_user(request: UserInfoRequest, db: Session = Depends(get_db)):
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            # Update existing user
            existing_user.full_name = request.full_name
            existing_user.country = request.country
            existing_user.mobile_no = request.mobile_no
        else:
            # Create new user
            new_user = User(
                full_name=request.full_name,
                country=request.country,
                mobile_no=request.mobile_no,
                email=request.email
            )
            db.add(new_user)
        
        db.commit()
        return {"message": "User information saved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/country-info")
async def get_country_info(request: TripRequest):
    try:
        response = llm.invoke(country_info_prompt.format_messages(country=request.arrival_country))
        return {"country_info": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/flight-options")
async def get_flight_options(request: TripRequest):
    try:
        response = llm.invoke(flight_options_prompt.format_messages(
            departure=request.departure_country,
            arrival=request.arrival_country
        ))
        return {"flight_options": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/city-suggestions")
async def get_city_suggestions(request: InterestsRequest):
    try:
        response = llm.invoke(city_suggestion_prompt.format_messages(
            country=request.country,
            interests=', '.join(request.interests)
        ))
        return {"suggested_cities": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/optimize-route")
async def optimize_route(request: CitySelectionRequest):
    try:
        optimized_cities = reorder_cities_by_distance(
            request.selected_cities, 
            request.start_city, 
            request.country
        )
        
        # Calculate distances between consecutive cities
        route_distances = []
        coords_map = {}
        
        # Get coordinates for all cities with enhanced lookup
        print(f"Getting coordinates for cities: {optimized_cities} in country: {request.country}")
        for city in optimized_cities:
            coords = get_coordinates(city, request.country)
            if coords:
                coords_map[city] = coords
                print(f"Successfully got coordinates for {city}: {coords}")
            else:
                # Try alternative lookup without country for better results
                print(f"Retrying {city} without country")
                coords = get_coordinates(city)
                if coords:
                    coords_map[city] = coords
                    print(f"Successfully got coordinates for {city} (no country): {coords}")
                else:
                    print(f"Failed to get coordinates for {city}")
            time.sleep(1)  # Increased rate limiting
        
        # Calculate distances between consecutive cities
        print(f"Coordinates found for: {list(coords_map.keys())}")
        for i in range(len(optimized_cities) - 1):
            from_city = optimized_cities[i]
            to_city = optimized_cities[i + 1]
            
            if from_city in coords_map and to_city in coords_map:
                distance_km = geodesic(coords_map[from_city], coords_map[to_city]).km
                print(f"Calculated distance {from_city} -> {to_city}: {distance_km:.1f} km")
                route_distances.append({
                    "from": from_city,
                    "to": to_city,
                    "distance_km": round(distance_km, 1)
                })
            else:
                # Provide estimated distance when coordinates are not available
                estimated_distance = 50 + (i * 25)  # Simple estimation: 50km base + 25km per step
                print(f"Using estimated distance {from_city} -> {to_city}: {estimated_distance} km")
                route_distances.append({
                    "from": from_city,
                    "to": to_city,
                    "distance_km": estimated_distance
                })
        
        # Calculate date distribution
        start_date = datetime.now().date()
        days_per_city = request.total_days // len(optimized_cities)
        extra_days = request.total_days % len(optimized_cities)
        
        city_schedule = {}
        current_date = start_date
        
        for i, city in enumerate(optimized_cities):
            days = days_per_city + (1 if i < extra_days else 0)
            end_date = current_date + timedelta(days=days-1)
            city_schedule[city] = {
                "days": days,
                "start_date": current_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            }
            current_date = end_date + timedelta(days=1)
        
        # Prepare city coordinates for map display
        city_coordinates = []
        for city in optimized_cities:
            if city in coords_map:
                city_coordinates.append({
                    "city": city,
                    "lat": coords_map[city][0],
                    "lng": coords_map[city][1]
                })
        
        return {
            "optimized_cities": optimized_cities,
            "city_schedule": city_schedule,
            "route_distances": route_distances,
            "city_coordinates": city_coordinates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hotels-restaurants")
async def get_hotels_restaurants(request: HotelRestaurantRequest):
    try:
        print(f"Hotels request received - Country: {request.country}, Cities: {request.cities}")
        cities_str = ', '.join(request.cities)
        
        # Get Hotels
        hotels_response = llm.invoke(hotels_prompt.format_messages(
            country=request.country,
            cities=cities_str
        ))
        
        print(f"Hotels response length: {len(hotels_response.content)}")
        
        return {
            "hotels": hotels_response.content
        }
    except Exception as e:
        print(f"Hotels endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


    
    
@app.post("/key-points")
async def get_key_points(request: KeyPointsRequest):
    try:
        response = llm.invoke(key_points_prompt.format_messages(
            country=request.country,
            cities=', '.join(request.cities),
            interests=', '.join(request.interests),
            start_date=request.start_date,
            end_date=request.end_date
        ))
        
        import json
        data = json.loads(response.content)
        return data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse key points")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/transportation-options")
async def get_transportation_options(request: TransportationRequest):
    try:
        response = llm.invoke(transportation_prompt.format_messages(
            cities=' → '.join(request.cities),
            country=request.country
        ))
        return {"transportation": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


    

@app.post("/final-itinerary")
async def get_final_itinerary(request: FinalItineraryRequest):
    try:
        import json
        import re
        
        city_date_info = "\n".join([
            f"- {city}: {info.days} days ({info.start_date} to {info.end_date})"
            for city, info in (request.city_date_distribution or {}).items()
        ]) if request.city_date_distribution else "No city schedule available"
        
        response = llm.invoke(final_itinerary_prompt.format_messages(
            country=request.country,
            start_date=request.start_date,
            end_date=request.end_date,
            city_date_info=city_date_info,
            hotels=request.hotels or 'No hotel information available',
            transportation=request.transportation or 'No transportation information available'
        ))
        
        content = response.content.strip()
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
            content = content.strip()
        
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        data = json.loads(content)
        return data
    except json.JSONDecodeError as e:
        print(f"JSON Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse itinerary: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/free-media")
async def get_free_media(request: GoogleMediaRequest):
    try:
        print(f"Searching Pexels for country: {request.country}")  # Debug
        media = search_pexels_images(request.country)
        print(f"Success! Got {len(media)} images")  # Confirm
        return media
    except Exception as e:
        print(f"PEXELS ERROR: {type(e).__name__}: {e}")  # ← THIS IS KEY
        import traceback
        traceback.print_exc()  # Full stack trace
        raise HTTPException(status_code=500, detail="Failed to retrieve media.")

@app.post("/city-additional-details")
async def get_city_additional_details(request: CityAdditionalDetailsRequest):
    try:
        response = llm.invoke(city_additional_details_prompt.format_messages(
            city=request.city,
            country=request.country
        ))
        
        # Try to parse as JSON, fallback to structured text if needed
        try:
            import json
            data = json.loads(response.content)
            
            # Ensure all values are strings, not objects or arrays
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    data[key] = str(value)
            
            return data
        except json.JSONDecodeError:
            # Fallback: return structured data
            return {
                "best_time_to_visit": "Best time varies by season",
                "weather": "Weather information not available",
                "must_try_foods": "Local cuisine recommendations",
                "insider_tips": "Explore local markets and hidden gems"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/youtube-videos/{query}")
async def get_youtube_videos(query: str, max_results: int = 3):
    try:
        videos = search_youtube_videos(query, max_results)
        return {"videos": videos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch YouTube videos: {str(e)}")

@app.post("/chatbot")
async def chatbot(request: ChatbotRequest):
    try:
        response = get_chatbot_response(request.message, request.conversation_history)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/travel-suggestion")
async def travel_suggestion(request: TravelSuggestionRequest):
    try:
        response = get_travel_suggestion(request.destination, request.interests)
        return {"suggestion": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/medical-support")
async def medical_support(request: MedicalSupportRequest):
    try:
        medical_centers = search_nearby_medical_centers(
            request.latitude, 
            request.longitude, 
            request.radius
        )
        return {"medical_centers": medical_centers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emergency-contacts")
async def emergency_contacts(request: EmergencyContactRequest):
    try:
        contacts = get_emergency_contacts(request.country)
        return {"emergency_contacts": contacts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/virtual-doctor")
async def virtual_doctor(request: VirtualDoctorRequest):
    try:
        response = get_virtual_doctor_response(
            request.symptoms,
            request.location,
            request.duration
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/common-ailments")
async def common_ailments():
    try:
        ailments = get_common_travel_ailments()
        return ailments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emergency-numbers")
async def emergency_numbers(request: EmergencyNumberRequest):
    try:
        if request.latitude and request.longitude:
            result = get_emergency_numbers_by_location(request.latitude, request.longitude)
            if result:
                return result
        
        if request.country:
            result = get_emergency_numbers_by_country(request.country)
            return result
        
        raise HTTPException(status_code=400, detail="Provide either coordinates or country name")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the itinerary test routes (separate test endpoints)
from itinerary_routes import router as itinerary_router
app.include_router(itinerary_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")