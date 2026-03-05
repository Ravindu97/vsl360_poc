from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.getenv("groq_api_key")

llm = ChatGroq(
    temperature=0.3,
    groq_api_key=groq_api_key,
    model_name="llama-3.1-8b-instant"
)

virtual_doctor_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Virtual Travel Doctor providing first-aid guidance and medical advice for travelers.

IMPORTANT GUIDELINES:
- Provide immediate first-aid steps for common travel health issues
- Assess symptom severity (Mild/Moderate/Severe/Emergency)
- Recommend when to seek immediate medical attention
- Give practical advice for travelers
- Include preventive measures
- Always add medical disclaimer

For EMERGENCY symptoms (chest pain, difficulty breathing, severe bleeding, loss of consciousness):
- Immediately advise calling emergency services
- Provide critical first-aid steps
- Emphasize urgency

Format your response as JSON:
{{
    "severity": "Mild/Moderate/Severe/Emergency",
    "condition": "Likely condition name",
    "immediate_actions": ["Step 1", "Step 2", "Step 3"],
    "first_aid": ["Detailed first aid instruction 1", "Instruction 2"],
    "when_to_seek_help": "Clear guidance on when to visit hospital",
    "medications": ["Over-the-counter medication suggestions"],
    "prevention": ["Preventive measures for future"],
    "travel_tips": ["Specific advice for travelers"],
    "emergency_warning": "true/false",
    "disclaimer": "This is general medical information. For serious symptoms, seek immediate professional medical care."
}}

