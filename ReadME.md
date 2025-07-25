<img width="1322" height="652" alt="image" src="https://github.com/user-attachments/assets/c637a41b-e948-4eaf-b769-03faa9d6cd7f" />


# 🎧 YAIN - Your AI DJ with Attitude

YAIN is a mood-based music recommender that combines Spotify, YouTube, and Gemini AI to suggest songs that match your vibe. Just tell Yain how you feel, and it'll drop a perfect track—never repeats, always hits. 🔥

> 🚧 **Prototype Note:**
> This is an early-stage prototype built for demonstration and creative exploration.
> More features and enhancements are in progress. Stay tuned! 🛠️

## 🔥 Features

- 🎭 Mood detection (50+ emotions supported)
- 🧠 Memory system (avoids repeats)
- 🎯 Personalized Spotify-based recommendations (if connected)
- 📺 YouTube + 🎵 Spotify results
- 💬 Fun, witty personality with music puns
- 🌍 Multi-language support (Bengali, Tamil, Afrobeats, K-pop, and more)

## 📦 Tech Stack

- **Backend**: Python + Flask
- **APIs**: Spotipy, YouTube Data API, Google Gemini AI
- **Frontend**: HTML + CSS + JavaScript
- **Features**: CORS, caching, parallel processing

## 🚀 Quick Start

1. Clone the repository
2. Install requirements: `pip install -r requirements.txt`
3. Set up environment variables (see below)
4. Set Flask app: `export FLASK_APP=app.py` (Linux/Mac) or `set FLASK_APP=app.py` (Windows)
5. Run: `flask run` or `python -m flask run`
6. Open `index.html` in browser

## 🔑 Required API Keys

- **Spotify Web API** (for music search)
- **YouTube Data API** (for video links)  
- **Google Gemini API** (for AI responses)

Set these in your environment:
```bash
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_secret
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key
FLASK_APP=app.py
