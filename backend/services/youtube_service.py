# ------------------------------------------------------------
# © 2025 Samia Islam. All rights reserved.
# This file is part of the "YAIN" project.
# Released under CC BY-NC 4.0 license.
# For demo and educational use only — not for commercial use.
# ------------------------------------------------------------

# YouTube API integration module
# Handles video search requests using YouTube Data API v3

import requests
import os

# Initialize YouTube API configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_ENABLED = bool(YOUTUBE_API_KEY)

if not YOUTUBE_ENABLED:
    print("⚠️  YouTube API key not found")

def search_youtube_song(query):
    """
    Search YouTube for a single music video using the provided query
    
    Args:
        query (str): Search term for finding music video
        
    Returns:
        dict: Video metadata including title, URL, thumbnail, and channel
        None: If search fails or no results found
    """
    if not YOUTUBE_ENABLED:
        return None
    
    try:
        # Append search modifier to improve music video results
        search_query = f"{query} official music video"
        
        # YouTube Data API v3 search endpoint
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',                # Request video metadata
            'q': search_query,                 # Search query string
            'type': 'video',                   # Filter to video results only
            'videoCategoryId': '10',           # Music category filter
            'maxResults': 1,                   # Return single best result
            'key': YOUTUBE_API_KEY             # API authentication
        }
        
        # Execute API request
        response = requests.get(url, params=params)
        data = response.json()
        
        # Parse response and extract video data
        if 'items' in data and data['items']:
            video = data['items'][0]
            return {
                'title': video['snippet']['title'],
                'youtube_url': f"https://www.youtube.com/watch?v={video['id']['videoId']}",
                'thumbnail_url': video['snippet']['thumbnails']['medium']['url'],
                'channel': video['snippet']['channelTitle']
            }
            
    except Exception as e:
        print(f"YouTube search error: {e}")
    
    return None