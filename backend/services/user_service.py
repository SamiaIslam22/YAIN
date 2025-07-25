# ------------------------------------------------------------
# © 2025 Samia Islam. All rights reserved.
# This file is part of the "YAIN" project.
# Released under CC BY-NC 4.0 license.
# For demo and educational use only — not for commercial use.
# ------------------------------------------------------------

# User Service for Spotify Authentication and Profile Management
# This module handles user authentication with Spotify, profile creation,
# and music preference analysis.

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
import time
from datetime import datetime, timedelta

# 🔐 Spotify OAuth Configuration
SPOTIFY_SCOPE = [
    'user-read-private',           # Read user profile
    'user-read-email',             # Read user email
    'user-top-read',               # Read top artists and tracks
    'user-library-read',           # Read saved tracks
    'playlist-read-private',       # Read private playlists
    'playlist-read-collaborative', # Read collaborative playlists
    'user-read-recently-played',   # Read listening history
]

# 🗄️ In-memory user storage (replace with database later)
user_profiles = {}

# Fix the SpotifyUserAuth class in user_service.py

# Fix the SpotifyUserAuth class in user_service.py

class SpotifyUserAuth:
    """🔐 Handle Spotify OAuth and user authentication"""
    
    def __init__(self):  # ✅ PROPERLY INDENTED UNDER CLASS
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        # 🔧 FIX: Correct redirect URI for both dev and production
        if os.getenv('ENVIRONMENT') == 'production' or 'render.com' in os.getenv('RENDER_EXTERNAL_URL', ''):
            self.redirect_uri = 'https://yain.onrender.com/callback'
        else:
            self.redirect_uri = 'http://localhost:5000/callback'
        
        print(f"🔗 Using redirect URI: {self.redirect_uri}")
        print(f"🔑 Client ID: {'✅ Set' if self.client_id else '❌ Missing'}")
        print(f"🔒 Client Secret: {'✅ Set' if self.client_secret else '❌ Missing'}")
    
    def get_auth_url(self, user_id):
        """Get Spotify authorization URL for user"""
        try:
            if not self.client_id or not self.client_secret:
                print("❌ Missing Spotify credentials!")
                return None
                
            sp_oauth = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=' '.join(SPOTIFY_SCOPE),
                state=user_id,  # Use user_id as state for security
                show_dialog=True
            )
            
            auth_url = sp_oauth.get_authorize_url()
            print(f"✅ Generated auth URL: {auth_url[:50]}...")
            return auth_url
            
        except Exception as e:
            print(f"❌ Error creating auth URL: {e}")
            return None
    
    def get_user_token(self, code, user_id):
        """Exchange authorization code for access token"""
        try:
            sp_oauth = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=' '.join(SPOTIFY_SCOPE),
                state=user_id
            )
            
            token_info = sp_oauth.get_access_token(code)
            print(f"✅ Token obtained for user: {user_id}")
            return token_info
            
        except Exception as e:
            print(f"❌ Error getting access token: {e}")
            return None
