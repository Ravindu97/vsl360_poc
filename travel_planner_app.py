import streamlit as st
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
import operator
from urllib.parse import quote_plus
import re
import pandas as pd

# Load environment variables
load_dotenv()

# Map functionality removed
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.distance import geodesic
import time

import pandas as pd

# small in-memory cache to reduce repeat geocoding during a session
_GEOCODE_CACHE = {}

@st.cache_data(show_spinner=False)
def _cached_geocode(city_query: str):
    # This caches the raw geocode tuple (lat, lon) or None
    return _GEOCODE_CACHE.get(city_query)

def _cache_store(city_query: str, coords):
    _GEOCODE_CACHE[city_query] = coords

def get_coordinates(city_name: str, country: str | None = None, max_retries: int = 3, pause: float = 1.0):
    """
    Robust geocoding using Nominatim (OpenStreetMap).
    Returns (lat, lon) or None on failure.
    - Retries on timeout.
    - Uses small in-memory cache for the session.
    """
    if not city_name:
        return None

    # build a query string as "City, Country" when possible
    query = f"{city_name}, {country}" if country else city_name

    # check cache first
    cached = _cached_geocode(query)
    if cached is not None:
        return cached

    geolocator = Nominatim(user_agent="travel_planner_ai_streamlit")
    last_exc = None

    for attempt in range(1, max_retries + 1):
        try:
            # Geocode with a timeout
            location = geolocator.geocode(query, timeout=10)
            if location:
                coords = (location.latitude, location.longitude)
                _cache_store(query, coords)
                return coords
            else:
                # Try a shorter query (city only) if "City, Country" failed
                if country:
                    try_short = f"{city_name}"
                    location2 = geolocator.geocode(try_short, timeout=10)
                    if location2:
                        coords = (location2.latitude, location2.longitude)
                        _cache_store(query, coords)
                        return coords
                # No result
                last_exc = None
                break
        except GeocoderTimedOut as e:
            last_exc = e
            # backoff and retry
            time.sleep(pause)
        except GeocoderServiceError as e:
            # service error (likely network or rate limiting) -> abort
            last_exc = e
            break
        except Exception as e:
            last_exc = e
            break

    # store None to cache to avoid repeated failing calls
    _cache_store(query, None)

    # show debug info for the user
    if last_exc:
        st.warning(f"⚠️ Geocoding '{query}' failed: {type(last_exc).__name__}: {str(last_exc)}")
    else:
        st.info(f"ℹ️ No geocoding result for '{query}'")

    return None

def reorder_cities_by_distance(selected_cities: list, start_city: str, country: str | None = None):
    """
    Reorder the selected_cities starting from start_city using a nearest-neighbor heuristic.
    If any city cannot be geocoded, falls back to preserving original user order (with start_city first).
    Returns the reordered list (or original on failure).
    """
    if not selected_cities:
        return []

    if start_city not in selected_cities:
        # ensure start is included; if not present, prepend it
        if start_city:
            selected_cities = [start_city] + [c for c in selected_cities if c != start_city]

    # Attempt to get coordinates for all cities
    coords_map = {}
    failed_cities = []
    with st.spinner("Geocoding cities (this needs internet access)..."):
        for city in selected_cities:
            coords = get_coordinates(city, country)
            if coords:
                coords_map[city] = coords
            else:
                failed_cities.append(city)
            # be polite with the geocoding service
            time.sleep(1.0)

    if failed_cities:
        st.warning(
            "Some cities couldn't be geocoded: "
            + ", ".join(failed_cities)
            + ".\nFalling back to the original selection order."
        )
        # return order with start city first (if chosen), then the rest in original order
        if start_city in selected_cities:
            ordered = [start_city] + [c for c in selected_cities if c != start_city]
            return ordered
        return selected_cities

    # Now compute nearest-neighbour ordering
    if start_city not in coords_map:
        st.warning("Start city has no coordinates — returning original order.")
        return selected_cities

    ordered = [start_city]
    remaining = [c for c in selected_cities if c != start_city]
    current = start_city

    try:
        while remaining:
            current_coords = coords_map[current]
            # find the nearest remaining city to current
            nearest = min(
                remaining,
                key=lambda c: geodesic(current_coords, coords_map[c]).km
            )
            ordered.append(nearest)
            remaining.remove(nearest)
            current = nearest
    except Exception as e:
        st.error(f"Error while computing distances: {e}. Returning original order.")
        # fallback
        if start_city in selected_cities:
            return [start_city] + [c for c in selected_cities if c != start_city]
        return selected_cities

    return ordered

# Set page config
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🌍",
    layout="wide"
)

# Initialize session state
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'travel_state' not in st.session_state:
    st.session_state.travel_state = {}

# Define State
class TravelPlannerState(TypedDict):
    messages: Annotated[List, operator.add]
    departure_country: str
    arrival_country: str
    travel_start_date: str
    travel_end_date: str
    total_days: int
    country_info: str
    user_likes_country: bool
    flight_options: str
    interests: List[str]
    selected_cities: List[str]
    city_date_distribution: dict
    suggested_cities: str
    activities: str
    hotels: str
    restaurants: str
    weather_forecast: str
    transportation: str
    final_itinerary: str

# Initialize LLM
@st.cache_resource
def get_llm():
    return ChatGroq(
        temperature=0.7,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant"  # Using smaller model due to rate limits
    )

llm = get_llm()



# Country list
countries = [
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
    
    Include:
    1. Country Overview: Culture, landscape, cuisine, and unique heritage (2-3 paragraphs)
    2. Key Attractions: Top 5-7 must-visit places with brief descriptions
    3. Visitor Information:
       - Visa policy (general information for international travelers)
       - Healthcare facilities and recommendations
       - Demographics and language information
    
    Format the response clearly with headers."""),
    ("human", "Tell me about {country}")
])

flight_options_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a flight booking expert. Suggest 3-4 realistic flight options from {departure} to {arrival}.
    
    For each flight option, provide EXACTLY in this format for easy table creation:
    
    FLIGHT_OPTION_START
    Airline: [Name]
    Route: [Departure Airport] → [Arrival Airport]
    Duration: [X hours Y minutes]
    Price: [USD price range like $800-$1200]
    Economy: [Yes/No and price range]
    Business: [Yes/No and price range]
    First Class: [Yes/No and price range]
    FLIGHT_OPTION_END
    
    After all flight options, provide:
    
    BOOKING_WEBSITES:
    - Expedia: [Brief note]
    - Kayak: [Brief note]
    - Skyscanner: [Brief note]
    - Google Flights: [Brief note]
    - Direct Airlines: [Brief note]
    
    Be consistent with the format."""),
    ("human", "Show me flight options and booking websites")
])

city_suggestion_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a travel planner expert. Based on the traveler's interests: {interests}, suggest 6-8 MOST COMPATIBLE cities in {country} that perfectly match these interests.
    
    For each city, provide in this EXACT format:
    
    CITY_START
    City: [Name]
    Compatibility: [Perfect Match/Very High/High]
    Days Recommended: [Number]
    Best For: [Short description]
    Why Visit: [2-3 sentences]
    CITY_END
    
    Rank cities by compatibility score."""),
    ("human", "Suggest the most compatible cities for my interests")
])

hotels_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a hotel expert. Suggest 3-4 hotels for EACH of these cities in {country}: {cities}

    For each city, provide hotels in this EXACT format:

    CITY: [City Name]

    HOTEL_START
    Hotel: [Name]
    Category: [Budget/Mid-range/Luxury]
    Stars: [Number]
    Location: [Area]
    Price: [USD per night range]
    Amenities: [Key features]
    Booking: https://www.booking.com/searchresults.html?ss=[Hotel Name] [City Name]
    TripAdvisor: https://www.tripadvisor.com/Search?q=[Hotel Name] [City Name]
    Why: [Recommendation reason]
    HOTEL_END

    Be consistent with the format."""),
    ("human", "Suggest hotels with booking links for each city")
])

