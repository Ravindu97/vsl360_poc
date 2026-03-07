#!/usr/bin/env python3
"""
Quick test script to generate PDF with auto-populated images.
"""
import sys
import json

sys.path.insert(0, '/Users/ravindufernando/Documents/work/VSL360/poc/backend')

from itinerary_generator_playwright import generate_vsl360_itinerary_pdf_playwright

# Sample test data
test_payload = {
    "trip_name": "Sri Lanka Adventure",
    "customer_name": "Test Customer",
    "destination_country": "Sri Lanka",
    "template_name": "elegant_classic",
    "total_days": 2,
    "total_nights": 1,
    "start_date": "2026-03-15",
    "end_date": "2026-03-17",
    "overview_text": "Embark on an unforgettable journey through Sri Lanka, the Pearl of the Indian Ocean.",
    "location_summary": [
        {"city": "Colombo", "nights": 1}
    ],
    "days": [
        {
            "day": 1,
            "title": "Welcome to Sri Lanka",
            "city": "Colombo",
            "image_path": "",  # Will be auto-generated
            "activities": [
                {"time": "14:00", "description": "Arrive at Bandaranaike International Airport"},
                {"time": "15:00", "description": "Meet VSL 360 representative"}
            ],
            "travel_time": "30 minutes",
            "distance": "35 km",
            "overnight_city": "Colombo"
        },
        {
            "day": 2,
            "title": "Discovering Colombo",
            "city": "Colombo",
            "image_path": "",  # Will be auto-generated
            "activities": [
                {"time": "08:00", "description": "Breakfast at hotel"},
                {"time": "09:00", "description": "Guided city tour"},
                {"time": "12:00", "description": "Lunch at local restaurant"}
            ],
            "travel_time": "N/A",
            "distance": "City tour",
            "overnight_city": "Colombo"
        }
    ],
    "hotels": [
        {
            "night": "Night 1-2",
            "name": "The Kingsbury Hotel",
            "city": "Colombo",
            "room_type": "Deluxe Ocean View"
        }
    ],
    "tour_includes": [
        "Airport transfers",
        "2 nights accommodation",
        "Daily breakfast",
        "Guided city tour"
    ],
    "tour_excludes": [
        "International flights",
        "Travel insurance",
        "Personal expenses"
    ],
    "payment_info": [
        "50% deposit on booking",
        "Balance 30 days before arrival"
    ],
    "cancellation_policy": [
        "Free cancellation up to 45 days before departure",
        "50% refund if cancelled 30-45 days before",
        "No refund within 30 days"
    ]
}

try:
    pdf_path = generate_vsl360_itinerary_pdf_playwright(test_payload)
    print(f"✓ PDF generated successfully!")
    print(f"  Location: {pdf_path}")
except Exception as e:
    print(f"✗ Error generating PDF: {e}")
    import traceback
    traceback.print_exc()