class UserProfileAnalyzer:
    """🎭 Analyze user's Spotify profile and extract music preferences"""
    
    def __init__(self, access_token):
        self.spotify = spotipy.Spotify(auth=access_token)
        
    def get_user_profile(self):
        """Get basic user profile information"""
        try:
            user_info = self.spotify.current_user()
            return {
                'id': user_info['id'],
                'display_name': user_info.get('display_name', 'User'),
                'email': user_info.get('email'),
                'followers': user_info.get('followers', {}).get('total', 0),
                'country': user_info.get('country'),
                'image': user_info.get('images', [{}])[0].get('url') if user_info.get('images') else None
            }
        except Exception as e:
            print(f"❌ Error getting user profile: {e}")
            return None
    
    def get_top_artists(self, time_range='medium_term', limit=50):
        """Get user's top artists (short/medium/long term)"""
        try:
            results = self.spotify.current_user_top_artists(
                time_range=time_range, 
                limit=limit
            )
            
            artists = []
            for artist in results['items']:
                artists.append({
                    'name': artist['name'],
                    'genres': artist['genres'],
                    'popularity': artist['popularity'],
                    'spotify_url': artist['external_urls']['spotify']
                })
                
            return artists
            
        except Exception as e:
            print(f"❌ Error getting top artists: {e}")
            return []
    
    def get_top_tracks(self, time_range='medium_term', limit=50):
        """Get user's top tracks (short/medium/long term)"""
        try:
            results = self.spotify.current_user_top_tracks(
                time_range=time_range, 
                limit=limit
            )
            
            tracks = []
            for track in results['items']:
                tracks.append({
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'popularity': track['popularity'],
                    'spotify_url': track['external_urls']['spotify']
                })
                
            return tracks
            
        except Exception as e:
            print(f"❌ Error getting top tracks: {e}")
            return []
    
    def get_saved_tracks(self, limit=50):
        """Get user's saved (liked) tracks"""
        try:
            results = self.spotify.current_user_saved_tracks(limit=limit)
            
            tracks = []
            for item in results['items']:
                track = item['track']
                tracks.append({
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'added_at': item['added_at'],
                    'spotify_url': track['external_urls']['spotify']
                })
                
            return tracks
            
        except Exception as e:
            print(f"❌ Error getting saved tracks: {e}")
            return []
    
    def get_user_playlists(self, limit=20):
        """Get user's playlists"""
        try:
            results = self.spotify.current_user_playlists(limit=limit)
            
            playlists = []
            for playlist in results['items']:
                # Skip empty playlists
                if playlist['tracks']['total'] > 0:
                    playlists.append({
                        'name': playlist['name'],
                        'description': playlist.get('description', ''),
                        'track_count': playlist['tracks']['total'],
                        'public': playlist['public'],
                        'spotify_url': playlist['external_urls']['spotify'],
                        'id': playlist['id']
                    })
                    
            return playlists
            
        except Exception as e:
            print(f"❌ Error getting playlists: {e}")
            return []
    
    def analyze_music_preferences(self):
        """🎯 Comprehensive analysis of user's music taste"""
        print("🔍 Analyzing user's music preferences...")
        
        # Get all data
        top_artists_short = self.get_top_artists('short_term', 20)  # Last 4 weeks
        top_artists_medium = self.get_top_artists('medium_term', 30)  # Last 6 months
        top_tracks_short = self.get_top_tracks('short_term', 20)
        top_tracks_medium = self.get_top_tracks('medium_term', 30)
        saved_tracks = self.get_saved_tracks(50)
        playlists = self.get_user_playlists(15)
        
        # Analyze genres
        all_genres = []
        for artist in top_artists_short + top_artists_medium:
            all_genres.extend(artist['genres'])
        
        # Count genre frequency
        genre_counts = {}
        for genre in all_genres:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Get top genres
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Analyze favorite artists
        artist_counts = {}
        for artist in top_artists_short + top_artists_medium:
            name = artist['name']
            artist_counts[name] = artist_counts.get(name, 0) + 1
        
        top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        
        # Create user music profile
        music_profile = {
            'top_genres': [genre for genre, count in top_genres],
            'favorite_artists': [artist for artist, count in top_artists],
            'recent_favorites': [track['name'] + ' by ' + track['artist'] for track in top_tracks_short[:10]],
            'all_time_favorites': [track['name'] + ' by ' + track['artist'] for track in top_tracks_medium[:10]],
            'saved_songs_count': len(saved_tracks),
            'playlist_count': len(playlists),
            'music_diversity': len(set(all_genres)),  # How diverse their taste is
            'analysis_date': datetime.now().isoformat()
        }
        
        print(f"🎵 Analysis complete! Found {len(top_genres)} genres, {len(top_artists)} artists")
        return music_profile

