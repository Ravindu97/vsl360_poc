import requests
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def search_nearby_medical_centers(latitude: float, longitude: float, radius: int = 5000):
    """
    Search for nearby medical centers using Google Places API
    
    Args:
        latitude: User's current latitude
        longitude: User's current longitude
        radius: Search radius in meters (default 5000m = 5km)
        
    Returns:
        list: List of medical centers with contact details or fallback data
    """
    try:
        print(f"Searching medical centers at: {latitude}, {longitude}")
        print(f"API Key present: {bool(GOOGLE_MAPS_API_KEY)}")
        
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{latitude},{longitude}",
            "radius": radius,
            "type": "hospital",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"Response status: {response.status_code}")
        
        data = response.json()
        print(f"API Response: {data.get('status')}")
        print(f"Results count: {len(data.get('results', []))}")
        
        if data.get('status') == 'REQUEST_DENIED' or data.get('status') != 'OK':
            print(f"API Error: {data.get('error_message', 'Unknown error')}")
            print("Returning fallback data with Google Maps link...")
            # Return fallback data with Google Maps search link
            return get_fallback_medical_centers(latitude, longitude)
        
        medical_centers = []
        
        for place in data.get("results", [])[:10]:
            place_id = place.get("place_id")
            
            # Get detailed information including phone number
            details = get_place_details(place_id)
            
            medical_center = {
                "name": place.get("name"),
                "address": place.get("vicinity"),
                "location": {
                    "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                    "lng": place.get("geometry", {}).get("location", {}).get("lng")
                },
                "rating": place.get("rating"),
                "phone": details.get("phone"),
                "website": details.get("website"),
                "open_now": place.get("opening_hours", {}).get("open_now"),
                "types": place.get("types", []),
                "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={place.get('name')}&query_place_id={place_id}"
            }
            
            medical_centers.append(medical_center)
        
        print(f"Returning {len(medical_centers)} medical centers")
        return medical_centers
    
    except Exception as e:
        print(f"Error searching medical centers: {str(e)}")
        import traceback
        traceback.print_exc()
        return get_fallback_medical_centers(latitude, longitude)


def get_fallback_medical_centers(latitude: float, longitude: float):
    """
    Return fallback medical center data with Google Maps search link
    """
    google_maps_search_url = f"https://www.google.com/maps/search/hospitals/@{latitude},{longitude},14z"
    
    return [
        {
            "name": "Search Nearby Hospitals on Google Maps",
            "address": "Click to open Google Maps and find hospitals near your location",
            "location": {"lat": latitude, "lng": longitude},
            "rating": None,
            "phone": None,
            "website": None,
            "open_now": None,
            "types": ["search_link"],
            "google_maps_url": google_maps_search_url,
            "is_fallback": True
        }
    ]



def get_place_details(place_id: str):
    """
    Get detailed information about a place including phone number
    
    Args:
        place_id: Google Place ID
        
    Returns:
        dict: Place details with phone and website
    """
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,international_phone_number,website",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data.get("result", {})
        
        return {
            "phone": result.get("formatted_phone_number") or result.get("international_phone_number"),
            "website": result.get("website")
        }
    
    except Exception as e:
        print(f"Error getting place details: {str(e)}")
        return {"phone": None, "website": None}

def get_emergency_contacts(country: str):
    """
    Get emergency contact numbers for a specific country
    
    Args:
        country: Country name
        
    Returns:
        dict: Emergency contact numbers
    """
    # Common emergency numbers by country
    emergency_numbers = {
        "United States": {"ambulance": "911", "police": "911", "fire": "911"},
        "United Kingdom": {"ambulance": "999", "police": "999", "fire": "999"},
        "India": {"ambulance": "102", "police": "100", "fire": "101"},
        "Australia": {"ambulance": "000", "police": "000", "fire": "000"},
        "Canada": {"ambulance": "911", "police": "911", "fire": "911"},
        "Germany": {"ambulance": "112", "police": "110", "fire": "112"},
        "France": {"ambulance": "15", "police": "17", "fire": "18"},
        "Japan": {"ambulance": "119", "police": "110", "fire": "119"},
        "China": {"ambulance": "120", "police": "110", "fire": "119"},
        "Brazil": {"ambulance": "192", "police": "190", "fire": "193"},
        "Spain": {"ambulance": "112", "police": "112", "fire": "112"},
        "Italy": {"ambulance": "118", "police": "112", "fire": "115"},
        "Mexico": {"ambulance": "065", "police": "911", "fire": "911"},
        "South Africa": {"ambulance": "10177", "police": "10111", "fire": "10111"},
        "Singapore": {"ambulance": "995", "police": "999", "fire": "995"},
        "Thailand": {"ambulance": "1669", "police": "191", "fire": "199"},
        "UAE": {"ambulance": "998", "police": "999", "fire": "997"},
        "Sri Lanka": {"ambulance": "110", "police": "119", "fire": "111"}
    }
    
    return emergency_numbers.get(country, {
        "ambulance": "Check local emergency number",
        "police": "Check local emergency number",
        "fire": "Check local emergency number"
    })