restaurants_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a food expert. Suggest 4-5 restaurants for EACH of these cities in {country}: {cities}

    For each city, provide in this EXACT format:

    CITY: [City Name]

    RESTAURANT_START
    Restaurant: [Name]
    Cuisine: [Type]
    Location: [Area]
    Price: [$ / $$ / $$$]
    Specialty: [Must-try dishes]
    Atmosphere: [Brief description]
    TripAdvisor: https://www.tripadvisor.com/Search?q=[Restaurant Name] [City Name]
    RESTAURANT_END

    Include mix of: Local cuisine, Fine dining, Casual, Street food, Cafes"""),
    ("human", "Suggest restaurants with TripAdvisor links for each city")
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

gear_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a travel gear expert. Suggest essential gear and packing items for EACH of these cities in {country}: {cities}

    Consider the traveler's interests: {interests}
    Travel dates: {start_date} to {end_date}

    For each city, provide in this EXACT format:

    CITY: [City Name]

    GEAR_START
    Essential: [Must-have items for this city]
    Clothing: [Weather-appropriate clothing]
    Electronics: [Cameras, chargers, adapters]
    Activities: [Gear for specific activities/interests]
    Health: [Sunscreen, medications, first aid]
    Shopping: [Where to buy gear locally if needed]
    GEAR_END

    Be specific to each city's climate, activities, and culture."""),
    ("human", "Suggest recommended gear for each city")
])

travel_tips_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a travel consultant expert. Provide comprehensive travel advice for {country}.

    Cities: {cities}
    Travel dates: {start_date} to {end_date}
    Interests: {interests}

    Provide in this EXACT format:

    PACKING_START
    Essential: [Must-pack items for the trip]
    Clothing: [Weather and culture appropriate clothing]
    Documents: [Passport, visa, insurance, etc.]
    Electronics: [Chargers, adapters, cameras]
    Health: [Medications, first aid, health items]
    PACKING_END

    CULTURAL_START
    Customs: [Local customs and etiquette]
    Language: [Key phrases and communication tips]
    Currency: [Money exchange and payment methods]
    Tipping: [Tipping culture and guidelines]
    Dress: [Dress code and cultural considerations]
    CULTURAL_END

    TIME_START
    Planning: [How to plan your days efficiently]
    Booking: [When to book activities and restaurants]
    Transport: [Best times to travel between cities]
    Activities: [Time allocation for different activities]
    Rest: [Importance of rest and downtime]
    TIME_END

    BUDGET_START
    Accommodation: [Hotel costs per night range]
    Food: [Daily food budget range]
    Transport: [Transportation costs]
    Activities: [Activity and entrance fees]
    Shopping: [Souvenir and shopping budget]
    Emergency: [Emergency fund recommendations]
    Total: [Estimated total trip cost]
    BUDGET_END

    HOTELS_TIPS_START
    Budget: [Best budget hotel chains and booking tips]
    Luxury: [Top luxury hotels and when to book]
    Location: [Best areas to stay in each city]
    Booking: [Best booking platforms and timing]
    Deals: [How to find deals and discounts]
    HOTELS_TIPS_END

    RESTAURANTS_TIPS_START
    Local: [Must-try local restaurants and dishes]
    Fine: [Best fine dining experiences]
    Street: [Popular street food locations]
    Reservations: [Which restaurants need reservations]
    Budget: [Best budget-friendly eating options]
    RESTAURANTS_TIPS_END

    Be specific and practical."""),
    ("human", "Provide travel tips and budget information")
])

final_itinerary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a master travel planner. Create a comprehensive day-by-day itinerary from {start_date} to {end_date} for {country}.

    Cities with dates:
    {city_date_info}

    Hotels: {hotels}
    Restaurants: {restaurants}
    Transportation: {transportation}
    Gear: {gear}
    Tips: {tips}

    Create detailed day-by-day plan in this EXACT format:

    DAY_START
    Day: [Number]
    Date: [YYYY-MM-DD]
    City: [City Name]
    Weather: [Temperature and conditions]
    Hotel: [Hotel name from recommendations]
    Morning: [8:00 AM - 12:00 PM activity with location]
    Lunch: [12:00 PM - 2:00 PM restaurant with specialty]
    Afternoon: [2:00 PM - 6:00 PM activity with location]
    Dinner: [7:00 PM onwards restaurant with ambiance]
    Evening: [Optional activities or rest]
    Travel: [If changing cities, transportation details]
    DAY_END

    Include summary with key tips and budget overview."""),
    ("human", "Create my complete final itinerary")
])

def extract_key_attractions_with_desc(text: str, max_attractions: int = 6) -> list:
    """
    Extract a list of (name, description) pairs from the 'Key Attractions' section.
    Tolerant to:
      - "Key Attractions:" header
      - numbered lists (1. Place — desc)
      - bullets (- Place: desc)
      - multi-line descriptions (they get concatenated)
    """
    if not text:
        return []
    lower = text.lower()
    start_idx = lower.find('key attractions')
    if start_idx == -1:
        start_idx = lower.find('attractions')
        if start_idx == -1:
            return []

    slice_text = text[start_idx:]
    # stop at probable next headers
    stop_markers = ['visitor information', 'visitor info', 'visitor', 'visa', 'healthcare', 'visitor information:','visitor info:']
    end_idx = len(slice_text)
    for m in stop_markers:
        pos = slice_text.lower().find(m)
        if pos != -1 and pos < end_idx:
            end_idx = pos
    slice_text = slice_text[:end_idx]

    lines = slice_text.splitlines()
    items = []
    buffer = ''
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            # blank line usually separates items -- treat as separator
            if buffer:
                items.append(buffer.strip())
                buffer = ''
            continue

        # detect start of new item: begins with bullet or number
        if re.match(r'^\s*([-*•]\s+|\d+\.\s+)', line):
            if buffer:
                items.append(buffer.strip())
            buffer = line.strip()
        else:
            # continuation of previous line (description continuation)
            if buffer:
                buffer += ' ' + line.strip()
            else:
                # sometimes items don't have bullets; collect them anyway
                buffer = line.strip()
    if buffer:
        items.append(buffer.strip())

    parsed = []
    for itm in items:
        if len(parsed) >= max_attractions:
            break
        # remove leading bullet/number
        itm_clean = re.sub(r'^\s*([-*•]\s+|\d+\.\s+)', '', itm).strip()
        name = None
        desc = None

        # Prefer separators with spaces around them to avoid splitting names with hyphens
        separators = [' — ', ' – ', ' - ', ': ']
        for sep in separators:
            if sep in itm_clean:
                parts = itm_clean.split(sep, 1)
                name = parts[0].strip()
                desc = parts[1].strip()
                break

        if not name:
            # fallback: try regex capturing "Name — desc" variants without spaces
            m = re.match(r'^(?P<name>[^—–:-]+)[—–:-]\s*(?P<desc>.+)$', itm_clean)
            if m:
                name = m.group('name').strip()
                desc = m.group('desc').strip()

        if not name:
            # If still not available, take up to comma as name
            if ',' in itm_clean:
                name, rest = itm_clean.split(',', 1)
                name = name.strip()
                desc = rest.strip()
            else:
                # as last resort, if it's long, take first 6 words as name
                parts = itm_clean.split()
                if len(parts) > 6:
                    name = ' '.join(parts[:6]).strip()
                    desc = ' '.join(parts[6:]).strip()
                else:
                    # treat whole thing as name without description
                    name = itm_clean.strip()
                    desc = ''

        # ensure description isn't excessively long duplicates of the name
        if desc and desc.lower().startswith(name.lower()):
            desc = desc[len(name):].strip(' -:—–')

        parsed.append({'name': name, 'description': desc})

    # filter out empty names, dedupe by name
    result = []
    seen = set()
    for p in parsed:
        n = p['name']
        if not n:
            continue
        if n.lower() in seen:
            continue
        seen.add(n.lower())
        result.append(p)
        if len(result) >= max_attractions:
            break
    return result

