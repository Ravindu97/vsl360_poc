"""
Automatic image generation/fetching for itinerary PDFs.
Uses Unsplash API for free stock photos and fallback placeholder generation.
"""
import base64
import io
import requests
from typing import Optional
from PIL import Image, ImageDraw, ImageFont


UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"
UNSPLASH_PARAMS = {
    "client_id": "YOUR_UNSPLASH_ACCESS_KEY",  # Will use public API as fallback
    "per_page": 1,
    "order_by": "relevant"
}


def _fetch_unsplash_image(query: str, width: int = 800, height: int = 600) -> Optional[str]:
    """
    Fetch a random image from Unsplash based on search query.
    Returns base64 data URI or None.
    """
    try:
        # Using Unsplash's source endpoint which doesn't require auth
        url = f"https://source.unsplash.com/{width}x{height}/?{query}"
        response = requests.get(url, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            mime_type = response.headers.get('content-type', 'image/jpeg')
            img_data = base64.b64encode(response.content).decode('ascii')
            return f"data:{mime_type};base64,{img_data}"
    except Exception as e:
        print(f"Error fetching from Unsplash: {e}")
    
    return None


def _generate_placeholder_image(text: str, width: int = 800, height: int = 600) -> str:
    """
    Generate a simple placeholder image with text.
    Returns base64 data URI.
    """
    try:
        # Create gradient background
        img = Image.new('RGB', (width, height), color=(72, 133, 182))  # Blue gradient
        draw = ImageDraw.Draw(img)
        
        # Try to use a reasonable font, fallback to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        text_color = (255, 255, 255)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill=text_color, font=font)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        img_data = base64.b64encode(buffer.getvalue()).decode('ascii')
        return f"data:image/jpeg;base64,{img_data}"
    except Exception as e:
        print(f"Error generating placeholder: {e}")
        return None


def get_auto_image(query: str, width: int = 800, height: int = 600, allow_placeholder: bool = True) -> Optional[str]:
    """
    Get an image automatically:
    1. Try Unsplash API first
    2. Fallback to placeholder generation
    3. Returns base64 data URI or None
    """
    # Try Unsplash
    img_uri = _fetch_unsplash_image(query, width, height)
    if img_uri:
        return img_uri
    
    # Fallback to placeholder
    if allow_placeholder:
        return _generate_placeholder_image(query, width, height)
    
    return None


def auto_populate_images(trip_data: dict) -> dict:
    """
    Auto-populate cover and day images in trip data.
    Only populates if image_path is empty or not set.
    """
    # Cover image
    if not trip_data.get('cover_image_path'):
        destination = trip_data.get('trip_name', 'travel')
        trip_data['cover_image_path'] = get_auto_image(
            destination, 
            width=1200, 
            height=1200
        )
    
    # Day images
    days = trip_data.get('days', [])
    for day in days:
        if not day.get('image_path'):
            city = day.get('city', f"Day {day.get('day', 1)}")
            day['image_path'] = get_auto_image(
                f"{city} tourism travel",
                width=600,
                height=400
            )
    
    return trip_data