Be concise, clear, and actionable. Prioritize traveler safety."""),
    ("human", "Symptoms: {symptoms}\nLocation: {location}\nDuration: {duration}")
])

def get_virtual_doctor_response(symptoms: str, location: str = "Unknown", duration: str = "Unknown"):
    """Get medical advice and first-aid guidance"""
    try:
        response = llm.invoke(virtual_doctor_prompt.format_messages(
            symptoms=symptoms,
            location=location,
            duration=duration
        ))
        
        import json
        data = json.loads(response.content)
        return data
    except json.JSONDecodeError:
        # Fallback response
        return {
            "severity": "Unknown",
            "condition": "Unable to assess",
            "immediate_actions": ["Seek medical attention if symptoms persist"],
            "first_aid": ["Rest and stay hydrated"],
            "when_to_seek_help": "If symptoms worsen or persist for more than 24 hours",
            "medications": ["Consult a pharmacist or doctor"],
            "prevention": ["Maintain good hygiene"],
            "travel_tips": ["Keep emergency contacts handy"],
            "emergency_warning": "false",
            "disclaimer": "This is general medical information. For serious symptoms, seek immediate professional medical care."
        }
    except Exception as e:
        raise Exception(f"Virtual doctor error: {str(e)}")

def get_common_travel_ailments():
    """Return common travel health issues with quick guidance"""
    return {
        "ailments": [
            {
                "name": "Food Poisoning / Traveler's Diarrhea",
                "symptoms": "Nausea, vomiting, diarrhea, stomach cramps",
                "quick_action": "Stay hydrated with ORS, rest, avoid solid foods initially"
            },
            {
                "name": "Altitude Sickness",
                "symptoms": "Headache, nausea, dizziness, fatigue at high altitude",
                "quick_action": "Descend to lower altitude, rest, drink water, avoid alcohol"
            },
            {
                "name": "Heat Exhaustion",
                "symptoms": "Heavy sweating, weakness, dizziness, nausea",
                "quick_action": "Move to shade, drink water, cool body with wet cloth"
            },
            {
                "name": "Insect Bites / Allergic Reaction",
                "symptoms": "Swelling, itching, redness, pain at bite site",
                "quick_action": "Clean area, apply ice, antihistamine cream, monitor for severe reaction"
            },
            {
                "name": "Motion Sickness",
                "symptoms": "Nausea, dizziness, vomiting during travel",
                "quick_action": "Fresh air, focus on horizon, ginger or anti-nausea medication"
            },
            {
                "name": "Sunburn",
                "symptoms": "Red, painful, hot skin after sun exposure",
                "quick_action": "Cool compress, aloe vera, stay hydrated, avoid further sun"
            },
            {
                "name": "Dehydration",
                "symptoms": "Dry mouth, fatigue, dark urine, dizziness",
                "quick_action": "Drink water/ORS slowly, rest in cool place, avoid caffeine"
            },
            {
                "name": "Minor Cuts / Wounds",
                "symptoms": "Bleeding, open wound from accident",
                "quick_action": "Clean with water, apply pressure, antiseptic, bandage"
            }
        ]
    }

def get_emergency_numbers_by_location(latitude: float, longitude: float):
    """Get emergency numbers based on geolocation"""
    from geopy.geocoders import Nominatim
    
    try:
        geolocator = Nominatim(user_agent="travel_emergency_locator")
        location = geolocator.reverse(f"{latitude}, {longitude}", language='en')
        
        if location and location.raw.get('address'):
            country = location.raw['address'].get('country', '')
            return get_emergency_numbers_by_country(country)
        
        return None
    except Exception as e:
        print(f"Error getting location: {str(e)}")
        return None

def get_emergency_numbers_by_country(country: str):
    """Get emergency numbers for a specific country"""
    emergency_numbers = {
        "United States": {"police": "911", "ambulance": "911", "fire": "911"},
        "United Kingdom": {"police": "999", "ambulance": "999", "fire": "999"},
        "Australia": {"police": "000", "ambulance": "000", "fire": "000"},
        "Canada": {"police": "911", "ambulance": "911", "fire": "911"},
        "India": {"police": "100", "ambulance": "102", "fire": "101"},
        "Germany": {"police": "110", "ambulance": "112", "fire": "112"},
        "France": {"police": "17", "ambulance": "15", "fire": "18"},
        "Italy": {"police": "113", "ambulance": "118", "fire": "115"},
        "Spain": {"police": "091", "ambulance": "061", "fire": "080"},
        "Japan": {"police": "110", "ambulance": "119", "fire": "119"},
        "China": {"police": "110", "ambulance": "120", "fire": "119"},
        "Brazil": {"police": "190", "ambulance": "192", "fire": "193"},
        "Mexico": {"police": "911", "ambulance": "911", "fire": "911"},
        "Russia": {"police": "102", "ambulance": "103", "fire": "101"},
        "South Africa": {"police": "10111", "ambulance": "10177", "fire": "10111"},
        "United Arab Emirates": {"police": "999", "ambulance": "998", "fire": "997"},
        "Saudi Arabia": {"police": "999", "ambulance": "997", "fire": "998"},
        "Singapore": {"police": "999", "ambulance": "995", "fire": "995"},
        "Thailand": {"police": "191", "ambulance": "1669", "fire": "199"},
        "Turkey": {"police": "155", "ambulance": "112", "fire": "110"},
        "South Korea": {"police": "112", "ambulance": "119", "fire": "119"},
        "Indonesia": {"police": "110", "ambulance": "118", "fire": "113"},
        "Malaysia": {"police": "999", "ambulance": "999", "fire": "994"},
        "Philippines": {"police": "117", "ambulance": "911", "fire": "160"},
        "Vietnam": {"police": "113", "ambulance": "115", "fire": "114"},
        "Egypt": {"police": "122", "ambulance": "123", "fire": "180"},
        "Argentina": {"police": "911", "ambulance": "107", "fire": "100"},
        "Chile": {"police": "133", "ambulance": "131", "fire": "132"},
        "Colombia": {"police": "112", "ambulance": "125", "fire": "119"},
        "Peru": {"police": "105", "ambulance": "117", "fire": "116"},
        "New Zealand": {"police": "111", "ambulance": "111", "fire": "111"},
        "Greece": {"police": "100", "ambulance": "166", "fire": "199"},
        "Portugal": {"police": "112", "ambulance": "112", "fire": "112"},
        "Netherlands": {"police": "112", "ambulance": "112", "fire": "112"},
        "Belgium": {"police": "101", "ambulance": "100", "fire": "100"},
        "Switzerland": {"police": "117", "ambulance": "144", "fire": "118"},
        "Austria": {"police": "133", "ambulance": "144", "fire": "122"},
        "Sweden": {"police": "112", "ambulance": "112", "fire": "112"},
        "Norway": {"police": "112", "ambulance": "113", "fire": "110"},
        "Denmark": {"police": "114", "ambulance": "112", "fire": "112"},
        "Finland": {"police": "112", "ambulance": "112", "fire": "112"},
        "Poland": {"police": "997", "ambulance": "999", "fire": "998"},
        "Czech Republic": {"police": "158", "ambulance": "155", "fire": "150"},
        "Ireland": {"police": "999", "ambulance": "999", "fire": "999"},
        "Israel": {"police": "100", "ambulance": "101", "fire": "102"},
        "Pakistan": {"police": "15", "ambulance": "115", "fire": "16"},
        "Bangladesh": {"police": "999", "ambulance": "999", "fire": "999"},
        "Sri Lanka": {"police": "119", "ambulance": "110", "fire": "110"},
        "Nepal": {"police": "100", "ambulance": "102", "fire": "101"},
        "Kenya": {"police": "999", "ambulance": "999", "fire": "999"},
        "Nigeria": {"police": "112", "ambulance": "112", "fire": "112"},
    }
    
    # Try exact match first
    if country in emergency_numbers:
        return {"country": country, "numbers": emergency_numbers[country]}
    
    # Try partial match
    for key in emergency_numbers.keys():
        if country.lower() in key.lower() or key.lower() in country.lower():
            return {"country": key, "numbers": emergency_numbers[key]}
    
    # Default to 112 (European emergency number)
    return {
        "country": country,
        "numbers": {"police": "112", "ambulance": "112", "fire": "112"},
        "note": "112 works in most countries. Verify local emergency numbers."
    }