def main():
    st.title("🌍 AI-Powered Travel Planner")
    st.markdown("Plan your perfect trip with our intelligent multi-agent system!")
    
    # Sidebar for navigation
    st.sidebar.title("Planning Steps")
    steps = [
        "Destination Info", 
        "Flight Options",
        "Your Interests",
        "City Suggestions",
        "Hotels & Restaurants",
        "Recommended Gear",
        "Transportation",
        "Travel Tips & Budget",
        "Final Itinerary"
    ]
    
    # Trip Details (Always visible at top)
    with st.container():
        st.subheader("✈️ Trip Details")
        
        col1, col2 = st.columns(2)
        with col1:
            departure = st.selectbox(
                "Departure Country", 
                options=countries,
                index=countries.index(st.session_state.travel_state.get('departure_country', 'United States')) if st.session_state.travel_state.get('departure_country') in countries else 0
            )
            start_date = st.date_input("Start Date", value=datetime.now().date())
        
        with col2:
            # compute a safer default index for arrival to avoid accidentally defaulting to Albania (index 1)
            default_arrival = st.session_state.travel_state.get('arrival_country', 'France')
            if default_arrival in countries:
                arrival_index = countries.index(default_arrival)
            else:
                # fall back to France if available, otherwise first country
                arrival_index = countries.index('France') if 'France' in countries else 0

            arrival = st.selectbox(
                "Destination Country", 
                options=countries,
                index=arrival_index
            )
            end_date = st.date_input("End Date", value=datetime.now().date() + timedelta(days=7))
        
        if departure and arrival and start_date and end_date:
            total_days = (end_date - start_date).days + 1
            st.success(f"Trip Duration: {total_days} days")
            
            # remember previous arrival to know if the user changed destination
            prev_arrival = st.session_state.travel_state.get('arrival_country')
            
            st.session_state.travel_state.update({
                'departure_country': departure,
                'arrival_country': arrival,
                'travel_start_date': start_date.strftime('%Y-%m-%d'),
                'travel_end_date': end_date.strftime('%Y-%m-%d'),
                'total_days': total_days
            })

            # If arrival changed, clear cached country_info so new info will be fetched
            if prev_arrival != arrival:
                st.session_state.travel_state.pop('country_info', None)
            
            if st.button("Get Destination Info"):
                st.session_state.current_step = 1
                st.rerun()
        
        st.divider()
    
    # Destination Information
    if st.session_state.current_step >= 1:
        st.header(f"📍 About {st.session_state.travel_state.get('arrival_country', '')}")
        
        if 'country_info' not in st.session_state.travel_state:
            if 'arrival_country' in st.session_state.travel_state and st.session_state.travel_state['arrival_country']:
                with st.spinner("Gathering destination information..."):
                    try:
                        response = llm.invoke(country_info_prompt.format_messages(
                            country=st.session_state.travel_state['arrival_country']
                        ))
                        st.session_state.travel_state['country_info'] = response.content
                    except Exception as e:
                        st.error(f"Error getting destination info: {e}")
                        return
            else:
                st.warning("Please enter a destination country first.")
                return
        
        # Parse and display country info without duplicate attractions
        country_info = st.session_state.travel_state['country_info']
        
        # Split content and remove duplicate Key Attractions section
        sections = country_info.split('##')
        filtered_content = []
        attractions_found = False
        
        for section in sections:
            section_lower = section.lower().strip()
            if 'key attractions' in section_lower:
                if not attractions_found:
                    filtered_content.append(section)
                    attractions_found = True
                # Skip duplicate attractions sections
            else:
                filtered_content.append(section)
        
        # Display filtered content
        clean_content = '##'.join(filtered_content)
        # Clean up any JSON-like formatting in country info
        import re
        clean_content = re.sub(r'\{[^}]*\}', '', clean_content)
        clean_content = re.sub(r'"([^"]+)":', r'**\1:**', clean_content)
        clean_content = re.sub(r'"([^"]+)"', r'\1', clean_content)
        st.markdown(clean_content)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ I want to visit this country"):
                st.session_state.travel_state['user_likes_country'] = True
                st.session_state.current_step = 2
                st.rerun()
        
        with col2:
            if st.button("❌ Choose different destination"):
                st.session_state.current_step = 0
                st.session_state.travel_state = {}
                st.rerun()
    
    # Flight Options
    if st.session_state.current_step >= 2:
        st.header("✈️ Flight Options")
        
        if 'flight_options' not in st.session_state.travel_state:
            with st.spinner("Searching for flights..."):
                try:
                    response = llm.invoke(flight_options_prompt.format_messages(
                        departure=st.session_state.travel_state['departure_country'],
                        arrival=st.session_state.travel_state['arrival_country']
                    ))
                    st.session_state.travel_state['flight_options'] = response.content
                except Exception as e:
                    st.error(f"Error getting flight options: {e}")
                    return
        
        # Parse and display flight options
        content = st.session_state.travel_state['flight_options']
        
        # Extract flight data from structured format
        flights = []
        lines = content.split('\n')
        current_flight = {}
        
        for line in lines:
            line = line.strip()
            if 'Airline:' in line:
                current_flight['Airline'] = line.split('Airline:')[1].strip()
            elif 'Route:' in line:
                current_flight['Route'] = line.split('Route:')[1].strip()
            elif 'Duration:' in line:
                current_flight['Duration'] = line.split('Duration:')[1].strip()
            elif 'Price:' in line:
                current_flight['Price'] = line.split('Price:')[1].strip()
            elif 'FLIGHT_OPTION_END' in line and current_flight:
                flights.append(current_flight.copy())
                current_flight = {}
        
        if flights:
            st.subheader("Available Flights")
            for i, flight in enumerate(flights):
                with st.expander(f"Flight {i+1}: {flight.get('Airline', 'N/A')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Route:** {flight.get('Route', 'N/A')}")
                        st.write(f"**Duration:** {flight.get('Duration', 'N/A')}")
                    with col2:
                        st.write(f"**Price:** {flight.get('Price', 'N/A')}")
        
        # Show booking websites with hyperlinks
        if "BOOKING_WEBSITES:" in content:
            st.subheader("Booking Websites")
            booking_section = content.split("BOOKING_WEBSITES:")[1]
            
            # Create hyperlinks for booking websites
            booking_links = {
                'Expedia': 'https://www.expedia.com',
                'Kayak': 'https://www.kayak.com',
                'Skyscanner': 'https://www.skyscanner.com',
                'Google Flights': 'https://www.google.com/flights',
                'Direct Airlines': '#'
            }
            

            
            for line in booking_section.split('\n'):
                if line.strip() and line.strip().startswith('-'):
                    # Example line: "- Expedia: Expedia offers a wide range of flights..."
                    line = line.strip().lstrip('-').strip()
                    if ':' in line:
                        name, desc = line.split(':', 1)
                        name = name.strip()
                        desc = desc.strip()
                        link = booking_links.get(name, '#')
                        # ✅ Display title as a clickable hyperlink, then show description
                        st.markdown(f"**[{name}]({link})**: {desc}")
                else:
                    st.write(line.strip())
        
        if st.button("Continue to Interests"):
            st.session_state.current_step = 3
            st.rerun()
    
    # Interests
    if st.session_state.current_step >= 3:
        st.header("🎯 Your Travel Interests")
        
        st.markdown("Select your travel interests to get personalized city recommendations:")
        
        interest_options = [
            "Beaches", "History", "Food", "Adventure", "Culture", 
            "Nightlife", "Nature", "Shopping", "Photography", "Museums",
            "Architecture", "Festivals", "Wildlife", "Mountains", "Art"
        ]
        
        # Use checkboxes for better multiple selection
        st.write("Choose your interests:")
        selected_interests = []
        
        # Create columns for better layout
        cols = st.columns(3)
        for i, interest in enumerate(interest_options):
            with cols[i % 3]:
                if st.checkbox(interest, key=f"interest_{interest}", value=interest in st.session_state.travel_state.get('interests', [])):
                    selected_interests.append(interest)
        
        if selected_interests:
            st.session_state.travel_state['interests'] = selected_interests
            st.success(f"Selected interests: {', '.join(selected_interests)}")
            
            if st.button("Get City Recommendations"):
                st.session_state.current_step = 4
                st.rerun()
    
    # City Suggestions
    if st.session_state.current_step >= 4:
        st.header("🏙️ Recommended Cities")
        
        if 'suggested_cities' not in st.session_state.travel_state:
            with st.spinner("Finding the best cities for you..."):
                try:
                    response = llm.invoke(city_suggestion_prompt.format_messages(
                        country=st.session_state.travel_state['arrival_country'],
                        interests=', '.join(st.session_state.travel_state['interests'])
                    ))
                    st.session_state.travel_state['suggested_cities'] = response.content
                except Exception as e:
                    st.error(f"Error getting city suggestions: {e}")
                    return
        
        # Parse city suggestions from structured format
        content = st.session_state.travel_state['suggested_cities']
        cities = []
        lines = content.split('\n')
        current_city = {}
        
        for line in lines:
            line = line.strip()
            if 'City:' in line:
                current_city['City'] = line.split('City:')[1].strip()
            elif 'Compatibility:' in line:
                current_city['Compatibility'] = line.split('Compatibility:')[1].strip()
            elif 'Days Recommended:' in line:
                current_city['Days'] = line.split('Days Recommended:')[1].strip()
            elif 'Best For:' in line:
                current_city['Best For'] = line.split('Best For:')[1].strip()
            elif 'Why Visit:' in line:
                current_city['Why Visit'] = line.split('Why Visit:')[1].strip()
            elif 'CITY_END' in line and current_city:
                cities.append(current_city.copy())
                current_city = {}
        
        # If still no cities parsed, try alternative parsing
        if not cities:
            st.warning("No cities found in structured format. Trying alternative parsing...")
            # Simple fallback: look for city names in the content
            import re
            city_matches = re.findall(r'(?:City|\d+\.)\s*([A-Za-z\s]+?)(?:\s*[-–—:]|\n)', content)
            for i, city_name in enumerate(city_matches[:8]):  # Limit to 8 cities
                cities.append({
                    'City': city_name.strip(),
                    'Compatibility': 'High',
                    'Days': '2-3',
                    'Best For': 'Various activities',
                    'Why Visit': 'Recommended destination'
                })
        
        if cities:
            st.subheader("Recommended Cities (Ranked by Compatibility)")
            for city in cities:
                compatibility_color = {
                    'Perfect Match': '🟢',
                    'Very High': '🟡', 
                    'High': '🟠'
                }.get(city.get('Compatibility', ''), '⚪')
                
                with st.expander(f"{compatibility_color} {city.get('City', 'N/A')} - {city.get('Compatibility', 'N/A')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Recommended Days:** {city.get('Days', 'N/A')}")
                        st.write(f"**Best For:** {city.get('Best For', 'N/A')}")
                    with col2:
                        st.write(f"**Why Visit:** {city.get('Why Visit', 'N/A')}")
        else:
            st.error("No cities could be parsed from the response. Please try again or check the raw response above.")
        
        # City selection
        st.subheader("Select Your Cities")
        city_names = [city.get('City', '') for city in cities if city.get('City')]
        
        # Use checkboxes for better city selection
        st.write("Choose cities to visit:")
        selected_cities = []
        
        # Create columns for better layout
        cols = st.columns(2)
        for i, city in enumerate(city_names):
            with cols[i % 2]:
                if st.checkbox(city, key=f"city_{city}", value=city in st.session_state.travel_state.get('selected_cities', [])):
                    selected_cities.append(city)
        
        # Reorder cities by distance
        if selected_cities:
            st.write("Choose your starting city and we'll optimize the route by distance:")
            
            # Let user choose starting city
            start_city = st.selectbox(
                "Starting city (first city to visit):", 
                selected_cities, 
                key="start_city_select"
            )
            
            if st.button("Optimize Route by Distance", key="optimize_route"):
                # Reorder cities using distance-based algorithm
                optimized_cities = reorder_cities_by_distance(
                    selected_cities, 
                    start_city, 
                    st.session_state.travel_state['arrival_country']
                )
                selected_cities = optimized_cities
                # Store the optimized order in session state
                st.session_state.travel_state['optimized_cities'] = selected_cities
                st.success(f"Route optimized! Order: {' → '.join(selected_cities)}")
            
            # Show route summary if optimized cities exist
            if 'optimized_cities' in st.session_state.travel_state:
                st.subheader("🗺️ Your Optimized Route")
                
                # Calculate and display distances
                city_coords = []
                for city in st.session_state.travel_state['optimized_cities']:
                    coords = get_coordinates(city, st.session_state.travel_state['arrival_country'])
                    if coords:
                        city_coords.append({'city': city, 'lat': coords[0], 'lon': coords[1]})
                
                # Display Route Order and Route Details in the same row
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Route Order:**")
                    for i, city in enumerate(st.session_state.travel_state['optimized_cities'], 1):
                        st.write(f"{i}. {city}")
                
                with col2:
                    if len(city_coords) > 1:
                        st.write("**Route Details:**")
                        total_distance = 0
                        for i in range(len(city_coords) - 1):
                            from_city = city_coords[i]
                            to_city = city_coords[i + 1]
                            distance = geodesic(
                                (from_city['lat'], from_city['lon']),
                                (to_city['lat'], to_city['lon'])
                            ).kilometers
                            total_distance += distance
                            st.write(f"{from_city['city']} → {to_city['city']}: {distance:.0f} km")
                        st.write(f"**Total Distance: {total_distance:.0f} km**")

        
        if selected_cities:
            # Use optimized order if available, otherwise use selected order
            if 'optimized_cities' in st.session_state.travel_state:
                # Check if optimized cities match current selection
                if set(st.session_state.travel_state['optimized_cities']) == set(selected_cities):
                    selected_cities = st.session_state.travel_state['optimized_cities']
            st.session_state.travel_state['selected_cities'] = selected_cities
            
            # Date distribution
            st.subheader("Days per City")
            total_days = st.session_state.travel_state['total_days']
            city_days = {}
            remaining_days = total_days
            
            for i, city in enumerate(selected_cities):
                if i == len(selected_cities) - 1:
                    # Last city gets remaining days
                    days = remaining_days
                    st.write(f"{city}: {days} days (remaining)")
                else:
                    max_days = remaining_days - (len(selected_cities) - i - 1)
                    days = st.number_input(
                        f"Days in {city}:",
                        min_value=1,
                        max_value=max_days,
                        value=min(3, max_days),
                        key=f"days_{city}"
                    )
                    remaining_days -= days
                
                city_days[city] = days
            
            # Calculate dates
            start_date = datetime.strptime(st.session_state.travel_state['travel_start_date'], '%Y-%m-%d')
            current_date = start_date
            city_date_distribution = {}
            
            for city, days in city_days.items():
                end_date = current_date + timedelta(days=days-1)
                city_date_distribution[city] = {
                    'days': days,
                    'start_date': current_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
                current_date = end_date + timedelta(days=1)
            
            st.session_state.travel_state['city_date_distribution'] = city_date_distribution
            
            # Display schedule
            st.subheader("Your Travel Schedule")
            for city, info in city_date_distribution.items():
                st.write(f"**{city}:** {info['days']} days ({info['start_date']} to {info['end_date']})")
            
            if st.button("Get Hotels & Restaurants"):
                st.session_state.current_step = 5
                st.rerun()
    
    # Hotels & Restaurants
    if st.session_state.current_step >= 5:
        st.header("🏨 Hotels & Restaurants")
        
        if 'hotels' not in st.session_state.travel_state:
            with st.spinner("Finding hotels for your cities..."):
                try:
                    response = llm.invoke(hotels_prompt.format_messages(
                        cities=', '.join(st.session_state.travel_state['selected_cities']),
                        country=st.session_state.travel_state['arrival_country']
                    ))
                    st.session_state.travel_state['hotels'] = response.content
                except Exception as e:
                    st.error(f"Error getting hotels: {e}")
                    return
        
        if 'restaurants' not in st.session_state.travel_state:
            with st.spinner("Finding restaurants for your cities..."):
                try:
                    response = llm.invoke(restaurants_prompt.format_messages(
                        cities=', '.join(st.session_state.travel_state['selected_cities']),
                        country=st.session_state.travel_state['arrival_country']
                    ))
                    st.session_state.travel_state['restaurants'] = response.content
                except Exception as e:
                    st.error(f"Error getting restaurants: {e}")
                    return
        
        # Display Hotels with dropdown by city
        st.subheader("🏨 Hotel Recommendations")
        
        # Parse hotels by city
        import re
        hotels_by_city = {}
        
        # Extract city sections from hotels content
        city_sections = re.split(r'CITY:\s*([^\n]+)', st.session_state.travel_state['hotels'])
        
        if len(city_sections) > 1:
            # Has city markers
            for i in range(1, len(city_sections), 2):
                if i + 1 < len(city_sections):
                    city_name = city_sections[i].strip()
                    city_content = city_sections[i + 1]
                    
                    hotels = []
                    hotel_blocks = re.split(r'HOTEL_START|HOTEL_END', city_content)
                    
                    for block in hotel_blocks:
                        if block.strip() and 'Hotel:' in block:
                            hotel_data = {}
                            for field in ['Hotel', 'Category', 'Stars', 'Location', 'Price', 'Amenities', 'Why', 'Booking', 'TripAdvisor']:
                                match = re.search(f'{field}:\s*([^\n]+)', block)
                                hotel_data[field] = match.group(1).strip() if match else 'N/A'
                            hotels.append(hotel_data)
                    
                    if hotels:
                        hotels_by_city[city_name] = hotels
        else:
            # No city markers, group all hotels under selected cities
            hotel_blocks = re.split(r'HOTEL_START|HOTEL_END', st.session_state.travel_state['hotels'])
            all_hotels = []
            
            for block in hotel_blocks:
                if block.strip() and 'Hotel:' in block:
                    hotel_data = {}
                    for field in ['Hotel', 'Category', 'Stars', 'Location', 'Price', 'Amenities', 'Why', 'Booking', 'TripAdvisor']:
                        match = re.search(f'{field}:\s*([^\n]+)', block)
                        hotel_data[field] = match.group(1).strip() if match else 'N/A'
                    all_hotels.append(hotel_data)
            
            # Distribute hotels among selected cities
            cities = st.session_state.travel_state.get('selected_cities', [])
            hotels_per_city = len(all_hotels) // len(cities) if cities else 0
            
            for i, city in enumerate(cities):
                start_idx = i * hotels_per_city
                end_idx = start_idx + hotels_per_city if i < len(cities) - 1 else len(all_hotels)
                hotels_by_city[city] = all_hotels[start_idx:end_idx]
        
        # Display hotels with dropdown
        if hotels_by_city:
            selected_city_hotels = st.selectbox(
                "Select city to view hotels:",
                options=list(hotels_by_city.keys()),
                key="hotel_city_selector"
            )
            
            if selected_city_hotels and selected_city_hotels in hotels_by_city:
                for hotel in hotels_by_city[selected_city_hotels]:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="
                                border: 2px solid #e0e0e0;
                                border-radius: 15px;
                                padding: 20px;
                                margin: 15px 0;
                                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            ">
                                <h3 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 1.4em;">🏨 {hotel['Hotel']}</h3>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                    <p style="margin: 5px 0;"><strong>⭐ Category:</strong> {hotel['Category']}</p>
                                    <p style="margin: 5px 0;"><strong>🌟 Stars:</strong> {hotel['Stars']}</p>
                                    <p style="margin: 5px 0;"><strong>📍 Location:</strong> {hotel['Location']}</p>
                                    <p style="margin: 5px 0;"><strong>💰 Price:</strong> {hotel['Price']}</p>
                                </div>
                                <p style="margin: 10px 0 5px 0;"><strong>🎯 Amenities:</strong> {hotel['Amenities']}</p>
                                <p style="margin: 5px 0; font-style: italic; color: #555;"><strong>💡 Why Choose:</strong> {hotel['Why']}</p>
                                <div style="margin-top: 15px; display: flex; gap: 10px;">
                                    {f'<a href="{hotel["Booking"]}" target="_blank" style="background: #0066cc; color: white; padding: 8px 16px; border-radius: 5px; text-decoration: none; font-size: 14px;">📅 Book Now</a>' if hotel.get('Booking') and hotel['Booking'] != 'N/A' else ''}
                                    {f'<a href="{hotel["TripAdvisor"]}" target="_blank" style="background: #00af87; color: white; padding: 8px 16px; border-radius: 5px; text-decoration: none; font-size: 14px;">⭐ Reviews</a>' if hotel.get('TripAdvisor') and hotel['TripAdvisor'] != 'N/A' else ''}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        

        
        # Display Restaurants with dropdown by city
        st.subheader("🍽️ Restaurant Recommendations")
        
        # Parse restaurants by city
        restaurants_by_city = {}
        
        # Extract city sections from restaurants content
        city_sections = re.split(r'CITY:\s*([^\n]+)', st.session_state.travel_state['restaurants'])
        
        if len(city_sections) > 1:
            # Has city markers
            for i in range(1, len(city_sections), 2):
                if i + 1 < len(city_sections):
                    city_name = city_sections[i].strip()
                    city_content = city_sections[i + 1]
                    
                    restaurants = []
                    restaurant_blocks = re.split(r'RESTAURANT_START|RESTAURANT_END', city_content)
                    
                    for block in restaurant_blocks:
                        if block.strip() and 'Restaurant:' in block:
                            restaurant_data = {}
                            for field in ['Restaurant', 'Cuisine', 'Location', 'Price', 'Specialty', 'Atmosphere', 'TripAdvisor']:
                                match = re.search(f'{field}:\s*([^\n]+)', block)
                                restaurant_data[field] = match.group(1).strip() if match else 'N/A'
                            restaurants.append(restaurant_data)
                    
                    if restaurants:
                        restaurants_by_city[city_name] = restaurants
        else:
            # No city markers, group all restaurants under selected cities
            restaurant_blocks = re.split(r'RESTAURANT_START|RESTAURANT_END', st.session_state.travel_state['restaurants'])
            all_restaurants = []
            
            for block in restaurant_blocks:
                if block.strip() and 'Restaurant:' in block:
                    restaurant_data = {}
                    for field in ['Restaurant', 'Cuisine', 'Location', 'Price', 'Specialty', 'Atmosphere', 'TripAdvisor']:
                        match = re.search(f'{field}:\s*([^\n]+)', block)
                        restaurant_data[field] = match.group(1).strip() if match else 'N/A'
                    all_restaurants.append(restaurant_data)
            
            # Distribute restaurants among selected cities
            cities = st.session_state.travel_state.get('selected_cities', [])
            restaurants_per_city = len(all_restaurants) // len(cities) if cities else 0
            
            for i, city in enumerate(cities):
                start_idx = i * restaurants_per_city
                end_idx = start_idx + restaurants_per_city if i < len(cities) - 1 else len(all_restaurants)
                restaurants_by_city[city] = all_restaurants[start_idx:end_idx]
        
        # Display restaurants with dropdown
        if restaurants_by_city:
            st.write(f"Found restaurants for {len(restaurants_by_city)} cities: {list(restaurants_by_city.keys())}")
            selected_city_restaurants = st.selectbox(
                "Select city to view restaurants:",
                options=list(restaurants_by_city.keys()),
                key="restaurant_city_selector"
            )
            
            if selected_city_restaurants and selected_city_restaurants in restaurants_by_city:
                for restaurant in restaurants_by_city[selected_city_restaurants]:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="
                                border: 2px solid #e0e0e0;
                                border-radius: 15px;
                                padding: 20px;
                                margin: 15px 0;
                                background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            ">
                                <h3 style="margin: 0 0 15px 0; color: #d84315; font-size: 1.4em;">🍽️ {restaurant['Restaurant']}</h3>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                    <p style="margin: 5px 0;"><strong>🍽️ Cuisine:</strong> {restaurant['Cuisine']}</p>
                                    <p style="margin: 5px 0;"><strong>💰 Price:</strong> {restaurant['Price']}</p>
                                    <p style="margin: 5px 0;"><strong>📍 Location:</strong> {restaurant['Location']}</p>
                                    <p style="margin: 5px 0;"><strong>🎭 Atmosphere:</strong> {restaurant['Atmosphere']}</p>
                                </div>
                                <p style="margin: 10px 0 5px 0; font-style: italic; color: #555;"><strong>🥘 Must Try:</strong> {restaurant['Specialty']}</p>
                                <div style="margin-top: 15px; display: flex; gap: 10px;">
                                    {f'<a href="{restaurant["TripAdvisor"]}" target="_blank" style="background: #00af87; color: white; padding: 8px 16px; border-radius: 5px; text-decoration: none; font-size: 14px;">⭐ Reviews</a>' if restaurant.get('TripAdvisor') and restaurant['TripAdvisor'] != 'N/A' else ''}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        if st.button("Get Recommended Gear"):
            st.session_state.current_step = 6
            st.rerun()
    
    # Recommended Gear
    if st.session_state.current_step >= 6:
        st.header("🎒 Recommended Gear & Packing")
        
        if 'gear' not in st.session_state.travel_state:
            with st.spinner("Finding recommended gear for your cities..."):
                try:
                    response = llm.invoke(gear_prompt.format_messages(
                        cities=', '.join(st.session_state.travel_state['selected_cities']),
                        country=st.session_state.travel_state['arrival_country'],
                        interests=', '.join(st.session_state.travel_state['interests']),
                        start_date=st.session_state.travel_state['travel_start_date'],
                        end_date=st.session_state.travel_state['travel_end_date']
                    ))
                    st.session_state.travel_state['gear'] = response.content
                except Exception as e:
                    st.error(f"Error getting gear recommendations: {e}")
                    return
        
        # Display Gear Recommendations with dropdown by city
        st.subheader("🎒 Gear Recommendations")
        
        # Parse gear by city
        import re
        gear_by_city = {}
        
        # Extract city sections from gear content
        city_sections = re.split(r'CITY:\s*([^\n]+)', st.session_state.travel_state['gear'])
        
        if len(city_sections) > 1:
            # Has city markers
            for i in range(1, len(city_sections), 2):
                if i + 1 < len(city_sections):
                    city_name = city_sections[i].strip()
                    city_content = city_sections[i + 1]
                    
                    gear_items = []
                    gear_blocks = re.split(r'GEAR_START|GEAR_END', city_content)
                    
                    for block in gear_blocks:
                        if block.strip() and ('Essential:' in block or 'Clothing:' in block):
                            gear_data = {}
                            for field in ['Essential', 'Clothing', 'Electronics', 'Activities', 'Health', 'Shopping']:
                                match = re.search(f'{field}:\s*([^\n]+)', block)
                                gear_data[field] = match.group(1).strip() if match else 'N/A'
                            gear_items.append(gear_data)
                    
                    if gear_items:
                        gear_by_city[city_name] = gear_items
        else:
            # No city markers, group all gear under selected cities
            gear_blocks = re.split(r'GEAR_START|GEAR_END', st.session_state.travel_state['gear'])
            all_gear = []
            
            for block in gear_blocks:
                if block.strip() and ('Essential:' in block or 'Clothing:' in block):
                    gear_data = {}
                    for field in ['Essential', 'Clothing', 'Electronics', 'Activities', 'Health', 'Shopping']:
                        match = re.search(f'{field}:\s*([^\n]+)', block)
                        gear_data[field] = match.group(1).strip() if match else 'N/A'
                    all_gear.append(gear_data)
            
            # Distribute gear among selected cities
            cities = st.session_state.travel_state.get('selected_cities', [])
            gear_per_city = len(all_gear) // len(cities) if cities else 0
            
            for i, city in enumerate(cities):
                start_idx = i * gear_per_city
                end_idx = start_idx + gear_per_city if i < len(cities) - 1 else len(all_gear)
                gear_by_city[city] = all_gear[start_idx:end_idx]
        
        # Display gear with dropdown
        if gear_by_city:
            selected_city_gear = st.selectbox(
                "Select city to view recommended gear:",
                options=list(gear_by_city.keys()),
                key="gear_city_selector"
            )
            
            if selected_city_gear and selected_city_gear in gear_by_city:
                for gear in gear_by_city[selected_city_gear]:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="
                                border: 2px solid #e0e0e0;
                                border-radius: 15px;
                                padding: 20px;
                                margin: 15px 0;
                                background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            ">
                                <h3 style="margin: 0 0 15px 0; color: #2e7d32; font-size: 1.4em;">🎒 Recommended Gear for {selected_city_gear}</h3>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                    <p style="margin: 5px 0;"><strong>🎯 Essential:</strong> {gear['Essential']}</p>
                                    <p style="margin: 5px 0;"><strong>👕 Clothing:</strong> {gear['Clothing']}</p>
                                    <p style="margin: 5px 0;"><strong>📱 Electronics:</strong> {gear['Electronics']}</p>
                                    <p style="margin: 5px 0;"><strong>🏃 Activities:</strong> {gear['Activities']}</p>
                                    <p style="margin: 5px 0;"><strong>💊 Health:</strong> {gear['Health']}</p>
                                    <p style="margin: 5px 0;"><strong>🛒 Shopping:</strong> {gear['Shopping']}</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        
        if st.button("Get Transportation Options"):
            st.session_state.current_step = 7
            st.rerun()
    
    # Transportation
    if st.session_state.current_step >= 7:
        st.header("🚗 Transportation Between Cities")
        
        if 'transportation' not in st.session_state.travel_state:
            with st.spinner("Finding transportation options..."):
                try:
                    response = llm.invoke(transportation_prompt.format_messages(
                        cities=' → '.join(st.session_state.travel_state['selected_cities']),
                        country=st.session_state.travel_state['arrival_country']
                    ))
                    st.session_state.travel_state['transportation'] = response.content
                except Exception as e:
                    st.error(f"Error getting transportation: {e}")
                    return
        
        # Display Transportation Options with dropdown by route
        st.subheader("🚗 Transportation Options")
        
        # Parse transportation by route
        import re
        transport_by_route = {}
        
        # Extract route sections from transportation content
        route_sections = re.split(r'ROUTE:\s*([^\n]+)', st.session_state.travel_state['transportation'])
        
        if len(route_sections) > 1:
            # Has route markers
            for i in range(1, len(route_sections), 2):
                if i + 1 < len(route_sections):
                    route_name = route_sections[i].strip()
                    # Clean up HTML entities in route name
                    route_name = route_name.replace('&gt;', '→').replace('-&gt;', '→')
                    route_content = route_sections[i + 1]
                    
                    transports = []
                    transport_blocks = re.split(r'TRANSPORT_START|TRANSPORT_END', route_content)
                    
                    for block in transport_blocks:
                        if block.strip() and ('Type:' in block or 'Service:' in block):
                            transport_data = {}
                            for field in ['Type', 'Service', 'Distance', 'Duration', 'Cost', 'Frequency', 'Pros', 'Cons']:
                                match = re.search(f'{field}:\s*([^\n]+)', block)
                                transport_data[field] = match.group(1).strip() if match else 'N/A'
                            transports.append(transport_data)
                    
                    if transports:
                        transport_by_route[route_name] = transports
        else:
            # No route markers, create routes from selected cities
            cities = st.session_state.travel_state.get('selected_cities', [])
            if len(cities) > 1:
                for i in range(len(cities) - 1):
                    route_name = f"{cities[i]} → {cities[i+1]}"
                    # Create sample transport data
                    transport_by_route[route_name] = [{
                        'Type': 'Multiple Options Available',
                        'Service': 'Various Providers',
                        'Distance': 'Check route details',
                        'Duration': 'Varies by transport type',
                        'Cost': 'Price varies',
                        'Frequency': 'Multiple daily options',
                        'Pros': 'Multiple transport modes available',
                        'Cons': 'Booking required in advance'
                    }]
        
        # Display transportation with dropdown
        if transport_by_route:
            # Clean route names by removing ** marks
            clean_route_names = {k.replace('**', ''): v for k, v in transport_by_route.items()}
            
            selected_route = st.selectbox(
                "Select route to view transportation options:",
                options=list(clean_route_names.keys()),
                key="transport_route_selector"
            )
            
            if selected_route and selected_route in clean_route_names:
                st.subheader(f"🚗 Transportation Options for {selected_route}")
                for i, transport in enumerate(clean_route_names[selected_route], 1):
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="
                                border: 2px solid #e0e0e0;
                                border-radius: 15px;
                                padding: 20px;
                                margin: 15px 0;
                                background: linear-gradient(135deg, #fff3e0 0%, #ffcc80 100%);
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            ">
                                <h3 style="margin: 0 0 15px 0; color: #e65100; font-size: 1.4em;">🚗 Option {i}: {transport['Type']}</h3>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                    <p style="margin: 5px 0;"><strong>🚆 Type:</strong> {transport['Type']}</p>
                                    <p style="margin: 5px 0;"><strong>🏢 Service:</strong> {transport['Service']}</p>
                                    <p style="margin: 5px 0;"><strong>📏 Distance:</strong> {transport['Distance']}</p>
                                    <p style="margin: 5px 0;"><strong>⏱️ Duration:</strong> {transport['Duration']}</p>
                                    <p style="margin: 5px 0;"><strong>💰 Cost:</strong> {transport['Cost']}</p>
                                    <p style="margin: 5px 0;"><strong>🔄 Frequency:</strong> {transport['Frequency']}</p>
                                </div>
                                <div style="margin-top: 10px;">
                                    <p style="margin: 5px 0;"><strong>✅ Pros:</strong> {transport['Pros']}</p>
                                    <p style="margin: 5px 0;"><strong>❌ Cons:</strong> {transport['Cons']}</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        
        else:
            # Clean display of raw transportation content
            transport_content = st.session_state.travel_state.get('transportation', '')
            if transport_content:
                # Clean up JSON-like formatting and display as readable text
                import re
                cleaned_content = transport_content
                
                # Remove JSON brackets and quotes
                cleaned_content = re.sub(r'\{[^}]*\}', '', cleaned_content)
                cleaned_content = re.sub(r'\[[^\]]*\]', '', cleaned_content)
                cleaned_content = re.sub(r'"([^"]+)":', r'**\1:**', cleaned_content)
                cleaned_content = re.sub(r'"([^"]+)"', r'\1', cleaned_content)
                cleaned_content = re.sub(r'[{}\[\]"\\]', '', cleaned_content)
                
                # Format as readable sections
                lines = cleaned_content.split('\n')
                formatted_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(','):
                        # Make route headers stand out
                        if '→' in line or 'ROUTE:' in line:
                            formatted_lines.append(f"### 🚗 {line.replace('ROUTE:', '').strip()}")
                        elif ':' in line and len(line.split(':')) == 2:
                            key, value = line.split(':', 1)
                            formatted_lines.append(f"**{key.strip()}:** {value.strip()}")
                        elif line:
                            formatted_lines.append(line)
                
                if formatted_lines:
                    st.markdown('\n\n'.join(formatted_lines))
                else:
                    st.info("Transportation information is being processed. Details will be available in your final itinerary.")
            else:
                st.info("No transportation data available. Transportation options will be included in your final itinerary.")
        
        if st.button("Get Travel Tips & Budget"):
            st.session_state.current_step = 8
            st.rerun()
    
    # Travel Tips & Budget
    if st.session_state.current_step >= 8:
        st.header("💰 Travel Tips & Budget")
        
        if 'travel_tips' not in st.session_state.travel_state:
            with st.spinner("Preparing travel tips and budget information..."):
                try:
                    response = llm.invoke(travel_tips_prompt.format_messages(
                        country=st.session_state.travel_state['arrival_country'],
                        cities=', '.join(st.session_state.travel_state['selected_cities']),
                        start_date=st.session_state.travel_state['travel_start_date'],
                        end_date=st.session_state.travel_state['travel_end_date'],
                        interests=', '.join(st.session_state.travel_state['interests'])
                    ))
                    st.session_state.travel_state['travel_tips'] = response.content
                except Exception as e:
                    st.error(f"Error getting travel tips: {e}")
                    return
        
        # Parse and display travel tips
        tips_content = st.session_state.travel_state['travel_tips']
        
        # Check if structured format exists
        has_structured = 'PACKING_START' in tips_content or 'CULTURAL_START' in tips_content or 'BUDGET_START' in tips_content
        
        if not has_structured:
            # Display raw content in readable format
            st.markdown(tips_content)
        else:
            # Packing Suggestions
            if 'PACKING_START' in tips_content:
                st.subheader("🎒 Packing Suggestions")
                packing_section = tips_content.split('PACKING_START')[1].split('PACKING_END')[0]
                
                col1, col2 = st.columns(2)
                lines = packing_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if 'Essential:' in line:
                        with col1:
                            st.write(f"**🎯 Essential:** {line.split('Essential:')[1].strip()}")
                    elif 'Clothing:' in line:
                        with col1:
                            st.write(f"**👕 Clothing:** {line.split('Clothing:')[1].strip()}")
                    elif 'Documents:' in line:
                        with col1:
                            st.write(f"**📄 Documents:** {line.split('Documents:')[1].strip()}")
                    elif 'Electronics:' in line:
                        with col2:
                            st.write(f"**📱 Electronics:** {line.split('Electronics:')[1].strip()}")
                    elif 'Health:' in line:
                        with col2:
                            st.write(f"**💊 Health:** {line.split('Health:')[1].strip()}")
        
            # Cultural Tips
            if 'CULTURAL_START' in tips_content:
                st.subheader("🎭 Local Tips & Cultural Notes")
                cultural_section = tips_content.split('CULTURAL_START')[1].split('CULTURAL_END')[0]
                
                col1, col2 = st.columns(2)
                lines = cultural_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if 'Customs:' in line:
                        with col1:
                            st.write(f"**🌏 Customs:** {line.split('Customs:')[1].strip()}")
                    elif 'Language:' in line:
                        with col1:
                            st.write(f"**🗣️ Language:** {line.split('Language:')[1].strip()}")
                    elif 'Currency:' in line:
                        with col1:
                            st.write(f"**💵 Currency:** {line.split('Currency:')[1].strip()}")
                    elif 'Tipping:' in line:
                        with col2:
                            st.write(f"**💰 Tipping:** {line.split('Tipping:')[1].strip()}")
                    elif 'Dress:' in line:
                        with col2:
                            st.write(f"**👗 Dress Code:** {line.split('Dress:')[1].strip()}")
        
            # Time Management
            if 'TIME_START' in tips_content:
                st.subheader("⏰ Time Management Suggestions")
                time_section = tips_content.split('TIME_START')[1].split('TIME_END')[0]
                
                col1, col2 = st.columns(2)
                lines = time_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if 'Planning:' in line:
                        with col1:
                            st.write(f"**📅 Planning:** {line.split('Planning:')[1].strip()}")
                    elif 'Booking:' in line:
                        with col1:
                            st.write(f"**📆 Booking:** {line.split('Booking:')[1].strip()}")
                    elif 'Transport:' in line:
                        with col1:
                            st.write(f"**🚗 Transport:** {line.split('Transport:')[1].strip()}")
                    elif 'Activities:' in line:
                        with col2:
                            st.write(f"**🎯 Activities:** {line.split('Activities:')[1].strip()}")
                    elif 'Rest:' in line:
                        with col2:
                            st.write(f"**😴 Rest:** {line.split('Rest:')[1].strip()}")
        
            # Budget Overview
            if 'BUDGET_START' in tips_content:
                st.subheader("💰 Budget Overview")
                budget_section = tips_content.split('BUDGET_START')[1].split('BUDGET_END')[0]
                
                # Create budget table
                budget_data = []
                lines = budget_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if 'Accommodation:' in line:
                        budget_data.append(['🏨 Accommodation', line.split('Accommodation:')[1].strip()])
                    elif 'Food:' in line:
                        budget_data.append(['🍽️ Food', line.split('Food:')[1].strip()])
                    elif 'Transport:' in line:
                        budget_data.append(['🚗 Transport', line.split('Transport:')[1].strip()])
                    elif 'Activities:' in line:
                        budget_data.append(['🎯 Activities', line.split('Activities:')[1].strip()])
                    elif 'Shopping:' in line:
                        budget_data.append(['🛒 Shopping', line.split('Shopping:')[1].strip()])
                    elif 'Emergency:' in line:
                        budget_data.append(['🆘 Emergency', line.split('Emergency:')[1].strip()])
                    elif 'Total:' in line:
                        budget_data.append(['💵 **Total Estimated**', f"**{line.split('Total:')[1].strip()}**"])
                
                for category, amount in budget_data:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.write(category)
                    with col2:
                        st.write(amount)
        
            # Hotel Tips
            if 'HOTELS_TIPS_START' in tips_content:
                st.subheader("🏨 Hotel Booking Tips")
                hotels_tips_section = tips_content.split('HOTELS_TIPS_START')[1].split('HOTELS_TIPS_END')[0]
                
                col1, col2 = st.columns(2)
                lines = hotels_tips_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if 'Budget:' in line:
                        with col1:
                            st.write(f"**💰 Budget Hotels:** {line.split('Budget:')[1].strip()}")
                    elif 'Luxury:' in line:
                        with col1:
                            st.write(f"**⭐ Luxury Hotels:** {line.split('Luxury:')[1].strip()}")
                    elif 'Location:' in line:
                        with col1:
                            st.write(f"**📍 Best Locations:** {line.split('Location:')[1].strip()}")
                    elif 'Booking:' in line:
                        with col2:
                            st.write(f"**📅 Booking Tips:** {line.split('Booking:')[1].strip()}")
                    elif 'Deals:' in line:
                        with col2:
                            st.write(f"**🎯 Finding Deals:** {line.split('Deals:')[1].strip()}")
        
            # Restaurant Tips
            if 'RESTAURANTS_TIPS_START' in tips_content:
                st.subheader("🍽️ Dining Recommendations")
                restaurants_tips_section = tips_content.split('RESTAURANTS_TIPS_START')[1].split('RESTAURANTS_TIPS_END')[0]
                
                col1, col2 = st.columns(2)
                lines = restaurants_tips_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if 'Local:' in line:
                        with col1:
                            st.write(f"**🏠 Local Cuisine:** {line.split('Local:')[1].strip()}")
                    elif 'Fine:' in line:
                        with col1:
                            st.write(f"**🍾 Fine Dining:** {line.split('Fine:')[1].strip()}")
                    elif 'Street:' in line:
                        with col1:
                            st.write(f"**🥘 Street Food:** {line.split('Street:')[1].strip()}")
                    elif 'Reservations:' in line:
                        with col2:
                            st.write(f"**📞 Reservations:** {line.split('Reservations:')[1].strip()}")
                    elif 'Budget:' in line:
                        with col2:
                            st.write(f"**💵 Budget Dining:** {line.split('Budget:')[1].strip()}")
        
        if st.button("Create Final Itinerary"):
            st.session_state.current_step = 9
            st.rerun()
    
    # Final Itinerary
    if st.session_state.current_step >= 9:
        st.header("📋 Your Complete Itinerary")
        
        if 'final_itinerary' not in st.session_state.travel_state:
            with st.spinner("Creating your personalized itinerary..."):
                try:
                    city_date_info = "\n".join([
                        f"- {city}: {info['days']} days ({info['start_date']} to {info['end_date']})"
                        for city, info in st.session_state.travel_state['city_date_distribution'].items()
                    ])
                    
                    response = llm.invoke(final_itinerary_prompt.format_messages(
                        country=st.session_state.travel_state['arrival_country'],
                        start_date=st.session_state.travel_state['travel_start_date'],
                        end_date=st.session_state.travel_state['travel_end_date'],
                        city_date_info=city_date_info,
                        hotels=st.session_state.travel_state.get('hotels', ''),
                        restaurants=st.session_state.travel_state.get('restaurants', ''),
                        transportation=st.session_state.travel_state.get('transportation', ''),
                        gear=st.session_state.travel_state.get('gear', ''),
                        tips=st.session_state.travel_state.get('travel_tips', '')
                    ))
                    st.session_state.travel_state['final_itinerary'] = response.content
                except Exception as e:
                    st.error(f"Error creating itinerary: {e}")
                    return
        
        # Display trip summary
        st.subheader("🎯 Trip Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Destination", st.session_state.travel_state['arrival_country'])
            st.metric("Duration", f"{st.session_state.travel_state['total_days']} days")
        
        with col2:
            st.metric("Start Date", st.session_state.travel_state['travel_start_date'])
            st.metric("End Date", st.session_state.travel_state['travel_end_date'])
        
        with col3:
            st.metric("Cities", len(st.session_state.travel_state['selected_cities']))
            st.metric("Interests", len(st.session_state.travel_state['interests']))
        
        # Display itinerary in table format
        st.subheader("📅 Detailed Day-by-Day Itinerary")
        
        # Parse itinerary into structured format
        itinerary_content = st.session_state.travel_state['final_itinerary']
        
        # Try to parse structured format first
        days = []
        if 'DAY_START' in itinerary_content:
            lines = itinerary_content.split('\n')
            current_day = {}
            
            for line in lines:
                line = line.strip()
                if 'Day:' in line:
                    current_day['Day'] = line.split('Day:')[1].strip()
                elif 'Date:' in line:
                    current_day['Date'] = line.split('Date:')[1].strip()
                elif 'City:' in line:
                    current_day['City'] = line.split('City:')[1].strip()
                elif 'Weather:' in line:
                    current_day['Weather'] = line.split('Weather:')[1].strip()
                elif 'Hotel:' in line:
                    current_day['Hotel'] = line.split('Hotel:')[1].strip()
                elif 'Morning:' in line:
                    current_day['Morning'] = line.split('Morning:')[1].strip()
                elif 'Lunch:' in line:
                    current_day['Lunch'] = line.split('Lunch:')[1].strip()
                elif 'Afternoon:' in line:
                    current_day['Afternoon'] = line.split('Afternoon:')[1].strip()
                elif 'Dinner:' in line:
                    current_day['Dinner'] = line.split('Dinner:')[1].strip()
                elif 'Evening:' in line:
                    current_day['Evening'] = line.split('Evening:')[1].strip()
                elif 'Travel:' in line:
                    current_day['Travel'] = line.split('Travel:')[1].strip()
                elif 'DAY_END' in line and current_day:
                    days.append(current_day.copy())
                    current_day = {}
        
        # Display itinerary
        if days:
            
            for day in days:
                with st.expander(f"📅 Day {day.get('Day', 'N/A')} - {day.get('Date', 'N/A')} - {day.get('City', 'N/A')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"🌤️ **Weather:** {day.get('Weather', 'N/A')}")
                        st.write(f"🏨 **Hotel:** {day.get('Hotel', 'N/A')}")
                    with col2:
                        if day.get('Travel'):
                            st.write(f"🚗 **Travel:** {day.get('Travel', 'N/A')}")
                    
                    # Time table format
                    st.markdown("### 📋 Daily Schedule")
                    
                    # Create a table-like structure
                    schedule_data = [
                        ["🌅 Morning (8:00-12:00)", day.get('Morning', 'N/A')],
                        ["🍽️ Lunch (12:00-14:00)", day.get('Lunch', 'N/A')],
                        ["☀️ Afternoon (14:00-18:00)", day.get('Afternoon', 'N/A')],
                        ["🌙 Dinner (19:00+)", day.get('Dinner', 'N/A')],
                        ["🌃 Evening", day.get('Evening', 'N/A')]
                    ]
                    
                    for time_slot, activity in schedule_data:
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.write(f"**{time_slot}**")
                        with col2:
                            st.write(activity)
        else:
            # Fallback to original format
            st.markdown(st.session_state.travel_state['final_itinerary'])
        
        # Download option
        st.download_button(
            label="📄 Download Itinerary",
            data=st.session_state.travel_state['final_itinerary'],
            file_name=f"itinerary_{st.session_state.travel_state['arrival_country'].replace(' ', '_')}.txt",
            mime="text/plain"
        )
        
        if st.button("🔄 Plan Another Trip"):
            st.session_state.current_step = 1
            st.session_state.travel_state = {}
            st.rerun()

if __name__ == "__main__":
    main()