class UserPreferenceManager:
    """💾 Manage user preferences and personalized recommendations"""
    
    @staticmethod
    def save_user_profile(user_id, profile_data, music_preferences):
        """Save user profile and music preferences"""
        # 🔧 FIX 1: Use consistent naming - 'preferences' not 'music_preferences'
        user_profiles[user_id] = {
            'profile': profile_data,
            'preferences': music_preferences,  # ✅ Fixed: consistent naming
            'last_updated': datetime.now().isoformat(),
            'song_suggestions_history': []  # Track what we've suggested
        }
        
        print(f"💾 Saved profile for user {user_id}")
        print(f"🎵 Top genres: {music_preferences.get('top_genres', [])[:3]}")
        print(f"🎤 Favorite artists: {music_preferences.get('favorite_artists', [])[:3]}")
        return True
    
    @staticmethod
    def get_user_profile(user_id):
        """Get user profile and preferences"""
        user_data = user_profiles.get(user_id)
        if user_data:
            print(f"📊 Retrieved profile for {user_id}")
            print(f"🎵 Genres available: {len(user_data.get('preferences', {}).get('top_genres', []))}")
            print(f"🎤 Artists available: {len(user_data.get('preferences', {}).get('favorite_artists', []))}")
        else:
            print(f"❌ No profile found for user {user_id}")
        return user_data
    
    @staticmethod
    def update_suggestion_history(user_id, suggested_song):
        """Track what songs we've suggested to this user"""
        if user_id in user_profiles:
            user_profiles[user_id]['song_suggestions_history'].append({
                'song': suggested_song,
                'timestamp': datetime.now().isoformat()
            })
    
    @staticmethod
    def get_personalized_search_terms(user_id, emotion_type):
        """🎯 Generate personalized search terms based on user preferences"""
        user_data = user_profiles.get(user_id)
        
        if not user_data:
            print(f"❌ No user data found for personalized search: {user_id}")
            return None
        
        # 🔧 FIX 2: Use correct data structure key
        preferences = user_data.get('preferences', {})  # ✅ Fixed: was 'music_preferences'
        
        if not preferences:
            print(f"❌ No preferences found for user {user_id}")
            return None
        
        # Base search terms from emotion
        base_terms = []
        
        # Add user's favorite genres
        top_genres = preferences.get('top_genres', [])[:5]
        print(f"🎭 User's top genres for {emotion_type}: {top_genres}")
        
        for genre in top_genres:
            base_terms.append(f"{emotion_type} {genre}")
        
        # Add user's favorite artists
        top_artists = preferences.get('favorite_artists', [])[:3]
        print(f"🎤 User's top artists for {emotion_type}: {top_artists}")
        
        for artist in top_artists:
            base_terms.append(f"songs like {artist}")
        
        # Add genre-specific emotional terms
        if top_genres:
            main_genre = top_genres[0] if top_genres else 'pop'
            base_terms.append(f"{emotion_type} {main_genre} music")
        
        print(f"🎯 Generated {len(base_terms)} personalized search terms: {base_terms}")
        return base_terms[:8]  # Return top 8 personalized search terms

# 🎯 Initialize OAuth handler
try:
    spotify_auth = SpotifyUserAuth()
    print("✅ Spotify auth handler initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Spotify auth: {e}")
    # Create a dummy handler so imports don't fail
    spotify_auth = None

def initialize_spotify_auth():
    """Initialize Spotify auth handler with error handling"""
    try:
        auth_handler = SpotifyUserAuth()
        if not auth_handler.client_id or not auth_handler.client_secret:
            print("❌ Spotify credentials missing - auth disabled")
            return None
        print("✅ Spotify auth handler initialized successfully")
        return auth_handler
    except Exception as e:
        print(f"❌ Error initializing Spotify auth: {e}")
        return None

spotify_auth = initialize_spotify_auth()

# 🎯 Initialize OAuth handler
spotify_auth = initialize_spotify_auth()

def create_user_profile(access_token):
    """🔍 Create complete user profile from Spotify data"""
    try:
        analyzer = UserProfileAnalyzer(access_token)
        
        # Get basic profile
        profile_data = analyzer.get_user_profile()
        if not profile_data:
            print("❌ Failed to get profile data")
            return None
        
        # Analyze music preferences
        music_preferences = analyzer.analyze_music_preferences()
        if not music_preferences:
            print("❌ Failed to analyze music preferences")
            return None
        
        # Save everything
        user_id = profile_data['id']
        UserPreferenceManager.save_user_profile(user_id, profile_data, music_preferences)
        
        # Return consistent structure for immediate use
        return {
            'user_id': user_id,
            'profile': profile_data,
            'preferences': music_preferences
        }
        
    except Exception as e:
        print(f"❌ Error creating user profile: {e}")
        import traceback
        traceback.print_exc()
        return None