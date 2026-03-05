# backend/fetch_videos.py
import os
from googleapiclient.discovery import build

# You should store this in your .env file ideally
YOUTUBE_API_KEY = "AIzaSyCFzNRnnuw5w-TVMt5NMnWwJzc5OgutbwY"

def get_related_videos(city_name):
    """
    Searches YouTube for travel guides related to the city.
    Returns a list of video details (title, thumbnail, video_id).
    """
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        print("Warning: No valid YouTube API Key provided.")
        return []

    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

        # Search query: e.g., "Paris travel guide"
        search_query = f"{city_name} travel guide"

        request = youtube.search().list(
            part="snippet",
            maxResults=5,
            q=search_query,
            type="video"
        )
        response = request.execute()

        videos = []
        for item in response.get('items', []):
            video_data = {
                "title": item['snippet']['title'],
                "thumbnail": item['snippet']['thumbnails']['medium']['url'],
                "video_id": item['id']['videoId'],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            }
            videos.append(video_data)
        
        return videos

    except Exception as e:
        print(f"Error fetching YouTube videos: {e}")
        return []