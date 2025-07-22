# ------------------------------------------------------------
# © 2025 Samia Islam. All rights reserved.
# This file is part of the "YAIN" project.
# Released under CC BY-NC 4.0 license.
# For demo and educational use only — not for commercial use.
# ------------------------------------------------------------

# YouTube service for YAIN
# Handles YouTube API interactions for music video searches


import requests
import os

# Configure YouTube
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_ENABLED = bool(YOUTUBE_API_KEY)

if not YOUTUBE_ENABLED:
    print("⚠️  YouTube API key not found")

def search_youtube_song(query):
    """Search for ONE music video on YouTube"""
    if not YOUTUBE_ENABLED:
        return None
    
    try:
        # Add "official music video" to get better results
        search_query = f"{query} official music video"
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': search_query,
            'type': 'video',
            'videoCategoryId': '10',  # Music category
            'maxResults': 1,
            'key': YOUTUBE_API_KEY
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
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